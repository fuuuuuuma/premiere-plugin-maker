---
id: uc-verify-probe-by-return-value
title: 診断の合格が「呼べた」だけで、実際には効果が付いていなかった（QE の addVideoEffect）
kind: usecase
tags: [検証, プローブ, QE, addVideoEffect, 戻り値, 日本語 UI, 判定表]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 実機で API を試す診断の合否は、呼べたかではなく、戻り値と状態の変化で判定する。日本語の UI では、効果の名前を日本語、英語の順に試す
parts: [probe, ppro-kit]
related: [uc-cep-qe-effect-locale, uc-uxp-api-doc-vs-device, core-verification]
---
## 症状

最初の診断の判定表は、QE の `addVideoEffect` を英語名の `getVideoEffectByName("Transform")` で引けるとして「合格」にしていた。ところが日本語 UI の実機では、効果が付いていなかった。

## 原因

判定のときに戻り値を見ていなかった。実際には `addVideoEffect` の戻り値は `false` だった。

## 直し方

1. 判定表に 2026-09-18 付の補足の行を足して、「付かない」に訂正する。
2. 効果の名前は、日本語の名前、英語の名前の順に試す。

## 再発防止

- 効果の追加は、戻り値と、部品（コンポーネント）の数が増えたことで確かめる。
- 診断は「例外が出なかった」で合格にしない。

## 出どころ

- Effect & Design の診断と受け入れの記録（2026-09-17〜09-18、Premiere 26.5 の日本語 UI）。受け入れのときに実機で訂正した。
