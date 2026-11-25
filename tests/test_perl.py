from torporea.detect import scan
from torporea.perl import routes, translate

MOJO = """#!/usr/bin/env perl
use Mojolicious::Lite -signatures;

# get '/ignored' => sub { };
get '/' => sub {
  my $c = shift;
  $c->render(text => 'Welcome');
};
get '/hello/:name' => sub {
  my $c = shift;
  $c->render(text => 'Hello, ' . $c->param('name') . '!');
};
get '/api/status' => sub ($c) {
  $c->render(json => {ok => 1, tags => ['a', "b"], nil => undef});
};
post '/users' => sub {
  my $c = shift;
  my $u = $c->req->json;
  $c->render(json => $u);
};
app->start;
"""
DANCER = """package App;
use Dancer2;
get '/d/<id>' => sub { return 'item ' . route_parameters->get('id'); };
del '/d/:id' => sub { database->quick_delete('t', {id => param('id')}); return 'ok' };
any '/ping' => sub { 'pong' };
1;
"""


def make(tmp_path):
    (tmp_path / "app.pl").write_text(MOJO, encoding="utf-8")
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "App.pm").write_text(DANCER, encoding="utf-8")
    return str(tmp_path)


def test_detect(tmp_path):
    fws = {(f.framework, f.language) for f in scan(make(tmp_path))}
    assert ("mojolicious", "perl") in fws and ("dancer", "perl") in fws


def test_routes(tmp_path):
    rs = {(m, p): tr for m, p, _, tr, _ in routes(make(tmp_path))}
    assert ("GET", "/ignored") not in rs
    assert rs[("GET", "/")] == ("text", [("lit", "Welcome")])
    assert rs[("GET", "/hello/:name")] == ("text", [("lit", "Hello, "), ("param", "name"), ("lit", "!")])
    assert rs[("GET", "/api/status")] == ("json", {"ok": 1, "tags": ["a", "b"], "nil": None})
    assert rs[("POST", "/users")] is None
    assert rs[("GET", "/d/:id")] == ("text", [("lit", "item "), ("param", "id")])
    assert rs[("DELETE", "/d/:id")] is None
    assert rs[("PUT", "/ping")] == ("text", [("lit", "pong")])


def test_translate_rejects():
    assert translate('return "hi $name";', []) is None
    assert translate("$c->render(text => 'x', status => 201)", []) is None
    assert translate("return uc('a');", []) is None
