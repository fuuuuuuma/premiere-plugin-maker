---
id: uc-fps-mixed-ticks-basis
title: 終盤ほどカットがずれる（フレームと ticks の基準の混在）
kind: usecase
tags: [fps, ticks, pproTicks, FCP7 XML, in/out, rate, ずれ, 換算]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: XML の中でフレーム値・in/out・ticks が別々の基準を持つと、差が位置に比例して貯まる。全部を同じ基準で換算し、実際の XML で確かめるまで規則を固定しない
parts: [fcpxml, silence-cut]
related: [uc-fps-vfr-timebase, uc-fps-conform-rate-trust, uc-fps-override-not-in-file-rate, ref-fcp7-xml, ref-ticktime]
---
## 症状

- 約 10fps の画面収録で、終盤が約 14 秒ずれる。
- 「30 でカットしたのに 29 で返ってくる」。
- フレームレートが混在する XML で、字幕作りが「速度変更またはタイムリマップされた音声クリップは未対応です」で失敗する。

## 原因

XML の中の時間が、要素ごとに別の基準で書かれていた。

- フレーム値（`start`・`end`）は、宣言された timebase（例: 10）で数えるのに、`pproTicks` は実際の fps（例: 10.056）基準だった。差は 0.57% でも、位置に比例して貯まり、Premiere は ticks のほうを優先して読んだ。
- `in`・`out` は「クリップ自身の rate」で数える単位なのに、`start`・`end`（シーケンスの rate）と同じ単位として換算していた。

## 直し方

1. `in`・`out`・`pproTicks`・無音の検出を、クリップが宣言している rate で換算する（`clip_declared_fps()`）。
2. すべての `<rate>` を本当のレートへ張り替え、`pproTicks` を計算し直す。
3. 実際の約 10fps の動画と、宣言が 10 の XML、30fps のシーケンスに 60fps のクリップ rate が混ざる XML で、書き出しと読み直しの往復を、先に落ちるテストにして確かめる。

## 再発防止

- どの数字が「どの基準」かを表にして、換算の前に確かめる。フレームなのか、秒なのか、ticks なのか。シーケンス基準なのか、クリップ基準なのか。
- 実際の XML で確かめるまで、規則を固定しない。この件の診断は 3 回変わった（2026-07-18 の「宣言 timebase に統一」、「カットエンジンは 30fps 前提」、v0.7.6 の rate だけの張り替え）。これらは古い診断なので、それをもとにした実装があれば疑う。
- 同じエラーは、別の原因（`uc-fps-property-missing`）でも出る。レート混在だけが唯一の原因だとは決めつけない。

## 出典

- Cut & SRT の作業記録（2026-07-17〜07-20、v0.6.0 と v0.7.5〜v0.7.7）
- 混在レートの実 XML は手元に無く、合成した素材で確かめた段階（確度は未確認）
