---
id: uc-uxp-override-frame-rate
title: 素材のフレームレートを変えると、ほかのクリップまで変わる
kind: usecase
tags: [UXP, フレームレート, 上書き, ClipProjectItem, 素材単位, 取り消し]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 素材のフレームレートの上書きは ClipProjectItem.createSetOverrideFrameRateAction で、素材単位。全クリップ・全シーケンスに連動するので、画面で明示する
parts: [ppro-kit]
related: [core-api-patterns, ref-ticktime, uc-fps-property-missing]
---
## 症状

選択したクリップの素材のフレームレートを変える UXP の API が分からなかった（機能追加のときの調査）。実装してみると、変更が思わぬ範囲に及ぶ。

## 原因

`ClipProjectItem.createSetOverrideFrameRateAction(fps)`（Since 25.6、「フッテージを変換」に相当）は、クリップ単位でなく素材（ProjectItem）単位で効く。同じ素材を使うすべてのクリップと、すべてのシーケンスに連動する。

## 直し方

1. 公式サンプルとリファレンスで実在を確かめる。
2. `getProjectItem()` → `getId()` で素材ごとに重複を除く。
3. `ClipProjectItem.cast` したあと、`lockedAccess` → `executeTransaction` の 1 取引で適用する（取り消しは 1 回）。
4. ネストしたシーケンスは `isSequence()` でスキップする。
5. 画面とガイドに、「素材単位で連動する」と明記する。API が無い環境は、原因つきのエラーで止める。

## 再発防止

- 重複を除く処理、API が無いときのエラー、不正なフレームレートの値の試験を持つ。
- フレームレートの変化、連動の範囲、取り消しは、実機で未検証なので、確かめるまで断定しない。

## 出どころ

- Cut & SRT の引き継ぎ書（2026-07-24、Premiere 25.6 以降 / 取引の規約は 26.3 以降）
- 公式ドキュメントでの実在確認と Node の試験のみ
