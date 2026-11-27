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

## 2026-11-25 再開用メッセージ(別アカウントでそのまま貼り付け) / Resume message (paste as is)
**日本語**: 前の続きです。`F:\2RPoRea\PORTING.md` 末尾の「現状と完成予定」と本節を読んでから再開してください。作業は手元PC(WSL含む)で行い、VPSは配備と確認のみ。まず `F:\2RPoRea` で `git status` を見て、未コミットの `src/torporea/jsx.py`・`reaxt_gen.py`・`tests/test_reaxt_gen.py`(fetch/axios を Server Action に対応付ける作業途中。`test_fetch_detection_maps_to_action` が失敗中)を直し、`python -m pytest -q tests` を全件成功にしてから進めます(PowerShell で `$env:PYTHONPATH='F:\2RPoRea\src'`、cargo は `$env:USERPROFILE\.cargo\bin` を PATH に)。続きの順: (1)fetch の Server Action 化の完成、(2)委譲出力 `backend-java`・`backend-cobol` の起動と HTTP 応答確認(今は `cargo check` まで)、(3)WASM ハイドレーション生成(クリック更新の確認)、(4)式の props と状態を持つ子の展開、(5)2MFastAPI の対応言語拡張(Java/COBOL 委譲、Node.js/TypeScript は `--node` で任意)、(6)Java_to の `@Mappings`・`expression=`、COBOL_to の非 snake_case 警告修正と起動確認、(7)MFastAPI の Mojo 実機確認(WSL の mojo と RMojo の `compat/wsl-bridge`)。同時に開発する対象: COBOL_to・Java_to・MFastAPI・2MFastAPI・RMojo・RPoRea・2RPoRea・Reaxt。決まり: 確認せず自動で進める、実際に動かした範囲だけ「確認済み」と書く、業務ロジックを移せたと偽らない、新しいRESTは作らない、秘密は書かない、README/CLAUDE/PORTING/POLICY を日英で同じ日に更新、返答は日本語のみ、`rm -rf` は使わず削除は本人に頼む(scratch の `F:\_work_2rporea_*` は本人が整理)。
**English**: Continuing from before. Read "Status and plan" at the end of `F:\2RPoRea\PORTING.md` and this section, then resume. Develop and test on the local PC (including WSL); use the VPS only to deploy and verify. First run `git status` in `F:\2RPoRea`: fix the uncommitted `src/torporea/jsx.py`, `reaxt_gen.py` and `tests/test_reaxt_gen.py` (work in progress mapping fetch/axios to a Server Action; `test_fetch_detection_maps_to_action` is failing) and get `python -m pytest -q tests` fully green before moving on (in PowerShell set `$env:PYTHONPATH='F:\2RPoRea\src'`; put `$env:USERPROFILE\.cargo\bin` on PATH for cargo). Then, in order: (1) finish the fetch-to-Server-Action work; (2) start the delegated outputs `backend-java` and `backend-cobol` and check HTTP responses (so far only `cargo check`); (3) generate WASM hydration and verify click updates; (4) expression props and stateful children; (5) expand 2MFastAPI source languages (Java/COBOL delegation, optional Node.js/TypeScript via `--node`); (6) Java_to `@Mappings` and `expression=`, COBOL_to non-snake-case warning fix and startup check; (7) a real Mojo check of MFastAPI (WSL mojo and RMojo's `compat/wsl-bridge`). Developed together: COBOL_to, Java_to, MFastAPI, 2MFastAPI, RMojo, RPoRea, 2RPoRea, Reaxt. Rules: continue without asking; call only what was actually run "verified"; never claim business logic was ported when it was not; no new REST; never write secrets; update README/CLAUDE/PORTING/POLICY in Japanese and English the same day; reply in Japanese only; do not use `rm -rf` (ask the owner to delete; the owner cleans up the scratch folders `F:\_work_2rporea_*`).

## 2026-11-25 追記: fetch/axios の Server Action 対応付けを修正 / Fix: fetch/axios to Server Action mapping
**日本語**: `test_fetch_detection_maps_to_action` の失敗原因は、`jsx.py` の正規表現に `\b`・`\1` が制御文字として書き込まれていたことでした。正しい正規表現に直し、テスト13件がすべて成功しました。次は、委譲した出力(`backend-java`・`backend-cobol`)を起動して HTTP の応答を確かめます。
**English**: `test_fetch_detection_maps_to_action` failed because `\b` and `\1` had been written into the regexes in `jsx.py` as control characters. The regexes are fixed and all 13 tests pass. Next: start the delegated outputs (`backend-java`, `backend-cobol`) and check their HTTP responses.

## 2026-11-25 追記: 委譲出力の起動確認と、相互変換の最優先指示 / Delegated outputs started; cross-conversion is top priority
**日本語**
- **確認済み(実際に起動)**: Java_to の出力(`backend-java`)は起動して `GET /x` が 200 `"ok"`、存在しない経路は 404。COBOL_to の RPoem 向け出力は、これまでライブラリだけで起動できなかったため、**起動用サーバー(`src/main.rs`、`POST /cobol_to.Program/Run`、Connect の単純呼び出し、REST なし)を生成するよう COBOL_to を変更**した。`Hello.cbl` を変換して起動し、`{"program":"hello"}` で 200 `{"output":"HI\n"}`、不明な名前 404、壊れた JSON 400、GET 405 を確認。COBOL_to の試験25件成功。RPoem の場所は環境変数 `RPOEM_DIR`(既定 `F:/RPoem`)。
- **最優先の指示(ユーザー、2026-11-25)**: メインフレーム・Linux・UNIX・Windows などの COBOL、Java、Fortran、PHP、Perl などから、FastAPI・Poem・RPoem・RMojo/Mojo・MFastAPI・RPoRea・Fortran などへの**相互変換**を最優先で進める。担当は COBOL_to・Java_to・pl2pl・2MFastAPI・2RPoRea(同時開発)。
- **現状の対応範囲(正直に)**: COBOL→RPoem/Axum/FastAPI/MFastAPI(単純なプログラム)、Java(Spring)→RPoem の骨組み(本体は単純な return 以外 TODO)、Python→RPoem(2Poem)、C/C++/Fortran→Rust(pl2pl、単純なもの)、COBOL→別 OS の COBOL(pl2pl cobol)。**未対応**: PHP・Perl からの業務ロジック変換、COBOL→Java・COBOL→Fortran、Java→Fortran/COBOL、RMojo/Mojo を変換先にすること、変換の逆方向全般。
- **次の手(この順)**: (1) 変換元×変換先の対応表を作り、空いている組み合わせを洗い出す、(2) PHP→RPoem/MFastAPI(Laravel の経路から)、(3) Perl→同、(4) COBOL→Java、(5) Mojo/RMojo を変換先に追加。

**English**
- **Verified (actually started)**: Java_to's output (`backend-java`) starts; `GET /x` returns 200 `"ok"` and an unknown path returns 404. COBOL_to's RPoem output used to be a library only and could not start, so **COBOL_to now also generates a server (`src/main.rs`, `POST /cobol_to.Program/Run`, a Connect unary call, no REST)**. `Hello.cbl` was converted and started: `{"program":"hello"}` gives 200 `{"output":"HI\n"}`, an unknown name 404, broken JSON 400, GET 405. COBOL_to's 25 tests pass. The RPoem location comes from env `RPOEM_DIR` (default `F:/RPoem`).
- **Top-priority instruction (user, 2026-11-25)**: give top priority to **cross-conversion** from COBOL (mainframe, Linux, UNIX, Windows and so on), Java, Fortran, PHP, Perl and others into FastAPI, Poem, RPoem, RMojo/Mojo, MFastAPI, RPoRea, Fortran and others. Owners: COBOL_to, Java_to, pl2pl, 2MFastAPI and 2RPoRea, developed together.
- **Honest current coverage**: COBOL to RPoem/Axum/FastAPI/MFastAPI (simple programs); Java (Spring) to an RPoem scaffold (bodies TODO except simple returns); Python to RPoem (2Poem); C/C++/Fortran to Rust (pl2pl, simple code); COBOL to COBOL for another OS (pl2pl cobol). **Not yet**: business-logic conversion from PHP and Perl, COBOL to Java, COBOL to Fortran, Java to Fortran/COBOL, Mojo/RMojo as a target, and most reverse directions.
- **Next (in order)**: (1) build a source-by-target matrix and list the empty pairs; (2) PHP to RPoem/MFastAPI (starting from Laravel routes); (3) Perl likewise; (4) COBOL to Java; (5) add Mojo/RMojo as a target.

## 2026-11-25 追記: PHP(Laravel)→RPoem 変換 / PHP (Laravel) to RPoem conversion
**日本語**
- 2RPoRea の `convert` が PHP(Laravel)を RPoem サーバー(`backend-php`)へ変換するようになった(`src/torporea/php.py`)。`routes/web.php`・`routes/api.php`(`/api` 付き)の `Route::get/post/put/delete/any` を読み、クロージャ・`fn() =>`・`[XController::class, 'm']`・`'XController@m'` の本体をたどる。
- **本体まで訳すのは「return 1つだけ」の場合のみ**: 文字列、文字列とルート引数の連結(`'Hello, ' . $name`)、配列リテラル(`response()->json([...])` も可)。それ以外(DB 呼び出しや複数の文)は 501 と TODO にする。業務ロジックを移せたとは書かない。PATCH は RPoem 互換層に補助関数が無いため未対応(件数を報告)。元の URL はそのまま残す(既存アプリの移行のため)。
- **確認済み(実際に起動)**: Laravel の例を変換してビルド・起動し、`GET /` 200「Welcome」、`GET /hello/Taro` 200「Hello, Taro!」、`GET /users/5` 200 `{"id":7,"name":"Taro"}`(コントローラー経由)、`GET /api/status` 200(JSON)、`POST /users`・`DELETE /x` は 501、未定義は 404。テスト16件成功。
- **未了**: Laravel 以外の素の PHP、`$request` の入力や変数・if を含む本体、PATCH、Perl、COBOL→Java、Mojo/RMojo を変換先に。対応表は runo の `CONVERSION-MATRIX.md`。

**English**
- 2RPoRea's `convert` now turns PHP (Laravel) into an RPoem server (`backend-php`, `src/torporea/php.py`). It reads `Route::get/post/put/delete/any` in `routes/web.php` and `routes/api.php` (with the `/api` prefix) and follows closures, `fn() =>`, `[XController::class, 'm']` and `'XController@m'` to their bodies.
- **A body is translated only when it is a single return** of a string, a concatenation of strings and route parameters (`'Hello, ' . $name`), or an array literal (also via `response()->json([...])`). Anything else (database calls, several statements) answers 501 with a TODO; business logic is never claimed as ported. PATCH is not supported yet (the RPoem compatibility layer has no helper; the count is reported). Original URLs are kept, since this migrates an existing app.
- **Verified (actually started)**: a sample Laravel app was converted, built and started. `GET /` 200 "Welcome", `GET /hello/Taro` 200 "Hello, Taro!", `GET /users/5` 200 `{"id":7,"name":"Taro"}` (through a controller), `GET /api/status` 200 (JSON); `POST /users` and `DELETE /x` 501; unknown paths 404. 16 tests pass.
- **Open**: plain PHP without Laravel; bodies with `$request` input, variables or `if`; PATCH; Perl; COBOL to Java; Mojo/RMojo as a target. The matrix is `CONVERSION-MATRIX.md` in runo.

## 2026-11-25 追記: Perl(Mojolicious・Dancer2)→RPoem 変換 / Perl (Mojolicious, Dancer2) to RPoem conversion
**日本語**
- 2RPoRea が Perl の Web アプリ(Mojolicious::Lite と Dancer/Dancer2)を検出し、`convert` で RPoem サーバー(`backend-perl`)へ変換するようになった(`src/torporea/perl.py`)。`get/post/put/del/any '/経路' => sub {...}`(シグネチャ `sub ($c)` も可)を読み、`:name`・`<name>` を RPoem の `:name` にする。
- **本体まで訳すのは単純な1つの応答だけ**: Mojolicious の `$c->render(text => ...)`・`$c->render(json => {...})`、Dancer の `return '文字列'`・最後の式・`to_json(...)`。文字列とルート引数(`$c->param('x')`・`route_parameters->get('x')`・`param('x')`)の `.` 連結に対応。変数展開する `"..."`、`status =>` などの追加指定、DB 呼び出しや複数の文は 501 と TODO。PATCH は未対応(件数を報告)。
- **確認済み(実際に起動)**: Mojolicious と Dancer2 の例を変換してビルド・起動。`GET /` 200「Welcome」、`GET /hello/Taro` 200「Hello, Taro!」、`GET /api/status` 200(JSON)、`GET /d/42` 200「item 42」、`PUT /ping` 200「pong」(any)、`POST /users`・`DELETE /d/1` は 501、未定義は 404。テスト19件成功。
- **未了**: CGI.pm・Catalyst などほかの Perl の方式、変数や if を含む本体、PATCH、COBOL→Java、Mojo/RMojo を変換先に。

**English**
- 2RPoRea now detects Perl web apps (Mojolicious::Lite and Dancer/Dancer2), and `convert` turns them into an RPoem server (`backend-perl`, `src/torporea/perl.py`). It reads `get/post/put/del/any '/path' => sub {...}` (signatures like `sub ($c)` too) and maps `:name` and `<name>` to RPoem's `:name`.
- **Only a single simple response is translated**: Mojolicious `$c->render(text => ...)` and `$c->render(json => {...})`; Dancer `return 'string'`, a final expression, or `to_json(...)`. Strings joined with `.` to route parameters (`$c->param('x')`, `route_parameters->get('x')`, `param('x')`) are supported. Interpolating `"..."`, extra options such as `status =>`, database calls and several statements answer 501 with a TODO. PATCH is not supported yet (the count is reported).
- **Verified (actually started)**: Mojolicious and Dancer2 samples were converted, built and started. `GET /` 200 "Welcome", `GET /hello/Taro` 200 "Hello, Taro!", `GET /api/status` 200 (JSON), `GET /d/42` 200 "item 42", `PUT /ping` 200 "pong" (any); `POST /users` and `DELETE /d/1` 501; unknown paths 404. 19 tests pass.
- **Open**: other Perl styles such as CGI.pm and Catalyst; bodies with variables or `if`; PATCH; COBOL to Java; Mojo/RMojo as a target.

## 2026-11-25 追記: PATCH と単純なローカル変数 / PATCH and simple local variables
**日本語**
- RPoem の互換層に `patch()` を追加(RPoem `178d6d4`、実 TCP の試験つき)。PHP・Perl 変換は PATCH 経路も出力し、件数は `PATCH routes` として報告する。
- PHP は `$x = 式;` を並べた後の `return 式;`、Perl は `my $x = 式;` を並べた後の最後の文を訳す(式は文字列・ルート引数の連結、PHP は配列リテラルも可)。関数呼び出しや if などを含む本体は従来どおり 501。
- **確認済み(実際に起動)**: 例を変換・ビルド・起動し、PHP の `PATCH /greet/Taro` 200「Hi Taro!」、`GET /cfg` 200 `{"v":2}`、`DELETE /x` 501、同じ経路への GET は 405。Perl の `PATCH /greet/Taro` 200「Hi Taro!」、`POST /users` 501。テスト23件成功。
- **未了**: `$request` の入力・if・関数呼び出しを含む本体、CGI.pm・Catalyst。

**English**
- Added `patch()` to RPoem's compatibility layer (RPoem `178d6d4`, with a real-TCP test). PHP and Perl conversion now emit PATCH routes; the count is reported as `PATCH routes`.
- PHP bodies of `$x = EXPR;` statements followed by `return EXPR;`, and Perl bodies of `my $x = EXPR;` statements followed by a translatable final statement, are now translated (EXPR = strings joined with route parameters; PHP also array literals). Bodies with function calls, `if` and so on still answer 501.
- **Verified (actually started)**: samples converted, built and started. PHP: `PATCH /greet/Taro` 200 "Hi Taro!", `GET /cfg` 200 `{"v":2}`, `DELETE /x` 501, GET on the PATCH-only path 405. Perl: `PATCH /greet/Taro` 200 "Hi Taro!", `POST /users` 501. 23 tests pass.
- **Open**: bodies using `$request` input, `if` or function calls; CGI.pm and Catalyst.

## Versionless API の方針 / Versionless API policy (2026-11-25)
**日本語**: このリポジトリのAPIは **Versionless**(URL・パッケージ名に `v1` 等を付けず、互換性を壊さず足すだけで進化させる)。欄は足すだけ・足す欄は省略可能・知らない欄は無視・名前変更は新名を足して旧を非推奨に(期限は既定で6か月以上、使用0を確認してから削除)・enumは未知の値を許容・安全上の緊急修正は例外。既存の `.v1` は呼び出し側を壊さないよう当面残し、版なしの別名を追加して段階的に畳む。詳細・出典は [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md) 末尾。適用はこれから順に行う。
**English**: This repository's APIs are **Versionless**: no `v1` in URLs or package names; evolve by adding only, without breaking compatibility. Only add fields, new fields are optional, ignore unknown fields, rename by adding the new name and deprecating the old (default deadline 6 months or more, remove only after confirming zero use), tolerate unknown enum values, emergency security fixes are the exception. Existing `.v1` names stay for now so callers do not break; a versionless alias is added and `.v1` is retired in stages. Details and sources: the end of [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md). Rollout is step by step.

## API 方針: REST 全廃・gRPC / Connect へ
**日本語**: このリポジトリでは **REST API を新規に作らない**。ブラウザ・`curl` から呼ぶ API は **Connect の単純呼び出し**(`POST /<パッケージ>.<Service>/<Method>`、`content-type: application/json`)、サービス間は **gRPC / gRPC-web**。GraphQL は読み取り専用。既存の REST は触るときに移し、移したら旧経路は消す。JSON は RS-JSON(`from_str_secure` / `parse_secure`)で読む。例外は相手の規格が形を決めるもの(ACME、OAuth/OIDC のコールバック、第三者の Webhook、ヘルスチェック、静的ファイル、OTLP)のみ。迷ったら Connect。正本は [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md)。
**English**: This repository **does not add new REST APIs**. APIs called from browsers or `curl` use **Connect unary calls** (`POST /<package>.<Service>/<Method>`, `content-type: application/json`); service-to-service calls use **gRPC / gRPC-web**. GraphQL is read-only. Existing REST is migrated when touched and the old route is removed. Read JSON with RS-JSON (`from_str_secure` / `parse_secure`). Exceptions are only shapes dictated by someone else's standard (ACME, OAuth/OIDC callbacks, third-party webhooks, health checks, static files, OTLP). When in doubt, use Connect. Source of truth: the link above.

## 完成まで作り切る方針 / Finish everything policy (2026-11-27)
**日本語**: 全リポジトリで、**未確認は自動で確認し、未実施は実施し、未了は完成させる**(確認を求めず進める)。使用頻度が低いと判断される機能や、**1から作り直す大規模開発になる内容でも、やめずに最後まで開発・TEST・DEBUGする**(別の方式で済ませない、後回しにしない)。進め方: 調査(英語・日本語の検索とGitHub) → 設計 → 実装 → 実機/実データで確認 → 失敗は原因を直して再試験 → README・CLAUDE・PORTING・POLICY を日英で更新 → push。「できた」と書くのは実測した範囲だけ、確認できなかった所は「未確認」と正直に書く。例外(確認を取る): 元に戻せない削除、秘密の公開、所有者の認証・決済・実機操作が要るもの、利用者のシステム設定の変更。
**English**: In every repository, **verify what is unverified, do what is not yet done, and finish what is unfinished** automatically, without asking. Even features that look rarely used, or work that means **a large rewrite from scratch, are developed, tested and debugged to the end** (no substituting another approach, no postponing). Method: research (English and Japanese search plus GitHub) -> design -> implement -> verify on real devices or data -> fix causes and retest on failure -> update README, CLAUDE, PORTING and POLICY in Japanese and English -> push. Write "done" only for what was measured, and say "unverified" honestly for the rest. Exceptions that still need confirmation: irreversible deletions, publishing secrets, anything needing the owner's authentication, payment or real-device actions, and changes to the user's system settings.

## 2026-11-27 追記: PHP の `if ($経路パラメータ == "文字列")` / Update: PHP if on a route parameter
**日本語**: Laravel の本体で、`if ($name === 'admin') { return ...; }`(`==` `===` `!=` `!==`、経路パラメータと文字列リテラルの比較、`else` あり・なし、連鎖も可)を、Rust の `if params.get("name").unwrap_or("") == "admin" { .. } else { .. }` に訳すようにした(`php.py` の `translate` が `("if", ...)` を返す)。中身が単純な `return` だけのときに限り、それ以外(関数呼び出し・経路パラメータでない変数・入れ子)は従来どおり 501。**実測**: 単体テスト25件成功。さらに `routes/web.php` を `2rporea convert` で変換して `cargo build`、起動し、`GET /hello/admin` が 200 `Hello boss`、`GET /hello/Taro` が 200 `Hi Taro`(WSL Ubuntu-24.04)。**未了**: `$request` の入力・関数呼び出しを含む本体、Perl 側の `if`、CGI.pm・Catalyst。
**English**: In Laravel bodies, `if ($name === 'admin') { return ...; }` (`==`, `===`, `!=`, `!==`; a route parameter against a string literal; with or without `else`; chains allowed) is translated to Rust `if params.get("name").unwrap_or("") == "admin" { .. } else { .. }` (`translate` in `php.py` returns `("if", ...)`). Only when the branches are simple `return`s; anything else (function calls, variables that are not route parameters, nesting) still answers 501. **Measured**: 25 unit tests pass. Also converted `routes/web.php` with `2rporea convert`, ran `cargo build` and started it: `GET /hello/admin` gave 200 `Hello boss` and `GET /hello/Taro` gave 200 `Hi Taro` (WSL Ubuntu-24.04). **Open**: bodies using `$request` input or function calls, `if` on the Perl side, CGI.pm and Catalyst.

## 2026-11-27 Laravel の `$request->input()` を訳す / Translating `$request->input()`
**日本語**: Laravel の本体で `$request->input('x', '既定')`・`$request->query()`・`$request->get()`・`request('x', '既定')` を、生成する Rust の `query_param(&req, "x", "既定")`(クエリ文字列の値、`%XX` と `+` を復号、無ければ既定値)に訳すようにした。試験25件成功。WSL で生成サーバーをビルドして curl で実測: `/hi`→`Hi guest!`、`/hi?who=Taro%20Y`→`Hi Taro Y!`、`/hi?who=a+b`→`Hi a b!`、`/u/ken?q=x%26y`→`User ken q=x&y`。未了: POST 本文(フォーム・JSON)の入力、`$request->all()`、関数呼び出しを含む本体、CGI.pm・Catalyst。
**English**: Laravel bodies now translate `$request->input('x', 'default')`, `$request->query()`, `$request->get()` and `request('x', 'default')` into the generated Rust `query_param(&req, "x", "default")` (query-string value with `%XX` and `+` decoded, else the default). 25 tests pass. The generated server was built in WSL and checked with curl: `/hi` -> `Hi guest!`, `/hi?who=Taro%20Y` -> `Hi Taro Y!`, `/hi?who=a+b` -> `Hi a b!`, `/u/ken?q=x%26y` -> `User ken q=x&y`. Open: POST bodies (form/JSON), `$request->all()`, bodies with function calls, CGI.pm, Catalyst.

## 2026-11-27 POST 本文の入力にも対応 / POST body input
**日本語**: `$request->input()` 等は、Laravel と同じくクエリ文字列と本文(`application/x-www-form-urlencoded` または JSON オブジェクト、本文が優先、上限1MiB)をまとめて読むようにした(生成コードの `read_input`、入力を読むハンドラーだけで本文を読む)。WSL で生成サーバーを curl で実測: フォーム `item=りんご&n=3`→`Got りんご x3`、JSON `{"item":"pen","n":2}`→`Got pen x2`、`?item=q&n=9`+本文`item=b`→`Got b x9`、入力なし→既定値。試験25件成功。未了: `$request->all()`、関数呼び出しを含む本体、multipart、CGI.pm・Catalyst。
**English**: `$request->input()` and friends now read the query string merged with the body (`application/x-www-form-urlencoded` or a JSON object; body wins; 1 MiB cap), as Laravel does (`read_input` in the generated code, only for handlers that read input). Measured with curl in WSL: form `item=りんご&n=3` -> `Got りんご x3`; JSON `{"item":"pen","n":2}` -> `Got pen x2`; `?item=q&n=9` plus body `item=b` -> `Got b x9`; no input -> defaults. 25 tests pass. Open: `$request->all()`, bodies with function calls, multipart, CGI.pm, Catalyst.

## 2026-11-27 `$request->all()` に対応 / `$request->all()`
**日本語**: `return $request->all();` と `return response()->json($request->all());` を、生成コードで入力(クエリ+本文)を JSON で返す処理に訳すようにした。試験26件成功。curl で実測: `?a=1` +フォーム `b=日&c=3`→`{"a":"1","c":"3","b":"日"}`、JSON `{"x":"y","n":2}`→`{"n":"2","x":"y"}`。**Laravel との違い**: JSON 本文の数値・真偽値も文字列で返す(Laravel は元の型のまま)。キーの順は不定。未了: 型の保持、`only()`/`except()`、関数呼び出しを含む本体、multipart、CGI.pm・Catalyst。
**English**: `return $request->all();` and `return response()->json($request->all());` now translate to returning the input (query plus body) as JSON. 26 tests pass. Measured with curl: `?a=1` plus form `b=日&c=3` -> `{"a":"1","c":"3","b":"日"}`; JSON `{"x":"y","n":2}` -> `{"n":"2","x":"y"}`. **Difference from Laravel**: numbers and booleans in a JSON body come back as strings (Laravel keeps their types); key order is unspecified. Open: keeping types, `only()`/`except()`, bodies with function calls, multipart, CGI.pm, Catalyst.

## 2026-11-27 22:45 `$request->only()` / `except()`
**日本語**: Laravel の `$request->only([...])`・`$request->except([...])`(キーは文字列の配列リテラルのみ、`response()->json(...)` 包みも可)を、`read_input` の結果を絞った JSON 応答へ変換。WSL でビルドしcurl実測: only → `{"a":"1","c":"3"}`、except → `{"b":"2"}`。テスト27件成功。変数のキー配列は未対応(501)。
**English**: Laravel `$request->only([...])` / `$request->except([...])` (literal string-key arrays only, also inside `response()->json(...)`) now become a filtered JSON response over `read_input`. Built in WSL and measured with curl: only gives `{"a":"1","c":"3"}`, except gives `{"b":"2"}`. 27 tests pass. Key arrays held in variables are not supported (501).

## 2026-11-27 22:50 JSON の型を保持 / JSON types kept
**日本語**: `read_input` を `HashMap<String, serde_json::Value>` に変更し、JSON本文の数値・真偽値・入れ子をそのまま返す(前回の既知の差=数値が文字列になる、を解消)。curl実測: `{"x":"y","n":2,"ok":true,"o":{"k":[1]}}` → `{"n":2,"ok":true,"o":{"k":[1]},"x":"y"}`。form・query は従来どおり文字列。テスト27件成功。
**English**: `read_input` now returns `HashMap<String, serde_json::Value>`, so JSON bodies keep numbers, booleans and nesting (fixes the earlier known difference where numbers became strings). Measured with curl: `{"x":"y","n":2,"ok":true,"o":{"k":[1]}}` comes back as `{"n":2,"ok":true,"o":{"k":[1]},"x":"y"}`. Form and query values stay strings. 27 tests pass.

## 2026-11-27 23:00 `$request->has()` / `filled()`
**日本語**: `if ([!]$request->has('k')) {...} [else {...}]` と `filled('k')`(キーがあり、空文字・null でない)を条件分岐へ変換。curl実測: `name=Bob`→filled、`name=`→empty、`x=1`→missing。テスト28件成功。条件の組み合わせ(&&・||)は未対応(501)。
**English**: `if ([!]$request->has('k')) {...} [else {...}]` and `filled('k')` (present and not an empty string or null) now become branches. Measured with curl: `name=Bob` gives filled, `name=` gives empty, `x=1` gives missing. 28 tests pass. Combined conditions (&&, ||) are not supported (501).

## 2026-11-27 23:10 has/filled の && ・ || 組み合わせ / Combined conditions
**日本語**: `has`/`filled`(否定つき可)を `&&`・`||` でつないだ条件を変換(PHPとRustは&&が||より優先で同じなので、そのまま出力)。curl実測: `filled(a) && !has(b) || has(c)` で a=1→yes、a=1&b=2→no、b=2&c=3→yes、a=→no。テスト29件。括弧や他の条件との混在は未対応(501)。
**English**: Conditions joining `has`/`filled` (optionally negated) with `&&` and `||` are now converted (PHP and Rust share && over || precedence, so they are emitted as written). Measured with curl for `filled(a) && !has(b) || has(c)`: a=1 yes, a=1&b=2 no, b=2&c=3 yes, a= no. 29 tests. Parentheses or mixing with other conditions are not supported (501).

## 2026-11-27 23:20 `abort(code[, 'message'])`
**日本語**: Laravel の `abort(404)`・`abort(422, 'msg')`(本体の最後、または if の分岐内)を、その状態コードと本文の応答へ変換。curl実測: `k=1`→`ok [200]`、`x=1`→`need k [422]`。テスト30件。Laravel既定のエラーページ(HTML)は再現せず、本文は渡した文字列のみ。
**English**: Laravel `abort(404)` and `abort(422, 'msg')` (as the last statement or inside an if branch) now return that status code with the message body. Measured with curl: `k=1` gives `ok [200]`, `x=1` gives `need k [422]`. 30 tests. Laravel's default error page (HTML) is not reproduced; the body is just the given string.

## 2026-11-27 23:30 `return redirect('/path')`
**日本語**: 固定パスへの `return redirect('/path')` を 302 + `Location` 応答へ変換。curl実測: `/old` → `302`、転送先 `/new`。テスト31件。`redirect()->route(...)`・変数・`back()` は未対応(501)。
**English**: `return redirect('/path')` to a fixed path now becomes a 302 with a `Location` header. Measured with curl: `/old` gives `302` to `/new`. 31 tests. `redirect()->route(...)`, variables and `back()` are not supported (501).

## 2026-11-27 23:40 `back()` / `redirect()->back()`
**日本語**: `return back();`・`return redirect()->back();` を、`Referer` の先へ302(無ければ `/`)に変換。入力を読む処理より先に `Referer` を控える。curl実測: 空送信→`302` で元のページ、値あり→`saved`。テスト32件。Laravelのセッション経由の入力引き継ぎ(`withInput`)は未対応。
**English**: `return back();` and `return redirect()->back();` now 302 to the `Referer` (or `/` when absent); the referer is captured before the input is read. Measured with curl: empty submit gives `302` back to the page, a value gives `saved`. 32 tests. Laravel's session-based input flashing (`withInput`) is not supported.

## 2026-11-27 22:50 `response('text', code)` / `response()->json(..., code)`
**日本語**: 状態コードつきの `response('本文', 201)`・`response()->json([...], 201)`(`$request->all()` 等も可)を変換。curl実測: `/mk`→`{"ok":true} [201]`、`/gone`→`Gone away [410]`。テスト33件。状態コードは数値リテラルのみ、ヘッダー指定(第3引数・`->header()`)は未対応(501)。
**English**: `response('body', 201)` and `response()->json([...], 201)` (also with `$request->all()` etc.) are now converted with their status code. Measured with curl: `/mk` gives `{"ok":true} [201]`, `/gone` gives `Gone away [410]`. 33 tests. Status codes must be numeric literals; headers (third argument, `->header()`) are not supported (501).

## 2026-11-27 22:52 `->header('K', 'V')`
**日本語**: `response(...)` / `response()->json(...)` の後ろに続く `->header('名前', '値')`(複数可、文字列リテラルのみ)を応答ヘッダーへ変換。curl実測: `/hd` → `201 Created` と `x-id: 7`。テスト34件。
**English**: `->header('Name', 'Value')` chained after `response(...)` or `response()->json(...)` (several allowed, string literals only) now sets response headers. Measured with curl: `/hd` gives `201 Created` and `x-id: 7`. 34 tests.

## 2026-11-27 22:58 `redirect()->route('name')` / `to_route('name')`
**日本語**: `->name('名前')` を付けたルートを集め、`redirect()->route('名前')`・`to_route('名前')` をそのパスへの302に変換(パラメーター付きのルート・存在しない名前は501)。curl実測: `/go` → `302` で `/dash`。テスト35件。
**English**: Routes tagged with `->name('name')` are collected, and `redirect()->route('name')` / `to_route('name')` become a 302 to that path (routes with parameters or unknown names stay 501). Measured with curl: `/go` gives `302` to `/dash`. 35 tests.

## 2026-11-27 23:02 パラメーター付き名前付きルートへの転送 / Named routes with parameters
**日本語**: `redirect()->route('users.show', ['id' => $id])`(値はルートパラメーターか文字列リテラル)を、`{id}` を埋めたパスへの302に変換。足りないパラメーター・余ったキー(Laravelはクエリ文字列にする)は501。curl実測: `/me/42` → `302` で `/users/42`。テスト36件。
**English**: `redirect()->route('users.show', ['id' => $id])` (values are route parameters or string literals) now becomes a 302 to the path with `{id}` filled in. Missing parameters or extra keys (Laravel turns them into a query string) stay 501. Measured with curl: `/me/42` gives `302` to `/users/42`. 36 tests.

## 2026-11-27 22:57 余ったキーをクエリ文字列へ / Extra keys become a query string
**日本語**: 名前付きルートへの転送で、パスに無いキーを Laravel と同じくクエリ文字列として付ける(値は文字列リテラルのみ、RFC 3986 でエンコード)。curl実測: `/me2/7` → `302` で `/users/7?tab=a%20b`。値がルートパラメーターの余りは501。テスト37件。
**English**: For named-route redirects, keys not in the path are appended as a query string like Laravel (string-literal values only, RFC 3986 encoded). Measured with curl: `/me2/7` gives `302` to `/users/7?tab=a%20b`. Extra keys whose value is a route parameter stay 501. 37 tests.

## 2026-11-27 23:00 ルートパラメーターをクエリ値に / Route parameters as query values
**日本語**: 余ったキーの値がルートパラメーターでも、一度URLデコードしてからRFC 3986でエンコードしてクエリ文字列に付ける(二重エンコードを防止)。curl実測: `/me3/a%20b%26c` → `302` で `/users/1?q=a%20b%26c`。テスト37件。注意: 共有の `form_decode` を使うため、パス中の `+` は空白として扱われる。
**English**: Extra keys whose value is a route parameter are now URL-decoded once and re-encoded (RFC 3986) into the query string, avoiding double encoding. Measured with curl: `/me3/a%20b%26c` gives `302` to `/users/1?q=a%20b%26c`. 37 tests. Note: the shared `form_decode` treats `+` in the path as a space.

## 2026-11-27 23:04 `Route::redirect` / `Route::permanentRedirect`
**日本語**: `Route::redirect('/a', '/b'[, 307])`(既定302)と `Route::permanentRedirect('/a', '/b')`(301)を、全メソッド(GET/POST/PUT/DELETE)の転送ルートへ変換。curl実測: `/here`→`302 /there`、`/old2`→`301 /new2`。テスト38件。パラメーター付きのパスは未対応(除外)。
**English**: `Route::redirect('/a', '/b'[, 307])` (default 302) and `Route::permanentRedirect('/a', '/b')` (301) become redirect routes for every method (GET/POST/PUT/DELETE). Measured with curl: `/here` gives `302 /there`, `/old2` gives `301 /new2`. 38 tests. Paths with parameters are skipped.

## 2026-11-27 23:06 `Route::view` (静的ビューのみ / static views only)
**日本語**: `Route::view('/about', 'pages.about')` を `resources/views/pages/about.blade.php` の内容を返すGETルートへ変換。Blade構文(`{{ }}`・`{!! !!}`・`@ディレクティブ`)を含むビューは501(TODO)のまま。curl実測: `/about`→HTML、`/dyn`→501。テスト39件。
**English**: `Route::view('/about', 'pages.about')` becomes a GET route returning `resources/views/pages/about.blade.php`. Views with Blade syntax (`{{ }}`, `{!! !!}`, `@directives`) stay 501 (TODO). Measured with curl: `/about` returns the HTML, `/dyn` returns 501. 39 tests.

## 2026-11-27 23:08 `Route::view` のデータ / Route::view data
**日本語**: `Route::view('/hi', 'hi', ['name' => '値'])`(値は文字列リテラル)で、ビューの `{{ $name }}` をBladeと同じくHTMLエスケープして埋め込む。curl実測: `Taro <&>` → `Hi Taro &lt;&amp;&gt;`。値が変数のもの・他のBlade構文は501。テスト40件。
**English**: `Route::view('/hi', 'hi', ['name' => 'value'])` (string-literal values) fills `{{ $name }}` in the view, HTML-escaped as Blade does. Measured with curl: `Taro <&>` gives `Hi Taro &lt;&amp;&gt;`. Variable values and other Blade syntax stay 501. 40 tests.

## 2026-11-27 23:11 条件のかっこ / Parenthesized conditions
**日本語**: `if (($request->has('a') || $request->has('b')) && !$request->filled('c'))` のように、`has`/`filled` を `&&`・`||`・`!`・かっこで組んだ条件を変換(かっこの対応を数えて切り出し、1語ずつ読む)。curl実測: `a=1`→yes、`b=1&c=`→yes、`b=1&c=x`→no、`c=1`→no。`!(...)` も可。テスト41件。`withInput` はセッションの仕組みが無いため未対応(501のまま)。
**English**: Conditions built from `has`/`filled` with `&&`, `||`, `!` and parentheses now translate (balanced-paren split plus a small tokenizer). Measured with curl: `a=1` yes, `b=1&c=` yes, `b=1&c=x` no, `c=1` no. `!(...)` works too. 41 tests. `withInput` stays unsupported (501) because there is no session layer.

## 2026-11-27 23:13 `$request->missing()` / missing()
**日本語**: `$request->missing('k')`(=has の否定)を、単独・`&&`/`||`/かっこの条件の中で変換。curl実測: `a=1`→a-only、`x=1`→none、`a=1&b=2`→other。テスト42件。
**English**: `$request->missing('k')` (the negation of has) translates alone and inside `&&`/`||`/parenthesized conditions. Measured with curl: `a=1` a-only, `x=1` none, `a=1&b=2` other. 42 tests.

## 2026-11-27 23:15 `$request->boolean()` / boolean()
**日本語**: 条件の中の `$request->boolean('k')` を変換(Laravelと同じく 1・"1"・true・"true"・"on"・"yes" が真)。curl実測: `on=yes`/`on=1`/JSON `true`→T、`on=0`/無し→F。テスト43件。
**English**: `$request->boolean('k')` inside conditions translates (true for 1, "1", true, "true", "on", "yes", as Laravel). Measured: `on=yes`, `on=1`, JSON `true` give T; `on=0` and absent give F. 43 tests.

## 2026-11-27 23:17 配列形の has/filled/hasAny/anyFilled / Array forms
**日本語**: `$request->has(['a','b'])`・`filled([...])`(すべて)と `hasAny([...])`・`anyFilled([...])`(どれか)を、かっこ付きの `&&`/`||` に展開して変換。curl実測4件一致(`b=1&c=1&d=`→ng、`b=1&c=1&d=2`→ok など)。テスト44件。
**English**: `has([...])` / `filled([...])` (all) and `hasAny([...])` / `anyFilled([...])` (any) expand into parenthesized `&&`/`||`. Four curl checks match (e.g. `b=1&c=1&d=` ng, `b=1&c=1&d=2` ok). 44 tests.

## 2026-11-27 23:19 入力値の比較条件 / Input comparisons in conditions
**日本語**: 条件の中の `$request->input('k') === 'v'`(`==`・`!=`・`!==` も)を変換。かっこ・`&&`/`||` と組める。curl実測: `mode=dark`→hit、`mode=light`→miss、`x=1&y=a`→hit、`x=1&y=z`→miss。数値など文字列でないJSON値は文字列と等しくならない扱い(PHPの `==` の型変換とは違う点がある)。テスト45件。
**English**: `$request->input('k') === 'v'` (also `==`, `!=`, `!==`) inside conditions translates and combines with parentheses and `&&`/`||`. Measured: `mode=dark` hit, `mode=light` miss, `x=1&y=a` hit, `x=1&y=z` miss. Non-string JSON values never equal a string (unlike PHP's loose `==` conversion). 45 tests.
