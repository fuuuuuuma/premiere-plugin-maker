---
id: uc-ui-flex-rows-collapse
title: 一覧の行やカードが中身より低く潰れて、ボタンが文字に重なる
kind: usecase
tags: [UXP, CSS, flex, flex-shrink, grid, スクロール, 下見]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP の flex は、子に「中身より小さくならない下限」が無く、行が溢れると縮む。スクロールさせる列の子には flex:0 0 auto を付け、下見は UXP と同じ条件にして、件数を増やした状態で見る
parts: [ui-kit]
related: [core-ui-rules, uc-ui-narrow-dock, uc-ui-uxp-css-limits]
---
## 症状

- 行の中のボタンがテキストに重なって押せない（キューが 33 件のとき）。
- CEP のパネルでは、カード 8 枚の枠が、本来 175px のところ 101px に潰れた。
- 3 回再発した（分割の行、辞書の一覧、素材のタブ）。

## 原因

- 縦に並べた flex の列（`max-height` と `overflow-y:auto`）で、行が溢れると、`flex-shrink` が 1 なので行が縮む。UXP には、`min-height:auto` に当たる下限（中身より小さくならない保証）が無い。普通のブラウザ（Chromium）の下見では、この崩れは見えない。
- grid では、`overflow:hidden` のカードが「自動の行」になり、最小の高さが 0 になる。

最初は `flex-wrap` を疑ったが、誤りだった。

## 直し方

1. 縮めたくない子（一覧の行など）に `flex: 0 0 auto` を付ける（例: `.dict-list > *`）。溢れた分は、親のスクロールに任せる。
2. grid では `grid-auto-rows: max-content` にする。

## 再発防止

- 下見には `*{min-width:0;min-height:0}` を加えて、UXP と同じ条件にし、偽のデータで中身を入れて描く。
- 件数を増やした状態で見る。機械による検査のあとに、目でも確かめる。ある時は、下見で 0 件だったので崩れが見えず、実機で崩れた。

## 出どころ

- Cut & SRT と Effect & Design の失敗記録（2026-07-24〜09-23、UXP 実機で確認）
