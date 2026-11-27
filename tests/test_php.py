import os

from torporea.php import routes, render_main, translate

WEB = """<?php
use Illuminate\\Support\\Facades\\Route;
use App\\Http\\Controllers\\UserController;

// comment Route::get('/ignored', fn() => 'no');
Route::get('/', function () {
    return 'Welcome';
});
Route::get('/hello/{name}', fn($name) => 'Hello, ' . $name . '!');
Route::get('/users/{id}', [UserController::class, 'show']);
Route::post('/users', 'UserController@store');
Route::delete('/x', function () { $a = count([]); return 'no'; });
Route::patch('/greet/{name}', function ($name) {
    $greeting = 'Hi ' . $name;
    $msg = $greeting . '!';
    return $msg;
});
Route::get('/cfg', function () { $data = ['v' => 2]; return response()->json($data); });
"""
API = """<?php
use Illuminate\\Support\\Facades\\Route;
Route::get('/status', function () {
    return response()->json(['ok' => true, 'n' => 3, 'tags' => ['a', "b"], 'nil' => null]);
});
"""
CTRL = """<?php
namespace App\\Http\\Controllers;
class UserController extends Controller {
    public function show($id) { return ['id' => 7, 'name' => 'Taro']; }
    public function store(Request $r) { return User::create($r->all()); }
}
"""


