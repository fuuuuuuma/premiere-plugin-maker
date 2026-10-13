---
id: uc-ui-textarea-null
title: 入力欄の値が null で、文字列に "null" が混ざる・NaN が設定を壊す
kind: usecase
tags: [UXP, textarea, input, null, NaN, parseFloat, JSON, 二重防御]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP の textarea や空の入力欄は、value が null のことがある。文字列には空文字を先に入れ、数値は送信前に有限かどうかを見て落とし、サーバー側でも検査する
parts: [ui-kit, local-server]
related: [core-ui-rules, uc-ui-select-wheel, uc-fps-silent-default-30]
---
## 症状

- `textarea` に `+=` で文字を足すと、先頭に "null" という文字が混ざる。
- 空の入力欄を数値にすると `NaN` になり、JSON にすると `null` になって、設定やジョブの引数を壊す。

## 原因

UXP の `textarea` は、初期の `value` が null のことがある。空の入力欄の `value` も null で、`parseFloat(null)` は `NaN` になる。`NaN` は JSON にすると `null` に変わる。

## 直し方

1. 文字列の入力欄は、操作の前に `if (!el.value) el.value = ""` を入れる。
2. 送信の前に、数値でないもの（非有限数）を落とす関数（`dropNonFinite`）を通す。
3. サーバー側でも、型と有限性を検査する（二重の防御）。

## 再発防止

- 境界を越える値は、両側で検査する。
- 空の入力、未設定の入力を、実機で試す。

## 出どころ

- Cut & SRT の失敗記録と実装の記録（実機で確認）
