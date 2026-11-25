import os
from torporea.convert import plan, run


def _mk(tmp, rel, text=""):
    p = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


def test_plan_dispatch(tmp_path):
    s = str(tmp_path)
    _mk(s, "a.py", "from flask import Flask\n")
    _mk(s, "B.java", "import org.springframework.web.bind.annotation.*;\n")
    _mk(s, "c.cbl", "IDENTIFICATION DIVISION.\n")
    _mk(s, "package.json", '{"dependencies":{"react":"1","express":"4"}}')
    steps = {x.framework: x for x in plan(s, str(tmp_path / "o"))}
    assert steps["flask"].tool == "2poem" and "rpoem" in steps["flask"].argv
    assert steps["spring"].tool == "java_to" and "rpoem" in steps["spring"].argv
    assert steps["cobol"].tool == "cobol_to"
    assert steps["react"].tool == "todo" and steps["express"].tool == "todo"


def test_dry_run_writes_migration(tmp_path):
    s = str(tmp_path / "src")
    _mk(s, "index.jsx", "")
    out = str(tmp_path / "out")
    assert run(s, out, dry_run=True) == 0
    t = open(os.path.join(out, "MIGRATION.md"), encoding="utf-8").read()
    assert "TODO `react`" in t
