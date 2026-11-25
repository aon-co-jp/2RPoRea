"""Detect the languages and frameworks of a source tree.

Backend sources: Python (Flask / Django / FastAPI), Java (Spring / JAX-RS / Servlet / Spark),
COBOL, PHP (Laravel), Node.js (Express / Nest.js).
Frontend sources: React, Next.js, Nuxt.js, Vue.  Detection is by files and dependency names only;
nothing is executed.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

SKIP_DIRS = {".git", "node_modules", "target", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".nuxt"}
COBOL_EXT = {".cbl", ".cob", ".cobol", ".cpy"}


@dataclass
class Finding:
    kind: str          # "backend" or "frontend"
    framework: str     # e.g. "flask", "spring", "next"
    language: str      # e.g. "python", "java"
    evidence: list = field(default_factory=list)


def _walk(root: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def _read(p: str, limit: int = 200_000) -> str:
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def _pkg_deps(p: str) -> set:
    try:
        j = json.loads(_read(p))
    except ValueError:
        return set()
    out = set()
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        v = j.get(k)
        if isinstance(v, dict):
            out.update(v)
    return out


def scan(root: str) -> list:
    found: dict = {}

    def add(kind, fw, lang, ev):
        f = found.setdefault((kind, fw), Finding(kind, fw, lang))
        if ev not in f.evidence and len(f.evidence) < 5:
            f.evidence.append(os.path.relpath(ev, root) if os.path.isabs(ev) else ev)

    for p in _walk(root):
        name = os.path.basename(p)
        ext = os.path.splitext(name)[1].lower()
        if name == "package.json":
            deps = _pkg_deps(p)
            for dep, kind, fw in (("next", "frontend", "next"), ("nuxt", "frontend", "nuxt"), ("react", "frontend", "react"),
                                  ("vue", "frontend", "vue"), ("@nestjs/core", "backend", "nest"), ("express", "backend", "express")):
                if dep in deps:
                    add(kind, fw, "typescript" if "typescript" in deps else "javascript", p)
        elif ext == ".py":
            t = _read(p)
            for pat, fw in ((r"^\s*(from|import)\s+flask\b", "flask"), (r"^\s*(from|import)\s+fastapi\b", "fastapi"),
                            (r"^\s*(from|import)\s+django\b", "django")):
                if re.search(pat, t, re.M):
                    add("backend", fw, "python", p)
        elif ext == ".java":
            t = _read(p)
            for pat, fw in ((r"org\.springframework\.", "spring"), (r"javax\.ws\.rs|jakarta\.ws\.rs", "jaxrs"),
                            (r"javax\.servlet|jakarta\.servlet", "servlet"), (r"spark\.Spark", "spark")):
                if re.search(pat, t):
                    add("backend", fw, "java", p)
        elif ext in COBOL_EXT:
            add("backend", "cobol", "cobol", p)
        elif ext == ".php":
            if re.search(r"Illuminate\\|use\s+Laravel", _read(p)):
                add("backend", "laravel", "php", p)
        elif ext in (".pl", ".pm", ".psgi"):
            t = _read(p)
            if re.search(r"^\s*use\s+Mojolicious::Lite\b", t, re.M):
                add("backend", "mojolicious", "perl", p)
            elif re.search(r"^\s*use\s+Dancer2?\b", t, re.M):
                add("backend", "dancer", "perl", p)
        elif ext in (".jsx", ".tsx"):
            add("frontend", "react", "typescript" if ext == ".tsx" else "javascript", p)
        elif ext == ".vue":
            add("frontend", "vue", "javascript", p)
    return sorted(found.values(), key=lambda f: (f.kind, f.framework))
