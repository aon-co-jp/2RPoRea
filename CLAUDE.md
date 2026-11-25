# CLAUDE.md — 2RPoRea

## 役割 / Role
**日本語**: 他の言語・フレームワークのプロジェクトを RPoRea(RPoem と Reaxt を統合したフレームワーク。Reaxt は React・Next.js・Nuxt.js・Nest.js の統合)へ変換する。`pl2pl`・`RPoem`・`open-cosmo`・`RMojo`・`MFastAPI`・`2MFastAPI`・`Reaxt`・`RPoRea`・`COBOL_to`・`Java_to` と**いつも同時に**開発する。1つ変えたら、ほかの確認と README・CLAUDE・PORTING・POLICY の更新を同じ日に行う。
**English**: Converts projects in other languages and frameworks to RPoRea (the framework integrating RPoem and Reaxt; Reaxt integrates React, Next.js, Nuxt.js and Nest.js). Always developed **together with** `pl2pl`, `RPoem`, `open-cosmo`, `RMojo`, `MFastAPI`, `2MFastAPI`, `Reaxt`, `RPoRea`, `COBOL_to` and `Java_to`. When one changes, check the others and update README, CLAUDE, PORTING and POLICY the same day.

## 開発の決まり / Rules
- **日本語**: 未了は確認なしで完成まで自動で進める。需要が少ない・大規模な作り直しが要る場合も、別の方法で済ませず、1から真摯に作り直す。新しい REST は作らない(Connect のみ)。秘密は書かない。本物で確かめてから「完了」と書く。文書は日本語と英語を基本に毎回編集する。
- **English**: Carry unfinished work through to completion without asking. Even when demand looks low or a large from-scratch rewrite is needed, do not substitute another approach; do the real work. No new REST (Connect only). Never write secrets. Say "done" only after checking on a real system. Edit docs in Japanese and English every time.
- Node.js / TypeScript は**例外的に選択可**で、選ばない選択も必ず動くこと。 / Node.js and TypeScript are an optional exception, and choosing neither must always work.

## 構成 / Layout
- `src/torporea/detect.py`: 検出(`scan`)。ファイルと依存の名前だけ。 / detection by file and dependency names only.
- `src/torporea/cli.py`: `2rporea scan <path>`。 / CLI.
- `tests/test_detect.py`: 検出の試験。 / detection tests.
- テスト: `python -m pytest -q tests` / Tests: `python -m pytest -q tests`

## 落とし穴 / Pitfalls
- **日本語**: シェルの heredoc で正規表現のバックスラッシュが半分になることがある。ファイルの編集は Edit/Write ツールで行う。
- **English**: A shell heredoc can halve backslashes in regexes; edit files with the Edit/Write tools.

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
