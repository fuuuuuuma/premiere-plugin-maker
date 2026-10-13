---
id: uc-mogrt-otio-track-pick
title: 辞書の差分学習で、テロップの本文をどのトラックから読むか決まらない
kind: usecase
tags: [OTIO, テロップ, 辞書, 差分学習, トラック, 行数, 一時ファイル]
os: [mac, windows]
premiere: ">=26.3"
status: verified
summary: OTIO のテロップ本文を動画トラックごとに抽出し、直前の SRT の本文の行数に最も近いトラックを採る。比べる行数は表示用の字幕数と分けて持ち、一時ファイルは両側で消す
parts: [ppro-kit, fcpxml]
related: [uc-mogrt-source-text-unreadable, uc-mogrt-binary-rule-without-data, feat-cutsrt-dictionary]
---
## 症状

テロップの本文を直接読めないので、SRT との差分から辞書を学ぶことができなかった。

## 原因

Source Text が複合型で、API で読めないため（`uc-mogrt-source-text-unreadable`）。OTIO で読めるようにしても、どのトラックが「今回のテロップ」かは、自動では決まらない。

## 直し方

1. OTIO をサーバーの学習の入口（`POST /dictionary/learn`）に渡す。
2. `extract_telop_texts` が動画トラックごとの行数を返し、直前の SRT に最も行数が近いトラックを採る。
3. Premiere 26.3 の実機で、V2 を OTIO 経由で読み、「学習完了: ビデオ2 / 差分1箇所」と出ることと、一時の OTIO が残らないことを確認した。

## 再発防止

- 比べる行数（`expectedCount`）は、最終的な SRT の本文の行数にする。1 件が 2 行になる字幕があるので、表示用の字幕数とは別に持つ。
- 一時の `.otio` は、書き出した側と受け取った側の両方の `finally` で消す。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-14、Premiere Pro 26.3.0、UXP）。この事例は辞書の機能に固有で、ほかのプラグインでは参考程度
