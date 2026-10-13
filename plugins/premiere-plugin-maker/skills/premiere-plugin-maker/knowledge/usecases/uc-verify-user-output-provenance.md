---
id: uc-verify-user-output-provenance
title: 利用者が出した「カット後の XML」の出どころを確かめずに分析しそうになった
kind: usecase
tags: [検証, 出自, XML, 診断, 入力の保持, sequence id]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 持ち込まれたツールの出力は、出自を確かめてから分析する。調査に要る入力は、成功しても失敗しても消さず、オプトインで残せるようにする
parts: [silence-cut, logger]
related: [uc-verify-reproduce-with-real-data, uc-xml-invalid-input-fail-closed, uc-verify-diagnose-before-evidence]
---
## 症状

利用者が出した「カット後」の XML は、`<sourcetrack><trackindex>` が入力と入れ替わっていた。ところが、同じ入力と実素材で現行版と旧版を動かすと、入れ替わらない。しかも入力の XML が消えていて、比較できなかった。

## 原因

- 提出物は `<sequence id>` と `<uuid>` が入力と別で、`_1` を付けた名前も既定の名前と合わなかった。Premiere が再び書き出したものである可能性が最も高い（断定はできない）。
- 入力の XML は、サーバーが成否に関わらず削除していた。

## 直し方

環境変数 `CUTSRT_KEEP_DIAGNOSTIC_XML=1` で、入力の XML を残すオプトインの保持を足す。既定はオフ、置き場所は一時フォルダ、7 日で掃除する。

## 再発防止

- 提出物は、シーケンスの id / uuid とファイル名で出自を確かめてから分析する。
- 調査に必要な入力は、失敗したときこそ残す。ただし利用者の素材を勝手に溜めないよう、既定はオフにする。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-27、v0.9.13）。機械検証のみ。
