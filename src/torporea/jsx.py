"""A small JSX -> Reaxt VNode converter for the STATIC part of a component.

Handled: elements, nesting, fragments, string-literal attributes (className->class, htmlFor->for),
text, self-closing and void tags. NOT handled (kept visible, never dropped silently): `{expr}` children
become a text node `{TODO: expr}`; non-literal attributes (`onClick={...}`, `style={...}`) are listed as
TODO comments. State (useState), effects and data fetching are not ported.
"""
from __future__ import annotations

import re

ATTR = {"className": "class", "htmlFor": "for"}
VOID = {"br", "hr", "img", "input", "meta", "link"}
_TAG = re.compile(r"<(/?)([A-Za-z][\w.-]*)?")


class Node:
    def __init__(self, tag, attrs, children, todo):
        self.tag, self.attrs, self.children, self.todo = tag, attrs, children, todo


def find_jsx(src: str):
    """Text starting at the `<` of the last `return (<` / `return <` in the source."""
    ms = list(re.finditer(r"return\s*\(?\s*(<)", src))
    return src[ms[-1].start(1):] if ms else None


def _balanced(s: str, i: int) -> int:
    d = 0
    while i < len(s):
        if s[i] == "{":
            d += 1
        elif s[i] == "}":
            d -= 1
            if d == 0:
                return i
        i += 1
    return len(s) - 1


def parse(s: str, i: int = 0):
    """Parse one element at s[i] == '<'. Returns (Node, next_index)."""
    m = _TAG.match(s, i)
    tag = m.group(2) or ""
    i = m.end()
    attrs, todo = {}, []
    while i < len(s):
        while s[i].isspace():
            i += 1
        if s.startswith("/>", i):
            return Node(tag, attrs, [], todo), i + 2
        if s[i] == ">":
            i += 1
            break
        am = re.compile(r"([\w:-]+)(\s*=\s*)?").match(s, i)
        if not am:
            i += 1
            continue
        name, i = am.group(1), am.end()
        if am.group(2):
            if s[i] in "\"'":
                q = s[i]
                j = s.index(q, i + 1)
                attrs[ATTR.get(name, name)] = s[i + 1:j]
                i = j + 1
            elif s[i] == "{":
                j = _balanced(s, i)
                todo.append(f"{name}={s[i:j + 1]}")
                i = j + 1
        else:
            attrs[ATTR.get(name, name)] = ""
    children = []
    if tag in VOID:
        return Node(tag, attrs, children, todo), i
    buf = ""
    while i < len(s):
        if s.startswith("</", i):
            if buf.strip():
                children.append(buf.strip())
            j = s.index(">", i)
            return Node(tag, attrs, children, todo), j + 1
        if s[i] == "<":
            if buf.strip():
                children.append(buf.strip())
            buf = ""
            n, i = parse(s, i)
            children.append(n)
        elif s[i] == "{":
            j = _balanced(s, i)
            if buf.strip():
                children.append(buf.strip())
            buf = ""
            children.append(("expr", s[i + 1:j].strip()))
            i = j + 1
        else:
            buf += s[i]
            i += 1
    return Node(tag, attrs, children, todo), i


def _q(t: str) -> str:
    return '"' + t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


class Ctx:
    """Collected state hooks and handlers while converting one component."""

    def __init__(self, states=None):
        self.states = states or {}   # name -> (setter, rust type, rust init)
        self.pre = []                # statements emitted before the VNode expression
        self.n = 0


_STATE = re.compile(r"const\s*\[\s*(\w+)\s*,\s*(set\w+)\s*\]\s*=\s*useState(?:<[^>(]*>)?\(\s*([^)]*?)\s*\)")
_INC = re.compile(r"^\(\s*\)\s*=>\s*(set\w+)\(\s*(\w+)\s*([+-])\s*(\d+)\s*\)$")
_SETLIT = re.compile(r"^\(\s*\)\s*=>\s*(set\w+)\(\s*([^()]+?)\s*\)$")


def _rust_init(v: str):
    if re.fullmatch(r"-?\d+", v):
        return "i32", f"{v}i32"
    if re.fullmatch(r"-?\d+\.\d+", v):
        return "f64", f"{v}f64"
    if v in ("true", "false"):
        return "bool", v
    m = re.fullmatch(r"[\"'](.*)[\"']", v)
    if m:
        return "String", f'String::from({_q(m.group(1))})'
    return None


