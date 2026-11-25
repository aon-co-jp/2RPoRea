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
Route::delete('/x', function () { $a = 1; return 'no'; });
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
