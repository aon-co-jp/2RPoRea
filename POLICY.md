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
