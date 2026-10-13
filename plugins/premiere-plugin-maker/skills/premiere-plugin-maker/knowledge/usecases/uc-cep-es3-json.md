---
id: uc-cep-es3-json
title: ExtendScript で「JSON is undefined」。再生ボタンが無反応になる
kind: usecase
tags: [ExtendScript, ES3, JSON, CEP, evalScript, EvalScript error]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: ExtendScript は ES3 で、JSON オブジェクトが無い。JSON.stringify を呼ぶと "EvalScript error." としか返らない。必要な形だけ自前で文字列にする
parts: [cep-helper]
related: [ref-cep-extendscript, uc-cep-node-exec-callback, uc-cep-umd-window]
---
## 症状

パネルの再生ボタンを押しても、何も起きない。ホスト側の ExtendScript の呼び出し（`evalScript`）の結果は、"EvalScript error." としか返らず、原因が分からない。

## 原因

ExtendScript は ES3 相当で、`JSON` オブジェクトが無い。`JSON.stringify` を呼ぶと、エラーになる。2026-08-16 に、実機で再生ボタンが無反応だった真因として分かった。

## 直し方

1. 必要な形だけを、自前で文字列に組み立てる関数を書く（Effect & Design では `edJson()`）。配列の判定は、`instanceof Array` が環境によって効かないことがあるので、注意する。
2. ホスト側の公開関数は、引数を JSON の文字列で受け取り、戻りも JSON の文字列にする形に揃える。受け取る側は、パネル（Chromium）の `JSON.parse` で読む。

## 再発防止

- ExtendScript のコードを書くときは、ES3 で使える機能だけにする（`JSON` のほか、新しい構文も使えない）。
- 実機で押して確かめる。

## 出どころ

- Cut & SRT の再生補助と Effect & Design のホスト側スクリプト（2026-08-16、実機で確認）
