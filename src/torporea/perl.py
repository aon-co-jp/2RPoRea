"""Perl (Mojolicious::Lite / Dancer2) -> RPoem server.

Reads route declarations (`get '/path' => sub { ... };`, also post/put/del/del(ete)/any) from
`.pl` / `.pm` / `.psgi` files that use Mojolicious::Lite or Dancer/Dancer2. Route placeholders
`:name` and Mojolicious `<name>` become RPoem `:name`.

A handler body is translated only when, after dropping `my $c = shift;` and any number of
`my $x = EXPR;` text assignments, its final statement is exactly one of:

* Mojolicious: `$c->render(text => EXPR)` or `$c->render(json => LITERAL)`
* Dancer:      `return EXPR` / a bare final `EXPR`, or `return to_json/encode_json(LITERAL)`

where EXPR is string literals and route parameters joined with `.`
(`$c->param('name')`, `$c->stash('name')`, `route_parameters->get('name')`, `param('name')`),
and LITERAL is a hash/array of scalars. Everything else answers 501 with a TODO. Single-quoted
strings are literal; double-quoted strings are accepted only without `$`/`@` interpolation.
Output reuses the PHP emitter (same RPoem server shape).
"""
from __future__ import annotations

import os
import re

from .php import _balanced, render_main

_ROUTE = re.compile(r"^\s*(get|post|put|del|delete|patch|any)\s*(?:\(\s*)?(['\"])(.*?)\2\s*(?:,|=>)\s*sub\s*(?:\([^)]*\)\s*)?\{", re.M)


class _Unsupported(Exception):
    pass


_TOK = re.compile(r"""\s*(?:(?P<str>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")|(?P<num>-?\d+(?:\.\d+)?)|(?P<param>\$c->(?:param|stash)\(\s*['"](\w+)['"]\s*\)|route_parameters->get\(\s*['"](\w+)['"]\s*\)|\bparam\(\s*['"](\w+)['"]\s*\))|(?P<var>\$\w+)|(?P<op>=>|[{}\[\],.()])|(?P<word>[A-Za-z_]\w*))""")


def _toks(s: str):
    out, pos = [], 0
    while s[pos:].strip():
        m = _TOK.match(s, pos)
        if not m:
            raise _Unsupported(s[pos:pos + 20])
        pos = m.end()
        k = m.lastgroup
        if k == "param":
            out.append(("param", m.group(4) or m.group(5) or m.group(6)))
        else:
            out.append((k, m.group(k)))
    return out


def _unquote(lit: str) -> str:
    body = lit[1:-1]
    if lit[0] == "'":
        return body.replace("\\'", "'").replace("\\\\", "\\")
    if re.search(r"(?<!\\)[$@]", body):
        raise _Unsupported("interpolation")
    return body.encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1").decode("utf-8")


class _P:
    def __init__(self, s, params, env=None):
        self.t, self.i, self.params = _toks(s), 0, params
        self.env = env or {}

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, v=None):
        k, val = self.peek()
        if k is None or (v is not None and val != v):
            raise _Unsupported("expected %s" % v)
        self.i += 1
        return k, val

    def literal(self):
        k, v = self.peek()
        if v == "{":
            self.take()
            d = {}
            while self.peek()[1] != "}":
                kk, kv = self.take()
                key = _unquote(kv) if kk == "str" else kv if kk in ("word", "num") else None
                if key is None:
                    raise _Unsupported("hash key")
                self.take("=>")
                d[key] = self.literal()
                if self.peek()[1] == ",":
                    self.take(",")
            self.take("}")
            return d
        if v == "[":
            self.take()
            a = []
            while self.peek()[1] != "]":
                a.append(self.literal())
                if self.peek()[1] == ",":
                    self.take(",")
            self.take("]")
            return a
        if k == "num":
            self.take()
            return float(v) if "." in v else int(v)
        if k == "str":
            self.take()
            return _unquote(v)
        if k == "word" and v == "undef":
            self.take()
            return None
        raise _Unsupported(str(v))

    def text(self):
        parts = []
        while True:
            k, v = self.take()
            if k == "str":
                parts.append(("lit", _unquote(v)))
            elif k == "param" and v in self.params:
                parts.append(("param", v))
            elif k == "var" and v[1:] in self.env:
                parts.extend(self.env[v[1:]])
            else:
                raise _Unsupported(str(v))
            if self.peek()[1] != ".":
                return parts
            self.take(".")

    def done(self):
        return self.i == len(self.t)


