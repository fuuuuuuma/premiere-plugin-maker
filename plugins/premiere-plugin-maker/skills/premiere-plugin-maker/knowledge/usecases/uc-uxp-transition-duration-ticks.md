---
id: uc-uxp-transition-duration-ticks
title: トランジションの長さがずれる
kind: usecase
tags: [UXP, トランジション, 長さ, ティック, コマ, TransitionFactory]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 長さを秒で渡すとコマに切り捨てられる。コマ数 × 1 コマのティックで渡し、内部名は実機から読んで対応を取る
parts: [ppro-kit]
related: [core-api-patterns, ref-ticktime, uc-uxp-keyframe-extra-and-wrapped]
---
## 症状

トランジションの長さを 0.5 秒で渡したら、14 コマ（29.97fps で約 0.47 秒）に短くなった。

## 原因

長さを秒で渡すと、コマの単位に切り捨てられる。29.97fps では 0.5 秒が 14.985 コマになり、小数が落ちる（切り捨てだと考えられる）。

## 直し方

1. トランジションは `TransitionFactory.createVideoTransition(内部名)` で作り、`clip.createAddVideoTransitionAction(t, AddTransitionOptions)` で足す。
2. 長さは、秒でなく「コマ数 × 1 コマのティック」で渡す。1 コマのティックは、シーケンスのフレームレートから求める（ref-ticktime）。
3. 内部名は表示名と違う。ExtendScript で一度付けてみて、DOM が持つ matchName を読み、対応表を作る。
4. 入れたあとに、実際の長さを読んで確かめる。

## 再発防止

- 時間は秒でなくティックで渡すと決め、変換を 1 か所の関数にまとめる。
- 標準搭載のトランジションは、matchName までしか読めず、設定項目（components）は null で変えられない。効き方を変えたいときは、別の効果で動きを作る（uc-uxp-qe-transition-settings）。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09-18）
- 「切り捨て」の理由の説明は推測
