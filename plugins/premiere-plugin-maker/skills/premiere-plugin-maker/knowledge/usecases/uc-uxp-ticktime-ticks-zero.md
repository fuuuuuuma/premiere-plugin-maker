---
id: uc-uxp-ticktime-ticks-zero
title: 位置を読むといつも 0 になる・未設定の入点が -400000 秒で返る
kind: usecase
tags: [UXP, TickTime, ticks, ticksNumber, 番兵値, 貼り付け]
os: [mac, windows]
premiere: ">=26.0"
status: partial
summary: 実機の TickTime は .ticks が 0 になることがある。.ticksNumber を先に見て、未設定の入点の番兵値 -400000 秒は未設定として扱う
parts: [ppro-kit]
related: [ref-ticktime, core-api-patterns, uc-uxp-getmediatype-guid]
---
## 症状

クリップを貼り付ける機能で、貼れたように見えて実は範囲外に置かれている（同じシーケンスでも）。UXP のログでは、すべてのクリップの開始位置が `start:0` だった。別の件では、未設定の入点が -400000 秒という異常な値で返ってきた。

## 原因

実機の Premiere では、`getStartTime()` や `getPlayerPosition()` が返す TickTime の `.ticks` が 0 になることがある。そのため、差分（offset）が絶対値になり、複製したクリップが画面の外へ飛んでいった。未設定の入点は、-400000 秒という番兵値（「無い」を表す特別な値）で返る。

「別のシーケンスでは元のクリップを再取得できない」という以前の結論は、この原因が分かって覆った。

## 直し方

1. 位置を数値にする関数を 1 つ作り、`.ticksNumber` を優先して読む。位置の取得はすべてこの関数にそろえる。
2. 番兵値（-400000 秒など）は、「未設定」として正規化する。
3. UXP のログの位置の行を最初に見て、貼り付けた結果を実機で確かめる。

## 再発防止

- `check.py` の J010 が、`.ticks` を直接読む書き方を警告する。
- TickTime の値は 0 や特別な値で返りうると考え、必ずログで実際の値を見る。

## 出どころ

- Cut & SRT の引き継ぎ書（2026-07-14 / 07-21、v0.8.0 予定、Premiere 2026）
- `.ticks` が 0 になることは実機のログで確認した。修正後の実機での貼り付けは未確認なので partial
- 別の機能（26.5）では `ticks` を文字列として扱って動いていた記録もある。キットの部品は、`ticksNumber` を先頭にした防御の連鎖に合わせた
