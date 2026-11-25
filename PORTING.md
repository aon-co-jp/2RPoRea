# PORTING.md — 2RPoRea

## 2026-11-25 新設と到達点 / Created, and where it stands
**日本語**
- ユーザー指示により新設(2026-11-25)。目的: 他の言語・フレームワークから **RPoRea**(RPoem と Reaxt を統合したフレームワーク)への変換。Reaxt は React・Next.js・Nuxt.js・Nest.js を統合したフレームワーク。
- 済み: 検出 `2rporea scan`(Python・Java・COBOL・PHP・Node.js/Nest と、React・Next・Nuxt・Vue)、単体テスト3件成功。
- 未了(この順): (1)バックエンド変換(Python=2Poem、Java=Java_to、COBOL=COBOL_to を RPoem 向けに呼ぶ)、(2)フロントエンド変換(React/Next/Nuxt/Vue → Reaxt。コンポーネント・ルート・データ取得・SSR)、(3)Node.js・TypeScript を例外的に選べる/選ばない選択、(4)`pl2pl` との統合、(5)毎晩の自動追従(2Poem と同様)、(6)紹介ページ(easy-web.tokyo)。
- 再開: `python -m pytest -q tests` で3件成功を確認してから(1)へ。

**English**
- Created on 2026-11-25 at the user's request. Goal: convert projects in other languages and frameworks to **RPoRea** (the framework integrating RPoem and Reaxt). Reaxt is the framework integrating React, Next.js, Nuxt.js and Nest.js.
- Done: detection `2rporea scan` (Python, Java, COBOL, PHP, Node.js/Nest, and React, Next, Nuxt, Vue) and 3 passing unit tests.
- Open (in this order): (1) backend conversion (call 2Poem for Python, Java_to for Java, COBOL_to for COBOL, targeting RPoem); (2) UI and Node-style server conversion (React/Next/Nuxt/Vue/Nest/Express to Reaxt: components, routes, data fetching, SSR); (3) Node.js / TypeScript as an optional exception, including choosing neither; (4) integration with `pl2pl`; (5) nightly auto-follow like 2Poem; (6) an intro page on easy-web.tokyo.
- To resume: run `python -m pytest -q tests`, confirm 3 pass, then start on (1).
