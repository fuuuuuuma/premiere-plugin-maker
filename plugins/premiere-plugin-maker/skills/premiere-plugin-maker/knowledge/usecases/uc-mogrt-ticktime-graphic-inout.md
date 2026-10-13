---
id: uc-mogrt-ticktime-graphic-inout
title: テロップの整列で、着地がずれる・カット点を飛び越える（TickTime 算術とグラフィックの in/out）
kind: usecase
tags: [UXP, TickTime, グラフィック, setInPoint, setOutPoint, 整列, 吸着, 検証]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: TickTime の引き算は負で異常値を返す。グラフィックは in/out を動かさず start/end だけを使い、候補の境界は始点と終点を分け、適用後に読み戻して確かめる
parts: [ppro-kit]
related: [uc-mogrt-place-snap-edit-points, feat-caption-align, feat-cutsrt-align, ref-ticktime]
---
## 症状

整列したあと、テロップが着地点でずれた（初版）、2 フレームずれた（次の 2 版）、V1 のカット点を 3 フレーム飛び越えた（その次の版）。

## 原因

- `tickTime.subtract()` は、結果が負になるときに異常な値を返す。
- グラフィックのクリップは、負の TickTime を `setInPointAction` と `setOutPointAction` に渡すと、二重に適用される。グラフィックは素材に入点・出点を持たないので、in/out の意味が映像や音声のクリップと違う。
- V1 のクリップは、隣り合う間に 2 フレームの隙間がある。吸着の候補の境界を 1 本の集合にまとめると、終点が次の始点に吸着してしまう。

## 直し方

1. 差分は「大きい方 − 小さい方」で作り、負にしない。
2. TickTime は、比率から作り直さず、取得したものをそのまま再利用する。
3. グラフィックのクリップは、in/out に触れず、`createSetStartAction` と `createSetEndAction` だけで動かす。
4. 吸着の候補は、始点用と終点用を分ける（`startBoundaries` と `endBoundaries`）。

## 再発防止

- 適用したあとに実際の位置を読み戻し、期待との差をログに出す（`verify end: actual=X 期待=X 差=0`）。実機の読み戻しで、差が 0 になったことを確認した。
- 既知の限界: 許容の幅の中に偽の V1 の境界があると、動かないはずのテロップが 1〜2 フレーム動く。

## 出典

- Caption Align の記録（2026-04-29、v1.0.0〜v1.0.4、Premiere 25.x）。読み戻しの検証ログで差 0 を確認
