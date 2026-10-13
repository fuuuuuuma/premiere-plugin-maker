---
id: uc-cep-node-exec-callback
title: CEP で外部コマンドを呼んでも、返事のコールバックが永久に来ない
kind: usecase
tags: [CEP, Node, child_process, exec, execFile, execFileSync, コールバック]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: CEP の Node 環境では、child_process の exec / execFile の非同期のコールバックが呼ばれないことがある。execFileSync を、setTimeout(…, 0) で一拍置いて呼ぶ
parts: [cep-helper]
related: [ref-cep-extendscript, uc-cep-umd-window, uc-cep-es3-json]
---
## 症状

Node の単体テストは全部通るのに、実機の CEP パネルでは、外部コマンドの返事が来ない。「読み込んでいます…」の表示のまま止まる。

## 原因

CEP の Node 環境で、`cep_node.require("child_process")` の `exec` / `execFile` は、非同期のコールバックが永久に呼ばれない。Node 単体のテストでは、この問題が再現しない。

## 直し方

1. 外部プロセスは、同期版の `execFileSync` で呼ぶ。
2. 画面の描画を止めないよう、`setTimeout(…, 0)` で一拍置いてから呼ぶ。
3. CEP から見える `python3` は、`/usr/bin/python3`（3.9）。呼ぶコマンドは、絶対パスで指定する。

## 再発防止

- 実機の状態は、CDP（デバッグ用のポート → `curl localhost:PORT/json` → WebSocket の `Runtime.evaluate`）で読む。
- `location.reload()` では新しい JS が載らないことがある。CDP の `Network.setCacheDisabled` と `Page.reload(ignoreCache)` で入れ替える。
- CEP は、Node と古い Chromium の混在環境で、単体テストが通っても実機でだけ止まる。

## 出どころ

- Effect & Design の受け入れ記録と作者の実測メモ（2026-09-17〜09-21、Premiere 26.5・CEP）
