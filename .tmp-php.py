import re
p = "src/torporea/php.py"
s = open(p, encoding="utf-8").read()
old = '''def translate(body: str, params: list):
    """('json', value) / ('text', parts) for a body made only of simple local assignments
    (`$x = EXPR;`) followed by one `return EXPR;`, else None."""
    stmts ='''
new = '''_IF = re.compile(r"\s*if\s*\(\s*\$(\w+)\s*(===?|!==?)\s*('(?:[^'\\\\]|\\\\.)*'|\\"(?:[^\\"\\\\]|\\\\.)*\\")\s*\)\s*\{([^{}]*)\}\s*", re.S)
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
    stmts ='''
assert old in s
s = s.replace(old, new)
s = s.replace('''def routes(root: str) -> list:''', '''def _leaf_rs(tr) -> str:
    if tr[0] == "if":
        cmp_ = "!=" if tr[2] else "=="
        return "if params.get(%s).unwrap_or(\\"\\") %s %s { %s } else { %s }" % (_rs_str(tr[1]), cmp_, _rs_str(tr[3]), _leaf_rs(tr[4]), _leaf_rs(tr[5]))
    if tr[0] == "json":
        return "hyper_compat::json_response(StatusCode::OK, &serde_json::from_str::<serde_json::Value>(%s).unwrap())" % _rs_str(json.dumps(tr[1], ensure_ascii=False))
    pieces = ["s.push_str(%s);" % _rs_str(v) if k == "lit" else "s.push_str(params.get(%s).unwrap_or(\\"\\"));" % _rs_str(v) for k, v in tr[1]]
    return "{ let mut s = String::new(); %s hyper_compat::html_response(StatusCode::OK, s) }" % " ".join(pieces)


def routes(root: str) -> list:''', 1)
i = s.index('        elif tr[0] == "json":')
j = s.index("        fns.append(")
s = s[:i] + "        else:\n            body = _leaf_rs(tr)\n" + s[j:]
open(p, "w", encoding="utf-8").write(s)
