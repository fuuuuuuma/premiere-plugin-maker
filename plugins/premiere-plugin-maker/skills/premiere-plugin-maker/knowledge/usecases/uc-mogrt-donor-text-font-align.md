---
id: uc-mogrt-donor-text-font-align
title: パッチした文言が反映されない・日本語が豆腐になる・中央揃えが右揃えになる
kind: usecase
tags: [MOGRT, clientControls, フォント, mAlignment, 日本語, ドナー, 豆腐]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 画面用の既定文字（clientControls）も一緒にパッチし、非ASCIIにはその言語のフォントを指定し、揃えの enum は推測せず突き合わせて確かめる（0=左、1=右、2=中央）
parts: [mogrt-text]
related: [uc-mogrt-donor-patch-method, uc-mogrt-position-coordinates, uc-mogrt-empty-graphic-misdiagnosis, ref-mogrt]
---
## 症状

- 日本語が「豆腐」（四角の欠字）になる。
- パッチした文言が、ドナーの元の文字（"LIVE"）に戻ってしまう。
- 中央揃えにしたはずが、右揃えになる。

## 原因

3 つの原因が重なっていた。

1. 全言語の定義を en_US 版で上書きし、和文を `RobotoSlab-Light`（ラテン文字専用のフォント）で描かせた。
2. `clientControls` の `value.strDB` に、ドナーの元の文言が入っており、挿入のときに `mText` を上書きした。
3. `mAlignment` を「1 = 中央」と推測した。Photoshop 由来の enum は 0 = 左、1 = 右、2 = 中央。

## 直し方

1. ASCII 以外の本文は、`usedFontsLocalized.ja_JP` のフォント（`SourceHanSansJP-Regular`）に替える。
2. `clientControls` の文言も、全言語で差し替える。
3. 中央揃えは `mAlignment = 2` にする。

## 再発防止

- 生成した MOGRT から、文字列・サイズ・アライメントを復元して照合する往復の検証を置く（実ドナーを含む 41 件）。
- 画面に注入される既定値（clientControls）も、同時にパッチする。未知の enum は、突き合わせて確定する。
- 描画そのものは、実機で確かめていない。これらは空グラフィックの原因の候補だったが、直しても実機の空は直らなかった（`uc-mogrt-empty-graphic-misdiagnosis`）。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-25、v0.9.4 で欠陥、v0.9.5〜v0.9.6 で修正、日本語 UI）
