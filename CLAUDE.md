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
