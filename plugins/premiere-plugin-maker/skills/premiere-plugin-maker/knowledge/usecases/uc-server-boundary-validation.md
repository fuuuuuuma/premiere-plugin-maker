---
id: uc-server-boundary-validation
title: 空の数値入力や AI の応答の NaN で設定や候補が壊れる（境界での検査）
kind: usecase
tags: [NaN, null, JSON, 検証, debounce, 設定, エラー応答, LLM]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 画面や AI から来る数値は、送る側と受ける側の両方で検査する。実行時に影響する設定は、実行の要求の本文に明示し、通信のエラーと業務のエラーを混ぜない
parts: [local-server, ppro-kit]
related: [uc-server-lock-order-cancel, uc-server-bridge-contract-drift, uc-fps-silent-default-30]
---
## 症状

- 空の数値入力で、設定が静かに壊れる。
- 設定を変えた直後に実行すると、保存前（500ms の debounce）の古い値で動く。
- AI の応答の `score` が NaN で、候補の窓ごと捨てられる。
- SRT の失敗が、画面に 3 回表示される。

## 原因

- `parseFloat(null)` は `NaN` になり、`JSON.stringify` で `null` に変わり、サーバー側の `json.loads` は NaN を通す。
- 通信の層（`bridgeFetch`）が、ジョブの状態を取る `GET /jobs/<id>` の error の応答を、通信の例外として扱い、`waitForJob` が 3 回取り直した。業務のエラー（ジョブの失敗）を通信エラーと混ぜていた。

## 直し方

1. 数値の設定は、送る前に有限でないものを落とし、サーバーの境界でも検査して、既定値へ戻す。
2. AI の数値は `math.isfinite` で確かめ、不正な候補だけを捨てる（全体は捨てない）。
3. 実行に影響する設定は、実行の要求の本文（body）に、画面の現在の値を明示して送る。
4. ジョブの取得だけは、error の payload を状態の判定まで通す。

## 再発防止

- 回帰テストを置く。トークンの比較を定時間にすること、JSON でない応答を受けたときの保護も、同じ見直しで入れた。
- 画面と AI から来る値は、両端で検査する。業務のエラーと通信のエラーを混ぜない。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-14〜07-23、v0.4.0 より前〜v0.8.0）
