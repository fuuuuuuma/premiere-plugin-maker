---
id: uc-server-lock-order-cancel
title: 同時に走ってしまう・キャンセルが失敗の通知になる（ロックと終了状態の順序）
kind: usecase
tags: [ロック, キャンセル, 非同期, await, プロセス停止, PID, 状態]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 排他ロックは await の前に取り、終了の状態は後処理が済んでから 1 回だけ公開する。プロセスの停止は、PID だけでなく identity（起動時刻など）で照合し、キャンセルとエラーは画面まで区別する
parts: [local-server, ppro-kit]
related: [uc-server-atomic-output, uc-server-boundary-validation, core-transactions]
---
## 症状

- 辞書の学習が、単一実行のロックの外で、並行して走れてしまう。
- 翻訳のダイアログを表示している間に、ほかのジョブが始まった。キャンセルの `finally` が、他のジョブのロックを解除してしまった。
- キャンセルが「失敗」の通知として表示された。

## 原因

- ロックが、Converter API を呼ぶ操作の全部を覆っておらず、取得するのも `await` のあとだった。
- 終了の状態を、後処理より先に公開していた。
- PID だけを書いた印（marker）では、PID が再利用されたときに、別のプロセスを止めてしまう恐れがあった。

## 直し方

1. Converter API を呼ぶ操作は、すべて `setRunning` で排他する。ロックの取得は、ダイアログを出す前にする。
2. `finally` では、一時ファイルの掃除だけを行う。終了の状態は、後処理が済んでから 1 回だけ公開する。
3. marker に、起動時の boot ID・開始時刻・command・PGID を保存し、同じ identity のものだけに TERM → KILL を送る。
4. パネル側は、`cancelled` と `error` を別の状態として扱う。
5. 辞書の学習の前に、SRT を生成したときのシーケンスの識別子と照合し、不一致なら止める。

## 再発防止

- ロックの順序を、静的なテストで確かめる。
- 排他は await の前、停止は identity の照合、キャンセルとエラーは UI まで区別する、の 3 つを決まりにする。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-14〜07-23、v0.7〜v0.8.0）。機械検証まで
