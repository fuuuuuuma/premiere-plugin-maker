---
id: uc-fps-vfr-timebase
title: 最後の 100 秒だけカットされない（宣言の timebase と実際の fps の食い違い）
kind: usecase
tags: [fps, VFR, timebase, FCP7 XML, 画面収録, 末尾, 同期]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 可変フレームレート素材は、実際は 29.998fps でも XML には整数の timebase=29 で書かれる。宣言された値と実際の値は一致しない前提で、解析の窓を実際の長さに抑え、レートを張り替える
parts: [fcpxml, silence-cut]
related: [uc-fps-mixed-ticks-basis, uc-fps-conform-rate-trust, ref-fcp7-xml, ref-ticktime]
---
## 症状

- 無音カットの最後の約 100 秒が、まったく切られずに残る。
- 文字起こしが、最大で約 38 秒先の音声を読んでしまう。
- カットのあと、タイムラインに赤い「同期ずれ」の印（+17、+18 のような数字）が出る。

同じ原因が 3 回、違う形で出た（2026-06-15 は末尾の未カット、2026-07-20 は同期の印、のちに文字起こしのずれ）。

## 原因

スマートフォンや画面収録の素材は、可変フレームレート（VFR。1 秒あたりのコマ数が一定でない）のことがある。実際は約 29.998fps でも、Premiere が書く FCP7 XML は、それを `timebase=29`・`ntsc=FALSE`（整数の 29fps）に切り捨てて宣言する。すると次のことが重なる。

- 解析する窓の長さが、実際の音声の長さを超える。
- `<rate>`・`in/out`・`pproTicks`（Premiere 内部の時間単位）が、すべて 29 基準のまま残る。
- 29 と 29.998 の差は約 3% あり、位置に比例してずれが貯まる。後ろへ行くほど大きい。

## 直し方

1. 編集は、標準的な 30 または 29.97fps のシーケンスか、固定フレームレート（CFR）の素材で行う。
2. 解析の窓を、実際の音声の長さに切り詰める（クランプ）。
3. サーバー側で、すべての `<rate>`・`start`・`end`・`in`・`out`・`pproTicks` を、本当のレートに張り替える（`conform_sequence_rate`）。張り替えの信頼境界は `uc-fps-conform-rate-trust` を見る。
4. 時間をフレームに直すときは、`start.ticks / timebase` のように ticks から出す方法が安全。

## 再発防止

- 文字起こし用の音声のキャッシュの鍵に、実 fps と pproTicks を含める。古い版との混在は、通信の版番号（`bridgeProtocol`）を上げて止める。
- 「宣言された fps」と「実際の fps」と「ticks」が別物だと、最初から設計に書く。換算の基準は `uc-fps-mixed-ticks-basis` を読む。
- 2026-06-15 に採った「実 fps 基準の換算」は、貯まるずれ（累積ドリフト）を生み、06-19 に「宣言 timebase 基準」へ訂正された。のち、その規則もさらに変わっている。いま実機の XML で確かめるまで、換算の規則を固定しない。

## 出典

- Cut & SRT の記録（2026-06-15、2026-07-20、v0.7.7、v0.10.3）と、README の VFR の節
- Effect & Design の実機の記録（Premiere 26.5）。実 XML と実素材で再現したが、修正後に読み込み直した結果の記録は無い
