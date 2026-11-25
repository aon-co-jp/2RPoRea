import os
from torporea.convert import run


def _src(tmp_path):
    s = tmp_path / "src"
    s.mkdir()
    (s / "server.js").write_text("app.get('/users/:id', h)", encoding="utf-8")
    (s / "package.json").write_text('{"dependencies":{"express":"4"}}', encoding="utf-8")
    return str(s)


def test_default_has_no_node(tmp_path):
    out = str(tmp_path / "o")
    assert run(_src(tmp_path), out) == 0
    assert os.path.isdir(os.path.join(out, "reaxt-server")) and not os.path.exists(os.path.join(out, "node-client"))


def test_node_opt_in(tmp_path):
    out = str(tmp_path / "o")
    assert run(_src(tmp_path), out, node=True) == 0
    t = open(os.path.join(out, "node-client", "src", "client.ts"), encoding="utf-8").read()
    assert 'call("GetUsersById"' in t
