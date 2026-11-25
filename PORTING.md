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
