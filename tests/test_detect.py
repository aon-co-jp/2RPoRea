import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from torporea.detect import scan


def mk(tmp_path, files):
    for rel, body in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def pairs(root):
    return {(f.kind, f.framework) for f in scan(str(root))}


def test_python_and_react(tmp_path):
    mk(tmp_path, {"app.py": "from flask import Flask\n", "web/package.json": json.dumps({"dependencies": {"react": "19", "next": "15"}})})
    assert {("backend", "flask"), ("frontend", "react"), ("frontend", "next")} <= pairs(tmp_path)


def test_java_cobol_php_nest(tmp_path):
    mk(tmp_path, {"A.java": "import org.springframework.web.bind.annotation.*;", "p.cbl": "IDENTIFICATION DIVISION.",
                  "r.php": "<?php use Illuminate\Support\Facades\Route;",
                  "api/package.json": json.dumps({"dependencies": {"@nestjs/core": "11"}, "devDependencies": {"typescript": "5"}})})
    assert {("backend", "spring"), ("backend", "cobol"), ("backend", "laravel"), ("backend", "nest")} <= pairs(tmp_path)


def test_skips_node_modules(tmp_path):
    mk(tmp_path, {"node_modules/x/a.py": "import flask\n"})
    assert pairs(tmp_path) == set()
