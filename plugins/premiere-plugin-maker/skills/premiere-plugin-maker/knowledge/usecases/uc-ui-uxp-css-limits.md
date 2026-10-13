---
id: uc-ui-uxp-css-limits
title: UXP の CSS・HTML はブラウザと同じに書けない（Grid・影・input の中央揃え・SVG）
kind: usecase
tags: [UXP, CSS, Grid, box-shadow, text-align, SVG, Spectrum, 制約]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: UXP は Grid、外向きの影、input の text-align、複雑な SVG に対応しない。レイアウトは flex、影は inset だけ、色は 16 進数の直書きにして、描けないものは画像で同梱する
parts: [ui-kit]
related: [core-ui-rules, uc-ui-flex-rows-collapse, uc-ui-details-hidden, uc-ui-sp-button-inactive]
---
## 症状

- FPS の入力欄の `text-align:center` が効かない（contenteditable・padding・外側の flex を使っても、完全な中央にならない）。
- SVG では、テロップの見本の表現が足りない。

## 原因

UXP が、Grid、外向きの影、`<input>` の `text-align`、複雑な SVG の描画に対応していない。SVG の件は、公式の既知の問題の記述による。

## 直し方

| 項目 | 回避の方法 |
|---|---|
| レイアウト | flex だけを使う |
| 影 | `box-shadow` は inset だけ |
| 色 | 16 進数の直書き（CSS 変数は未確認） |
| グラデーション | UXP 8.1 以降なら使えるが、直前に単色を書いてフォールバックにする |
| Spectrum 部品（`sp-button`） | 既定の色が強いので、`!important` で上書きする |
| 中央揃えの入力 | 入力欄でなく、ステッパー（− N +）の UI にする |
| 見本の描画 | Chromium で描いた透過 PNG を、事前に生成して同梱する |

## 再発防止

- CSS の色をパレットだけに限定するテストを置く。
- UXP の可否は、公式の対応を確認する。UXP 実機での確認は必要。
- CEP（Chromium 99）の拡張では Grid を使えているので、UXP と CEP で可否が違う。

## 出どころ

- Cut & SRT と Silence Cut の設計書・引き継ぎ記録（2026-05-01〜09-25）。設計書と公式の対応の確認のみ
