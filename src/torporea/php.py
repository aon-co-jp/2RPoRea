"""PHP (Laravel) -> RPoem server.

Reads `routes/web.php` and `routes/api.php` (api routes get the `/api` prefix), resolves each
handler (closure, `fn() =>`, `[XController::class, 'm']`, `'XController@m'`) and translates the
handler only when its whole body is a single return of something we can translate exactly:

* a string literal, or a concatenation of string literals and route parameters (`'Hi ' . $name`)
* a PHP array literal of scalars / nested arrays, returned as is or via `response()->json([...])`

Everything else becomes HTTP 501 with a TODO naming the original route and file. Business logic
is never claimed as ported. The output keeps the original URLs (it is a migration of an existing
app), served by RPoem's poem-compatible API.
"""
from __future__ import annotations

import json
import os
import re

_ROUTE = re.compile(r"Route::(get|post|put|patch|delete|any)\s*\(\s*(['\"])(.*?)\2\s*,", re.S)
_CTRL_ARR = re.compile(r"\[\s*\\?([\w\\]+)::class\s*,\s*['\"](\w+)['\"]\s*\]")
_CTRL_STR = re.compile(r"['\"]([\w\\]+)@(\w+)['\"]")


def _balanced(text: str, i: int, open_ch: str = "{", close_ch: str = "}"):
    """Index just after the bracket that closes text[i] (which must be open_ch); skips strings."""
    depth, q = 0, None
    while i < len(text):
        c = text[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _strip_comments(t: str) -> str:
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"(?m)^\s*(//|#).*$", "", t)