def _split(b: str):
    out, cur = [], ""
    for piece in re.split(r"('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")", b):
        if piece[:1] in ("'", '"'):
            cur += piece
            continue
        segs = piece.split(";")
        cur += segs[0]
        for sg in segs[1:]:
            out.append(cur.strip())
            cur = sg
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]


def _last(b: str, params: list, env: dict):
    m = re.fullmatch(r"(?:return\s+)?\$\w+->render\s*\(\s*(text|json)\s*=>\s*(.*)\)", b, re.S)
    if m:
        p = _P(m.group(2), params, env)
        r = ("text", p.text()) if m.group(1) == "text" else ("json", p.literal())
        if p.peek()[1] == ",":
            return None  # extra render options (status => ...) are not translated
        return r if p.done() else None
    m = re.fullmatch(r"(?:return\s+)?(?:to_json|encode_json)\s*\(?\s*(.*?)\s*\)?", b, re.S)
    if m and re.match(r"(?:return\s+)?(?:to_json|encode_json)", b):
        p = _P(m.group(1), params, env)
        v = p.literal()
        return ("json", v) if p.done() else None
    m = re.fullmatch(r"(?:return\s+)?(.*)", b, re.S)
    p = _P(m.group(1), params, env)
    r = ("text", p.text())
    return r if p.done() else None


def translate(body: str, params: list):
    """Zero or more `my $x = EXPR;` (text EXPR only), then one translatable final statement."""
    b = re.sub(r"(?m)#.*$", "", body)
    b = re.sub(r"^\s*my\s*\(?\s*\$\w+\s*\)?\s*=\s*(?:shift|@_)\s*;", "", b).strip()
    stmts = _split(b)
    if not stmts:
        return None
    env = {}
    try:
        for st in stmts[:-1]:
            m = re.fullmatch(r"my\s+\$(\w+)\s*=\s*(.+)", st, re.S)
            if not m:
                return None
            p = _P(m.group(2), params, env)
            parts = p.text()
            if not p.done():
                return None
            env[m.group(1)] = parts
        return _last(stmts[-1], params, env)
    except (_Unsupported, UnicodeError, ValueError):
        return None


def routes(root: str) -> list:
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ("local", "blib", ".git", "node_modules")]
        for fn in sorted(files):
            if not fn.endswith((".pl", ".pm", ".psgi")):
                continue
            p = os.path.join(d, fn)
            t = open(p, encoding="utf-8", errors="replace").read()
            if not re.search(r"^\s*use\s+(Mojolicious::Lite|Dancer2?)\b", t, re.M):
                continue
            t = re.sub(r"(?ms)^=\w+.*?^=cut\s*$", "", t)  # POD
            rel = os.path.relpath(p, root).replace("\\", "/")
            for m in _ROUTE.finditer(t):
                meth = {"del": "DELETE", "any": "ANY"}.get(m.group(1), m.group(1).upper())
                path = re.sub(r"<(\w+)>", r":\1", m.group(3))
                path = re.sub(r"[:*](\w+)", r":\1", path)
                params = re.findall(r":(\w+)", path)
                e = _balanced(t, m.end() - 1)
                tr = translate(t[m.end():e - 1], params) if e else None
                for mm in (["GET", "POST", "PUT", "DELETE"] if meth == "ANY" else [meth]):
                    out.append((mm, path, params, tr, rel))
    return out


def write(root: str, out: str, rpoem_path: str = "F:/RPoem") -> dict:
    rts = routes(root)
    rp = os.path.abspath(rpoem_path).replace("\\", "/")
    os.makedirs(os.path.join(out, "src"), exist_ok=True)
    with open(os.path.join(out, "Cargo.toml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('[package]\nname = "perl-ported"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\n'
                'open-runo-poem-compat = { path = "%s/crates/open-runo-poem-compat" }\n'
                'open-runo-poem-compat-macro = { path = "%s/crates/open-runo-poem-compat-macro" }\n'
                'serde_json = "1"\ntokio = { version = "1", features = ["rt-multi-thread", "macros", "net"] }\n' % (rp, rp))
    main = render_main(rts).replace("PHP(Laravel)", "Perl(Mojolicious/Dancer)").replace("(Laravel)", "(Perl)").replace("unwrap_or(3002)", "unwrap_or(3003)")
    with open(os.path.join(out, "src", "main.rs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(main)
    done = sum(1 for r in rts if r[3] is not None)
    return {"routes": len(rts), "translated": done, "todo": len(rts) - done,
            "patch": sum(1 for r in rts if r[0] == "PATCH")}