def find_states(text: str) -> dict:
    out = {}
    for name, setter, init in _STATE.findall(text):
        r = _rust_init(init)
        if r:
            out[name] = (setter, r[0], r[1])
    return out


def unported(text: str) -> list:
    notes = []
    if re.search(r"useEffect\s*\(", text):
        notes.append("useEffect")
    for m in re.finditer(r"(fetch|axios(?:\.\w+)?)\s*\(\s*([^,)]*)", text):
        notes.append(f"data fetching {m.group(1)}({m.group(2).strip()})")
    for m in _STATE.finditer(text):
        if _rust_init(m.group(3)) is None:
            notes.append(f"useState({m.group(3)}) with a non-literal initial value")
    return notes


def _handler(expr: str, ctx):
    """Rust closure body for a simple onClick, or None."""
    by_setter = {v[0]: k for k, v in ctx.states.items()}
    m = _INC.match(expr)
    if m and m.group(1) in by_setter and by_setter[m.group(1)] == m.group(2) and ctx.states[m.group(2)][1] in ("i32", "f64"):
        s = ctx.states[m.group(2)]
        return m.group(1), f"|c| c {m.group(3)} {m.group(4)}{s[1]}"
    m = _SETLIT.match(expr)
    if m and m.group(1) in by_setter:
        r = _rust_init(m.group(2))
        if r and r[0] == ctx.states[by_setter[m.group(1)]][1]:
            return m.group(1), f"|_| {r[1]}"
    return None


def to_rust(n, ctx=None) -> str:
    ctx = ctx or Ctx()
    if isinstance(n, tuple):
        e = n[1]
        if e in ctx.states:
            return f'reaxt::react::VNode::text(format!("{{}}", {e}))'
        return f"reaxt::react::VNode::text({_q('{TODO: ' + e + '}')})"
    if isinstance(n, str):
        return f"reaxt::react::VNode::text({_q(' '.join(n.split()))})"
    if not n.tag:  # fragment
        kids = n.children
        if len(kids) == 1:
            return to_rust(kids[0], ctx)
        out = 'reaxt::react::VNode::element("div")'
    else:
        tag = n.tag if n.tag[0].islower() else "div"
        out = f'reaxt::react::VNode::element("{tag}")'
        if n.tag[0].isupper():
            out += f'.attr("data-component", {_q(n.tag)})'
    for k, v in n.attrs.items():
        out += f'.attr({_q(k)}, {_q(v)})'
    for t in n.todo:
        h = _handler(t.split("=", 1)[1][1:-1].strip(), ctx) if t.startswith("onClick=") else None
        if h:
            ctx.n += 1
            sv = [k for k, v in ctx.states.items() if v[0] == h[0]][0]
            ctx.pre.append(f'let (k{ctx.n}, v{ctx.n}) = reaxt::hydrate::on_click("h{ctx.n}", {{ let s = set_{sv}.clone(); move || s.update({h[1]}) }});')
            out += f".attr(k{ctx.n}, v{ctx.n})"
            continue
        out += f'.attr("data-todo", {_q("TODO attr " + t)})'
    for c in n.children:
        out += f".child({to_rust(c, ctx)})"
    return out + ".build()" if n.tag or len(n.children) != 1 else out


def convert_file(text: str):
    """Rust VNode expression for the component's JSX, or None when no JSX is found."""
    j = find_jsx(text)
    if j is None:
        return None
    try:
        node, _ = parse(j)
    except (ValueError, IndexError):
        return None
    ctx = Ctx(find_states(text))
    body = to_rust(node, ctx)
    lets = "".join(f"let ({n}, set_{n}) = reaxt::react::use_state(|| {v[2]}); " for n, v in ctx.states.items())
    inner = "{ " + lets + " ".join(ctx.pre) + " " + body + " }"
    if ctx.states:
        # hooks need a component instance: render inside run_component, then drop it (SSR keeps no state)
        return ("{ let t = reaxt::react::hooks::run_component(1, || " + inner + "); "
                "reaxt::react::hooks::drop_instance(1); t }")
    return inner