def make(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(WEB, encoding="utf-8")
    (tmp_path / "routes" / "api.php").write_text(API, encoding="utf-8")
    d = tmp_path / "app" / "Http" / "Controllers"
    d.mkdir(parents=True)
    (d / "UserController.php").write_text(CTRL, encoding="utf-8")
    return str(tmp_path)


def test_routes_and_translation(tmp_path):
    rs = {(m, p): tr for m, p, _, tr, _ in routes(make(tmp_path))}
    assert ("GET", "/ignored") not in rs
    assert rs[("GET", "/")] == ("text", [("lit", "Welcome")])
    assert rs[("GET", "/hello/:name")] == ("text", [("lit", "Hello, "), ("param", "name"), ("lit", "!")])
    assert rs[("GET", "/users/:id")] == ("json", {"id": 7, "name": "Taro"})
    assert rs[("POST", "/users")] is None
    assert rs[("DELETE", "/x")] is None
    assert rs[("GET", "/api/status")] == ("json", {"ok": True, "n": 3, "tags": ["a", "b"], "nil": None})


def test_translate_rejects_logic():
    assert translate("return $undefined;", []) is None
    assert translate("return strtoupper('a');", []) is None
    assert translate("return 'a'; return 'b';", []) is None


def test_render(tmp_path):
    s = render_main(routes(make(tmp_path)))
    assert '.at("/hello/:name", get(' in s and "NOT_IMPLEMENTED" in s and 'params.get("name")' in s


def test_locals_and_patch(tmp_path):
    rts = routes(make(tmp_path))
    rs = {(m, p): tr for m, p, _, tr, _ in rts}
    assert rs[("PATCH", "/greet/:name")] == ("text", [("lit", "Hi "), ("param", "name"), ("lit", "!")])
    assert rs[("GET", "/cfg")] == ("json", {"v": 2})
    s = render_main(rts)
    assert '.at("/greet/:name", patch(' in s


def test_locals_rejects():
    assert translate("$x = foo(); return $x;", []) is None
    assert translate("$x = 'a'; if ($x) { return 'b'; }", []) is None
    assert translate("$name = 'z'; return $name;", ["name"]) is None
    assert translate("$x = 'a;b'; return $x . 'c';", []) == ("text", [("lit", "a;b"), ("lit", "c")])


def test_if_on_route_parameter():
    t = translate("if ($name === 'admin') { return 'Hello boss'; } return 'Hi ' . $name;", ["name"])
    assert t == ("if", "name", False, "admin", ("text", [("lit", "Hello boss")]), ("text", [("lit", "Hi "), ("param", "name")]))
    t2 = translate("if ($n != \"a\") { return ['ok' => true]; } else { return 'a'; }", ["n"])
    assert t2[:4] == ("if", "n", True, "a") and t2[4] == ("json", {"ok": True})
    # chained: the rest is itself an if
    t3 = translate("if ($n == 'a') { return '1'; } if ($n == 'b') { return '2'; } return '3';", ["n"])
    assert t3[5][0] == "if"
    # not a route parameter, or a body with logic inside: still 501
    assert translate("if ($x == 'a') { return '1'; } return '2';", ["n"]) is None
    assert translate("if ($n == 'a') { foo(); return '1'; } return '2';", ["n"]) is None
    s = render_main([("GET", "/w/:name", ["name"], t, "routes/web.php")])
    assert 'if params.get("name").unwrap_or("") == "admin" {' in s and "} else {" in s


def test_request_input():
    t = translate("$who = $request->input('who', 'guest'); return 'Hi ' . $who . ' ' . request('n');", [])
    assert t == ("text", [("lit", "Hi "), ("query", ("who", "guest")), ("lit", " "), ("query", ("n", ""))])
    assert translate("return $request->input($k);", []) is None
    s = render_main([("GET", "/q", [], t, "routes/web.php")])
    assert 'input.get("who")' in s and '"guest".to_string()' in s and "async fn read_input(" in s


def test_request_all():
    assert translate("return $request->all();", []) == ("input_all",)
    assert translate("return response()->json($request->all());", []) == ("input_all",)
    assert translate("return $request->all() . 'x';", []) is None
    s = render_main([("POST", "/echo", [], ("input_all",), "routes/web.php")])
    assert "let input = read_input(req).await;" in s and "json_response(StatusCode::OK, &input)" in s


def test_request_only_except():
    assert translate("return response()->json($request->only(['a', 'c']));", []) == ("input_all", "only", ["a", "c"])
    assert translate("return $request->except(['a']);", []) == ("input_all", "except", ["a"])
    assert translate("return $request->only($keys);", []) is None
    s = render_main([("POST", "/o", [], ("input_all", "except", ["a"]), "routes/web.php")])
    assert "let input = read_input(req).await;" in s and "!keys.contains" in s


def test_request_has_filled():
    t = translate("if ($request->filled('n')) { return 'a'; } return 'b';", [])
    assert t[0] == "ifhas" and t[1:4] == ("filled", "n", False)
    t = translate("if (!$request->has('n')) { return 'a'; } else { return 'b'; }", [])
    assert t[0] == "ifhas" and t[1:4] == ("has", "n", True)
    s = render_main([("POST", "/h", [], t, "routes/web.php")])
    assert "if !input.contains_key(\"n\")" in s and "let input = read_input(req).await;" in s


def test_request_has_combined():
    t = translate("if ($request->filled('a') && !$request->has('b') || $request->has('c')) { return 'y'; } return 'n';", [])
    assert t[0] == "ifcond" and t[1] == [("", False, "filled", "a"), ("&&", True, "has", "b"), ("||", False, "has", "c")]
    s = render_main([("POST", "/b", [], t, "routes/web.php")])
    assert '&& !input.contains_key("b") || input.contains_key("c")' in s


def test_abort():
    assert translate("abort(404);", []) == ("abort", 404, "")
    assert translate("abort(403, 'Forbidden');", []) == ("abort", 403, "Forbidden")
    s = render_main([("GET", "/a", [], ("abort", 403, "no"), "routes/web.php")])
    assert "StatusCode::from_u16(403)" in s


def test_redirect():
    assert translate("return redirect('/home');", []) == ("redirect", "/home")
    assert translate("return redirect($to);", []) is None
    s = render_main([("GET", "/o", [], ("redirect", "/n"), "routes/web.php")])
    assert "StatusCode::FOUND" in s and '"/n".parse()' in s


def test_back():
    assert translate("return back();", []) == ("back",)
    assert translate("return redirect()->back();", []) == ("back",)
    t = translate("if (!$request->filled('t')) { return back(); } return 'ok';", [])
    s = render_main([("POST", "/s", [], t, "routes/web.php")])
    assert s.index("let back_referer") < s.index("let input = read_input")


def test_response_status():
    assert translate("return response('Created', 201);", []) == ("status", 201, ("text", [("lit", "Created")]))
    assert translate("return response()->json(['ok' => true], 201);", []) == ("status", 201, ("json", {"ok": True}))
    assert translate("return response('x');", []) == ("text", [("lit", "x")])
    s = render_main([("GET", "/g", [], ("status", 410, ("text", [("lit", "g")])), "routes/web.php")])
    assert "StatusCode::from_u16(410)" in s


def test_response_header():
    t = translate("return response('a', 201)->header('X-Id', '7');", [])
    assert t == ("hdr", [("X-Id", "7")], ("status", 201, ("text", [("lit", "a")])))
    s = render_main([("GET", "/h", [], t, "routes/web.php")])
    assert 'insert("x-id", "7".parse().unwrap())' in s


def test_redirect_route(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::get('/dash', function () { return 'd'; })->name('dashboard');\n"
        "Route::get('/go', function () { return redirect()->route('dashboard'); });\n"
        "Route::get('/x', function () { return to_route('missing'); });\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/go"] == ("redirect", "/dash") and rs["/x"] is None


def test_redirect_route_params(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::get('/users/{id}', function ($id) { return 'u'; })->name('users.show');\n"
        "Route::get('/me/{id}', function ($id) { return redirect()->route('users.show', ['id' => $id]); });\n"
        "Route::get('/bad', function () { return to_route('users.show'); });\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/me/:id"] == ("redirectp", [("lit", "/users/"), ("param", "id")]) and rs["/bad"] is None


def test_redirect_route_extra_query(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::get('/u/{id}', function ($id) { return 'u'; })->name('u');\n"
        "Route::get('/a/{id}', function ($id) { return to_route('u', ['id' => $id, 'tab' => 'a b']); });\n"
        "Route::get('/b/{id}', function ($id) { return to_route('u', ['id' => '1', 'x' => $id]); });\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/a/:id"] == ("redirectp", [("lit", "/u/"), ("param", "id"), ("lit", "?tab="), ("lit", "a%20b")]) and rs["/b/:id"][1][-1] == ("penc", "id")


def test_route_redirect_shortcuts(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::redirect('/here', '/there');\nRoute::permanentRedirect('/old', '/new');\n"
        "Route::redirect('/t', '/u', 307);\n", encoding="utf-8")
    rs = {(m, p): tr for m, p, _, tr, _ in routes(str(tmp_path))}
    assert rs[("GET", "/here")] == ("redirect", "/there")
    assert rs[("POST", "/old")] == ("status", 301, ("redirect", "/new"))
    assert rs[("GET", "/t")] == ("status", 307, ("redirect", "/u"))


def test_route_view_static(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views" / "pages"
    v.mkdir(parents=True)
    (v / "about.blade.php").write_text("<h1>About</h1>\n", encoding="utf-8")
    (v / "dyn.blade.php").write_text("<h1>{{ $x }}</h1>\n", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::view('/about', 'pages.about');\nRoute::view('/dyn', 'pages.dyn');\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/about"] == ("text", [("lit", "<h1>About</h1>\n")]) and rs["/dyn"] is None


def test_route_view_with_data(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "hi.blade.php").write_text("<h1>Hi {{ $name }}</h1>", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::view('/hi', 'hi', ['name' => 'T <&>']);\nRoute::view('/hj', 'hi', ['name' => $x]);\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/hi"] == ("text", [("lit", "<h1>Hi T &lt;&amp;&gt;</h1>")]) and rs["/hj"] is None


def test_paren_conditions(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/c', function (Request $request) {\n"
        "    if (($request->has('a') || $request->has('b')) && !$request->filled('c')) { return 'yes'; }\n"
        "    return 'no';\n});\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    tr = rs["/c"]
    assert tr[0] == "ifcond" and [k for _, _, k, _ in tr[1]] == ["(", "has", "has", ")", "filled"]


def test_missing(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/m', function (Request $request) {\n    if ($request->missing('a')) { return 'none'; }\n    return 'got';\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/m"]
    assert tr[0] == "ifhas" and tr[1] == "missing"


def test_boolean(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/b', function (Request $request) {\n    if ($request->boolean('on')) { return 'T'; }\n    return 'F';\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/b"]
    assert tr[0] == "ifhas" and tr[1] == "boolean"


def test_has_any(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/a', function (Request $request) {\n    if ($request->hasAny(['a', 'b']) && $request->filled(['c', 'd'])) { return 'ok'; }\n    return 'ng';\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/a"]
    assert tr[0] == "ifcond" and [k for _, _, k, _ in tr[1]] == ["(", "has", "has", ")", "(", "filled", "filled", ")"]


def test_input_eq_condition(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/e', function (Request $request) {\n    if ($request->input('m') === 'd' || $request->input('y') != 'z') { return 'hit'; }\n    return 'miss';\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/e"]
    assert tr[0] == "ifcond" and [(n, k) for _, n, k, _ in tr[1]] == [(False, "eq"), (True, "eq")]


def test_elseif(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/e', function (Request $request) {\n    if ($request->has('a')) { return 'a'; } elseif ($request->has('b')) { return 'b'; } else { return 'c'; }\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/e"]
    assert tr[0] == "ifhas" and tr[5][0] == "ifhas"
