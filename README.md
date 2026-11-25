# 2RPoRea

**日本語**: さまざまな言語・フレームワークで作られたプロジェクトを、**RPoRea**(バックエンド=RPoem、フロントエンド=Reaxt。Reaxt は React・Next.js・Nuxt.js・Nest.js の良いところを Rust で統合したもの)へ変換するためのツールです。姉妹の [2MFastAPI](https://github.com/aon-co-jp/2MFastAPI)・[2Poem](https://github.com/aon-co-jp/2Poem)・[2FastAPI](https://github.com/aon-co-jp/2FastAPI) と同じ流儀で作ります。**現在は最初の一歩(検出 `scan`)だけです。変換そのものは開発中で、まだ動きません。**
**English**: A tool to convert projects written in many languages and frameworks to **RPoRea** (backend = RPoem, frontend = Reaxt, which merges the good parts of React, Next.js, Nuxt.js and Nest.js in Rust). It follows the same style as its siblings [2MFastAPI](https://github.com/aon-co-jp/2MFastAPI), [2Poem](https://github.com/aon-co-jp/2Poem) and [2FastAPI](https://github.com/aon-co-jp/2FastAPI). **Today only the first step exists (detection, `scan`). Conversion itself is under development and does not work yet.**

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
2. フロントエンドの変換: React・Next.js・Nuxt.js・Vue のコンポーネント・ルート・データ取得を **Reaxt**(Rust だけ)へ。1から作る大きな仕事で、近道はしません。 / Frontend conversion of React / Next.js / Nuxt.js / Vue components, routes and data fetching to **Reaxt** (Rust only). This is a large from-scratch job and we take no shortcuts.
3. Node.js・TypeScript は、2MFastAPI と同様に例外的に選べるようにし、**選ばない**こともできるようにする。 / Node.js and TypeScript are an optional exception (as in 2MFastAPI), and choosing neither must also work.

## 現況・未了 / Status (2026-11-25)
**日本語**: `scan` と単体テスト3件(Python+React/Next、Java+COBOL+PHP+Nest、`node_modules` の除外)が動きます。変換は未着手です。実機(Mac・iPhone)の確認も未了です。
**English**: `scan` and 3 unit tests (Python + React/Next, Java + COBOL + PHP + Nest, `node_modules` skipping) work. Conversion is not started. Real Mac/iPhone checks are open.

ライセンス / License: MIT