def _handler_body(text: str, start: int):
    """Returns ('body', php-statements) / ('ctrl', (class, method)) / (None, None) for the handler after start."""
    rest = text[start:]
    m = re.match(r"\s*(?:static\s+)?function\s*\([^)]*\)\s*(?:use\s*\([^)]*\)\s*)?(?::\s*[\w\\?]+\s*)?\{", rest)
    if m:
        b = start + m.end() - 1
        e = _balanced(text, b)
        return ("body", text[b + 1:e - 1]) if e else (None, None)
    m = re.match(r"\s*fn\s*\([^)]*\)\s*(?::\s*[\w\\?]+\s*)?=>", rest)
    if m:
        expr_start = start + m.end()
        depth, i = 0, expr_start
        while i < len(text):
            c = text[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth == 0:
                    break
                depth -= 1
            i += 1
        return "body", "return " + text[expr_start:i].strip() + ";"
    m = _CTRL_ARR.match(rest.lstrip()) or _CTRL_STR.match(rest.lstrip())
    if m:
        return "ctrl", (m.group(1).split("\\")[-1], m.group(2))
    return None, None


def _controller_method(root: str, cls: str, meth: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ("vendor", "node_modules", ".git", "storage")]
        if cls + ".php" in files:
            p = os.path.join(d, cls + ".php")
            t = _strip_comments(open(p, encoding="utf-8", errors="replace").read())
            m = re.search(r"function\s+%s\s*\([^)]*\)\s*(?::\s*[\w\\?]+\s*)?\{" % re.escape(meth), t)
            if m:
                e = _balanced(t, m.end() - 1)
                return (t[m.end():e - 1] if e else None), os.path.relpath(p, root)
            return None, os.path.relpath(p, root)
    return None, None


# --- PHP literal parsing -------------------------------------------------------------------

class _Unsupported(Exception):
    pass


def _tokens(s: str):
    pos = 0
    tok = re.compile(r"""\s*(?:(?P<str>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\$])*")|(?P<num>-?\d+(?:\.\d+)?)|(?P<var>\$\w+)|(?P<op>=>|->|[\[\],.();])|(?P<word>[A-Za-z_]\w*))""")
    while pos < len(s):
        if not s[pos:].strip():
            break
        m = tok.match(s, pos)
        if not m:
            raise _Unsupported(s[pos:pos + 20])
        pos = m.end()
        kind = m.lastgroup
        yield kind, m.group(kind)


def _unquote(lit: str) -> str:
    body = lit[1:-1]
    if lit[0] == "'":
        return body.replace("\\'", "'").replace("\\\\", "\\")
    return bytes(body, "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")


class _P:
    def __init__(self, s, params):
        self.t = list(_tokens(s))
        self.i = 0
        self.params = params

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, val=None):
        k, v = self.peek()
        if val is not None and v != val:
            raise _Unsupported("expected %s got %s" % (val, v))
        self.i += 1
        return k, v

    def value(self):
        k, v = self.peek()
        if v == "[":
            return ("json", self.array())
        if k == "word" and v.lower() in ("true", "false", "null"):
            self.take()
            return ("json", {"true": True, "false": False, "null": None}[v.lower()])
        if k == "num":
            self.take()
            return ("json", float(v) if "." in v else int(v))
        if k == "word" and v == "response":
            self.take(); self.take("("); self.take(")")
            self.take("->"); k2, v2 = self.take()
            if v2 != "json":
                raise _Unsupported("response()->" + v2)
            self.take("(")
            inner = self.value()
            self.take(")")
            if inner[0] != "json":
                raise _Unsupported("json of non-literal")
            return ("json", inner[1])
        return self.concat()

    def concat(self):
        parts = []
        while True:
            k, v = self.take()
            if k == "str":
                parts.append(("lit", _unquote(v)))
            elif k == "var" and v[1:] in self.params:
                parts.append(("param", v[1:]))
            else:
                raise _Unsupported(str(v))
            if self.peek()[1] != ".":
                break
            self.take(".")
        return ("text", parts)

    def array(self):
        self.take("[")
        items, keyed = [], None
        while self.peek()[1] != "]":
            v = self.value()
            if v[0] != "json" and not (v[0] == "text" and all(p[0] == "lit" for p in v[1])):
                raise _Unsupported("non-literal in array")
            val = v[1] if v[0] == "json" else "".join(p[1] for p in v[1])
            if self.peek()[1] == "=>":
                self.take("=>")
                v2 = self.value()
                if v2[0] != "json" and not (v2[0] == "text" and all(p[0] == "lit" for p in v2[1])):
                    raise _Unsupported("non-literal value")
                val2 = v2[1] if v2[0] == "json" else "".join(p[1] for p in v2[1])
                if keyed is False:
                    raise _Unsupported("mixed array")
                keyed = True
                items.append((str(val), val2))
            else:
                if keyed:
                    raise _Unsupported("mixed array")
                keyed = False
                items.append(val)
            if self.peek()[1] == ",":
                self.take(",")
        self.take("]")
        return dict(items) if keyed else items


def translate(body: str, params: list):
    """('json', value) / ('text', parts) for a body that is exactly one return, else None."""
    b = _strip_comments(body).strip()
    m = re.fullmatch(r"return\s+(.*?);?\s*", b, re.S)
    if not m or ";" in m.group(1).rstrip(";").replace("';'", "").replace('";"', ""):
        return None
    try:
        p = _P(m.group(1).rstrip(";"), params)
        v = p.value()
        if p.i != len(p.t):
            return None
        return v
    except (_Unsupported, StopIteration, ValueError, UnicodeError):
        return None


# --- route collection and Rust emission -----------------------------------------------------

def routes(root: str) -> list:
    """[(METHOD, path, params, translation-or-None, source-file)]"""
    out = []
    for rel, prefix in (("routes/web.php", ""), ("routes/api.php", "/api")):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        t = _strip_comments(open(p, encoding="utf-8", errors="replace").read())
        for m in _ROUTE.finditer(t):
            meth, path = m.group(1).upper(), m.group(3)
            full = (prefix + "/" + path.strip("/")).rstrip("/") or "/"
            params = [x.rstrip("?") for x in re.findall(r"\{(\w+\??)\}", full)]
            full = re.sub(r"\{(\w+)\??\}", r":\1", full)
            kind, h = _handler_body(t, m.end())
            src = rel
            body = None
            if kind == "body":
                body = h
            elif kind == "ctrl":
                body, cf = _controller_method(root, *h)
                src = cf or rel
            tr = translate(body, params) if body is not None else None
            for mm in (["GET", "POST", "PUT", "DELETE"] if meth == "ANY" else [meth]):
                out.append((mm, full, params, tr, src))
    return out


