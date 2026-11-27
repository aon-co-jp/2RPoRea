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
        if k == "var" and v == "$request" and self.t[self.i + 1:self.i + 5] == [("op", "->"), ("word", "all"), ("op", "("), ("op", ")")]:
            self.i += 5
            return ("input_all",)
        if k == "var" and v == "$request" and self.t[self.i + 1:self.i + 3] and self.t[self.i + 1] == ("op", "->") and self.t[self.i + 2] in (("word", "only"), ("word", "except")):
            mode = self.t[self.i + 2][1]
            self.i += 3
            self.take("(")
            arr = self.value()
            self.take(")")
            if arr[0] != "json" or not isinstance(arr[1], list) or not all(isinstance(x, str) for x in arr[1]):
                raise _Unsupported("$request->%s needs a list of literal keys" % mode)
            return ("input_all", mode, list(arr[1]))
        if v == "[":
            return ("json", self.array())
        if k == "word" and v.lower() in ("true", "false", "null"):
            self.take()
            return ("json", {"true": True, "false": False, "null": None}[v.lower()])
        if k == "num":
            self.take()
            return ("json", float(v) if "." in v else int(v))
        if k == "word" and v == "response":
            r = self._response()
            hs = []
            while self.peek()[1] == "->" and self.t[self.i + 1] == ("word", "header"):
                self.take("->"); self.take(); self.take("(")
                hk = self.value(); self.take(","); hv = self.value(); self.take(")")
                if any(x[0] != "text" or any(p[0] != "lit" for p in x[1]) for x in (hk, hv)):
                    raise _Unsupported("non-literal header")
                hs.append(("".join(p[1] for p in hk[1]), "".join(p[1] for p in hv[1])))
            return ("hdr", hs, r) if hs else r
        return self.concat()

    def _response(self):
        self.take(); self.take("(")
        if self.peek()[1] != ")":
            body = self.value()
            code = 200
            if self.peek()[1] == ",":
                self.take(",")
                kc, vc = self.take()
                if kc != "num":
                    raise _Unsupported("non-literal status")
                code = int(vc)
            self.take(")")
            if body[0] not in ("text", "json") or (body[0] == "json" and not isinstance(body[1], str)):
                raise _Unsupported("response() body")
            if body[0] == "json":
                body = ("text", [("lit", body[1])])
            return ("status", code, body) if code != 200 else body
        self.take(")")
        self.take("->"); k2, v2 = self.take()
        if v2 != "json":
            raise _Unsupported("response()->" + v2)
        self.take("(")
        inner = self.value()
        code = 200
        if self.peek()[1] == ",":
            self.take(",")
            kc, vc = self.take()
            if kc != "num":
                raise _Unsupported("non-literal status")
            code = int(vc)
        self.take(")")
        if code != 200:
            if inner[0] not in ("json", "input_all"):
                raise _Unsupported("json of non-literal")
            return ("status", code, inner)
        if inner[0] == "input_all":
            return inner
        if inner[0] != "json":
            raise _Unsupported("json of non-literal")
        return ("json", inner[1])

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
_IFHAS = re.compile(r"\s*if\s*\(\s*(!?)\s*\$request->(has|filled|missing|boolean)\(\s*'(\w+)'\s*\)\s*\)\s*\{([^{}]*)\}\s*", re.S)
_ONE = r"!?\s*\$request->(?:has|filled|missing|boolean)\(\s*'\w+'\s*\)"
_IFMULTI = re.compile(r"\s*if\s*\(\s*(" + _ONE + r"(?:\s*(?:&&|\|\|)\s*" + _ONE + r")+)\s*\)\s*\{([^{}]*)\}\s*", re.S)
_ATOM = re.compile(r"(&&|\|\|)?\s*(!?)\s*\$request->(has|filled|missing|boolean)\(\s*'(\w+)'\s*\)")
_ELSE = re.compile(r"\s*else\s*\{([^{}]*)\}\s*$", re.S)


_TOK = re.compile(r"\s*(&&|\|\||!|\(|\)|\$request->(has|filled|missing|boolean)\(\s*'(\w+)'\s*\)|\$request->input\(\s*'(\w+)'\s*\)\s*(===?|!==?)\s*'([^'\\]*)')")


