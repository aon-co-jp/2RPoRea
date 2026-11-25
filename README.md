# 2RPoRea

**日本語**: さまざまな言語・フレームワークで作られたプロジェクトを、**RPoRea**(RPoem と Reaxt を統合したフレームワーク。Reaxt は React・Next.js・Nuxt.js・Nest.js を統合したフレームワークで、画面もサーバー側も含む)へ変換するためのツールです。姉妹の [2MFastAPI](https://github.com/aon-co-jp/2MFastAPI)・[2Poem](https://github.com/aon-co-jp/2Poem)・[2FastAPI](https://github.com/aon-co-jp/2FastAPI) と同じ流儀で作ります。**現在は最初の一歩(検出 `scan`)だけです。変換そのものは開発中で、まだ動きません。**
**English**: A tool to convert projects written in many languages and frameworks to **RPoRea** (a framework that integrates RPoem and Reaxt; Reaxt itself integrates React, Next.js, Nuxt.js and Nest.js, covering both the UI and the server side). It follows the same style as its siblings [2MFastAPI](https://github.com/aon-co-jp/2MFastAPI), [2Poem](https://github.com/aon-co-jp/2Poem) and [2FastAPI](https://github.com/aon-co-jp/2FastAPI). **Today only the first step exists (detection, `scan`). Conversion itself is under development and does not work yet.**

## 使い方 / Usage
```bash
pip install .                      # 開発中 / under development
2rporea scan ./my-project          # バックエンドとフロントエンドを検出 / detect backends and frontends
```

## 検出できるもの / What `scan` detects
| 種別 / Kind | 対象 / Targets |
|---|---|
| バックエンド / backend | Python(Flask・Django・FastAPI)、Java(Spring・JAX-RS・Servlet・Spark)、COBOL、PHP(Laravel)、Node.js(Express・Nest.js) |
| フロントエンド / frontend | React、Next.js、Nuxt.js、Vue |

ファイルと依存の名前だけで判定し、コードは実行しません。`node_modules`・`target`・`.git` などは見ません。 / Detection uses file names and dependency names only; nothing is executed. `node_modules`, `target`, `.git` and similar are skipped.

## これからの予定 / Plan (not done yet)
1. バックエンドの変換: Python は 2Poem の仕組み、Java は [Java_to](https://github.com/aon-co-jp/Java_to)、COBOL は [COBOL_to](https://github.com/aon-co-jp/COBOL_to) を RPoem 向けに呼ぶ。 / Backend conversion by delegating to 2Poem (Python), Java_to (Java) and COBOL_to (COBOL), targeting RPoem.
2. 画面側と Node 系サーバー側の変換: React・Next.js・Nuxt.js・Vue のコンポーネント・ルート・データ取得と、Nest.js・Express のサーバー側を **Reaxt**(Rust だけ)へ。1から作る大きな仕事で、近道はしません。 / UI and Node-style server conversion: React / Next.js / Nuxt.js / Vue components, routes and data fetching, plus Nest.js / Express server code, to **Reaxt** (Rust only). This is a large from-scratch job and we take no shortcuts.
3. Node.js・TypeScript は、2MFastAPI と同様に例外的に選べるようにし、**選ばない**こともできるようにする。 / Node.js and TypeScript are an optional exception (as in 2MFastAPI), and choosing neither must also work.

## 現況・未了 / Status (2026-11-25)
**日本語**: `scan` と単体テスト3件(Python+React/Next、Java+COBOL+PHP+Nest、`node_modules` の除外)が動きます。変換は未着手です。実機(Mac・iPhone)の確認も未了です。
**English**: `scan` and 3 unit tests (Python + React/Next, Java + COBOL + PHP + Nest, `node_modules` skipping) work. Conversion is not started. Real Mac/iPhone checks are open.

ライセンス / License: MIT

## 2026-11-25 追記: `convert`(バックエンド) / Update: `convert` (backend)
**日本語**: `2rporea convert <path> -o <out>` を追加。Python は 2Poem、Java は Java_to、COBOL は COBOL_to を `--target rpoem` で呼び、出力先に `backend-*` を作ります。PHP・Node 系サーバー・画面側(React/Next/Nuxt/Vue)は**まだ変換できず**、黙って捨てずに `MIGRATION.md` へ TODO として残します。Flask の小さな例で実行確認済み、試験5件成功。Java_to / COBOL_to は実行ファイルを PATH、`TORPOREA_JAVA_TO` / `TORPOREA_COBOL_TO`、または隣の `target/release` から探します。
**English**: Added `2rporea convert <path> -o <out>`. It calls 2Poem (Python), Java_to (Java) and COBOL_to (COBOL) with `--target rpoem`, writing `backend-*` under the output. PHP, Node-style servers and frontends (React/Next/Nuxt/Vue) **cannot be converted yet**; they are never dropped silently but listed as TODO in `MIGRATION.md`. Verified end to end on a small Flask example; 5 tests pass. Java_to / COBOL_to binaries are found on PATH, via `TORPOREA_JAVA_TO` / `TORPOREA_COBOL_TO`, or in a sibling `target/release`.

<!-- directive-20261125-1130 -->
## 2026-11-25 指示(11:30 まで確認不要) / Directive (no confirmation until 11:30)
**日本語**: 2026-11-25 11:30 まで、未了は確認なしで完成まで自動で進める。需要が少ない・必要性が低いと判断される、あるいは1から大規模に作り直す必要があっても、別の方式で済ませず、正面から作り直す。同時に開発する対象: COBOL_to・Java_to・MFastAPI・2MFastAPI(他の言語・フレームワークから MFastAPI 互換へ。Node.js・TypeScript は例外的に選べ、選ばない選択も可能)・RMojo・RPoRea(RPoem と Reaxt の統合)・2RPoRea(他の言語・フレームワークから RPoRea へ)・Reaxt(React+Next.js+Nuxt.js+Nest.js の統合)。1つ変えたら他を確認し、README・CLAUDE・PORTING・POLICY を日英で同じ日に更新する。
**English**: Until 2026-11-25 11:30, carry unfinished work through to completion automatically without asking. Even if demand looks low or a large from-scratch rewrite is needed, do not substitute another approach; do the real work. Developed together: COBOL_to, Java_to, MFastAPI, 2MFastAPI (converts other languages and frameworks to MFastAPI-compatible code; Node.js and TypeScript are an optional exception and choosing neither is allowed), RMojo, RPoRea (RPoem and Reaxt integrated), 2RPoRea (converts other languages and frameworks to RPoRea) and Reaxt (React + Next.js + Nuxt.js + Nest.js integrated). When one changes, check the others and update README, CLAUDE, PORTING and POLICY in Japanese and English the same day.

<!-- directive-20261125-mojo -->
## 2026-11-25 追記: MFastAPI は Mojo から使えること / Addendum: MFastAPI must be usable from Mojo
**日本語**: MFastAPI は **Mojo から使用できる仕様**を保つ(Python 構文・Rust 実装・Mojo 対応、Windows では RMojo の `compat/wsl-bridge` 経由で WSL 上の Mojo を使う)。2MFastAPI の変換結果も Mojo から使えること。現状: `mojo/` は参照実装で、段階B・Cのサーバーは実験的。Mojo からの呼び出しの実機確認は、確認済みの範囲だけを「確認済み」と書く。11:30 まで確認なしで自動で進める。
**English**: MFastAPI keeps the **specification of being usable from Mojo** (Python syntax, Rust core, Mojo support; on Windows the real Mojo in WSL is driven through RMojo's `compat/wsl-bridge`). Output of 2MFastAPI must be usable from Mojo too. Current state: `mojo/` is a reference implementation and its stage B/C servers are experimental. Only what was actually run is called "verified". Continue automatically without asking until 11:30.

## 2026-11-25 追記: 移植対象の一覧 / Update: porting inventory
**日本語**: `convert` が、Express・Nest の経路と Next/Nuxt のページ、React/Vue のコンポーネントを `MIGRATION.md` の「Reaxt porting inventory」に一覧します(`inventory.py`)。**コードの変換ではなく**、Reaxt への移植で何を覆うべきかを具体的にするためのものです。テスト6件成功。
**English**: `convert` now lists Express/Nest routes, Next/Nuxt pages and React/Vue components under "Reaxt porting inventory" in `MIGRATION.md` (`inventory.py`). This is **not code conversion**; it makes the Reaxt port's scope concrete. 6 tests pass.

## 2026-11-25 追記: Reaxt サーバーの雛形生成 / Update: Reaxt server scaffold
**日本語**: `convert` が、Express/Nest の経路ごとに Reaxt のアクション(GET は Query)を持つ Rust の雛形 `reaxt-server/` を出力します(`reaxt_gen.py`)。各ハンドラーは **HTTP 501 と TODO を返すだけ**で、業務ロジックは移していません。生成物は Reaxt(`../Reaxt`)に対して `cargo check` が通ることを確認済み(2経路の例)。画面側(ページ・コンポーネント)の Reaxt 生成は未了。テスト7件成功。
**English**: `convert` now emits `reaxt-server/`, a Rust scaffold with one Reaxt action per Express/Nest route (GET becomes a query) (`reaxt_gen.py`). Every handler **only returns HTTP 501 with a TODO**; no business logic is ported. The output passes `cargo check` against Reaxt (`../Reaxt`) on a 2-route example. Frontend (pages/components) generation is still open. 7 tests pass.

## 2026-11-25 追記: 画面側ページの Reaxt 雛形 / Update: Reaxt page scaffold
**日本語**: `convert` が、Next/Nuxt のページごとに Reaxt の `pages/` 規約(`blog/[slug].rs`、`[...rest].rs`)で `.page(...)` を `reaxt-server/` に追加します。中身は「TODO: port page …」を出すだけで、**コンポーネント・状態・データ取得は移していません**。経路+ページ入りの例で `cargo check` が通ることを確認(サーバー起動・描画の確認は未了)。テスト8件成功。React Router など設定ベースのルートは未対応で、MIGRATION.md の一覧に出るのみ。
**English**: `convert` now adds a `.page(...)` per Next/Nuxt page to `reaxt-server/`, using Reaxt's `pages/` naming (`blog/[slug].rs`, `[...rest].rs`). Each page only renders "TODO: port page ..."; **components, state and data fetching are not ported**. `cargo check` passes on a routes-plus-pages example (starting the server and rendering are not verified). 8 tests pass. Config-based routes such as React Router are not handled and only appear in the MIGRATION.md inventory.
