from torporea.reaxt_gen import render


def test_render_stubs():
    s = render([("express", "GET", "/users/:id", "s.js"), ("nest", "POST", "/cats", "c.ts"), ("express", "GET", "/users/:id", "t.js")])
    assert '"GetUsersById"' in s and '"GetUsersById2"' in s and '"Cats"' in s
    assert "Denied::new(501" in s and "TODO: port GET /users/:id from s.js" in s
