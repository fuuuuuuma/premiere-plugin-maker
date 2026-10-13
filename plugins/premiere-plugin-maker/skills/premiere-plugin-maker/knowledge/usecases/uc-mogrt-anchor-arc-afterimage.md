---
id: uc-mogrt-anchor-arc-afterimage
title: 画面下のテロップに拡大・回転を当てると画面中央へ弧を描く
kind: usecase
tags: [アニメーション, アンカーポイント, スケール, 回転, 残像, トランスフォーム, QE]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 既定のアンカーは画面中央。拡大や回転の前にアンカーを対象の位置へ移して位置を補正する。残像はトランスフォーム効果自身の動きにしか乗らない
parts: [mogrt-text, ppro-kit]
related: [ref-keyframe-interpolation, feat-ed-motion, uc-uxp-keyframe-curve-overshoot, ref-prfpset]
---
## 症状

画面の下にあるテロップに、拡大と回転のアニメを当てると、画面の中央へ向かって弧を描いて飛んでいく（14 本）。また、モーションの側にキーを打っても、残像（シャッター角度による動きのぼかし）が出なかった。

## 原因

- 既定のアンカーポイント（回転や拡大の中心）は、画面の中央（0.5 : 0.5）。クリップが中央以外にあると、回転や拡大の中心がクリップの外になり、弧を描く。
- シャッター角度の残像は、トランスフォーム効果自身の動きにしか乗らない。モーションの側のキーには効かない。

## 直し方

1. スケールと回転のキーの前に、アンカーを文字の位置へ移し、位置を同じ量だけ補正する（`edPivotToText`）。傾きや既存のキーがあるときは、警告を出す。
2. 残像が要る動きは、最初からトランスフォーム効果にキーを打つ（動きの定義で `target: "transform"`）。
3. QE のクリップには、プリセットを適用する口が見つからなかった。キーは、`setTimeVarying` → `addKey` → `setValueAtKey` → `setInterpolationTypeAtKey` の順に打つ。

## 再発防止

- 直した 14 本を、書き出し直して一覧で確認する。
- 注意: ExtendScript の位置キーは、空間補間で行き過ぎが設計の約 2 倍（5% が 9.4%）になる。プリセットの接線を 0 にすれば出ないという想定は、未確認（`uc-uxp-keyframe-curve-overshoot`）。「口が無い」は、列挙しただけの弱い根拠。

## 出典

- Effect & Design の実機の記録（2026-09-17〜09-23、Premiere 26.5）。.prfpset の書式は機械検証まで
