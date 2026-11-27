"""PHP (Laravel) -> RPoem server.

Reads `routes/web.php` and `routes/api.php` (api routes get the `/api` prefix), resolves each
handler (closure, `fn() =>`, `[XController::class, 'm']`, `'XController@m'`) and translates the
handler only when its body is zero or more simple local assignments (`$x = EXPR;`) followed by
one return of something we can translate exactly:

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
    def __init__(self, s, params, env=None):
        self.t = list(_tokens(s))
        self.i = 0
        self.params = params
        self.env = env or {}

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
        if k == "var" and self.env.get(v[1:], ("", None))[0] == "json":
            self.take()
            return self.env[v[1:]]
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
            elif k == "var" and v[1:] in self.env and self.env[v[1:]][0] == "text":
                parts.extend(self.env[v[1:]][1])
            elif k == "var" and v[1:] in self.params:
                parts.append(("param", v[1:]))
            elif (k == "var" and v == "$request" and self.peek()[1] == "->") or (k == "word" and v == "request" and self.peek()[1] == "("):
                # $request->input('x'[, 'def']) / ->query / ->get / request('x'[, 'def']) -> query-string value
                if v == "$request":
                    self.take("->")
                    _, meth = self.take()
                    if meth not in ("input", "query", "get"):
                        raise _Unsupported("$request->" + str(meth))
                self.take("(")
                k2, name = self.take()
                if k2 != "str":
                    raise _Unsupported("request key")
                default = ""
                if self.peek()[1] == ",":
                    self.take(",")
                    k3, d = self.take()
                    if k3 == "str":
                        default = _unquote(d)
                    elif k3 == "num":
                        default = d
                    else:
                        raise _Unsupported("request default")
                self.take(")")
                parts.append(("query", (_unquote(name), default)))
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


def _split_stmts(b: str):
    """Top-level `;`-separated statements, ignoring `;` inside string literals."""
    out, cur, q, i = [], [], None, 0
    while i < len(b):
        c = b[i]
        if q:
            cur.append(c)
            if c == "\\" and i + 1 < len(b):
                cur.append(b[i + 1])
                i += 2
                continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c
            cur.append(c)
        elif c == ";":
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return out


def _expr(src: str, params: list, env: dict):
    p = _P(src, params, env)
    v = p.value()
    if p.i != len(p.t):
        raise _Unsupported("trailing")
    return v


_IF = re.compile(r"\s*if\s*\(\s*\$(\w+)\s*(===?|!==?)\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*\)\s*\{([^{}]*)\}\s*", re.S)
_ELSE = re.compile(r"\s*else\s*\{([^{}]*)\}\s*$", re.S)


def translate(body: str, params: list):
    """('json', value) / ('text', parts) for a body made only of simple local assignments
    (`$x = EXPR;`) followed by one `return EXPR;`; or ('if', param, negate, literal, then, else) for
    `if ($param == 'lit') { ... } [else { ... }]` on a route parameter followed by the rest. Else None."""
    b = _strip_comments(body).strip()
    m = _IF.match(b)
    if m and m.group(1) in params:
        lit = _P(m.group(3), params, {}).value()
        then = translate(m.group(4), params)
        rest = b[m.end():]
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None or lit[0] != "text" or any(k != "lit" for k, _ in lit[1]):
            return None
        return ("if", m.group(1), m.group(2).startswith("!"), "".join(v for _, v in lit[1]), then, other)
    stmts = _split_stmts(_strip_comments(body).strip())
    if not stmts:
        return None
    env = {}
    try:
        for st in stmts[:-1]:
            m = re.fullmatch(r"\$(\w+)\s*=\s*(.+)", st, re.S)
            if not m or m.group(1) in params or m.group(1) == "this":
                return None
            env[m.group(1)] = _expr(m.group(2), params, env)
        m = re.fullmatch(r"return\s+(.+)", stmts[-1], re.S)
        if not m:
            return None
        return _expr(m.group(1), params, env)
    except (_Unsupported, StopIteration, ValueError, UnicodeError):
        return None


# --- route collection and Rust emission -----------------------------------------------------

def _leaf_rs(tr) -> str:
    if tr[0] == "if":
        cmp_ = "!=" if tr[2] else "=="
        return "if params.get(%s).unwrap_or(\"\") %s %s { %s } else { %s }" % (_rs_str(tr[1]), cmp_, _rs_str(tr[3]), _leaf_rs(tr[4]), _leaf_rs(tr[5]))
    if tr[0] == "json":
        return "hyper_compat::json_response(StatusCode::OK, &serde_json::from_str::<serde_json::Value>(%s).unwrap())" % _rs_str(json.dumps(tr[1], ensure_ascii=False))
    def piece(k, v):
        if k == "lit":
            return "s.push_str(%s);" % _rs_str(v)
        if k == "query":
            return "s.push_str(input.get(%s).map(String::as_str).unwrap_or(%s));" % (_rs_str(v[0]), _rs_str(v[1]))
        return "s.push_str(params.get(%s).unwrap_or(\"\"));" % _rs_str(v)
    pieces = [piece(k, v) for k, v in tr[1]]
    return "{ let mut s = String::new(); %s hyper_compat::html_response(StatusCode::OK, s) }" % " ".join(pieces)


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


_QUERY_HELPER = r"""/// Laravel `$request->input()`: query string merged with the body (form-urlencoded or a JSON object; body wins),
/// body capped at 1 MiB. Only built for handlers that read input.
async fn read_input(req: Request) -> std::collections::HashMap<String, String> {
    use http_body_util::BodyExt;
    let mut input = hyper_compat::query_params(&req);
    let ctype = req.headers().get("content-type").and_then(|v| v.to_str().ok()).unwrap_or("").to_ascii_lowercase();
    let limited = http_body_util::Limited::new(req.into_body(), 1 << 20);
    let Ok(body) = limited.collect().await.map(|c| c.to_bytes()) else { return input };
    if ctype.starts_with("application/json") {
        if let Ok(serde_json::Value::Object(m)) = serde_json::from_slice::<serde_json::Value>(&body) {
            for (k, v) in m {
                input.insert(k, match v { serde_json::Value::String(s) => s, other => other.to_string() });
            }
        }
    } else if ctype.starts_with("application/x-www-form-urlencoded") {
        for kv in String::from_utf8_lossy(&body).split('&').filter(|kv| !kv.is_empty()) {
            let (k, v) = kv.split_once('=').unwrap_or((kv, ""));
            input.insert(form_decode(k), form_decode(v));
        }
    }
    input
}