def _cond_tokens(s: str):
    """Tokenize `$request->has/filled` atoms joined by &&, ||, ! and parentheses into ifcond atoms
    (join, negate, kind, key); kind '(' / ')' are grouping marks. None when anything else appears."""
    out, i, j, neg, depth, want_atom = [], 0, "", False, 0, True
    while i < len(s):
        if not s[i:].strip():
            break
        m = _TOK.match(s, i)
        if not m:
            return None
        t, i = m.group(1), m.end()
        if want_atom:
            if t == "!":
                neg = not neg
            elif t == "(":
                out.append((j, neg, "(", "")); j, neg, depth = "", False, depth + 1
            elif m.group(2):
                out.append((j, neg, m.group(2), m.group(3))); j, neg, want_atom = "", False, False
            elif m.group(4):
                n2 = neg != m.group(5).startswith("!")
                out.append((j, n2, "eq", m.group(4) + "\0" + m.group(6))); j, neg, want_atom = "", False, False
            else:
                return None
        else:
            if t in ("&&", "||"):
                j, want_atom = t, True
            elif t == ")" and depth > 0:
                out.append(("", False, ")", "")); depth -= 1
            else:
                return None
    return out if depth == 0 and not want_atom and out else None


def _if_paren(b: str):
    """Split `if (COND) {THEN} REST` with balanced parentheses in COND; else None."""
    m = re.match(r"\s*if\s*\(", b)
    if not m:
        return None
    i, depth = m.end(), 1
    while i < len(b) and depth:
        depth += {"(": 1, ")": -1}.get(b[i], 0); i += 1
    if depth:
        return None
    m2 = re.match(r"\s*\{([^{}]*)\}\s*", b[i:], re.S)
    return (b[m.end():i - 1], m2.group(1), b[i + m2.end():]) if m2 else None


_MULTI = re.compile(r"\$request->(hasAny|anyFilled|has|filled)\(\s*\[([^\]]*)\]\s*\)")


def _expand_multi(b: str) -> str:
    """Rewrite array forms into single-key atoms: has([..]) / filled([..]) = all (&&),
    hasAny([..]) / anyFilled([..]) = any (||)."""
    def rep(m):
        keys = re.findall(r"'(\w+)'", m.group(2))
        if not keys or re.sub(r"'\w+'|[\s,]", "", m.group(2)):
            return m.group(0)
        kind = "has" if m.group(1) in ("has", "hasAny") else "filled"
        op = " || " if m.group(1) in ("hasAny", "anyFilled") else " && "
        return "(" + op.join("$request->%s('%s')" % (kind, k) for k in keys) + ")"
    return _MULTI.sub(rep, b)


def translate(body: str, params: list):
    """('json', value) / ('text', parts) for a body made only of simple local assignments
    (`$x = EXPR;`) followed by one `return EXPR;`; or ('if', param, negate, literal, then, else) for
    `if ($param == 'lit') { ... } [else { ... }]` on a route parameter followed by the rest. Else None."""
    b = _expand_multi(_strip_comments(body).strip())
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
    m = _IFMULTI.match(b)
    if m:
        then = translate(m.group(2), params)
        rest = b[m.end():]
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None:
            return None
        atoms = [(j or "", n == "!", k, key) for j, n, k, key in _ATOM.findall(m.group(1))]
        return ("ifcond", atoms, then, other)
    pm = _if_paren(b)
    toks = _cond_tokens(pm[0]) if pm and ("(" in re.sub(r"->(?:has|filled|missing|boolean|input)\(", "", pm[0]) or "->input(" in pm[0]) else None
    if toks:
        then = translate(pm[1], params)
        em = _ELSE.fullmatch(pm[2]) if pm[2].strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(pm[2], params)
        if then is None or other is None:
            return None
        return ("ifcond", toks, then, other)
    m = _IFHAS.match(b)
    if m:
        then = translate(m.group(4), params)
        rest = b[m.end():]
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None:
            return None
        return ("ifhas", m.group(2), m.group(3), m.group(1) == "!", then, other)
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
        ab = re.fullmatch(r"(?:return\s+)?abort\(\s*([1-5]\d\d)\s*(?:,\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*)?\)", stmts[-1], re.S)
        if ab:
            msg = "".join(v for _, v in _P(ab.group(2), params, env).value()[1]) if ab.group(2) else ""
            return ("abort", int(ab.group(1)), msg)
        if re.fullmatch(r"return\s+(?:back\(\s*\)|redirect\(\s*\)\s*->\s*back\(\s*\))", stmts[-1]):
            return ("back",)
        rr = re.fullmatch(r"return\s+(?:redirect\(\s*\)\s*->\s*route|to_route)\(\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*(?:,\s*\[([^\]]*)\])?\s*\)", stmts[-1], re.S)
        if rr:
            args = []
            if rr.group(2):
                for kv in [x for x in rr.group(2).split(",") if x.strip()]:
                    mm = re.fullmatch(r"\s*'(\w+)'\s*=>\s*(?:\$(\w+)|'([^'\\]*)')\s*", kv)
                    if not mm or (mm.group(2) and mm.group(2) not in params):
                        return None
                    args.append((mm.group(1), ("param", mm.group(2)) if mm.group(2) else ("lit", mm.group(3))))
            return ("routeredir", _unquote(rr.group(1)), args)
        rd = re.fullmatch(r"return\s+redirect\(\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*\)(?:\s*->\s*to\(\s*('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")\s*\))?", stmts[-1], re.S)
        if rd:
            target = rd.group(1) if rd.group(1) else rd.group(2)
            parts = _P(target, params, env).value()
            if parts[0] != "text" or any(k != "lit" for k, _ in parts[1]):
                return None
            return ("redirect", "".join(v for _, v in parts[1]))
        m = re.fullmatch(r"return\s+(.+)", stmts[-1], re.S)
        if not m:
            return None
        return _expr(m.group(1), params, env)
    except (_Unsupported, StopIteration, ValueError, UnicodeError):
        return None


