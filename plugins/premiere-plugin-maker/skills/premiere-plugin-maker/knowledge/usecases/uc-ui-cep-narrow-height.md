---
id: uc-ui-cep-narrow-height
title: CEP パネルの幅や高さが小さいと、操作が画面の外へ押し出される
kind: usecase
tags: [CEP, Chromium 99, レイアウト, ResizeObserver, media query, コンテナクエリ, ドック]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: パネルは幅も高さも変わる。操作の入口が画面の外へ出ないようにし、コンテナクエリなど新しい CSS に頼らず、ResizeObserver か media query で切り替える
parts: [ui-kit]
related: [core-ui-rules, uc-ui-narrow-dock, uc-ui-flex-rows-collapse]
---
## 症状

- 幅 316px で、上の段の検索欄と設定の歯車が画面の外へ出て、設定を開けない。
- 高さの低いパネルでは、見本が場所を取りつくして、一覧が潰れる。

## 原因

- 上の段が折り返さない。
- 見本と一覧の面積を、高さに応じて配分していない。
- CEP の Chromium は 99 で、コンテナクエリが無い。`vw`/`vh` を基準にした切り替えは、不具合の元だった。

## 直し方

1. 上の段を折り返す作りにする。
2. 切り替えには、`ResizeObserver` で `.wide` のようなクラスを付け外しするか、`@media (max-height:520px)` を使う。
3. 見本は `aspect-ratio` と、実寸のピクセルの `max-height` で作り、`vw`/`vh` を使わない。

## 再発防止

- 幅 435・320・400、高さ 600・500・400 の組み合わせで画面を撮って確かめる。
- CEP の Chromium 99 では、`:has()`・コンテナクエリ・CSS のネスト・`?.`・`??` も使えない。
- 316px の件は実機で確認した。ほかは設計書の記述で、実装後の確認はまだ。

## 出どころ

- Effect & Design の設計書と受け入れ記録（2026-09-19〜09-21、Chromium 99）
