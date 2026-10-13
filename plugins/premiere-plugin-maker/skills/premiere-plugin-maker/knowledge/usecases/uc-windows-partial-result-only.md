---
id: uc-windows-partial-result-only
title: Windows でだけ、結果が後半しか取れない（Mac で再現せず・未解決）
kind: usecase
tags: [Windows, 再現しない, 未解決, 文字起こし, faster-whisper, 切り分け]
os: [windows]
premiere: ">=25.6"
status: unverified
summary: カット後のシーケンスの文字起こしの結果が、Windows の利用者だけ、後半の分しか取れないと報告された。Mac では再現せず、原因は未確定。片方の OS で再現しないときは、実データで段階的に絞り、相手の環境のログを依頼する
parts: [transcribe-srt]
related: [platform-windows, uc-windows-cuda-dll, uc-windows-cp932, uc-install-support-pack]
---
## 症状

テスターから、カットしたあとのシーケンスの字幕が、後半しか取れないと報告された。Windows のみ。

## 原因

未確定。実際のカット後の XML と実際の素材で再構成しても、Mac の mlx-whisper は全 8 区間を取れた。Windows の faster-whisper に固有の問題かは、分からない。

## 直し方

未解決。次に必要なものは次のとおり。

1. テスターの字幕の出力。
2. Windows の文字起こしのログ。
3. その版（v0.7.7）で、フレームレートを 30fps に一貫させた後に、同じ操作を再実行した結果。

## 再発防止

- 片方の OS で再現しないときは、実データを使って段階ごとに検証し、範囲を絞る。
- 相手の環境のログを依頼する。このためにも、診断を一括で保存する仕組みが要る（サポートパックの項を参照）。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-20、v0.7.7、Windows）