fn form_decode(s: &str) -> String {
    let b = s.as_bytes();
    let mut out = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'+' {
            out.push(b' ');
        } else if b[i] == b'%' && i + 3 <= b.len() {
            match std::str::from_utf8(&b[i + 1..i + 3]).ok().and_then(|h| u8::from_str_radix(h, 16).ok()) {
                Some(v) => { out.push(v); i += 2; }
                None => out.push(b'%'),
            }
        } else {
            out.push(b[i]);
        }
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

"""


def _uses_input(tr) -> bool:
    if tr[0] == "if":
        return _uses_input(tr[4]) or _uses_input(tr[5])
    return tr[0] == "text" and any(k == "query" for k, _ in tr[1])


def render_main(rts: list) -> str:
    fns, ats, by_path = [], [], {}
    for i, (meth, path, params, tr, src) in enumerate(rts):
        name = "h%d" % i
        if tr is None:
            msg = "TODO: port %s %s from %s (Laravel)" % (meth, path, src)
            body = "hyper_compat::text_response(StatusCode::NOT_IMPLEMENTED, \"text/plain; charset=utf-8\", %s)" % _rs_str(msg)
        else:
            body = _leaf_rs(tr)
            if _uses_input(tr):
                body = "let input = read_input(req).await;"+chr(10)+"    " + body
        fns.append("/// %s %s <- %s\n#[open_runo_poem_compat_macro::handler]\nasync fn %s(req: Request, params: Params) -> Response {\n    let _ = (&req, &params);\n    %s\n}\n" % (meth, path, src, name, body))
        helper = {"GET": "get", "POST": "post", "PUT": "put", "PATCH": "patch", "DELETE": "delete"}.get(meth)
        if helper:
            by_path.setdefault(path, []).append("%s(%s())" % (helper, name))
    for path, hs in by_path.items():
        for h in hs:
            ats.append("        .at(%s, %s)" % (_rs_str(path), h))
    return ("//! 2RPoRea が PHP(Laravel) から生成した RPoem サーバー。訳せた return だけ本体あり、他は 501。\n"
            "#![allow(unused_variables, unused_imports, dead_code)]\n"
            "use open_runo_poem_compat::{delete, get, hyper_compat, patch, post, put, Params, Request, Response, Route, Server, StatusCode, TcpListener};\n\n"
            + _QUERY_HELPER + "\n".join(fns) +
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
                'http-body-util = "0.1"\nserde_json = "1"\ntokio = { version = "1", features = ["rt-multi-thread", "macros", "net"] }\n' % (rp, rp))
    with open(os.path.join(out, "src", "main.rs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_main(rts))
    done = sum(1 for r in rts if r[3] is not None)
    return {"routes": len(rts), "translated": done, "todo": len(rts) - done,
            "patch": sum(1 for r in rts if r[0] == "PATCH")}
