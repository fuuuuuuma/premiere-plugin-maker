---
id: uc-uxp-require-relative
title: 分けた JS が読み込めない
kind: usecase
tags: [UXP, require, モジュール, 相対パス, script, 起動, try-catch]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: UXP では require の相対パスが解決できない。単一ファイルにまとめるか、script タグの読み込み順を実機で確かめる。初期化は try-catch で守り、起動ログを出す
parts: [ui-kit, logger]
related: [core-ui-rules, uc-uxp-init-tdz, core-verification]
---
## 症状

純粋な関数を別のファイルに切り出し、Node の単体試験が全部通ったのに、Premiere の実機ではパネルが完全に動かなくなった。別の版では、ボタンもログの切り替えも反応しないパネルが報告された。

## 原因

1. UXP では `require("uxp")` と `require("premierepro")` は組み込みとして通るが、`require("./align-logic")` のような相対パスは解決できない。`<script src="外部.js">` で読む方法も、読み込み順の問題が起きやすい。
2. パネルの準備をする関数（setupPanel）の中のどこかで例外が飛ぶと、それ以降のリスナーの登録が全部実行されず、何も反応しなくなる。

## 直し方

1. 切り出した関数を、本体のファイルの中に書き戻す（インライン化）。または、複数の `<script src>` で読む場合は、読み込み順を実機で確かめる。
2. 準備の関数全体を try-catch で包む。あとから何かを足すときも、必ず try-catch の中に書き、例外はログに残す。
3. 起動したことをログに出す（「v1.0.4 起動」のような行）。

## 再発防止

- 「Node の試験が全部緑」は「実機で動く」の証拠にならない。実機で起動ログを見る。
- `check.py` の J006 が、相対パスの `require` を止める。
- 複数の script を静的に読む設計にするときは、どの経路で読めたかをログで判別できるようにして、実機で確定させる（確定は未実施）。

## 出どころ

- Caption Align（小型プラグイン）の失敗記録（v1.0.2〜v1.0.4、2026-04-29）
- Cut & SRT の引き継ぎ書（複数の script を使う設計の注記）
