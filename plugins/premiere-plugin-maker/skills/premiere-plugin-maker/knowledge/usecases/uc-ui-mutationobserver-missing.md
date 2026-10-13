---
id: uc-ui-mutationobserver-missing
title: UXP に MutationObserver が無く、起動の処理が止まって設定も一覧も読み込まれない
kind: usecase
tags: [UXP, MutationObserver, ReferenceError, 下見, 機能検出, 起動]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP には MutationObserver が無い。使う前に typeof で調べ、無ければ定期的な監視に切り替える。ブラウザでの下見が通しても、UXP に無い機能を削って確かめる
parts: [ui-kit]
related: [core-ui-rules, uc-uxp-init-tdz, uc-uxp-webview-not-browser]
---
## 症状

起動の処理（setup）が `ReferenceError` で止まり、設定の読み込みも、一覧の更新も行われなかった。ブラウザ（Chromium）での下見では、問題なく動いていた。

## 原因

UXP に `MutationObserver` が無い。ブラウザでの下見は、この欠落を再現できず、すり抜けた。

## 直し方

1. `typeof MutationObserver === "function"` で使えるかを調べ、使えなければ、1 秒ごとに class の変化を監視する処理に切り替える。
2. 新しい Web の機能を使うときは、UXP で使えるかを、毎回確かめる。

## 再発防止

- 下見のツールで、UXP に無い機能（`MutationObserver`）を意図的に削除してから描く。
- 同じ下見のツールに、UXP の flex の条件（`*{min-width:0;min-height:0}`）も入れる。
- 下見が通っても、実機のログを確かめる。

## 出どころ

- Cut & SRT の実機のログと下見ツールの記録（2026-09-24）
