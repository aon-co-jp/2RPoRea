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


_TOK = re.compile(r"\s*(&&|\|\||!|\(|\)|\$request->(has|filled|missing|boolean)\(\s*'(\w+)'\s*\)|\$(?!request\b)(\w+)\s*(===?|!==?)\s*'([^'\\]*)'|\$request->input\(\s*'(\w+)'\s*\)\s*(===?|!==?)\s*'([^'\\]*)')")


def _cond_tokens(s: str, params=()):
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
                if m.group(4) not in params:
                    return None
                n2 = neg != m.group(5).startswith("!")
                out.append((j, n2, "peq" if m.group(5) in ("===", "!==") else "lpeq", m.group(4) + "\0" + m.group(6))); j, neg, want_atom = "", False, False
            elif m.group(7):
                n2 = neg != m.group(8).startswith("!")
                out.append((j, n2, "eq" if m.group(8) in ("===", "!==") else "leq", m.group(7) + "\0" + m.group(9))); j, neg, want_atom = "", False, False
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


def _elseif(rest: str) -> str:
    """`elseif (...)` / `else if (...)` after a branch: the rest is just another if."""
    return re.sub(r"^\s*else\s*if\b|^\s*elseif\b", "if", rest, count=1)


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
        rest = _elseif(rest)
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None or lit[0] != "text" or any(k != "lit" for k, _ in lit[1]):
            return None
        if m.group(2) in ("==", "!="):
            # loose == / != on a route parameter: PHP numeric-string comparison
            return ("ifcond", [("", m.group(2).startswith("!"), "lpeq", m.group(1) + "\0" + "".join(v for _, v in lit[1]))], then, other)
        return ("if", m.group(1), m.group(2).startswith("!"), "".join(v for _, v in lit[1]), then, other)
    m = _IFMULTI.match(b)
    if m:
        then = translate(m.group(2), params)
        rest = b[m.end():]
        rest = _elseif(rest)
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None:
            return None
        atoms = [(j or "", n == "!", k, key) for j, n, k, key in _ATOM.findall(m.group(1))]
        return ("ifcond", atoms, then, other)
    pm = _if_paren(b)
    toks = _cond_tokens(pm[0], params) if pm and ("(" in re.sub(r"->(?:has|filled|missing|boolean|input)\(", "", pm[0]) or "->input(" in pm[0] or re.search(r"\$(?!request\b)\w+\s*[=!]=", pm[0])) else None
    if toks:
        then = translate(pm[1], params)
        rest = _elseif(pm[2])
        em = _ELSE.fullmatch(rest) if rest.strip().startswith("else") else None
        other = translate(em.group(1), params) if em else translate(rest, params)
        if then is None or other is None:
            return None
        return ("ifcond", toks, then, other)
    m = _IFHAS.match(b)
    if m:
        then = translate(m.group(4), params)
        rest = b[m.end():]
        rest = _elseif(rest)
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
    if kind == "peq":
        k, v = key.split("\0", 1)
        return "(params.get(%s).unwrap_or(\"\") == %s)" % (_rs_str(k), _rs_str(v))
    if kind in ("leq", "lpeq"):
        # PHP 8 loose ==: numeric strings compare as numbers, null == '', bools by truthiness.
        k, v = key.split("\0", 1)
        if kind == "lpeq":
            return "php_loose_eq(params.get(%s).map(|s| serde_json::Value::String(s.to_string())).as_ref(), %s)" % (_rs_str(k), _rs_str(v))
        return "php_loose_eq(input.get(%s), %s)" % (_rs_str(k), _rs_str(v))
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
        if k == "query_esc":
            return "s.push_str(&input.get(%s).map(|v| match v { serde_json::Value::String(t) => t.clone(), o => o.to_string() }).unwrap_or_else(|| %s.to_string()).replace('&', \"&amp;\").replace('<', \"&lt;\").replace('>', \"&gt;\").replace('\"', \"&quot;\").replace('\\'', \"&#039;\"));" % (_rs_str(v[0]), _rs_str(v[1]))
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
        for m in re.finditer(r"Route::view\s*\(\s*(['\"])(.*?)\1\s*,\s*(['\"])([\w.-]+)\3\s*(?:,\s*\[((?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*)\])?\s*\)", t, re.S):
            full = (prefix + "/" + m.group(2).strip("/")).rstrip("/") or "/"
            vf = os.path.join(root, "resources", "views", *m.group(4).split(".")) + ".blade.php"
            html = open(vf, encoding="utf-8").read() if os.path.exists(vf) else None
            if html is not None:
                # Blade comments {{-- ... --}} never reach the output.
                html = re.sub(r"\{\{--.*?--\}\}", "", html, flags=re.S)
                # @{{ ... }} is Blade's escape for a literal {{ ... }} (e.g. for JS templates).
                html = html.replace("@{{", "\x00LB\x00")
            if html is not None:
                # @for($i = A; $i < / <= B; $i++) with integer literals: unrolled at convert time (capped at 1000).
                def _for(mm):
                    v, a, op, b = mm.group(1), int(mm.group(2)), mm.group(4), int(mm.group(5))
                    if mm.group(3) != v or mm.group(6) != v:
                        return mm.group(0)
                    rng = range(a, b + 1 if op == "<=" else b)
                    if len(rng) > 1000:
                        return mm.group(0)
                    return "".join(re.sub(r"\{\{\s*\$" + v + r"\s*\}\}", str(i), mm.group(7)) for i in rng)
                html = re.sub(r"@for\s*\(\s*\$(\w+)\s*=\s*(-?\d+)\s*;\s*\$(\w+)\s*(<=?)\s*(-?\d+)\s*;\s*\$(\w+)\+\+\s*\)(.*?)@endfor\b", _for, html, flags=re.S)
            data = {}
            if html is not None and (m.group(5) or "@php" in html):
                # Route::view data: literal 'key' => 'value' pairs fill {{ $key }} (HTML-escaped, as Blade does).
                import html as _h
                # 'key' => 'value' or 'key' => ['a', 'b'] (a list of literal strings, for @foreach).
                rest = (m.group(5) or "").strip().rstrip(",").strip()
                parsed = _php_array("[" + rest + "]") if rest else {}
                if isinstance(parsed, list) and not parsed:
                    parsed = {}
                if not isinstance(parsed, dict):
                    html = None
                else:
                    data.update(parsed)
                # @php($x = 'v') and @php $x = 'v'; ... @endphp with only literal string assignments set view data.
                def _php(code):
                    for st in [x.strip() for x in code.split(";") if x.strip()]:
                        q = re.fullmatch(r"\$(\w+)\s*=\s*(.+)", st, re.S)
                        if not q:
                            return None
                        # RHS: literals and already-known $vars joined by '.' (concat) or by '+'/'-' (integers).
                        if "(" in q.group(2) or ("'" not in q.group(2) and '"' not in q.group(2)):
                            r = _int_expr(q.group(2), data)
                            if r is not None:
                                data[q.group(1)] = r
                                continue
                            if "(" in q.group(2):
                                return None
                        term = r"""'[^'\\]*'|"[^"\\$]*"|-?\d+|\$\w+"""
                        toks = re.findall(r"\s*(" + term + r")\s*([.+*/%-]|$)", q.group(2))
                        if not toks or toks[-1][1] or re.sub(r"\s", "", q.group(2)) != "".join(re.sub(r"\s", "", a) + o for a, o in toks):
                            return None
                        vals = []
                        for a, _ in toks:
                            if a[0] == "$":
                                if not isinstance(data.get(a[1:]), str):
                                    return None
                                vals.append(data[a[1:]])
                            else:
                                vals.append(a[1:-1] if a[0] in "'\"" else a)
                        ops = {o for _, o in toks[:-1]}
                        if not ops:
                            r = vals[0]
                        elif ops == {"."}:
                            r = "".join(vals)
                        elif ops <= {"+", "-", "*", "/", "%"} and all(re.fullmatch(r"-?\d+", x) for x in vals):
                            # integer arithmetic with PHP precedence (* / % before + -); '/' only when exact
                            # (PHP would give a float otherwise), '%' truncates toward zero like PHP.
                            nums, sums = [int(vals[0])], []
                            for (_, o), x in zip(toks[:-1], vals[1:]):
                                x = int(x)
                                if o in "*/%":
                                    if o != "*" and x == 0:
                                        return None
                                    a = nums[-1]
                                    if o == "*":
                                        nums[-1] = a * x
                                    elif o == "/":
                                        if a % x:
                                            return None
                                        nums[-1] = a // x
                                    else:
                                        nums[-1] = abs(a) % abs(x) * (1 if a >= 0 else -1)
                                else:
                                    sums.append(o)
                                    nums.append(x)
                            r = nums[0]
                            for o, x in zip(sums, nums[1:]):
                                r = r + x if o == "+" else r - x
                            r = str(r)
                        else:
                            return None
                        # integers print as decimal text; '' and '0' are falsy, like PHP
                        data[q.group(1)] = r
                    return ""
                if html is not None:
                    # inline @php( ... ) with balanced parentheses, then @php ... @endphp blocks
                    out_h, pos = [], 0
                    for st in re.finditer(r"@php\s*\(", html):
                        if st.start() < pos:
                            continue
                        depth, j = 1, st.end()
                        while j < len(html) and depth:
                            depth += {"(": 1, ")": -1}.get(html[j], 0)
                            j += 1
                        if depth:
                            break
                        code = html[st.end():j - 1]
                        out_h.append(html[pos:st.start()] + (html[st.start():j] if _php(code) is None else ""))
                        pos = j
                    html = "".join(out_h) + html[pos:]
                    html = re.sub(r"@php\b(?!\s*\()(.*?)@endphp\b", lambda q: q.group(0) if _php(q.group(1)) is None else "", html, flags=re.S)
                    # @while($i < N) ... @php($i++) ... @endwhile with an integer $i set by @php: unrolled (capped at 1000).
                    def _while(q):
                        v, op, n, body = q.group(1), q.group(2), int(q.group(3)), q.group(4)
                        steps = re.findall(r"@php\s*\(\s*\$" + v + r"\s*(\+\+|--)\s*\)", body)
                        if len(steps) != 1 or not re.fullmatch(r"-?\d+", data.get(v, "") if isinstance(data.get(v), str) else ""):
                            return q.group(0)
                        i, d, out = int(data[v]), (1 if steps[0] == "++" else -1), []
                        test = {"<": lambda a: a < n, "<=": lambda a: a <= n, ">": lambda a: a > n, ">=": lambda a: a >= n, "!=": lambda a: a != n}[op]
                        while test(i):
                            if len(out) >= 1000:
                                return q.group(0)
                            pre, post = re.split(r"@php\s*\(\s*\$" + v + r"\s*(?:\+\+|--)\s*\)", body)
                            out.append(re.sub(r"\{\{\s*\$" + v + r"\s*\}\}", str(i), pre) + re.sub(r"\{\{\s*\$" + v + r"\s*\}\}", str(i + d), post))
                            i += d
                        data[v] = str(i)
                        return "".join(out)
                    html = re.sub(r"@while\s*\(\s*\$(\w+)\s*(<=|>=|<|>|!=)\s*(-?\d+)\s*\)(.*?)@endwhile\b", _while, html, flags=re.S)
                if html is not None:
                    # @if($k) / @isset($k) ... [@else ...] @endif / @endisset with literal data: decided at convert time
                    # (PHP truthiness of a string: '' and '0' are false). Unknown keys keep the block (stays 501).
                    # @foreach($list as $v) ... @endforeach over a literal list: unrolled at convert time.
                    def _each(mm):
                        k, kk, v, body = mm.group(1), mm.group(2), mm.group(3), mm.group(4)
                        if isinstance(data.get(k), dict):
                            keys, xs = list(data[k].keys()), list(data[k].values())
                        elif isinstance(data.get(k), list):
                            keys, xs = [str(i) for i in range(len(data[k]))], data[k]
                        else:
                            return mm.group(0)
                        pre = mm.string[:mm.start()]
                        depth = len(re.findall(r"@foreach\b", pre)) - len(re.findall(r"@endforeach\b", pre)) + 1
                        def _one(i, x):
                            # nested @foreach blocks (outer-first unrolling) keep their own $loop; only $loop->parent-> is ours there.
                            segs, last, lvl, st0 = [], 0, 0, 0
                            for tm in re.finditer(r"@(end)?foreach\b", body):
                                if not tm.group(1):
                                    if lvl == 0:
                                        st0 = tm.start()
                                    lvl += 1
                                else:
                                    lvl -= 1
                                    if lvl == 0:
                                        segs.append((last, st0, tm.end()))
                                        last = tm.end()
                            if segs:
                                lp0 = {"index": str(i), "iteration": str(i + 1), "count": str(len(xs)), "remaining": str(len(xs) - i - 1), "depth": str(depth)}
                                out = []
                                for s0, s1, s2 in segs:
                                    out.append(_one_flat(i, x, body[s0:s1]))
                                    inn = re.sub(r"\{\{\s*\$loop->parent->(index|iteration|count|remaining|depth)\s*\}\}", lambda q: lp0[q.group(1)], body[s1:s2])
                                    if "$loop->parent" in inn:
                                        raise ValueError
                                    out.append(_one_flat(i, x, inn, keep_loop=True))
                                out.append(_one_flat(i, x, body[last:]))
                                return "".join(out)
                            return _one_flat(i, x, body)
                        def _one_flat(i, x, body, keep_loop=False):
                            # $loop->index/iteration/count/remaining/first/last, as Blade's $loop.
                            lp = {"index": str(i), "iteration": str(i + 1), "count": str(len(xs)), "remaining": str(len(xs) - i - 1),
                                  "first": "1" if i == 0 else "", "last": "1" if i == len(xs) - 1 else "",
                                  "odd": "1" if (i + 1) % 2 else "", "even": "" if (i + 1) % 2 else "1", "depth": str(depth)}
                            b = body if keep_loop else re.sub(r"@if\s*\(\s*(!?)\$loop->(first|last|odd|even)\s*\)(.*?)(?:@else(.*?))?@endif\b",
                                       lambda q: q.group(3) if bool(lp[q.group(2)]) != (q.group(1) == "!") else (q.group(4) or ""), body, flags=re.S)
                            if not keep_loop:
                                b = re.sub(r"\{\{\s*\$loop->(index|iteration|count|remaining|depth)\s*\}\}", lambda q: lp[q.group(1)], b)
                                # $loop->parent->X refers to the enclosing loop, which is unrolled later: hand it over as $loop->X.
                                b = b.replace("$loop->parent->", "$loop->")
                            if not isinstance(x, str):
                                # an array item: name it as hidden view data so inner loops / $v['k'] over it resolve later.
                                hid = "__fe%d" % len(data)
                                data[hid] = x
                                b = re.sub(r"\$" + v + r"(?!\w)", "$" + hid, b)
                            if kk:
                                b = re.sub(r"\{\{\s*\$" + kk + r"\s*\}\}", lambda _m: _h.escape(keys[i]), b)
                            b = re.sub(r"\{\{\s*\$" + v + r"\s*\}\}", lambda _m: _h.escape(x), b)
                            return re.sub(r"\{!!\s*\$" + v + r"\s*!!\}", lambda _m: x, b)
                        # @continue / @break, bare or with ($v == 'lit' / != / $loop->first|last|odd|even): cut the iteration there.
                        def _hit(cond, i, x):
                            if cond is None:
                                return True
                            c = re.fullmatch(r"\s*\$(\w+)\s*(===|!==|==|!=)\s*'([^'\\]*)'\s*", cond)
                            if c and c.group(1) == v and isinstance(x, str):
                                return (x == c.group(3)) == (c.group(2) in ("==", "==="))
                            c = re.fullmatch(r"\s*(!?)\$loop->(first|last|odd|even)\s*", cond)
                            if c:
                                on = {"first": i == 0, "last": i == len(xs) - 1, "odd": (i + 1) % 2 == 1, "even": (i + 1) % 2 == 0}[c.group(2)]
                                return on != (c.group(1) == "!")
                            raise ValueError
                        parts = []
                        for i, x in enumerate(xs):
                            try:
                                t = _one(i, x)
                            except ValueError:
                                return mm.group(0)
                            stop = False
                            for d in re.finditer(r"@(continue|break)\b(?:\s*\(([^()]*)\))?", t):
                                try:
                                    if not _hit(d.group(2), i, x):
                                        continue
                                except ValueError:
                                    return mm.group(0)
                                t, stop = t[:d.start()], d.group(1) == "break"
                                break
                            t = re.sub(r"@(continue|break)\b(?:\s*\([^()]*\))?", "", t)
                            parts.append(t)
                            if stop:
                                break
                        return "".join(parts)
                    # @forelse(...) body @empty alt @endforelse: the alt when the literal list/array is empty, else a @foreach.
                    def _forelse(mm):
                        v = data.get(mm.group(2))
                        if not isinstance(v, (list, dict)):
                            return mm.group(0)
                        return mm.group(4) if not v else "@foreach(" + mm.group(1) + ")" + mm.group(3) + "@endforeach"
                    html = re.sub(r"@forelse\s*\(\s*(\$(\w+)\s+as\s+[^)]*)\)(.*?)@empty\b(.*?)@endforelse\b", _forelse, html, flags=re.S)
                    # Innermost loops first, so nested @foreach over separate literal arrays unrolls too.
                    while True:
                        prev = html
                        html = re.sub(r"@foreach\s*\(\s*\$(\w+)\s+as\s+(?:\$(\w+)\s*=>\s*)?\$(\w+)\s*\)((?:(?!@foreach\b).)*?)@endforeach\b", _each, html, flags=re.S)
                        if html == prev:
                            # outer loops over arrays of arrays: unroll the outermost one first (only without $loop / @continue / @break inside).
                            for hm in re.finditer(r"@foreach\s*\(\s*\$(\w+)\s+as\s+(?:\$(\w+)\s*=>\s*)?\$(\w+)\s*\)", html):
                                if not isinstance(data.get(hm.group(1)), (list, dict)):
                                    continue
                                lvl, end = 1, None
                                for tm in re.finditer(r"@(end)?foreach\b", html[hm.end():]):
                                    lvl += -1 if tm.group(1) else 1
                                    if lvl == 0:
                                        end = (hm.end() + tm.start(), hm.end() + tm.end())
                                        break
                                inner = html[hm.end():end[0]] if end else ""
                                if not end or re.search(r"@(continue|break)\b", inner):
                                    continue
                                class _M:
                                    string = html
                                    def start(self):
                                        return hm.start()
                                    def group(self, n):
                                        return {0: html[hm.start():end[1]], 1: hm.group(1), 2: hm.group(2), 3: hm.group(3), 4: inner}[n]
                                html = html[:hm.start()] + _each(_M()) + html[end[1]:]
                                break
                            if html == prev:
                                break
                    # @switch($k) @case('v') ... @break ... @default ... @endswitch with a literal scalar: picked at convert time.
                    def _sw(mm):
                        k = mm.group(1)
                        if not isinstance(data.get(k), str):
                            return mm.group(0)
                        parts = re.split(r"""@(case\s*\(\s*(?:'([^'\\]*)'|"([^"\\$]*)")\s*\)|default)""", mm.group(2))
                        cases = [(parts[i + 1] if parts[i + 1] is not None else parts[i + 2], parts[i + 3])
                                 for i in range(1, len(parts) - 3, 4)]
                        hit = next((i for i, (lab, _) in enumerate(cases) if lab == data[k]), None)
                        if hit is None:
                            hit = next((i for i, (lab, _) in enumerate(cases) if lab is None), None)
                        if hit is None:
                            return ""
                        out = ""
                        for _, body in cases[hit:]:  # fall through until @break, as PHP does
                            if "@break" in body:
                                return out + body.split("@break", 1)[0]
                            out += body
                        return out
                    html = re.sub(r"@switch\s*\(\s*\$(\w+)\s*\)(.*?)@endswitch\b", _sw, html, flags=re.S)
                    def _blk(mm):
                        k = mm.group(2)
                        if mm.group(1) in ("if", "unless") and k not in data:
                            return mm.group(0)
                        ok = (k in data) if mm.group(1) == "isset" else (bool(data[k]) if isinstance(data[k], list) else data[k] not in ("", "0"))
                        if mm.group(1) == "unless":
                            ok = not ok
                        return mm.group(3) if ok else (mm.group(4) or "")
                    html = re.sub(r"@(if|isset|unless)\s*\(\s*\$(\w+)\s*\)(.*?)(?:@else(.*?))?@end(?:if|isset|unless)\b", _blk, html, flags=re.S)
                    html = re.sub(r"\{\{\s*\$(\w+)\s*\}\}", lambda mm: _h.escape(data[mm.group(1)]) if isinstance(data.get(mm.group(1)), str) else mm.group(0), html)
                    # {!! $key !!} prints the value unescaped, as Blade does.
                    html = re.sub(r"\{!!\s*\$(\w+)\s*!!\}", lambda mm: data[mm.group(1)] if isinstance(data.get(mm.group(1)), str) else mm.group(0), html)
            if html is not None:
                # {{ $k ?? 'default' }}: the literal value when given (escaped), else the default (escaped), as Blade does.
                import html as _h2
                _d = data
                html = re.sub(r"""\{\{\s*\$(\w+)\s*\?\?\s*(?:'([^'\\]*)'|"([^"\\$]*)")\s*\}\}""",
                              lambda q: _h2.escape(_d[q.group(1)] if isinstance(_d.get(q.group(1)), str)
                                                   else (q.group(2) if q.group(2) is not None else q.group(3))), html)
                # {{ $k ? 'a' : 'b' }} and {{ $k ?: 'b' }} over known data, with PHP truthiness ("" and "0" and [] are false).
                def _tern(q):
                    v = _d.get(q.group(1))
                    if v is None:
                        return q.group(0)
                    truthy = bool(v) and v != "0"
                    if q.group(2) is None:
                        if not truthy:
                            return _h2.escape(q.group(4))
                        return _h2.escape(v) if isinstance(v, str) else q.group(0)
                    return _h2.escape(q.group(2) if truthy else q.group(4))
                html = re.sub(r"""\{\{\s*\$(\w+)\s*\?\s*(?:'([^'\\]*)'\s*)?:\s*('([^'\\]*)')\s*\}\}""", _tern, html)
                # {{ $list[N] }} (escaped) and {!! $list[N] !!} for literal lists; a missing index stays a TODO.
                def _idx(q, esc):
                    v = _d.get(q.group(1))
                    i = int(q.group(2))
                    if not isinstance(v, list) or not (0 <= i < len(v)) or not isinstance(v[i], str):
                        return q.group(0)
                    return _h2.escape(v[i]) if esc else v[i]
                def _key(q, esc):
                    v = _d.get(q.group(1))
                    if not isinstance(v, dict) or not isinstance(v.get(q.group(2)), str):
                        return q.group(0)
                    return _h2.escape(v[q.group(2)]) if esc else v[q.group(2)]
                html = re.sub(r"\{\{\s*\$(\w+)\[\s*'(\w+)'\s*\]\s*\}\}", lambda q: _key(q, True), html)
                html = re.sub(r"\{!!\s*\$(\w+)\[\s*'(\w+)'\s*\]\s*!!\}", lambda q: _key(q, False), html)
                html = re.sub(r"\{\{\s*\$(\w+)\[\s*(\d+)\s*\]\s*\}\}", lambda q: _idx(q, True), html)
                html = re.sub(r"\{!!\s*\$(\w+)\[\s*(\d+)\s*\]\s*!!\}", lambda q: _idx(q, False), html)
                # {{ $k OP 'lit' ? 'a' : 'b' }} with == != === !== < > <= >= (PHP 8 string comparison: numeric strings compare as numbers).
                def _cmpt(q):
                    v, op, lit = _d.get(q.group(1)), q.group(2), (q.group(3) if q.group(3) is not None else q.group(4))
                    if not isinstance(v, str):
                        return q.group(0)
                    num = r"\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*"
                    if op in ("===", "!=="):
                        c = 0 if (v == lit and q.group(4) is None) else 1
                    elif q.group(4) is not None and not re.fullmatch(num, v):
                        return q.group(0)
                    elif re.fullmatch(num, v) and re.fullmatch(num, lit):
                        a, b = float(v), float(lit)
                        c = (a > b) - (a < b)
                    else:
                        c = (v > lit) - (v < lit) if op not in ("==", "!=") else (0 if v == lit else 1)
                    ok = {"==": c == 0, "===": c == 0, "!=": c != 0, "!==": c != 0, "<": c < 0, ">": c > 0, "<=": c <= 0, ">=": c >= 0}[op]
                    return _h2.escape(q.group(5) if ok else q.group(6))
                html = re.sub(r"""\{\{\s*\$(\w+)\s*(===|!==|==|!=|<=|>=|<|>)\s*(?:'([^'\\]*)'|(-?\d+(?:\.\d+)?))\s*\?\s*'([^'\\]*)'\s*:\s*'([^'\\]*)'\s*\}\}""", _cmpt, html)
            if html is not None:
                # {{ fn($k) }} for a few pure PHP string functions over literal data (escaped); count() for lists.
                _fns = {"strtoupper": str.upper, "strtolower": str.lower, "ucfirst": lambda x: x[:1].upper() + x[1:],
                        "lcfirst": lambda x: x[:1].lower() + x[1:], "ucwords": lambda x: re.sub(r"(^|\s)(\S)", lambda q: q.group(1) + q.group(2).upper(), x),
                        "trim": lambda x: x.strip(" \t\n\r\0\x0b"), "strlen": lambda x: str(len(x.encode("utf-8"))),
                        "strrev": lambda x: x[::-1], "nl2br": lambda x: x}
                def _num(op):
                    def g(x):
                        import math, decimal
                        if not re.fullmatch(r"-?\d+(?:\.\d+)?", x):
                            raise ValueError
                        v = float(x) if "." in x else int(x)
                        if op == "abs":
                            r = abs(v)
                        elif op == "intval":
                            r = int(v)
                        elif op == "floor":
                            r = float(math.floor(v))
                        elif op == "ceil":
                            r = float(math.ceil(v))
                        else:
                            r = float(decimal.Decimal(x).quantize(decimal.Decimal(1), rounding=decimal.ROUND_HALF_UP))
                        return str(r) if isinstance(r, int) else format(r, ".14g")
                    return g
                for _op in ("abs", "intval", "floor", "ceil", "round"):
                    _fns[_op] = _num(_op)
                # multi-argument calls over literals and known $vars: str_repeat, substr (ASCII), str_replace, implode, number_format(int)
                def _fnargs(q):
                    f, raw = q.group(1), q.group(2)
                    args = []
                    for a in re.findall(r"""\s*('[^'\\]*'|"[^"\\$]*"|-?\d+|\$\w+)\s*(?:,|$)""", raw):
                        args.append(data.get(a[1:]) if a[0] == "$" else (a[1:-1] if a[0] in "'\"" else int(a)))
                    if ",".join(re.sub(r"\s", "", x) for x in re.findall(r"""'[^'\\]*'|"[^"\\$]*"|-?\d+|\$\w+""", raw)) != re.sub(r"\s", "", raw) or None in args:
                        return q.group(0)
                    try:
                        if f == "str_repeat" and len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], int) and 0 <= args[1] <= 1000:
                            r = args[0] * args[1]
                        elif f == "substr" and len(args) in (2, 3) and isinstance(args[0], str) and args[0].isascii() and all(isinstance(x, int) for x in args[1:]):
                            s0, st = args[0], args[1]
                            st = max(len(s0) + st, 0) if st < 0 else st
                            if st > len(s0):
                                r = ""
                            elif len(args) == 2:
                                r = s0[st:]
                            else:
                                ln = args[2]
                                r = s0[st:st + ln] if ln >= 0 else s0[st:len(s0) + ln]
                        elif f == "str_replace" and len(args) == 3 and all(isinstance(x, str) for x in args) and args[0]:
                            r = args[2].replace(args[0], args[1])
                        elif f == "implode" and len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], list):
                            r = args[0].join(args[1])
                        elif f == "round" and len(args) == 2 and isinstance(args[0], str) and re.fullmatch(r"-?\d+(?:\.\d+)?", args[0]) and isinstance(args[1], int) and 0 <= args[1] <= 10:
                            import decimal
                            d = decimal.Decimal(args[0]).quantize(decimal.Decimal(1).scaleb(-args[1]), rounding=decimal.ROUND_HALF_UP)
                            r = format(float(d), ".14g")
                        elif f == "number_format" and len(args) in (1, 2, 3, 4) and all(isinstance(x, str) for x in args[2:]) and isinstance(args[0], str) and re.fullmatch(r"-?\d+(?:\.\d+)?", args[0]) and (len(args) == 1 or (isinstance(args[1], int) and 0 <= args[1] <= 10)):
                            import decimal
                            nd = args[1] if len(args) >= 2 else 0
                            d = decimal.Decimal(args[0]).quantize(decimal.Decimal(1).scaleb(-nd), rounding=decimal.ROUND_HALF_UP)
                            r = f"{d:,.{nd}f}"
                            if r.startswith("-") and not d:
                                r = r[1:]
                            if len(args) > 2:
                                dp, ts = args[2], args[3] if len(args) == 4 else ","
                                r = r.replace(",", "\x02").replace(".", dp).replace("\x02", ts)
                        else:
                            return q.group(0)
                    except Exception:
                        return q.group(0)
                    return _h2.escape(r)
                html = re.sub(r"\{\{\s*(\w+)\s*\(([^(){}]*,[^(){}]*|\s*(?:\$\w+|'[^'\\]*'|-?\d+)\s*)\)\s*\}\}", _fnargs, html)
                def _fn(q):
                    # nested calls apply innermost first: {{ ucfirst(trim($k)) }}
                    fs = re.findall(r"(\w+)\s*\(", q.group(1))
                    if len(fs) != q.group(3).count(")"):
                        return q.group(0)
                    val = data.get(q.group(2))
                    for f in reversed(fs):
                        if f == "count" and isinstance(val, list):
                            val = str(len(val))
                        elif f in _fns and f != "nl2br" and isinstance(val, str) and (val.isascii() or f in ("strlen", "trim")):
                            try:
                                val = _fns[f](val)
                            except ValueError:
                                return q.group(0)
                        else:
                            return q.group(0)
                    return _h2.escape(val)
                html = re.sub(r"\{\{\s*((?:\w+\s*\(\s*)+)\$(\w+)\s*((?:\)\s*)+)\}\}", _fn, html)
            rq = []
            if html is not None:
                def _rq(q):
                    rq.append((q.group(2), q.group(4) or ""))
                    return "%sRQ%d%s" % (chr(1), len(rq) - 1, chr(1))
                html = re.sub(r"\{\{\s*request\(\s*(['\"])(\w+)\1\s*(?:,\s*(['\"])([^'\"]*)\3\s*)?\)\s*\}\}", _rq, html)
            # Only plain HTML views: any Blade syntax ({{ }}, {!! !!}, @directives) stays a 501 TODO.
            if html is not None and ("{{" in html or "{!!" in html or re.search(r"(?m)^\s*@\w", html) or re.search(r"(?<![\w@])@(?:if|elseif|else|endif|isset|endisset|unless|foreach|for|while|php|include|extends|section|yield|csrf|method)\b", html)):
                html = None
            if html is not None:
                html = html.replace("\x00LB\x00", "{{")
            if "{" in full:
                continue
            tr_v = None
            if html is not None:
                tparts = []
                for i, seg in enumerate(re.split(chr(1) + r"RQ(\d+)" + chr(1), html)):
                    if i % 2:
                        tparts.append(("query_esc", rq[int(seg)]))
                    elif seg:
                        tparts.append(("lit", seg))
                tr_v = ("text", tparts or [("lit", "")])
            out.append(("GET", full, [], tr_v, os.path.relpath(vf, root).replace(os.sep, "/")))
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

