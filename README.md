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
