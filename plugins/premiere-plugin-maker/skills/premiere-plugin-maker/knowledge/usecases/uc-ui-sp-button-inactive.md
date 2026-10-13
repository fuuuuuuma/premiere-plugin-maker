---
id: uc-ui-sp-button-inactive
title: 起動したときから表示されているページのボタン（sp-button）が押せない
kind: usecase
tags: [UXP, sp-button, Spectrum, hidden, click, requestAnimationFrame, 不活性]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP の sp-button は、いったん非表示になって再び表示される遷移を経ないと、反応しない状態のままになる。最初のページを一度 hidden にして、次の描画で戻す。保険として pointerdown 後にクリックが来なければ実行する
parts: [ui-kit]
related: [core-ui-rules, uc-ui-details-hidden, uc-ui-uxp-css-limits]
---
## 症状

パネルを開いたときから見えているページの `sp-button`（Spectrum のボタン）が、押しても反応しない。別のタブへ移ってから戻ると、押せるようになる。

## 原因

UXP の `sp-button` は、非表示から表示への遷移を一度経ないと、不活性（反応しない状態）のままになる。起動時から表示されているページは、その遷移を経ていない。

## 直し方

1. 最初に表示するページを、一度 `hidden` にして、`requestAnimationFrame` で次の描画に戻す。`requestAnimationFrame` が不安定な環境に備え、無ければ `setTimeout(0)` を使う。
2. 保険として、`pointerdown` から 400ms 以内に `click` が来なければ、その処理を実行する。二重に実行されないよう、時刻でガードする。

## 再発防止

- 起動直後に表示されるボタンは、必ず実機で押して確かめる。ブラウザの下見では再現しない。
- `sp-button` の既定の見た目が強いので、`!important` で上書きする（別の項を参照）。

## 出どころ

- Cut & SRT のパネルの実装と実機の記録（Premiere 26.3 / Mac）