/// PHP 8 `$x == 'lit'` for a request value (strict `===` is a plain string comparison instead).
/// Numeric strings (optional surrounding whitespace, sign, decimals, exponent) compare as numbers.
fn php_loose_eq(v: Option<&serde_json::Value>, lit: &str) -> bool {
    fn num(s: &str) -> Option<f64> {
        let t = s.trim_matches(|c: char| matches!(c, ' ' | '\t' | '\n' | '\r' | '\x0b' | '\x0c'));
        let ok = !t.is_empty()
            && t.bytes().all(|b| b.is_ascii_digit() || matches!(b, b'+' | b'-' | b'.' | b'e' | b'E'))
            && t.bytes().any(|b| b.is_ascii_digit());
        if ok { t.parse::<f64>().ok() } else { None }
    }
    match v {
        None | Some(serde_json::Value::Null) => lit.is_empty(),
        Some(serde_json::Value::Bool(b)) => *b == !(lit.is_empty() || lit == "0"),
        Some(serde_json::Value::String(s)) => match (num(s), num(lit)) {
            (Some(a), Some(b)) => a == b,
            _ => s == lit,
        },
        Some(serde_json::Value::Number(n)) => match (n.as_f64(), num(lit)) {
            (Some(a), Some(b)) => a == b,
            _ => n.to_string() == lit,
        },
        _ => false,
    }
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
    return tr[0] == "input_all" or (tr[0] == "text" and any(k in ("query", "query_esc") for k, _ in tr[1]))


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


def _int_expr(src, data):
    """Evaluate a PHP integer expression with + - * / % and parentheses over literals and known $vars.

    Returns the decimal text, or None when it is not purely integer or PHP would differ (inexact /, division by 0)."""
    toks = re.findall(r"\s*(\d+\.\d+|\d+|\$\w+|[-+*/%()])", src)
    if re.sub(r"\s", "", src) != "".join(toks):
        return None
    vals = []
    for t in toks:
        if t[0] == "$":
            v = data.get(t[1:])
            if not isinstance(v, str) or not re.fullmatch(r"-?\d+(?:\.\d+)?", v):
                return None
            vals.append(float(v) if "." in v else int(v))
        else:
            vals.append(int(t) if t.isdigit() else float(t) if t[0].isdigit() else t)
    pos = [0]

    class _Bad(Exception):
        pass

    def peek():
        return vals[pos[0]] if pos[0] < len(vals) else None

    def take():
        pos[0] += 1
        return vals[pos[0] - 1]

    def atom():
        t = take() if peek() is not None else None
        if t == "(":
            r = add()
            if take() != ")":
                raise _Bad
            return r
        if t == "-":
            return -atom()
        if t == "+":
            return atom()
        if isinstance(t, (int, float)):
            return t
        raise _Bad

    def mul():
        r = atom()
        while peek() in ("*", "/", "%"):
            o, x = take(), atom()
            if o == "*":
                r *= x
            elif x == 0 or (o == "%" and (isinstance(r, float) or isinstance(x, float))):
                raise _Bad
            elif o == "/" and (isinstance(r, float) or isinstance(x, float) or r % x):
                r = r / x
            elif o == "/":
                r = r // x if (r >= 0) == (x > 0) else -(abs(r) // abs(x))
            else:
                r = abs(r) % abs(x) * (1 if r >= 0 else -1)
        return r

    def add():
        r = mul()
        while peek() in ("+", "-"):
            o, x = take(), mul()
            r = r + x if o == "+" else r - x
        return r

    try:
        r = add()
    except (_Bad, IndexError):
        return None
    if pos[0] != len(vals):
        return None
    if isinstance(r, float):
        if r != r or abs(r) >= 1e14 or (r != 0 and abs(r) < 1e-4):
            return None
        return format(r, ".14g")
    return str(r)


def _php_array(src):
    """Parse a PHP array literal of single-quoted strings, nested lists and 'key' => value pairs.

    Returns a list (no keys) or a dict (all keys given), or None when anything else appears."""
    pos = [0]

    def ws():
        while pos[0] < len(src) and src[pos[0]].isspace():
            pos[0] += 1

    def string():
        m = re.compile(r"'([^'\\]*)'").match(src, pos[0])
        if not m:
            return None
        pos[0] = m.end()
        return m.group(1)

    def value():
        ws()
        if src.startswith("[", pos[0]):
            return array()
        return string()

    def array():
        pos[0] += 1
        items, keys = [], []
        while True:
            ws()
            if src.startswith("]", pos[0]):
                pos[0] += 1
                break
            v = value()
            if v is None:
                return None
            ws()
            if src.startswith("=>", pos[0]):
                if not isinstance(v, str):
                    return None
                pos[0] += 2
                k, v = v, value()
                if v is None:
                    return None
                keys.append(k)
            else:
                keys.append(None)
            items.append(v)
            ws()
            if src.startswith(",", pos[0]):
                pos[0] += 1
            elif not src.startswith("]", pos[0]):
                return None
        if all(k is None for k in keys):
            return items
        if any(k is None for k in keys):
            return None
        return dict(zip(keys, items))

    ws()
    if not src.startswith("[", pos[0]):
        return None
    r = array()
    ws()
    return r if pos[0] == len(src) else None
