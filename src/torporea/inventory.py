"""Inventory of Node-style server routes and frontend pages, as input for Reaxt conversion.

This does NOT convert code. It lists what a Reaxt port has to cover (Express/Nest routes,
Next/Nuxt file-based pages, React/Vue components) so MIGRATION.md is concrete instead of a bare TODO.
"""
from __future__ import annotations

import os
import re

from .detect import _read, _walk

_EXPRESS = re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)['\"`]")
_RR_JSX = re.compile(r"""<Route\b[^>]*?\bpath=["']([^"']+)["'][^<]*?(?:element=\{\s*<(\w+)|Component=\{(\w+)\})""")
_RR_OBJ = re.compile(r"path:\s*[\"']([^\"']+)[\"']\s*,\s*(?:element:\s*<(\w+)|Component:\s*(\w+))")
_NEST_CTRL = re.compile(r"@Controller\(\s*['\"`]?([^'\"`)]*)['\"`]?\s*\)")
_NEST_ROUTE = re.compile(r"@(Get|Post|Put|Patch|Delete)\(\s*['\"`]?([^'\"`)]*)['\"`]?\s*\)")


def _page_route(rel: str):
    rel = rel.replace("\\", "/")
    for base in ("pages/", "src/pages/", "app/", "src/app/"):
        if rel.startswith(base):
            r = rel[len(base):]
            r = re.sub(r"\.(jsx?|tsx?|vue)$", "", r)
            if base.endswith("app/"):
                if not r.endswith("page"):
                    return None
                r = r[: -len("page")]
            r = re.sub(r"/?index$", "", r)
            r = re.sub(r"\[\.\.\.(\w+)\]", r"*\1", r)
            r = re.sub(r"\[(\w+)\]", r":\1", r)
            return "/" + r.strip("/")
    return None


def inventory(root: str) -> dict:
    routes, pages, components = [], [], []
    for p in _walk(root):
        rel = os.path.relpath(p, root).replace("\\", "/")
        ext = os.path.splitext(p)[1].lower()
        if ext in (".js", ".ts", ".mjs", ".cjs", ".jsx", ".tsx"):
            t = _read(p)
            for m, path in _EXPRESS.findall(t):
                routes.append(("express", m.upper(), path, rel))
            prefix = _NEST_CTRL.search(t)
            if prefix is not None:
                base = "/" + prefix.group(1).strip("/")
                for m, path in _NEST_ROUTE.findall(t):
                    routes.append(("nest", m.upper(), (base.rstrip("/") + "/" + path.strip("/")).rstrip("/") or "/", rel))
        if ext in (".jsx", ".tsx", ".js"):
            t2 = _read(p)
            for rx in (_RR_JSX, _RR_OBJ):
                for path, c1, c2 in rx.findall(t2):
                    pages.append(("/" + path.strip("/") if path != "*" else "/*rest", rel + "#" + (c1 or c2)))
        if ext in (".jsx", ".tsx", ".vue", ".js", ".ts"):
            pr = _page_route(rel)
            if pr is not None:
                pages.append((pr, rel))
            elif ext in (".jsx", ".tsx", ".vue"):
                components.append(rel)
    return {"routes": routes, "pages": pages, "components": components}