# --- route collection and Rust emission -----------------------------------------------------

def _has_rs(kind: str, key: str) -> str:
    if kind == "has":
        return "input.contains_key(%s)" % _rs_str(key)
    if kind == "eq":
        # Form and JSON strings compare as text; other JSON values never equal a string literal.
        k, v = key.split("\0", 1)
        return "(input.get(%s).and_then(|v| v.as_str()) == Some(%s))" % (_rs_str(k), _rs_str(v))
    if kind == "boolean":
        # Laravel boolean(): true for 1, "1", true, "true", "on", "yes"; anything else false.
        return "input.get(%s).is_some_and(|v| match v { serde_json::Value::Bool(b) => *b, serde_json::Value::Number(n) => n.as_i64() == Some(1), serde_json::Value::String(t) => matches!(t.to_ascii_lowercase().as_str(), \"1\" | \"true\" | \"on\" | \"yes\"), _ => false })" % _rs_str(key)
    if kind == "missing":
        return "!input.contains_key(%s)" % _rs_str(key)
    return "input.get(%s).is_some_and(|v| !matches!(v, serde_json::Value::Null) && v.as_str().map_or(true, |t| !t.trim().is_empty()))" % _rs_str(key)


def _leaf_rs(tr) -> str:
    if tr[0] == "hdr":
        sets = " ".join("r.headers_mut().insert(%s, %s.parse().unwrap());" % (_rs_str(k.lower()), _rs_str(v)) for k, v in tr[1])
        return "{ let mut r = { %s }; %s r }" % (_leaf_rs(tr[2]), sets)
    if tr[0] == "status":
        return "{ let mut r = { %s }; *r.status_mut() = StatusCode::from_u16(%d).unwrap(); r }" % (_leaf_rs(tr[2]), tr[1])
    if tr[0] == "back":
        return "{ let mut r = hyper_compat::html_response(StatusCode::FOUND, String::new()); r.headers_mut().insert(\"location\", back_referer.parse().unwrap_or_else(|_| \"/\".parse().unwrap())); r }"
    if tr[0] == "redirectp":
        def rp(k, v):
            if k == "lit":
                return "s.push_str(%s);" % _rs_str(v)
            if k == "penc":  # RFC 3986 percent-encoding of a route parameter used as a query value
                return "for b in form_decode(params.get(%s).unwrap_or(\"\")).bytes() { if b.is_ascii_alphanumeric() || b\"-._~\".contains(&b) { s.push(b as char) } else { s.push_str(&format!(\"%%{:02X}\", b)) } }" % _rs_str(v)
            return "s.push_str(params.get(%s).unwrap_or(\"\"));" % _rs_str(v)
        pieces = " ".join(rp(k, v) for k, v in tr[1])
        return "{ let mut s = String::new(); %s let mut r = hyper_compat::html_response(StatusCode::FOUND, String::new()); r.headers_mut().insert(\"location\", s.parse().unwrap_or_else(|_| \"/\".parse().unwrap())); r }" % pieces
    if tr[0] == "redirect":
        return "{ let mut r = hyper_compat::html_response(StatusCode::FOUND, String::new()); r.headers_mut().insert(\"location\", %s.parse().unwrap()); r }" % _rs_str(tr[1])
    if tr[0] == "abort":
        return "hyper_compat::html_response(StatusCode::from_u16(%d).unwrap(), %s.to_string())" % (tr[1], _rs_str(tr[2]))
    if tr[0] == "ifcond":
        # PHP and Rust share && over || precedence, so the chain is emitted as written.
        cond = " ".join(")" if k == ")" else ("%s %s%s" % (j, "!" if n else "", "(" if k == "(" else _has_rs(k, key))).strip() for j, n, k, key in tr[1])
        return "if %s { %s } else { %s }" % (cond, _leaf_rs(tr[2]), _leaf_rs(tr[3]))
    if tr[0] == "ifhas":
        cond = _has_rs(tr[1], tr[2])
        return "if %s%s { %s } else { %s }" % ("!" if tr[3] else "", cond, _leaf_rs(tr[4]), _leaf_rs(tr[5]))
    if tr[0] == "if":
        cmp_ = "!=" if tr[2] else "=="
        return "if params.get(%s).unwrap_or(\"\") %s %s { %s } else { %s }" % (_rs_str(tr[1]), cmp_, _rs_str(tr[3]), _leaf_rs(tr[4]), _leaf_rs(tr[5]))
    if tr[0] == "input_all":
        if len(tr) == 1:
            return "hyper_compat::json_response(StatusCode::OK, &input)"
        keys = ", ".join(_rs_str(k) for k in tr[2])
        keep = "" if tr[1] == "only" else "!"
        return "{ let keys: &[&str] = &[%s]; let picked: std::collections::HashMap<&String, &serde_json::Value> = input.iter().filter(|(k, _)| %skeys.contains(&k.as_str())).collect(); hyper_compat::json_response(StatusCode::OK, &picked) }" % (keys, keep)
    if tr[0] == "json":
        return "hyper_compat::json_response(StatusCode::OK, &serde_json::from_str::<serde_json::Value>(%s).unwrap())" % _rs_str(json.dumps(tr[1], ensure_ascii=False))
    def piece(k, v):
        if k == "lit":
            return "s.push_str(%s);" % _rs_str(v)
        if k == "query":
            return "s.push_str(&input.get(%s).map(|v| match v { serde_json::Value::String(t) => t.clone(), o => o.to_string() }).unwrap_or_else(|| %s.to_string()));" % (_rs_str(v[0]), _rs_str(v[1]))
        return "s.push_str(params.get(%s).unwrap_or(\"\"));" % _rs_str(v)
    pieces = [piece(k, v) for k, v in tr[1]]
    return "{ let mut s = String::new(); %s hyper_compat::html_response(StatusCode::OK, s) }" % " ".join(pieces)


