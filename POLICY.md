# POLICY.md — 2RPoRea

## 方針 / Policy (2026-11-25)
**日本語**
1. 変換先は RPoRea(RPoem と Reaxt を統合したフレームワーク)。Reaxt は React・Next.js・Nuxt.js・Nest.js を統合したもので、Rust だけで書き、Node.js・TypeScript・手書きの JavaScript に頼らない。
2. Node.js・TypeScript は**例外的に選べる**。選ばない場合も、同じ変換が最後まで動くこと。
3. 近道をしない。需要が少ない、あるいは1からの大規模な開発が必要でも、別の方式で済ませず、正面から作る。
4. できないものは黙って捨てず、`TODO` と理由、`MIGRATION.md` に残す。**業務ロジックを自動で移せたと偽らない**。
5. 新しい REST は作らない(Connect のみ)。JSON は RS-JSON。秘密は書かない。
6. 姉妹(pl2pl・RPoem・open-cosmo・RMojo・MFastAPI・2MFastAPI・Reaxt・RPoRea・COBOL_to・Java_to)と同時に開発し、同じ日に文書を更新する。
7. 文書は日本語と英語を基本に毎回編集する。ほかの言語は AI 翻訳で、ネイティブの確認前であることを明記する。

**English**
1. The target is RPoRea, the framework integrating RPoem and Reaxt. Reaxt integrates React, Next.js, Nuxt.js and Nest.js; it is written in Rust only and does not rely on Node.js, TypeScript or hand-written JavaScript.
2. Node.js and TypeScript are an **optional exception**. Choosing neither must still produce a conversion that runs end to end.
3. No shortcuts. Even if demand is low or a large from-scratch effort is needed, build the real thing instead of substituting another approach.
4. Never silently drop what cannot be converted; leave a `TODO` with the reason and a note in `MIGRATION.md`. **Never claim business logic was ported automatically when it was not.**
5. No new REST (Connect only). JSON via RS-JSON. Never write secrets.
6. Develop together with the siblings (pl2pl, RPoem, open-cosmo, RMojo, MFastAPI, 2MFastAPI, Reaxt, RPoRea, COBOL_to, Java_to) and update docs the same day.
7. Edit docs in Japanese and English every time. Other languages are AI-translated and must say they are not yet native-checked.

## 2026-11-25 追記: convert の方針 / Update: convert policy
**日本語**: 変換は自前で二重に作らず、2Poem(Python)・Java_to(Java)・COBOL_to(COBOL)へ委譲し、すべて RPoem 向け(`--target rpoem`)にする。変換できないもの(PHP・Node 系サーバー・画面側)は黙って捨てず `MIGRATION.md` に TODO と理由を残す。実行確認は実際に動かした経路だけを「確認済み」と書く(現在は Python のみ)。未了は確認なしで自動で進める。
**English**: Do not duplicate conversion logic: delegate to 2Poem (Python), Java_to (Java) and COBOL_to (COBOL), always targeting RPoem (`--target rpoem`). Anything that cannot be converted (PHP, Node-style servers, frontends) is never dropped silently; it goes to `MIGRATION.md` as a TODO with the reason. Only paths actually executed are called "verified" (currently Python only). Unfinished work continues automatically without asking.

<!-- directive-20261125-1130 -->
## 2026-11-25 指示(11:30 まで確認不要) / Directive (no confirmation until 11:30)
**日本語**: 2026-11-25 11:30 まで、未了は確認なしで完成まで自動で進める。需要が少ない・必要性が低いと判断される、あるいは1から大規模に作り直す必要があっても、別の方式で済ませず、正面から作り直す。同時に開発する対象: COBOL_to・Java_to・MFastAPI・2MFastAPI(他の言語・フレームワークから MFastAPI 互換へ。Node.js・TypeScript は例外的に選べ、選ばない選択も可能)・RMojo・RPoRea(RPoem と Reaxt の統合)・2RPoRea(他の言語・フレームワークから RPoRea へ)・Reaxt(React+Next.js+Nuxt.js+Nest.js の統合)。1つ変えたら他を確認し、README・CLAUDE・PORTING・POLICY を日英で同じ日に更新する。
**English**: Until 2026-11-25 11:30, carry unfinished work through to completion automatically without asking. Even if demand looks low or a large from-scratch rewrite is needed, do not substitute another approach; do the real work. Developed together: COBOL_to, Java_to, MFastAPI, 2MFastAPI (converts other languages and frameworks to MFastAPI-compatible code; Node.js and TypeScript are an optional exception and choosing neither is allowed), RMojo, RPoRea (RPoem and Reaxt integrated), 2RPoRea (converts other languages and frameworks to RPoRea) and Reaxt (React + Next.js + Nuxt.js + Nest.js integrated). When one changes, check the others and update README, CLAUDE, PORTING and POLICY in Japanese and English the same day.

