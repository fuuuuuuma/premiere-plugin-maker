---
id: uc-mogrt-flatbuffer-defaults
title: 書かれていない項目を 0 と決めつけて、色や縁が崩れる（FlatBuffer の既定値）
kind: usecase
tags: [prtextstyle, FlatBuffer, 既定値, テキストスタイル, 画素一致, 実測]
os: [mac]
premiere: ">=26.5"
status: verified
summary: FlatBuffer は既定値と同じ項目を書かない。欠けた項目を 0・黒・白と決めつけず、実機に描かせて画素が一致する値を既定値にする
parts: [mogrt-text]
related: [ref-prtextstyle, uc-mogrt-style-import-keep-blob, uc-mogrt-text-render-rules, feat-kazaru]
---
## 症状

テキストスタイルを、読み取った値から作り直すと、次のようにずれる。紫が茶色になる、白い縁が黒になる、光彩が増減する、斜体が落ちる、幅が 999 の縁で巨大な円が出る。

## 原因

FlatBuffer は、既定値と同じ項目を「書かない」。それなのに、欠けた項目を 0・黒・白だと決めつけた。縁の位置と、斜体の項目も読み落としていた。

## 直し方

実測した既定値を使う。

- 色の成分は 255。縁の色は白、影の色は黒
- 影: 濃さ 75、角度 135、距離 7、広がり 0、ぼかし 40
- 帯: 濃さ 75、広がり 0
- 縁の幅 1、文字サイズ 100
- 縁の位置: スタイルの f24（1 本目の縁）と、追加の縁の f5 で、1 = 内側、2 = 外側、無し = 中央
- 斜体: f15
- 見た目の情報は、Param 0 の base64 の blob（12 バイトのヘッダ + FlatBuffer）に入っている

## 再発防止

- 項目を抜いた MOGRT と、値を明示した MOGRT を Premiere に描かせ、1 画素まで一致するほうを既定値にする。71 本が 1 画素一致した。
- 旧い記述「色の既定値は 0」は訂正済み。非公開バイナリの欠けた項目の既定値は、推測しない。
- 帯の色の既定値だけは確認できていない。生成した物の実機での読み込みも未確認。

## 出典

- Effect & Design の実機の記録（2026-09-02〜09-19、Premiere 26.5、macOS）
