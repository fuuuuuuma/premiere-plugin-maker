---
id: uc-verify-node-green-device-broken
title: Node のテストもモックも全部緑なのに、UXP の実機では壊れていた
kind: usecase
tags: [検証, UXP, Node, モック, 完了報告, 実機確認, 引き継ぎ]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: Node のテストが全緑でも、「動きます」と言わない。保証できる範囲と実機の最終ゲートを分けて渡し、実機で確かめてほしい項目を番号つきで引き継ぐ。状態の更新は純関数に切り出して固定する
parts: [probe, ui-kit]
related: [core-verification, uc-verify-stub-wrong-shape, uc-verify-test-double-defaults, uc-uxp-ticktime-ticks-zero, uc-ui-select-wheel]
---
## 症状

Node のテスト 19 本が全部通って「修正完了」と報告したが、実機の UXP は起動しなかった。別の件では、Paste が Node では通るのに、実機では貼られなかった。のちに、select がホイールで値を変える問題を Node で固定したと書いたが、実機では無効だった。

## 原因

- Node のモックは、実際の API の戻り値（`.ticks` が 0 になる、select がホイールで値を変えるなど）を再現しない。
- AI のセッションは、Premiere も UDT の読み込み直しも操作できない。

## 直し方

1. 報告を「ここまでは保証する」と「実機では未確認」に分ける。
2. 実機で確かめてほしい項目を、番号つきで引き継ぐ。
3. 状態を更新する処理は純関数に切り出して Node で固定する。Premiere を呼ぶ部分は、スタブで「呼ばれたこと」と「引数」までを保証する。

## 再発防止

- 引き継ぎ書の各節の終わりに、「実機で確認してほしい箇所」を番号つきで残す。
- 完了の報告は、実機のログまたは画面写真を受け取ってから行う。

## 出どころ

- 作者の開発メモと Cut & SRT の引き継ぎ記録（2026-04-29〜07-24）。同じ型の失敗が 3 回あった。
