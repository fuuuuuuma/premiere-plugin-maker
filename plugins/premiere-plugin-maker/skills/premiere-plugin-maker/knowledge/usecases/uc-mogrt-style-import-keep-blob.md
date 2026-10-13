---
id: uc-mogrt-style-import-keep-blob
title: 取り込んだテキストスタイルの色・縁・光彩・斜体が半分ほど食い違う
kind: usecase
tags: [スタイル, 取り込み, blob, FlatBuffer, 本文差し替え, 画素一致, 設計判断]
os: [mac]
premiere: ">=26.5"
status: verified
summary: 非公開バイナリは作り直さず、元の blob を保ったまま必要な所（本文）だけを差し替える。元の画と取り込み後の画を全件比べて確かめる
parts: [mogrt-text]
related: [uc-mogrt-flatbuffer-defaults, uc-mogrt-text-render-rules, feat-ed-import-styles, ref-prtextstyle]
---
## 症状

読み取った値でスタイルを再構成すると、実物 78 種のうち約半数で、色・縁・光彩・斜体が食い違った。

## 原因

非公開のバイナリを、読み取った値から作り直す方式は、既定値の解釈や、縁の内外・斜体の読み落としを、防ぎきれない。

## 直し方

1. 元のソーステキストの blob を、`style.json` の `source` にそのまま持つ。
2. 適用するときは、run（文字の連なり）の本文だけを差し替える（`engine/style_tree.py` の `source_tree`）。
3. 取り込んだ物の置き場は、更新で消えない場所（`~/Library/Application Support/EffectDesign/` の下）にする。

## 再発防止

- 元の画と、取り込み後の画を、全件比べる。77/78 件が 1 画素まで一致した。
- 外部から取り込む非公開バイナリは、作り直さず、元のバイト列を保って、必要な所だけを書き換える。

## 出典

- Effect & Design の実機の記録（2026-09-19、v0.3.0、Premiere 26.5）。Premiere に描かせた画との全件比較で確認