def routes(root: str) -> list:
    """[(METHOD, path, params, translation-or-None, source-file)]"""
    out, names = [], {}
    for rel, prefix in (("routes/web.php", ""), ("routes/api.php", "/api")):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        t = _strip_comments(open(p, encoding="utf-8", errors="replace").read())
        starts = [(m.start(), (prefix + "/" + m.group(3).strip("/")).rstrip("/") or "/") for m in _ROUTE.finditer(t)]
        for nm in re.finditer(r"->\s*name\(\s*(['\"])([\w.-]+)\1\s*\)", t):
            prev = [pth for st, pth in starts if st < nm.start()]
            if prev:
                names.setdefault(nm.group(2), prev[-1])
        for m in re.finditer(r"Route::view\s*\(\s*(['\"])(.*?)\1\s*,\s*(['\"])([\w.-]+)\3\s*(?:,\s*\[([^\]]*)\])?\s*\)", t, re.S):
            full = (prefix + "/" + m.group(2).strip("/")).rstrip("/") or "/"
            vf = os.path.join(root, "resources", "views", *m.group(4).split(".")) + ".blade.php"
            html = open(vf, encoding="utf-8").read() if os.path.exists(vf) else None
            if html is not None and m.group(5):
                # Route::view data: literal 'key' => 'value' pairs fill {{ $key }} (HTML-escaped, as Blade does).
                import html as _h
                data = {}
                for kv in [x for x in m.group(5).split(",") if x.strip()]:
                    mm = re.fullmatch(r"\s*'(\w+)'\s*=>\s*'([^'\\]*)'\s*", kv)
                    if not mm:
                        html = None
                        break
                    data[mm.group(1)] = mm.group(2)
                if html is not None:
                    html = re.sub(r"\{\{\s*\$(\w+)\s*\}\}", lambda mm: _h.escape(data[mm.group(1)]) if mm.group(1) in data else mm.group(0), html)
            # Only plain HTML views: any Blade syntax ({{ }}, {!! !!}, @directives) stays a 501 TODO.
            if html is not None and ("{{" in html or "{!!" in html or re.search(r"(?m)^\s*@\w", html)):
                html = None
            if "{" in full:
                continue
            out.append(("GET", full, [], ("text", [("lit", html)]) if html is not None else None, os.path.relpath(vf, root).replace(os.sep, "/")))
        for m in re.finditer(r"Route::(redirect|permanentRedirect)\s*\(\s*(['\"])(.*?)\2\s*,\s*(['\"])(.*?)\4\s*(?:,\s*(\d{3})\s*)?\)", t, re.S):
            full = (prefix + "/" + m.group(3).strip("/")).rstrip("/") or "/"
            if "{" in full or "{" in m.group(5):
                continue
            code = 301 if m.group(1) == "permanentRedirect" else int(m.group(6) or 302)
            tr = ("redirect", m.group(5)) if code == 302 else ("status", code, ("redirect", m.group(5)))
            for mm in ("GET", "POST", "PUT", "DELETE"):
                out.append((mm, full, [], tr, rel))
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
    return [(a, b, c, _resolve_names(tr, names), e) for a, b, c, tr, e in out]


