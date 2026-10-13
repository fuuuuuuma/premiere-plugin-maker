---
id: uc-verify-claimed-proven-api-missing
title: 「実証済み」と書いた API が、公式にも利用者の実機にも無かった
kind: usecase
tags: [検証, API, 実証済み, 存在確認, typeof, UI の出し分け]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 「実証済み」と書くなら、環境と試した内容を併記する。公式の文書に無い API は実機にも無い前提で、使えない環境では機能を無効にして理由を出す
parts: [ppro-kit, probe]
related: [core-api-patterns, uc-uxp-api-doc-vs-device, uc-uxp-sequence-inout-missing, uc-uxp-host-version-too-old]
---
## 症状

「実証済み」としていた `setInPoint`・`setOutPoint`・`createSubsequence` を使って、サブシーケンス化のスイッチを作った。ところが利用者の実機では、`setInPoint` と `setOutPoint` が存在しなかった。

## 原因

`Sequence.setInPoint` / `setOutPoint` は公式のリファレンスに載っていない。「実証済み」の根拠（どの環境で何を試したか）も、記録に残っていなかった。

## 直し方

1. 3 つの API の存在を `typeof` で調べる関数を作り、1 つでも無ければスイッチを OFF かつ無効にして、「この環境では利用できません（UXP 未対応）」と出す。
2. 範囲を設定する別の経路（`createSetInPointAction` / `createSetOutPointAction`）が使えるかは、別に確かめる。

## 再発防止

- 「実証済み」と書く API には、確かめた環境（Premiere の版・OS）と試した内容を併記する。
- 公式の文書に無い API は、実機にも無い前提で、画面の出し分けを先に作る。
- サブシーケンス化の後に、アクティブなシーケンスが切り替わるかは実機で未確認のまま、記録に残す。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-23。v0.8.0 の記述が v0.9.1 で覆った）。欠落は利用者の実機と公式の文書で確認した。
