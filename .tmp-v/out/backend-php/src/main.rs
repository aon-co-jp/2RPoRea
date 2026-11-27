//! 2RPoRea が PHP(Laravel) から生成した RPoem サーバー。訳せた return だけ本体あり、他は 501。
#![allow(unused_variables, unused_imports, dead_code)]
use open_runo_poem_compat::{delete, get, hyper_compat, patch, post, put, Params, Request, Response, Route, Server, StatusCode, TcpListener};

/// GET /hello/:name <- routes/web.php
#[open_runo_poem_compat_macro::handler]
async fn h0(_req: Request, params: Params) -> Response {
    let _ = &params;
    if params.get("name").unwrap_or("") == "admin" { { let mut s = String::new(); s.push_str("Hello boss"); hyper_compat::html_response(StatusCode::OK, s) } } else { { let mut s = String::new(); s.push_str("Hi "); s.push_str(params.get("name").unwrap_or("")); hyper_compat::html_response(StatusCode::OK, s) } }
}

#[tokio::main]
async fn main() {
    let port: u16 = std::env::var("PORT").ok().and_then(|p| p.parse().ok()).unwrap_or(3002);
    let app = Route::new()
        .at("/hello/:name", get(h0()));
    let (addr, handle) = Server::new(TcpListener::bind(([127, 0, 0, 1], port))).run(app).await.expect("bind");
    println!("listening on {addr}");
    handle.await.ok();
}
