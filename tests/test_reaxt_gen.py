from torporea.reaxt_gen import render


def test_render_stubs():
    s = render([("express", "GET", "/users/:id", "s.js"), ("nest", "POST", "/cats", "c.ts"), ("express", "GET", "/users/:id", "t.js")])
    assert '"GetUsersById"' in s and '"GetUsersById2"' in s and '"Cats"' in s
    assert "Denied::new(501" in s and "TODO: port GET /users/:id from s.js" in s


def test_pages():
    from torporea.reaxt_gen import page_file
    assert page_file("/") == "index.rs" and page_file("/blog/:slug") == "blog/[slug].rs" and page_file("/d/*rest") == "d/[...rest].rs"
    s = render([], pages=[("/blog/:slug", "pages/blog/[slug].tsx")])
    assert '.page("blog/[slug].rs"' in s and "TODO: port page /blog/:slug" in s