<!-- directive-20261125-mojo -->
## 2026-11-25 追記: MFastAPI は Mojo から使えること / Addendum: MFastAPI must be usable from Mojo
**日本語**: MFastAPI は **Mojo から使用できる仕様**を保つ(Python 構文・Rust 実装・Mojo 対応、Windows では RMojo の `compat/wsl-bridge` 経由で WSL 上の Mojo を使う)。2MFastAPI の変換結果も Mojo から使えること。現状: `mojo/` は参照実装で、段階B・Cのサーバーは実験的。Mojo からの呼び出しの実機確認は、確認済みの範囲だけを「確認済み」と書く。11:30 まで確認なしで自動で進める。
**English**: MFastAPI keeps the **specification of being usable from Mojo** (Python syntax, Rust core, Mojo support; on Windows the real Mojo in WSL is driven through RMojo's `compat/wsl-bridge`). Output of 2MFastAPI must be usable from Mojo too. Current state: `mojo/` is a reference implementation and its stage B/C servers are experimental. Only what was actually run is called "verified". Continue automatically without asking until 11:30.

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

## Versionless API の方針 / Versionless API policy (2026-11-25)
**日本語**: このリポジトリのAPIは **Versionless**(URL・パッケージ名に `v1` 等を付けず、互換性を壊さず足すだけで進化させる)。欄は足すだけ・足す欄は省略可能・知らない欄は無視・名前変更は新名を足して旧を非推奨に(期限は既定で6か月以上、使用0を確認してから削除)・enumは未知の値を許容・安全上の緊急修正は例外。既存の `.v1` は呼び出し側を壊さないよう当面残し、版なしの別名を追加して段階的に畳む。詳細・出典は [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md) 末尾。適用はこれから順に行う。
**English**: This repository's APIs are **Versionless**: no `v1` in URLs or package names; evolve by adding only, without breaking compatibility. Only add fields, new fields are optional, ignore unknown fields, rename by adding the new name and deprecating the old (default deadline 6 months or more, remove only after confirming zero use), tolerate unknown enum values, emergency security fixes are the exception. Existing `.v1` names stay for now so callers do not break; a versionless alias is added and `.v1` is retired in stages. Details and sources: the end of [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md). Rollout is step by step.

## API 方針: REST 全廃・gRPC / Connect へ
**日本語**: このリポジトリでは **REST API を新規に作らない**。ブラウザ・`curl` から呼ぶ API は **Connect の単純呼び出し**(`POST /<パッケージ>.<Service>/<Method>`、`content-type: application/json`)、サービス間は **gRPC / gRPC-web**。GraphQL は読み取り専用。既存の REST は触るときに移し、移したら旧経路は消す。JSON は RS-JSON(`from_str_secure` / `parse_secure`)で読む。例外は相手の規格が形を決めるもの(ACME、OAuth/OIDC のコールバック、第三者の Webhook、ヘルスチェック、静的ファイル、OTLP)のみ。迷ったら Connect。正本は [`runo/API-POLICY.md`](https://github.com/aon-co-jp/runo/blob/main/API-POLICY.md)。
**English**: This repository **does not add new REST APIs**. APIs called from browsers or `curl` use **Connect unary calls** (`POST /<package>.<Service>/<Method>`, `content-type: application/json`); service-to-service calls use **gRPC / gRPC-web**. GraphQL is read-only. Existing REST is migrated when touched and the old route is removed. Read JSON with RS-JSON (`from_str_secure` / `parse_secure`). Exceptions are only shapes dictated by someone else's standard (ACME, OAuth/OIDC callbacks, third-party webhooks, health checks, static files, OTLP). When in doubt, use Connect. Source of truth: the link above.

## 完成まで作り切る方針 / Finish everything policy (2026-11-27)
**日本語**: 全リポジトリで、**未確認は自動で確認し、未実施は実施し、未了は完成させる**(確認を求めず進める)。使用頻度が低いと判断される機能や、**1から作り直す大規模開発になる内容でも、やめずに最後まで開発・TEST・DEBUGする**(別の方式で済ませない、後回しにしない)。進め方: 調査(英語・日本語の検索とGitHub) → 設計 → 実装 → 実機/実データで確認 → 失敗は原因を直して再試験 → README・CLAUDE・PORTING・POLICY を日英で更新 → push。「できた」と書くのは実測した範囲だけ、確認できなかった所は「未確認」と正直に書く。例外(確認を取る): 元に戻せない削除、秘密の公開、所有者の認証・決済・実機操作が要るもの、利用者のシステム設定の変更。
**English**: In every repository, **verify what is unverified, do what is not yet done, and finish what is unfinished** automatically, without asking. Even features that look rarely used, or work that means **a large rewrite from scratch, are developed, tested and debugged to the end** (no substituting another approach, no postponing). Method: research (English and Japanese search plus GitHub) -> design -> implement -> verify on real devices or data -> fix causes and retest on failure -> update README, CLAUDE, PORTING and POLICY in Japanese and English -> push. Write "done" only for what was measured, and say "unverified" honestly for the rest. Exceptions that still need confirmation: irreversible deletions, publishing secrets, anything needing the owner's authentication, payment or real-device actions, and changes to the user's system settings.

## 2026-11-28 08:13 PHP変換(ビュー)のまとめ / PHP view conversion summary
**日本語**: `Route::view` と Blade を変換時に解決できる範囲が広がった。数値(小数・`abs`/`intval`/`floor`/`ceil`/`round`/`number_format`)、三項演算子・比較、`request('k')`(エスケープ済み)、配列の添字・連想配列・配列の配列、`@foreach`(キー、`$loop` の各値、`parent`、入れ子、外側から展開する入れ子での `$loop`、`@continue`/`@break`)、`@forelse`。どれも変換したサーバーを curl で実測済み、テスト84件成功。解決できないものは従来どおり501のTODO。未了: `withInput`(セッション層が要る)。
**English**: More of `Route::view` and Blade is now resolved at convert time: numbers (floats, `abs`/`intval`/`floor`/`ceil`/`round`/`number_format`), ternaries and comparisons, `request('k')` (escaped), array indexes, associative and nested arrays, `@foreach` (keys, every `$loop` value, `parent`, nesting, `$loop` and `@continue`/`@break` in loops unrolled from the outside) and `@forelse`. All measured with curl against the converted server; 84 tests pass. Anything unresolved stays a 501 TODO. Open: `withInput` (needs a session layer).

- 08:14 `@for` の減少・刻み(`$i--`・`+= N`・`-= N`、`>`/`>=`/`!=`)に対応、curlで実測。 / `@for` counting down and steps supported, measured with curl.
- 08:15 `@for` の範囲に `count($xs)`・整数データ `$n` を使えるように、curlで実測。 / `@for` bounds from `count($xs)` and integer `$n`, measured with curl.
- 08:16 `@while` の条件に `count($xs)`・整数データ `$n` を使えるように、curlで実測。 / `@while` bounds from `count($xs)` and integer `$n`, measured with curl.
- 08:18 `@while` の刻み(`$i += N`・`$i -= N`)に対応、curlで実測。 / `@while` steps (`+= N`, `-= N`), measured with curl.
- 08:19 `@foreach(range(A, B[, 刻み]))` に対応、curlで実測。 / `@foreach(range(A, B[, step]))` supported, measured with curl.
- 08:21 ビューの計算式(`{{ $n * 3 }}` など)と要素への関数(`strtoupper($xs[0])`・`strlen('abc')`)に対応、curlで実測。 / View arithmetic and functions on items, measured with curl.
- 08:22 データなしビューの計算式にも対応、curlで実測。 / Arithmetic in views without data, measured with curl.
- 08:24 配列の関数(`max`・`min`・`end`・`reset`・`array_sum`・`in_array`の三項)に対応、curlで実測。 / Array helpers, measured with curl.
- 08:25 `str_pad`・`sprintf` に対応、curlで実測。 / `str_pad` and `sprintf`, measured with curl.
- 08:27 関数の引数に配列の要素(`$xs[0]`・`$u['k']`)を使えるように、curlで実測。 / Array items as function arguments, measured with curl.
- 08:29 文字列の連結(`.`)と配列の要素を使った計算に対応、curlで実測。 / Concatenation and arithmetic on items, measured with curl.
- 2026-11-28 比較の三項演算子 `{{ L op R ? 'a' : 'b' }}` に対応 / comparison ternary in views (96 tests, /tz measured).
- 2026-11-28 `@if(L op R)` の比較式に対応 / comparison @if (97 tests, /iz measured).
- 2026-11-28 入れ子の比較 @if に対応 / nested comparison @if (98 tests, /nz measured).
- 2026-11-28 @elseif の比較式に対応 / comparisons in @elseif (99 tests, /ez measured).
- 2026-11-28 単純な @if($k) と @elseif の不具合を修正 / fixed plain @if($k) with @elseif (100 tests, /pz measured).
- 2026-11-28 単純な変数の @elseif に対応 / plain-variable @elseif (101 tests, /vz measured).
- 2026-11-28 withInput() と old() に対応(クッキーで1回だけ受け渡し) / withInput() and old() via a one-request cookie (102 tests, /ozp and /oz measured).
- 2026-11-28 withInput の only/except に対応 / withInput with only/except (103 tests, /ozo and /oze measured).
- 2026-11-28 withErrors と @error・$errors->first に対応 / withErrors, @error and $errors->first (104 tests, /ozx and /oz3 measured).
- 2026-11-28 $errors->any/has/all に対応、エラーの順番を Laravel と同じに / $errors->any/has/all, Laravel order kept (105 tests, /oz4 measured).
- 2026-11-28: `$request->validate()` の単純な規則に対応 / simple-rule validate() supported (see PORTING.md).
- 2026-11-28: validate() に email・confirmed / email and confirmed rules (see PORTING.md).
- 2026-11-28: back()->with() と session() / back()->with() and session() (see PORTING.md).
