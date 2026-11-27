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
    # loose != becomes a PHP-style comparison (numeric strings compare as numbers)
    assert t2[0] == "ifcond" and t2[1][0][1:3] == (True, "lpeq") and t2[2] == ("json", {"ok": True})
    # chained: the rest is itself an if
    t3 = translate("if ($n == 'a') { return '1'; } if ($n == 'b') { return '2'; } return '3';", ["n"])
    assert t3[0] == "ifcond" and t3[3][0] == "ifcond"
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
    assert tr[0] == "ifcond" and [(n, k) for _, n, k, _ in tr[1]] == [(False, "eq"), (True, "leq")]


def test_elseif(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/e', function (Request $request) {\n    if ($request->has('a')) { return 'a'; } elseif ($request->has('b')) { return 'b'; } else { return 'c'; }\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/e"]
    assert tr[0] == "ifhas" and tr[5][0] == "ifhas"


def test_param_eq_condition(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::post('/p/{k}', function (Request $request, $k) {\n    if ($k === 'a' && $request->has('x')) { return 'ok'; }\n    return 'ng';\n});\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/p/:k"] if "/p/:k" in {p for _, p, _, _, _ in routes(str(tmp_path))} else next(tr for _, p, _, tr, _ in routes(str(tmp_path)) if p.startswith("/p/"))
    assert tr[0] == "ifcond" and [k for _, _, k, _ in tr[1]] == ["peq", "has"]


def test_view_raw_and_comment(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "r.blade.php").write_text("{{-- c --}}<p>{!! $x !!}|{{ $x }}</p>", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/r', 'r', ['x' => '<b>']);\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/r"]
    assert tr == ("text", [("lit", "<p><b>|&lt;b&gt;</p>")])


def test_view_at_escape(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "a.blade.php").write_text("<p>@{{ x }}</p>", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/a', 'a');\n", encoding="utf-8")
    tr = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/a"]
    assert tr == ("text", [("lit", "<p>{{ x }}</p>")])


def test_view_if_isset(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "c.blade.php").write_text("@if($a)A@else B@endif|@isset($b)b@endisset", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text(
        "<?php\nRoute::view('/c', 'c', ['a' => '0', 'b' => '']);\nRoute::view('/d', 'c', ['b' => 'x']);\n", encoding="utf-8")
    rs = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert rs["/c"] == ("text", [("lit", " B|b")]) and rs["/d"] is None


def test_view_unless(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "u.blade.php").write_text("@unless($a)N@else Y@endunless", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/u', 'u', ['a' => '']);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/u"] == ("text", [("lit", "N")])


def test_view_foreach(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "e.blade.php").write_text("@foreach($xs as $x)<i>{{ $x }}</i>@endforeach@if($xs)Y@endif", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/e', 'e', ['xs' => ['a<b', 'c']]);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/e"] == ("text", [("lit", "<i>a&lt;b</i><i>c</i>Y")])


def test_view_foreach_loop(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "e.blade.php").write_text("@foreach($xs as $x){{ $loop->iteration }}/{{ $loop->count }}={{ $x }}@if(!$loop->last),@endif@endforeach", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/e', 'e', ['xs' => ['a', 'b']]);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/e"] == ("text", [("lit", "1/2=a,2/2=b")])


def test_view_for(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "f.blade.php").write_text("@for($i = 1; $i <= 3; $i++)[{{ $i }}]@endfor", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/f', 'f');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/f"] == ("text", [("lit", "[1][2][3]")])


def test_view_switch(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "s.blade.php").write_text("@switch($t) @case('a') A @break @case(\"b\") B @case('c') C @break @default D @endswitch", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/b', 's', ['t' => 'b']);\nRoute::view('/z', 's', ['t' => 'z']);\n", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/b"] == ("text", [("lit", " B  C ")])
    assert r["/z"] == ("text", [("lit", " D ")])


def test_view_default(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "d.blade.php").write_text("{{ $a ?? 'x<' }}|{{ $b ?? \"y\" }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/d', 'd', ['a' => 'A']);\nRoute::view('/n', 'd');\n", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/d"] == ("text", [("lit", "A|y")])
    assert r["/n"] == ("text", [("lit", "x&lt;|y")])


def test_view_php_assign(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "p.blade.php").write_text("@php($a = 'A')\n@php $b = \"B\"; $c = '<'; @endphp{{ $a }}{{ $b }}{{ $c }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/p', 'p');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/p"] == ("text", [("lit", "\nAB&lt;")])


def test_view_php_int(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "p.blade.php").write_text("@php($n = 42)@php($z = 0){{ $n }}@if($z)Z@else-@endif", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/p', 'p');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/p"] == ("text", [("lit", "42-")])


def test_view_while(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "w.blade.php").write_text("@php($i = 0)@while($i < 3)[{{ $i }}]@php($i++)@endwhile{{ $i }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/w', 'w');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/w"] == ("text", [("lit", "[0][1][2]3")])


def test_view_php_expr(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "p.blade.php").write_text("@php $a = 'x'; $b = $a . \"-y\"; $n = 2; $m = $n + 3 - 1; @endphp{{ $b }}{{ $m }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/p', 'p');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/p"] == ("text", [("lit", "x-y4")])


def test_view_fn(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "f.blade.php").write_text("{{ strtoupper($a) }}|{{ ucfirst($a) }}|{{ strlen($j) }}|{{ count($xs) }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/f', 'f', ['a' => 'ab<', 'j' => '日本', 'xs' => ['1', '2']]);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/f"] == ("text", [("lit", "AB&lt;|Ab&lt;|6|2")])


def test_view_php_muldiv(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "p.blade.php").write_text("@php $a = 2 + 3 * 4; $b = 12 / 4 - 1; $c = -7 % 3; @endphp{{ $a }},{{ $b }},{{ $c }}", encoding="utf-8")
    (v / "q.blade.php").write_text("@php($d = 7 / 2){{ $d }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/p', 'p');\nRoute::view('/q', 'q');\n", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/p"] == ("text", [("lit", "14,2,-1")])
    assert r["/q"] == ("text", [("lit", "3.5")])


def test_view_php_parens(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "p.blade.php").write_text("@php($n = 3)@php($a = (2 + $n) * (4 - 1))@php $b = -(10 - 4) / 2; @endphp{{ $a }},{{ $b }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/p', 'p');\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/p"] == ("text", [("lit", "15,-3")])


def test_view_fn_nested(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "f.blade.php").write_text("{{ ucfirst(trim($a)) }}|{{ strlen(trim($a)) }}|{{ strtoupper(count($xs)) }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/f', 'f', ['a' => '  hi ', 'xs' => ['1']]);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/f"] == ("text", [("lit", "Hi|2|1")])


def test_view_fn_args(tmp_path):
    (tmp_path / "routes").mkdir()
    v = tmp_path / "resources" / "views"
    v.mkdir(parents=True)
    (v / "f.blade.php").write_text("{{ str_repeat($a, 3) }}|{{ substr($w, -3) }}|{{ substr($w, 1, 2) }}|{{ str_replace('l', 'L', $w) }}|{{ implode(', ', $xs) }}|{{ number_format($n) }}", encoding="utf-8")
    (tmp_path / "routes" / "web.php").write_text("<?php\nRoute::view('/f', 'f', ['a' => '<', 'w' => 'hello', 'xs' => ['a', 'b'], 'n' => '1234567']);\n", encoding="utf-8")
    assert {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}["/f"] == ("text", [("lit", "&lt;&lt;&lt;|llo|el|heLLo|a, b|1,234,567")])


def test_view_request_value(tmp_path):
    import torporea.php as php
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/rq', 'rq');\n", encoding="utf-8")
    (tmp_path / "resources/views/rq.blade.php").write_text("<p>{{ request('name', 'guest') }}</p>", encoding="utf-8")
    r = [x for x in php.routes(str(tmp_path)) if x[1] == "/rq"][0]
    assert r[3] == ("text", [("lit", "<p>"), ("query_esc", ("name", "guest")), ("lit", "</p>")])


def test_view_numeric_functions(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/n', 'n');\n", encoding="utf-8")
    (tmp_path / "resources/views/n.blade.php").write_text("@php($x = '-3.7')@php($y = '2.5'){{ abs($x) }} {{ floor($x) }} {{ ceil($x) }} {{ round($x) }} {{ intval($x) }} {{ round($y) }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/n"] == ("text", [("lit", "3.7 -4 -3 -4 -3 3")])


def test_view_round_precision(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/r', 'r');\n", encoding="utf-8")
    (tmp_path / "resources/views/r.blade.php").write_text("@php($x = '1.955'){{ round($x, 2) }} {{ round('-2.345', 2) }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/r"] == ("text", [("lit", "1.96 -2.35")])


def test_view_number_format_decimals(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/n', 'n');\n", encoding="utf-8")
    (tmp_path / "resources/views/n.blade.php").write_text("@php($x = '1234.565'){{ number_format($x, 2) }} {{ number_format($x) }} {{ number_format('-0.004', 2) }} {{ number_format('1000') }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/n"] == ("text", [("lit", "1,234.57 1,235 0.00 1,000")])


def test_view_number_format_separators(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/n', 'n');\n", encoding="utf-8")
    (tmp_path / "resources/views/n.blade.php").write_text("{{ number_format('1234567.891', 2, ',', '.') }} {{ number_format('1234.5', 2, ',') }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/n"] == ("text", [("lit", "1.234.567,89 1,234,50")])


def test_view_ternary(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/t', 't');\n", encoding="utf-8")
    (tmp_path / "resources/views/t.blade.php").write_text("@php($a = 'x')@php($z = '0'){{ $a ? 'yes' : 'no' }} {{ $z ? 'yes' : 'no' }} {{ $a ?: 'd' }} {{ $z ?: 'd' }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/t"] == ("text", [("lit", "yes no x d")])


def test_view_compare_ternary(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/c', 'c');\n", encoding="utf-8")
    (tmp_path / "resources/views/c.blade.php").write_text("@php($n = '10'){{ $n == '1e1' ? 'T' : 'F' }}{{ $n === 10 ? 'T' : 'F' }}{{ $n < '9' ? 'T' : 'F' }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/c"] == ("text", [("lit", "TFF")])


def test_view_list_index(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/i', 'i', ['xs' => ['a', '<b>']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/i.blade.php").write_text("{{ $xs[1] }}|{!! $xs[0] !!}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/i"] == ("text", [("lit", "&lt;b&gt;|a")])


def test_view_assoc_key(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/a', 'a', ['u' => ['name' => 'Ann', 'tag' => '<i>']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/a.blade.php").write_text("{{ $u['name'] }}|{{ $u['tag'] }}|{!! $u['tag'] !!}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/a"] == ("text", [("lit", "Ann|&lt;i&gt;|<i>")])


def test_view_foreach_key_value(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/f', 'f', ['u' => ['a' => 'x', 'b' => '<y>'], 'xs' => ['p', 'q']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("@foreach($u as $k => $v){{ $k }}={{ $v }};@endforeach@foreach($xs as $i => $x){{ $i }}{{ $x }}@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/f"] == ("text", [("lit", "a=x;b=&lt;y&gt;;0p1q")])


def test_view_forelse(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/f', 'f', ['xs' => ['a'], 'ys' => []]);\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("@forelse($xs as $x){{ $x }}@empty-@endforelse|@forelse($ys as $y){{ $y }}@empty-@endforelse", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/f"] == ("text", [("lit", "a|-")])


def test_view_loop_odd_even(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/o', 'o', ['xs' => ['a', 'b', 'c']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/o.blade.php").write_text("@foreach($xs as $x)@if($loop->odd)O@else{{ '' }}E@endif@endforeach".replace("{{ '' }}", ""), encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/o"] == ("text", [("lit", "OEO")])


def test_view_nested_foreach(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/n', 'n', ['rs' => ['1', '2'], 'cs' => ['a', 'b']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/n.blade.php").write_text("@foreach($rs as $r)@foreach($cs as $c){{ $c }}@endforeach{{ $r }};@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/n"] == ("text", [("lit", "ab1;ab2;")])


def test_view_loop_depth_parent(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/d', 'd', ['rs' => ['1', '2'], 'cs' => ['a']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/d.blade.php").write_text("@foreach($rs as $r)@foreach($cs as $c){{ $loop->depth }}{{ $loop->parent->iteration }}@endforeach{{ $loop->depth }};@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/d"] == ("text", [("lit", "211;221;")])


def test_view_continue_break(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/c', 'c', ['xs' => ['a', 'b', 'c', 'd']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/c.blade.php").write_text("@foreach($xs as $x)@continue($x == 'b'){{ $x }}@break($x == 'c')@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/c"] == ("text", [("lit", "ac")])


def test_view_nested_arrays(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['grid' => [['1', '2'], ['3']], 'us' => [['n' => 'A'], ['n' => '<B>']]]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@foreach($grid as $row)@foreach($row as $c){{ $c }}@endforeach;@endforeach@foreach($us as $u){{ $u['n'] }}@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "12;3;A&lt;B&gt;")])


def test_view_outer_loop_with_loop_vars(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['grid' => [['a', 'b'], ['c']]]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@foreach($grid as $row){{ $loop->iteration }}:@foreach($row as $c){{ $loop->parent->index }}.{{ $loop->index }}{{ $c }}@if($loop->last)!@endif @endforeach|@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "1:0.0a 0.1b! |2:1.0c! |")])


def test_view_outer_loop_continue_break(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['grid' => [['a', 'b'], ['c'], ['d']]]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@foreach($grid as $row)@if($loop->first)@continue@endif@foreach($row as $c){{ $c }}@endforeach|@break($loop->last)@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "c|d|")])


def test_view_outer_loop_inner_continue_break(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['grid' => [['a', 'b'], ['c']]]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@foreach($grid as $row)@foreach($row as $c)@continue($c == 'a'){{ $c }}@break@endforeach|@endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "b|c|")])


def test_view_for_steps(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/f', 'f');\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("@for($i = 5; $i > 0; $i -= 2){{ $i }},@endfor|@for($i = 0; $i <= 6; $i += 3){{ $i }}@endfor|@for($i=3;$i>=1;$i--){{ $i }}@endfor", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/f"] == ("text", [("lit", "5,3,1,|036|321")])


def test_view_for_bounds_from_data(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b', 'c'], 'n' => '2']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@for($i = 0; $i < count($xs); $i++){{ $i }}@endfor|@for($i = $n; $i >= 0; $i--){{ $i }}@endfor", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "012|210")])


def test_view_while_bounds_from_data(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b', 'c'], 'n' => '2']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@php($i = 0)@while($i < count($xs)){{ $i }}@php($i++)@endwhile|@php($j = 0)@while($j <= $n){{ $j }}@php($j++)@endwhile", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "012|012")])


def test_view_while_steps(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g');\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@php($i = 0)@while($i < 7){{ $i }},@php($i += 3)@endwhile|@php($j = 6)@while($j > 0){{ $j }}@php($j -= 2)@endwhile", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "0,3,6,|642")])


def test_view_foreach_range(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g');\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@foreach(range(1, 3) as $i){{ $i }}@endforeach|@foreach(range(10, 0, 5) as $i){{ $i }},@endforeach|@foreach(range(0,4,2) as $k => $i){{ $k }}={{ $i }} @endforeach", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "123|10,5,0,|0=0 1=2 2=4 ")])


def test_view_arith_and_item_functions(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b', 'c'], 'n' => '2']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ strtoupper($xs[0]) }}|{{ $n * 3 }}|{{ strlen('abc') }}|{{ ($n + 1) * 2 - 1 }}|{{ $n / 4 }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "A|6|3|5|0.5")])


def test_view_arith_without_data(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g');\nRoute::view('/u', 'u');\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ 1 + 2 * 3 }}|{{ strlen('ab') }}", encoding="utf-8")
    (tmp_path / "resources/views/u.blade.php").write_text("{{ $unknown }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "7|2")])
    assert r["/u"] is None


def test_view_array_helpers(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b', 'c'], 'n' => '2']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ max(1, $n, 5) }}|{{ min($n, 1) }}|{{ max([3, 9.5]) }}|{{ array_sum([1,2,3]) }}|{{ array_sum([1.5, 2]) }}|{{ end($xs) }}{{ reset($xs) }}|{{ in_array('b', $xs) ? 'y' : 'n' }}{{ in_array('z', $xs) ? 'y' : 'n' }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "5|1|9.5|6|3.5|ca|yn")])


def test_view_str_pad_sprintf(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['n' => '2']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ str_pad($n, 3, '0', STR_PAD_LEFT) }}|{{ str_pad('ab', 5, '-', STR_PAD_BOTH) }}|{{ sprintf('%03d', $n) }}|{{ sprintf('%.2f/%5s/%-3s|', 3.14159, 'x', 'y') }}{{ sprintf('%d%%', 50) }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "002|-ab--|002|3.14/    x/y  |50%")])


def test_view_function_args_from_items(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'ns' => ['3', '7'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ sprintf('%s-%03d', $xs[0], $u['age']) }}|{{ max($ns[0], $ns[1]) }}|{{ str_pad($xs[1], 3, '*') }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "a-009|7|b**")])


def test_view_concat_and_item_arith(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'ns' => ['3', '7'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ ucfirst($xs[1]) . '!' }}|{{ $xs[0] . '-' . $xs[1] }}|{{ $u['age'] + 1 }}|{{ $ns[0] * $ns[1] }}|{{ 'a.b' . 'c' }}|{{ 1.5 + 1 }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "B!|a-b|10|21|a.bc|2.5")])


def test_view_comparison_ternary(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'ns' => ['3', '7'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("{{ count($xs) > 1 ? 'many' : 'one' }}|{{ $u['age'] >= 10 ? 'adult' : 'kid' }}|{{ $ns[0] + $ns[1] == 10 ? 'ten' : 'no' }}|{{ count($xs) === 2 ? 'y' : 'n' }}", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "many|kid|ten|y")])


def test_view_if_comparison(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'ns' => ['3', '7'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@if(count($xs) > 1)M@else O@endif|@if($u['age'] >= 10)A@else K@endif|@if($ns[0] + $ns[1] == 10)T@endif", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "M| K|T")])


def test_view_if_comparison_nested(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@if(count($xs) > 1)[@if($u['age'] >= 10)A@else K@endif]@else O@endif", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "[ K]")])


def test_view_elseif_comparison(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'ns' => ['3', '7'], 'u' => ['age' => '9']]);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@if(count($xs) > 5)A@elseif($u['age'] >= 10)B@elseif($ns[0] == 3)C@else D@endif|@if(count($xs) > 5)A@elseif(count($xs) > 9)B@endif.", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "C|.")])


def test_view_plain_if_with_elseif(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'u' => ['age' => '9'], 'z' => '0']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@if($z)A@elseif($u['age'] >= 1)B@else C@endif|@if($xs)A@elseif($u['age'] >= 1)B@else C@endif|@if($z)A@elseif($u['age'] >= 100)B@else C@endif", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "B|A| C")])


def test_view_elseif_plain_var(tmp_path):
    from torporea.php import routes
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/g', 'g', ['xs' => ['a', 'b'], 'z' => '0']);\n", encoding="utf-8")
    (tmp_path / "resources/views/g.blade.php").write_text("@if(count($xs) > 5)A@elseif($z)B@elseif($xs)C@else D@endif", encoding="utf-8")
    r = {p: tr for _, p, _, tr, _ in routes(str(tmp_path))}
    assert r["/g"] == ("text", [("lit", "C")])


def test_back_with_input_and_old(tmp_path):
    from torporea.php import routes, render_main
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::post('/p', function (Request $request) { return back()->withInput(); });\nRoute::post('/q', function () { return redirect()->back(); });\nRoute::view('/f', 'f');\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("<input value=\"{{ old('name', 'none') }}\">", encoding="utf-8")
    rts = routes(str(tmp_path))
    r = {p: tr for _, p, _, tr, _ in rts}
    assert r["/p"] == ("back", "input")
    assert r["/q"] == ("back",)
    assert r["/f"] == ("text", [("lit", '<input value="'), ("old_esc", ("name", "none")), ("lit", '">')])
    src = render_main(rts)
    assert "flash_old_cookie(&input)" in src and "old_input(&req)" in src and "Max-Age=0" in src


def test_with_input_only_except(tmp_path):
    from torporea.php import routes, render_main
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::post('/a', function (Request $request) { return back()->withInput($request->only(['name'])); });\nRoute::post('/b', function (Request $request) { return redirect()->back()->withInput($request->except(['pw', 'pw2'])); });\nRoute::post('/c', function (Request $request) { return back()->withInput($request->only([$k])); });\n", encoding="utf-8")
    rts = routes(str(tmp_path))
    r = {p: tr for _, p, _, tr, _ in rts}
    assert r["/a"] == ("back", "input", "only", ["name"])
    assert r["/b"] == ("back", "input", "except", ["pw", "pw2"])
    assert r["/c"] is None
    assert "flash_old_cookie(&picked)" in render_main(rts)


def test_with_errors_and_error_directive(tmp_path):
    from torporea.php import routes, render_main
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::post('/p', function (Request $request) { return back()->withErrors(['name' => 'Required', 'age' => ['A', 'B']])->withInput($request->only(['name'])); });\nRoute::post('/q', function () { return back()->withErrors($v); });\nRoute::view('/f', 'f');\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("@error('name')<p>{{ $message }}</p>@enderror{{ $errors->first('age') }}", encoding="utf-8")
    rts = routes(str(tmp_path))
    r = {p: tr for _, p, _, tr, _ in rts}
    assert r["/p"] == ("backx", ("only", ["name"]), {"name": ["Required"], "age": ["A", "B"]})
    assert r["/q"] is None
    assert r["/f"] == ("text", [("err_blk", ("name", [("lit", "<p>"), ("msg", ""), ("lit", "</p>")])), ("err_first", "age")])
    src = render_main(rts)
    assert "flash_cookie(\"rporea_err\"" in src and "flashed_errs(&req)" in src


def test_errors_any_has_all(tmp_path):
    from torporea.php import routes, render_main
    (tmp_path / "routes").mkdir(); (tmp_path / "resources/views").mkdir(parents=True)
    (tmp_path / "routes/web.php").write_text("<?php\nRoute::view('/f', 'f');\nRoute::post('/p', function () { return back()->withErrors(['z' => 'Z', 'a' => 'A']); });\n", encoding="utf-8")
    (tmp_path / "resources/views/f.blade.php").write_text("@if($errors->any())<ul>@foreach($errors->all() as $e)<li>{{ $e }}</li>@endforeach</ul>@else OK@endif|@if($errors->has('age'))bad@endif", encoding="utf-8")
    rts = routes(str(tmp_path))
    r = {p: tr for _, p, _, tr, _ in rts}
    assert r["/f"] == ("text", [("err_if", ("", [("lit", "<ul>"), ("err_all", [("lit", "<li>"), ("msg", ""), ("lit", "</li>")]), ("lit", "</ul>")], [("lit", " OK")])), ("lit", "|"), ("err_if", ("age", [("lit", "bad")], []))])
    src = render_main(rts)
    assert "errs_all(&errs)" in src and "!errs.is_empty()" in src
    # the flashed bag keeps the given order (z before a), as Laravel's MessageBag does
    assert '[[\\"z\\", [\\"Z\\"]], [\\"a\\", [\\"A\\"]]]' in src


def test_request_validate_simple_rules(tmp_path):
    from torporea import php
    tr = php.translate("$request->validate(['name' => 'required|max:5', 'age' => 'integer']); return 'ok';", [])
    assert tr[0] == "valid" and tr[1] == [("name", ["required", "max:5"]), ("age", ["integer"])]
    rs = php._leaf_rs(tr)
    assert "validate_field(&input" in rs and "rporea_err" in rs and "password_confirmation" in rs
    assert php._uses_input(tr)
    # unknown rules stay a 501 TODO
    assert php.translate("$request->validate(['e' => 'email|confirmed']); return 'ok';", [])[0] == 'valid'
    assert php.translate("$request->validate(['e' => 'unique:users']); return 'ok';", []) is None
