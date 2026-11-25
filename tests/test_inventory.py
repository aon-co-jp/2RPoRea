import os
from torporea.inventory import inventory


def _mk(tmp, rel, text=""):
    p = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


def test_inventory(tmp_path):
    s = str(tmp_path)
    _mk(s, "server.js", "app.get('/users', h); router.post(\"/u/:id\", h)")
    _mk(s, "cats.controller.ts", "@Controller('cats')\nclass C { @Get(':id') f(){} @Post() g(){} }")
    _mk(s, "pages/index.tsx")
    _mk(s, "pages/blog/[slug].tsx")
    _mk(s, "components/Nav.vue")
    i = inventory(s)
    r = {(m, p) for _, m, p, _ in i["routes"]}
    assert ("GET", "/users") in r and ("POST", "/u/:id") in r
    assert ("GET", "/cats/:id") in r and ("POST", "/cats") in r
    pg = {p for p, _ in i["pages"]}
    assert "/" in pg and "/blog/:slug" in pg
    assert any("Nav.vue" in c for c in i["components"])
