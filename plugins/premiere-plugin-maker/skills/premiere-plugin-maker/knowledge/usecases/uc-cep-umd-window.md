---
id: uc-cep-umd-window
title: CEP で window.X が未定義になる。UMD 風の module の判定が Node 側へ入ってしまう
kind: usecase
tags: [CEP, UMD, module, window, グローバル, Node, Chromium 99]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: CEP はページにも module を作るので、typeof module の分岐は Node 側に入り、window に API が載らない。module.exports と window の両方に載せる
parts: [cep-helper]
related: [ref-cep-extendscript, uc-cep-node-exec-callback, uc-cep-es3-json]
---
## 症状

Node の単体テストは通るのに、実機のパネルで `window.EDCatalog` のような関数が未定義になり、「読み込んでいます…」で止まる。

## 原因

UMD 風の書き方（`typeof module !== "undefined"` で Node かブラウザかを分ける）は、CEP では誤動作する。CEP が、ページの側にも `module` を作るので、ブラウザの側でも Node の分岐に入り、`window` に API が載らない。

## 直し方

グローバルへの登録は、分岐にせず、両方に載せる。

```js
module.exports = api;
if (root) root.X = api;
```

## 再発防止

- CEP の Chromium は 99。`:has()`・コンテナクエリ・CSS のネスト・`?.`・`??` は使えない。
- 実機で確かめる。Node の単体テストの結果だけで、完了と言わない。

## 出どころ

- Effect & Design の受け入れ記録（2026-09-17〜09-21、Premiere 26.5・CEP）
