---
id: uc-fps-override-not-in-file-rate
title: FPS を上書きした素材が、カット後に元の fps へ戻って音ずれする
kind: usecase
tags: [fps, Interpret Footage, FCP7 XML, file, rate, 音ずれ, 29.97]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 素材のフレームレートを上書きしても、FCP XML の素材側 file の rate には載らない。クリップ側 rate と file 側 rate が食い違うときは揃えるが、変更前のレートが取れたときだけ注意を出す
parts: [fcpxml, silence-cut]
related: [uc-fps-mixed-ticks-basis, uc-fps-vfr-timebase, ref-fcp7-xml]
---
## 症状

29.97fps の素材を、`createSetOverrideFrameRateAction`（Interpret Footage 相当の「フレームレートの上書き」）で 30.00 に上書きしてから無音カットすると、カットしたシーケンスで素材が 29.97 に戻り、映像と音声が少しずつずれていく。

## 原因

FCP XML の書き出しは、上書きを `<clipitem><rate>`（配置の側）には反映するが、素材側の `<file>` の中の 3 か所の `<rate>` は元の 29.97 のままだった。Premiere から直接書き出した XML でも同じ。実機の XML で調べると、680 クリップ中 679 件でこの食い違いがあった。

最初の調査は、配置の軸（`start`・`end`、シーケンスの 30fps の格子）だけを見て「ずれなし」と結論していた。素材を参照する軸を見ていなかった（誤診）。

## 直し方

1. 全クリップの rate が 1 種類で、かつ `out - in == end - start` のときだけ、`<file>` 側の rate をクリップ側に揃える（`conform_file_rate_to_clipitem_rate()`）。
2. この機能自体は残す。ただし、`getFootageInterpretation().getFrameRate()` で変更前のレートが取れたときだけ、変化率と影響する秒数を、注意としてログに出す。
3. 使った fps は毎回ログに出す（`rateLabel`）。

## 再発防止

- 「ずれなし」と言う前に、配置の軸と素材の参照の軸を、両方検証する。
- 揃える処理は条件を厳しくして、確信が持てない XML には手を出さない。
- 進行性のずれの機序は、音声側に rate が無く、`in/out` の音声位置の換算が誤った 29.970 を使うためだと考えられる（推測、未検証）。

## 出典

- Cut & SRT の作業記録（2026-07-27、v0.9.16〜v0.9.18）
- 実際の XML を全件解析した（機械検証）。実機での再確認は未実施
