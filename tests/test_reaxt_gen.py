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


def test_component_with_state_and_router(tmp_path):
    from torporea.inventory import inventory
    (tmp_path / "App.jsx").write_text('<Routes><Route path="/c" element={<Counter />} /></Routes>', encoding="utf-8")
    (tmp_path / "Counter.jsx").write_text(
        'export function Counter(){ const [n, setN] = useState(0); useEffect(()=>{fetch("/api/x")},[]);\n'
        'return (<div><p>count={n}</p><button onClick={() => setN(n + 1)}>+1</button></div>); }', encoding="utf-8")
    inv = inventory(str(tmp_path))
    assert ("/c", "App.jsx#Counter") in inv["pages"]
    s = render([], pages=[("/c", "App.jsx#Counter")], src_root=str(tmp_path))
    assert "use_state(|| 0i32)" in s and "on_click" in s and "s.update(|c| c + 1i32)" in s
    assert "not ported: useEffect; data fetching fetch(" in s


def test_child_component_inlined(tmp_path):
    (tmp_path / "Nav.jsx").write_text('export function Nav(){ return (<nav><a href="/">{title}</a></nav>); }', encoding="utf-8")
    (tmp_path / "Page.jsx").write_text('export function Page(){ return (<main><Nav title="x" /><p>hi</p></main>); }', encoding="utf-8")
    s = render([], pages=[("/p", "Page.jsx")], src_root=str(tmp_path))
    assert 'element("nav")' in s and 'data-component", "Nav"' in s and "props title not passed" not in s and 'VNode::text("x")' in s
