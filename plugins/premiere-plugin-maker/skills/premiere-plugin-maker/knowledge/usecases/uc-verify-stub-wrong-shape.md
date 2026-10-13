---
id: uc-verify-stub-wrong-shape
title: テストは全部緑なのに実機では壊れていた（スタブが実機に無い形をまねていた）
kind: usecase
tags: [検証, テスト, スタブ, モック, 実機の形状, fps 検出]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: スタブの形は公式のリファレンスと実機の戻り値から起こし、実データで 1 度は照合する。誤った形のスタブは、テストを通してバグを固定してしまう
parts: [probe, ppro-kit]
related: [uc-fps-property-missing, uc-verify-test-double-defaults, uc-verify-node-green-device-broken, uc-verify-regression-fails-when-broken]
---
## 症状

パネルのテストは全部緑なのに、実機では fps の検出がいつも失敗し、60fps の XML が壊れていた。

## 原因

テストのシーケンスのスタブが、実機には存在しない形（`getSettings()` が `{videoFrameRate: fps}` を返す、など直接のプロパティ）をまねていた。実装の欠陥と、テストの前提が同じ誤りを共有していたので、緑のまま固定された。テストがバグを固定した、という状態。

## 直し方

1. スタブを実機の形（`getVideoFrameRate()` というメソッドが `FrameRate` のオブジェクトを返す）に直す。
2. 7 件のテストを新設する。
   - 実機の形で 60 / 59.94fps を検出する。
   - 旧実装が仮定した、存在しない形は「検出失敗」と明示される。
   - 例外を握りつぶしてクラッシュしない。
   - 検出に失敗したときは timebase を送らず、成功したときは送る。

## 再発防止

- 直す前のコードでテストが落ちること（fail-first）を確かめてから緑にする。
- スタブを、実機のログや実データと突き合わせる仕組みは、記録の時点では無かった。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の開発メモ（2026-07-24、v0.9.1）。スタブの形の誤りはコードの照合で確認した。実機での再確認の記録は無い。過去にも同じ型の事例があった。
