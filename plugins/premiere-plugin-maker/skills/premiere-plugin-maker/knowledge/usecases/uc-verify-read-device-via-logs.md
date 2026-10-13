---
id: uc-verify-read-device-via-logs
title: 実機の挙動が分からない。画面の操作でなく、ログ・保存領域・CDP で読む
kind: usecase
tags: [検証, 実機, UXPLogs, LocalStorage, CDP, ログ, 画面操作]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 接頭辞つきの診断ログを最初から入れ、実機の様子は UXP のログ・保存領域・CDP で読む。画面の操作は最終手段にして、使うときは座標をクリックする前に毎回スクリーンショットを撮る
parts: [logger, probe]
related: [core-verification, uc-verify-diagnose-before-evidence, uc-cep-node-exec-callback]
---
## 症状

「直っていない」と言われても、実機で何が動いたのか分からない。画面の操作で確かめようとすると、見えないオーバーレイにクリックを奪われたり、「読み込み直し（Reload）」のつもりが「取り外し（Unload）」に当たったりした。

## 原因

画面とフォーカスは利用者と共有の資源である。座標でのクリックはレイアウトの変更に弱く、最初のクリックはフォーカスの取得に使われてしまう。

## 直し方

1. コードに `console.log("[bootstrap] ...")` のように接頭辞をつけたログを入れる。UXP のログは `~/Library/Logs/Adobe/Adobe Premiere Pro 2026/UXPLogs_<起動日時>.log`（Mac）に出る。`grep -h "bootstrap\|select-guard"` で、防御の層と間欠の故障を切り分ける。
2. 保存したデータは `~/Library/Application Support/Adobe/UXP/PluginsStorage/PPRO/26/Developer/<プラグイン ID>/LocalStorage` を `strings` で読む。
3. CEP のパネルは、`.debug` ファイルに書いたポート（例: 8951）から CDP（Chrome DevTools Protocol）で読む。

## 再発防止

- 画面の操作が要るときは、座標をクリックする前に毎回スクリーンショットを撮る。
- 実機の検証は、専用のプロジェクトの V2 以上のトラックだけを使い、保存せずに片付ける。

## 出どころ

- 作者の開発メモと Cut & SRT / Effect & Design の記録（2026-07-16〜09-18、Premiere 26.x の UXP と CEP、Mac）。実機で確かめた。
