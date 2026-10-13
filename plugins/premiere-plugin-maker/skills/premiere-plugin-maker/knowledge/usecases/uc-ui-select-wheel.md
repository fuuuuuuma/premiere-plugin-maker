---
id: uc-ui-select-wheel
title: select の上でホイールを回すと、値が勝手に変わる
kind: usecase
tags: [UXP, select, wheel, 設定, 巻き戻し, 入力]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP の select は、上でホイールを回すと値が変わる。ホイールの抑止、直近のホイールで起きた変更の巻き戻し、1 秒周期の突き合わせの 3 層で守る
parts: [ui-kit]
related: [core-ui-rules, uc-ui-textarea-null, core-verification]
---
## 症状

パネルをスクロールしようとしてホイールを回すと、通りすがりの `select`（選択式の入力）の値が、利用者の意図なしに変わる。設定が知らないうちに書き換わる。

## 原因

UXP の `select` は、カーソルが上に乗っている状態でホイールを回すと、選択肢が切り替わる。

「ホイールを抑止した」と Node のテストで固定済みと書いた後に、実機で効いていなかったと分かった。Node のモックは、`select` がホイールで値を変える挙動を再現しない。

## 直し方

3 層で守る。

1. `wheel` イベントを抑止する。
2. 直近の `wheel` で起きた `change` を、元の値へ巻き戻す。
3. 1 秒周期で、保持している値と画面の値を突き合わせる。

## 再発防止

- 実機のログ（UXPLogs）で確かめる。Node のテストが通っても、実機の最終確認は別に行う。
- 設定の値は、画面の値でなく、保持している値を正にして、定期的に突き合わせる。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-24、UXPLogs で確認）