def _resolve_names(tr, names):
    """('routeredir', name) -> ('redirect', path) for named routes without parameters; else None (501)."""
    if tr is None:
        return None
    if tr[0] == "routeredir":
        path = names.get(tr[1])
        if not path:
            return None
        args = dict(tr[2]) if len(tr) > 2 else {}
        parts = []
        for piece in re.split(r"(\{\w+\??\})", path):
            pm = re.fullmatch(r"\{(\w+)\??\}", piece)
            if not pm:
                if piece:
                    parts.append(("lit", piece))
            elif pm.group(1) in args:
                parts.append(args.pop(pm.group(1)))
            else:
                return None
        if args:  # Laravel appends leftover keys as a query string; literal values only
            from urllib.parse import quote
            for n, (key, (kind, v)) in enumerate(args.items()):
                parts.append(("lit", ("?" if n == 0 else "&") + quote(key, safe="") + "="))
                parts.append(("lit", quote(v, safe="")) if kind == "lit" else ("penc", v))
        return ("redirect", parts[0][1]) if all(k == "lit" for k, _ in parts) and len(parts) == 1 else ("redirectp", parts)
    if tr[0] in ("if", "ifhas"):
        a, b = _resolve_names(tr[4], names), _resolve_names(tr[5], names)
        return None if a is None or b is None else tr[:4] + (a, b)
    if tr[0] == "ifcond":
        a, b = _resolve_names(tr[2], names), _resolve_names(tr[3], names)
        return None if a is None or b is None else (tr[0], tr[1], a, b)
    return tr


def _rs_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


_QUERY_HELPER = r"""/// Laravel `$request->input()`: query string merged with the body (form-urlencoded or a JSON object; body wins),
/// body capped at 1 MiB. JSON values keep their types (numbers, booleans, nested objects). Only built for handlers that read input.
async fn read_input(req: Request) -> std::collections::HashMap<String, serde_json::Value> {
    use http_body_util::BodyExt;
    let mut input: std::collections::HashMap<String, serde_json::Value> =
        hyper_compat::query_params(&req).into_iter().map(|(k, v)| (k, serde_json::Value::String(v))).collect();
    let ctype = req.headers().get("content-type").and_then(|v| v.to_str().ok()).unwrap_or("").to_ascii_lowercase();
    let limited = http_body_util::Limited::new(req.into_body(), 1 << 20);
    let Ok(body) = limited.collect().await.map(|c| c.to_bytes()) else { return input };
    if ctype.starts_with("application/json") {
        if let Ok(serde_json::Value::Object(m)) = serde_json::from_slice::<serde_json::Value>(&body) {
            for (k, v) in m {
                input.insert(k, v);
            }
        }
    } else if ctype.starts_with("application/x-www-form-urlencoded") {
        for kv in String::from_utf8_lossy(&body).split('&').filter(|kv| !kv.is_empty()) {
            let (k, v) = kv.split_once('=').unwrap_or((kv, ""));
            input.insert(form_decode(k), serde_json::Value::String(form_decode(v)));
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
    if tr[0] == "ifhas":
        return True
    if tr[0] == "ifcond":
        return True
    if tr[0] == "status":
        return _uses_input(tr[2])
    if tr[0] == "hdr":
        return _uses_input(tr[2])
    return tr[0] == "input_all" or (tr[0] == "text" and any(k == "query" for k, _ in tr[1]))


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
            if "back_referer" in body:
                body = "let back_referer = req.headers().get(\"referer\").and_then(|v| v.to_str().ok()).unwrap_or(\"/\").to_string();"+chr(10)+"    " + body
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
