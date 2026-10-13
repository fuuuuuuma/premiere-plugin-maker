---
id: uc-cep-qe-effect-locale
title: 日本語の Premiere で QE の効果が付かない
kind: usecase
tags: [QE, CEP, ExtendScript, 日本語, 効果名, ロケール, addVideoEffect]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 日本語の画面の Premiere の QE は、日本語の表示名でしか効果を引けない。英語名を渡すと名前の空の効果が返る。日本語名 → 英語名の順に試し、戻り値と部品の数で付いたか確かめる
parts: [cep-helper]
related: [ref-cep-extendscript, uc-uxp-qe-transition-settings, uc-uxp-keyframe-extra-and-wrapped]
---
## 症状

`getVideoEffectByName("Transform")` が、名前の空の効果を返し、`addVideoEffect` が false になった。英語名で引けるという事前の試験の判定は、誤読だったと受け入れの確認で分かった。

## 原因

日本語の画面の Premiere では、QE が日本語の表示名でしか効果を引けない。「トランスフォーム」と書けば付く（matchName は `AE.ADBE Geometry`）。「ｺﾝﾎﾟｼﾞｼｮﾝのｼｬｯﾀｰ角度を使用」のように、半角カナの名前の項目もある。

## 直し方

1. 効果は、日本語名 → 英語名の順に試す。
2. `addVideoEffect` の戻り値と、クリップの部品の数の増加で、付いたかを確かめる。
3. 全角と半角の揺れを吸収する。
4. 付かない項目は、定義ファイル（`motion.json`）の `fallback` で外す。

## 再発防止

- QE の名前引きは UI の言語に依存する。戻り値と部品の数で、必ず確かめる。
- UXP 側では、表示名でなく matchName（例 `AE.ADBE Geometry`）で足す。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5・日本語 UI、2026-09-17〜09-18）。受け入れの A4 は 3 回目で合格した
