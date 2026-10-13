---
id: uc-uxp-qe-transition-settings
title: 標準のトランジションは付くが、設定を変えられない
kind: usecase
tags: [QE, トランジション, 標準エフェクト, 日本語名, 設定項目]
os: [mac, windows]
premiere: ">=25.5"
status: verified
summary: 標準搭載の効果やトランジションは QE で付くが、トランジションは matchName までしか読めず設定項目を変えられない。動きの調整は効果で作り、書き出して確かめる
parts: [cep-helper]
related: [ref-cep-extendscript, uc-uxp-transition-duration-ticks, uc-cep-qe-effect-locale, feat-ed-motion]
---
## 症状

標準の効果を使った動きで、光（グリント）の「位置」を動かしても光が流れない。ブラー（方向）が縦にぶれる。全画面を使う系（テレビの電源、VHS の劣化など）は、文字だけのクリップだと枠が見えてしまう。

## 原因

トランジションは `matchName` までしか読めず、`components` が null で、設定項目を変えられない。全画面系は、文字だけのクリップだと枠が見える（推測）。

## 直し方

1. 日本語名の `getVideoEffectByName` / `getVideoTransitionByName` で、26 種の標準の動きが付く。
2. 設定を動かしたい動きは、トランジションでなく効果として作る（定義ファイルの `effects[].static / tracks`）。
3. ブラー（方向）は角度 90 が横。リニアワイプは 270 が左から右、0 が上から下。グリントは「強さ」を一瞬だけ上げる。
4. 全画面系は外す。
5. UXP では `TransitionFactory.createVideoTransition(内部名)` で作る。

## 再発防止

- 標準搭載の効果も QE で付くが、角度や効き方は、実際に書き出した画を目で見て、採否を決める。使えないものは外す。

## 出どころ

- Effect & Design の実機の記録（Premiere 25.5 以降、検証は 26.5・日本語 UI、2026-09-18〜09-19）。書き出しの目視で確認した
