# PORTING.md — 2RPoRea

## 2026-11-25 新設と到達点 / Created, and where it stands
**日本語**
- ユーザー指示により新設(2026-11-25)。目的: 他の言語・フレームワークから **RPoRea**(RPoem と Reaxt を統合したフレームワーク)への変換。Reaxt は React・Next.js・Nuxt.js・Nest.js を統合したフレームワーク。
- 済み: 検出 `2rporea scan`(Python・Java・COBOL・PHP・Node.js/Nest と、React・Next・Nuxt・Vue)、単体テスト3件成功。
- 未了(この順): (1)バックエンド変換(Python=2Poem、Java=Java_to、COBOL=COBOL_to を RPoem 向けに呼ぶ)、(2)画面側・Node 系サーバー側の変換(React/Next/Nuxt/Vue/Nest/Express → Reaxt。コンポーネント・ルート・データ取得・SSR)、(3)Node.js・TypeScript を例外的に選べる/選ばない選択、(4)`pl2pl` との統合、(5)毎晩の自動追従(2Poem と同様)、(6)紹介ページ(easy-web.tokyo)。
- 再開: `python -m pytest -q tests` で3件成功を確認してから(1)へ。

**English**
- Created on 2026-11-25 at the user's request. Goal: convert projects in other languages and frameworks to **RPoRea** (the framework integrating RPoem and Reaxt). Reaxt is the framework integrating React, Next.js, Nuxt.js and Nest.js.
- Done: detection `2rporea scan` (Python, Java, COBOL, PHP, Node.js/Nest, and React, Next, Nuxt, Vue) and 3 passing unit tests.
- Open (in this order): (1) backend conversion (call 2Poem for Python, Java_to for Java, COBOL_to for COBOL, targeting RPoem); (2) UI and Node-style server conversion (React/Next/Nuxt/Vue/Nest/Express to Reaxt: components, routes, data fetching, SSR); (3) Node.js / TypeScript as an optional exception, including choosing neither; (4) integration with `pl2pl`; (5) nightly auto-follow like 2Poem; (6) an intro page on easy-web.tokyo.
- To resume: run `python -m pytest -q tests`, confirm 3 pass, then start on (1).

## 2026-11-25 追記: convert / Update: convert
**日本語**: `src/torporea/convert.py`(plan/run/write_migration)と `tests/test_convert.py`、`tests/conftest.py` を追加。バックエンド変換は兄弟ツールへの委譲。未了(この順): Node系サーバーと画面側の Reaxt 変換、PHP、Node.js/TS の選択式、pl2pl 統合、毎晩の自動追従、紹介ページ。
**English**: Added `src/torporea/convert.py` (plan/run/write_migration), `tests/test_convert.py` and `tests/conftest.py`. Backend conversion delegates to the sibling tools. Open (in order): Node-style server and frontend conversion to Reaxt, PHP, the optional Node.js/TS choice, pl2pl integration, nightly auto-follow, an intro page.

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

