---
id: uc-uxp-sequence-inout-missing
title: 範囲を指定したサブシーケンスが作れない（setInPoint が実機に無い）
kind: usecase
tags: [UXP, Sequence, setInPoint, setOutPoint, サブシーケンス, XML, 無効化]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: Sequence.setInPoint / setOutPoint は実機に無かった。理由つきで機能を無効にし、最終的にはサーバーで作った XML を読み込んで新しいシーケンスにした
parts: [ppro-kit, fcpxml]
related: [uc-uxp-api-doc-vs-device, ref-fcp7-xml, core-capabilities]
---
## 症状

利用者の実機で、範囲を指定して新しいシーケンス（サブシーケンス）を作る機能が動かなかった。`Sequence.setInPoint` と `setOutPoint` が欠けていた。マーカーの色分けも反映されなかった。

## 原因

公式の文書に `Sequence.setInPoint / setOutPoint` が無い（クリップ側の `createSetIn/OutPointAction` はある）。範囲を指定したサブシーケンスは、この API が無いと成り立たない。`createSubsequence` と、マーカーの色を付ける `Marker.createSetColorByIndexAction` は、名前も引数も正しかった。

なお、別の記録では `Sequence.createSetInPointAction` は動くと書かれている。API の名前が違う（Action を作る形）ためだと思われる。

## 直し方

1. 対応しているかを 3 つの API の `typeof` で判定する関数を作る。対応していなければ、機能の切り替えを OFF にして押せなくし、「この環境では利用できません（UXP 未対応）」と理由を表示する（消すと混乱するので、存在は見せる）。
2. その後、この機能のスイッチ自体をやめた。サーバーが候補の区間を並べた FCP の XML を作り、パネルがそれを読み込んで新しいシーケンスとして開く方式に置き換えた。
3. 見送った案: トラック単位で組む API が無い、複製して不要な区間を削除するとリップルの事故が起きる、という理由。

## 再発防止

- 実機に無い API は、隠さず理由つきで無効にする。`typeof` のガードを最後の砦にする。
- API が無い機能は、XML を生成して読み込む形で作れるか考える。

## 出どころ

- Cut & SRT の引き継ぎ書（2026-07-23〜07-25、v0.9.1 → v0.9.4）
- 欠落は利用者の実機と公式の文書で確認した。XML への置き換えは実機で確かめていない
