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

## 2026-11-25 追記: Node.js・TypeScript は選べる/選ばない / Update: Node.js and TypeScript are optional
**日本語**: `2rporea convert --node` を付けたときだけ、`node-client/`(TypeScript の Connect クライアントと `package.json`・`tsconfig.json`)を追加します。**既定は付けない**(Rust だけ)で、その場合も `reaxt-server/` と `MIGRATION.md` は完全に出ます。生成した TypeScript は **`tsc` でのコンパイルを未確認**(Node.js 環境で未実行)。テスト10件成功(既定で `node-client` が出ないこと、`--node` で出ることを確認)。
**English**: Only with `2rporea convert --node` is `node-client/` added (a TypeScript Connect client plus `package.json` and `tsconfig.json`). **The default is off** (Rust only), and the result is still complete: `reaxt-server/` and `MIGRATION.md` are written either way. The generated TypeScript has **not been compiled with `tsc`** (not run in a Node.js environment). 10 tests pass (no `node-client` by default; present with `--node`).

## 2026-11-25 追記: 静的 JSX・状態・React Router の移植と実描画の確認 / Update: JSX, state, React Router, verified rendering
**日本語**: `jsx.py` を追加。ページ/コンポーネントの **JSX を Reaxt の VNode へ変換**(要素・属性・`className→class`・テキスト)、`useState(リテラル)` を `use_state`、`onClick={() => setN(n + 1)}`(と `setX(リテラル)`)を `on_click` へ変換します。React Router(`<Route path element>`、`{path, element}`)も一覧とページ生成に含めました。**実機確認**: 生成した `reaxt-server` を起動し、HTTP で `count=0` と `data-rx-click` のボタンが SSR で返ることを確認(テスト11件成功)。**まだ移していないもの(黙って捨てず、ページの `data-todo` と TODO 表示に出す)**: `useEffect`・`fetch`/`axios` によるデータ取得、リテラル以外の初期値、複雑なハンドラー・式、props、子コンポーネントの展開。クリックでの更新は**ブラウザ側 WASM のハイドレーション用バンドルを生成していないため未確認**(SSR の初期描画までが確認済み)。
**English**: Added `jsx.py`. It **converts a page/component's JSX to a Reaxt VNode** (elements, attributes, `className→class`, text), `useState(literal)` to `use_state`, and `onClick={() => setN(n + 1)}` (and `setX(literal)`) to `on_click`. React Router (`<Route path element>`, `{path, element}`) is now in the inventory and page generation. **Verified on a real run**: the generated `reaxt-server` was started and returned `count=0` plus a `data-rx-click` button over HTTP via SSR (11 tests pass). **Not yet ported (never silently dropped; shown in the page's `data-todo` and in the TODO text)**: `useEffect`, data fetching via `fetch`/`axios`, non-literal initial values, complex handlers and expressions, props, and expansion of child components. Click-driven updates are **unverified because the browser-side WASM hydration bundle is not generated** (only the initial SSR render is verified).

## 2026-11-25 追記: 子コンポーネントの展開 / Update: child component inlining
**日本語**: 状態(useState)を持たない子コンポーネント(例 `<Nav />`)を、同じ JSX 変換で親の中に展開します(深さ5まで)。**実機確認**: 生成した reaxt-server を起動し、親の `count=0` とボタン、子の `<nav>` が SSR で返ることを確認。**未対応**: props は渡さず(`data-todo` に 'props … not passed' と出す)、状態を持つ子は展開しません。fetch/useEffect のデータ取得も未移植です。
**English**: Child components without state (e.g. `<Nav />`) are now inlined into the parent by the same JSX conversion (up to depth 5). **Verified on a real run**: the generated reaxt-server returned the parent's `count=0` and button plus the child's `<nav>` over SSR. **Not handled**: props are not passed (reported in `data-todo` as 'props … not passed'), children with state are not inlined, and fetch/useEffect data loading is still unported.


## 2026-11-25 追記: 文字列リテラル props の受け渡し / Update: string-literal props
**日本語**: 親が `<Nav title="x" />` のように渡した**文字列リテラルの props**を、子の `{title}` / `{props.title}` に反映します。**実機確認**: 生成サーバーを起動し `<a href="/">x</a>` が SSR で返ることを確認(テスト12件成功)。**未対応**: 式の props(`{x}`)は `data-todo` に出す、fetch/useEffect、WASMハイドレーション、生成 TypeScript の `tsc` 確認(`tsc` 未導入、導入はダウンロード許可待ち)。
**English**: String-literal props passed by the parent (`<Nav title="x" />`) now fill the child's `{title}` / `{props.title}`. **Verified on a real run**: the generated server returned `<a href="/">x</a>` over SSR (12 tests pass). **Not handled**: expression props (`{x}`) are reported in `data-todo`; fetch/useEffect, WASM hydration, and a `tsc` check of the generated TypeScript (`tsc` is not installed; installing needs download permission).