def _rs_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def render_main(rts: list) -> str:
    fns, ats, by_path = [], [], {}
    for i, (meth, path, params, tr, src) in enumerate(rts):
        name = "h%d" % i
        if tr is None:
            msg = "TODO: port %s %s from %s (Laravel)" % (meth, path, src)
            body = "hyper_compat::text_response(StatusCode::NOT_IMPLEMENTED, \"text/plain; charset=utf-8\", %s)" % _rs_str(msg)
        elif tr[0] == "json":
            body = "hyper_compat::json_response(StatusCode::OK, &serde_json::from_str::<serde_json::Value>(%s).unwrap())" % _rs_str(json.dumps(tr[1], ensure_ascii=False))
        else:
            pieces = ["s.push_str(%s);" % _rs_str(v) if k == "lit" else "s.push_str(params.get(%s).unwrap_or(\"\"));" % _rs_str(v) for k, v in tr[1]]
            body = "{ let mut s = String::new(); %s hyper_compat::html_response(StatusCode::OK, s) }" % " ".join(pieces)
        fns.append("/// %s %s <- %s\n#[open_runo_poem_compat_macro::handler]\nasync fn %s(_req: Request, params: Params) -> Response {\n    let _ = &params;\n    %s\n}\n" % (meth, path, src, name, body))
        helper = {"GET": "get", "POST": "post", "PUT": "put", "DELETE": "delete"}.get(meth)
        if helper:
            by_path.setdefault(path, []).append("%s(%s())" % (helper, name))
    for path, hs in by_path.items():
        for h in hs:
            ats.append("        .at(%s, %s)" % (_rs_str(path), h))
    return ("//! 2RPoRea が PHP(Laravel) から生成した RPoem サーバー。訳せた return だけ本体あり、他は 501。\n"
            "#![allow(unused_variables, dead_code)]\n"
            "use open_runo_poem_compat::{delete, get, hyper_compat, post, put, Params, Request, Response, Route, Server, StatusCode, TcpListener};\n\n"
            + "\n".join(fns) +
            "\n#[tokio::main]\nasync fn main() {\n    let port: u16 = std::env::var(\"PORT\").ok().and_then(|p| p.parse().ok()).unwrap_or(3002);\n"
            "    let app = Route::new()\n" + "\n".join(ats) + ";\n"
            "    let (addr, handle) = Server::new(TcpListener::bind(([127, 0, 0, 1], port))).run(app).await.expect(\"bind\");\n"
            "    println!(\"listening on {addr}\");\n    handle.await.ok();\n}\n")


def write(root: str, out: str, rpoem_path: str = "F:/RPoem") -> dict:
    rts = routes(root)
    rp = os.path.abspath(rpoem_path).replace("\\", "/")
    os.makedirs(os.path.join(out, "src"), exist_ok=True)
    with open(os.path.join(out, "Cargo.toml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('[package]\nname = "php-ported"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\n'
                'open-runo-poem-compat = { path = "%s/crates/open-runo-poem-compat" }\n'
                'open-runo-poem-compat-macro = { path = "%s/crates/open-runo-poem-compat-macro" }\n'
                'serde_json = "1"\ntokio = { version = "1", features = ["rt-multi-thread", "macros", "net"] }\n' % (rp, rp))
    with open(os.path.join(out, "src", "main.rs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_main(rts))
    done = sum(1 for r in rts if r[3] is not None)
    skipped = [r for r in rts if r[0] == "PATCH"]
    return {"routes": len(rts), "translated": done, "todo": len(rts) - done, "patch_unsupported": len(skipped)}
