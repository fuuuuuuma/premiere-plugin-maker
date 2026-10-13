---
id: uc-ui-details-hidden
title: 折りたたみに details を使うと開閉が不安定。hidden を付けても消えない
kind: usecase
tags: [UXP, details, hidden, display, 折りたたみ, CSS, トグル]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: UXP では標準の HTML 要素の対応を当てにせず、ボタンと div の自前トグルにする。hidden を使う画面には、先に [hidden]{display:none!important} を置く
parts: [ui-kit]
related: [core-ui-rules, uc-ui-uxp-css-limits, uc-ui-sp-button-inactive]
---
## 症状

- `<details>` と `<summary>` が確実に開閉せず、何度も壊した。
- `el.hidden = true` にしても要素が消えず、選択のトレイが常に表示される。それが「そういうデザイン」に見えてしまい、気づけなかった。

## 原因

- UXP では `<details>` の挙動が不安定。
- `hidden` 属性は、ブラウザの初期スタイル（UA スタイル）の扱いで、作者が書いた `.tray{display:flex}` に負ける。

`hidden` の件は Web で確認した。UXP での確認と、`<details>` を避けた版（v0.8.0）の効果は、予防の判断で、検証は未実施。

## 直し方

1. ボタンと div の自前トグルにする（`.collapsed` クラスの付け外し、または hidden の切り替え）。
2. CSS の先頭に `[hidden]{display:none!important}` を置く。

## 再発防止

- `getComputedStyle(el).display` を実機で見て、`hidden===true` と食い違っていないか確かめる。
- ほかのプラグイン（無音カット）の引き継ぎ記録も、同じ結論に至っている。

## 出どころ

- Cut & SRT と Silence Cut の引き継ぎ記録、作者の Web 実装のメモ（2026-04-29〜2026-08）