## 2026-11-25 追記: Java_to / COBOL_to 委譲の実行確認 / Update: Java_to and COBOL_to delegation verified
**日本語**: 最小の Spring Boot(1経路)と COBOL(DISPLAY のみ)を混ぜたソースで `2rporea convert` を実行し、`java_to` と `cobol_to` が `--target rpoem` で呼ばれ、どちらも終了コード0で `backend-java`・`backend-cobol` を出力、MIGRATION.md に ok と記録されることを確認しました。**未確認**: 出力した RPoem プロジェクトの `cargo build` と起動(今回は生成までを確認)。
**English**: Running `2rporea convert` on a mixed source (a minimal Spring Boot app with one route plus a DISPLAY-only COBOL program) called `java_to` and `cobol_to` with `--target rpoem`; both exited 0, wrote `backend-java` and `backend-cobol`, and MIGRATION.md recorded ok. **Not verified**: `cargo build` and startup of the generated RPoem projects (only generation was checked).


## 2026-11-25 追記: 委譲出力の cargo check / Update: cargo check of delegated output
**日本語**: 前項の `backend-java`(Spring 1経路)と `backend-cobol`(DISPLAY のみ)を `cargo check`(RPoem へのパス依存)に通し、どちらも成功しました(COBOL 側は非 snake_case 名の警告1件のみ)。**未確認**: 起動して HTTP で応答を見る確認と、業務ロジックの同等性。
**English**: `cargo check` passes on the previous entry's `backend-java` (one Spring route) and `backend-cobol` (DISPLAY only), both with path dependencies on RPoem (one non-snake-case warning on the COBOL side). **Not verified**: starting them and checking HTTP responses, and business-logic equivalence.


## 2026-11-25 現状と完成予定 / Status and plan (as of 11:25)
**日本語**
- **済み(実行して確認)**: `scan`(検出)、`convert`(Python=2Poem・Java=Java_to・COBOL=COBOL_to を RPoem 向けに委譲。Java と COBOL は生成し `cargo check` 成功まで確認)、移植対象の一覧(MIGRATION.md)、Reaxt サーバー雛形(経路ごとの 501 アクション)、ページ生成(静的 JSX・`useState`・`onClick`・React Router)、状態なし子コンポーネントの展開、文字列リテラル props の受け渡し、`--node` による TypeScript クライアント(任意)。生成サーバーは起動して SSR 描画を確認。テスト12件成功。
- **作業途中(未コミット・未完成)**: `fetch`/`axios` を検出して Server Action に対応付ける変更(`jsx.py`・`reaxt_gen.py`・`tests/test_reaxt_gen.py`)。**テスト1件が失敗中**で、完成するまで確認済みとは書かない。並行エージェントを停止した際に途中で止まった。
- **未実施・未確認**: 委譲出力の起動と HTTP 応答の確認、WASM ハイドレーション生成(クリック更新の確認)、生成 TypeScript の `tsc` 確認(`tsc` 未導入)、式の props・状態を持つ子の展開、PHP・Express・Nest の業務ロジックの移植、`pl2pl` 統合、毎晩の自動追従、紹介ページ。
- **完成予定(この順)**: (1) fetch の Server Action 化を直してテスト成功、(2) 委譲出力の起動確認、(3) WASM ハイドレーション、(4) 式 props と状態付き子、(5) 2MFastAPI の対応言語拡張(Java/COBOL 委譲、Node/TS 任意選択)、(6) Java_to の `@Mappings`・`expression=`、COBOL_to の警告修正と起動確認、(7) MFastAPI の Mojo 実機確認。ユーザーの「一旦停止」により、ループと並行エージェントはすべて停止中。
**English**
- **Done (run and verified)**: `scan`; `convert` (Python via 2Poem, Java via Java_to, COBOL via COBOL_to, all targeting RPoem; Java and COBOL output was generated and passed `cargo check`); the porting inventory (MIGRATION.md); the Reaxt server scaffold (one 501 action per route); page generation (static JSX, `useState`, `onClick`, React Router); inlining of stateless child components; string-literal props; the optional TypeScript client via `--node`. The generated server was started and its SSR render checked. 12 tests pass.
- **In progress (uncommitted, unfinished)**: detecting `fetch`/`axios` and mapping it to a Server Action (`jsx.py`, `reaxt_gen.py`, `tests/test_reaxt_gen.py`). **One test is failing**, so this is not called verified until it is fixed. It was cut off midway when the parallel agents were stopped.
- **Not done / not verified**: starting the delegated output and checking HTTP responses; WASM hydration generation (and checking click updates); a `tsc` check of the generated TypeScript (`tsc` not installed); expression props and expanding children that have state; porting PHP / Express / Nest business logic; `pl2pl` integration; nightly auto-follow; an intro page.
- **Plan (in order)**: (1) fix the fetch-to-Server-Action change and get tests passing; (2) start the delegated output; (3) WASM hydration; (4) expression props and stateful children; (5) 2MFastAPI source-language expansion (Java/COBOL delegation, optional Node/TS); (6) Java_to `@Mappings` and `expression=`, COBOL_to warning fix and startup check; (7) a real-device Mojo check of MFastAPI. At the user's "stop", the loop and all parallel agents are halted.
