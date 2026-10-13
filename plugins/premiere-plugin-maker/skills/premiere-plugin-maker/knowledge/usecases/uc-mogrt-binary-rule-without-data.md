---
id: uc-mogrt-binary-rule-without-data
title: 非公開バイナリの読み取り規則を実物なしで変えて、アニメ付きテロップで 0 件になった
kind: usecase
tags: [OTIO, BinaryData, Source Text, バイリンガル, フィクスチャ, 抽出規則, 診断]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: 非公開バイナリを読む規則は、実データを 1 件でも手元に落としてから書き換える。本文は位置でなく内容で決め、決まらなければ止める。診断用の保存の道具を先に用意する
parts: [ppro-kit, fcpxml]
related: [uc-mogrt-source-text-unreadable, uc-mogrt-localized-name-lookup, uc-mogrt-otio-track-pick]
---
## 症状

辞書の差分学習が、OTIO からテロップの本文を取り出す処理で、バイリンガル表示（2 言語の字幕）で 0 件になった。その修正のあとも、アニメーション付きのテロップで、発覚する 3 週間後まで 0 件のままだった。

## 原因

実際のデータが無いまま、試験用のデータ（フィクスチャ）だけを根拠に、規則を 2 つ変えた。

- パラメータの特定を、表示名の完全一致から、構造上の位置に変えた。
- 本文の特定を、「最も長いバイト列」から「先頭に最も近いアンカー」に変えた。

その結果、アニメ付きテロップでは、本文より前にある `AnimationType` を本文と取り違えた。

## 直し方

1. 本文は内容で決める。日本語を含むものが最優先、次に空白や句読点を持つもの。ASCII 1 語だけのものは除外する。
2. パラメータは構造上の位置で特定し、一意に決まらなければ `OtioTextExtractError` で止める（fail-closed）。

## 再発防止

- 診断用の道具を、先に用意する。`CUTSRT_KEEP_DIAGNOSTIC_OTIO=1`（.otio を残す）と、`CUTSRT_DUMP_AMBIGUOUS_BLOB=1`（決まらなかった BinaryData を保存する）。
- 非公開のバイナリを読む規則は、実データを 1 件でも手元に落としてから書き換える。
- 未確認: バイリンガル表示での抽出成否は、実機で確かめていない。アニメ付きテロップで 0 件になる問題と、内容で決める修正は実機で確認した。

## 出典

- Cut & SRT の記録（2026-07-26 に規則を導入、2026-08-16 に発覚。v0.9.11）
