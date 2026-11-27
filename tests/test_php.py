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
    assert translate("return $request->all();", []) is None
    assert translate("return $request->input($k);", []) is None
    s = render_main([("GET", "/q", [], t, "routes/web.php")])
    assert 'query_param(&req, "who", "guest")' in s and "fn query_param(" in s
