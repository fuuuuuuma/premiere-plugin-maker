---
id: uc-windows-port-local-server
title: Mac 専用のローカルサーバー型プラグインを Windows に移すとき、OS 固有の 7 点を分ける
kind: usecase
tags: [Windows, 移植, ローカルサーバー, SendInput, タスクスケジューラ, 同梱, スモークテスト]
os: [windows]
premiere: ">=25.6"
status: unverified
summary: 入力の送出・メニュー操作・ファイル検索・常駐・黒い窓・ログ・文字コードを OS ごとに分け、Python と ffmpeg を同梱して導入作業をなくす。配布前に、動作を段階的に確かめる
parts: [silence-cut, local-server]
related: [platform-windows, uc-windows-daemon-process-paths, uc-windows-cp932]
---
## 症状

launchd 前提の Mac 専用で作られたローカルサーバー型プラグイン（無音カット）を Windows に移すと、初回の導入で、接続できない・メニュー操作が効かない・リップル削除が効かない・文字化けする、が想定された。

## 原因

launchd・AppleScript・Quartz・Spotlight への依存。作者は Mac だけで、実機で試せていない。

## 直し方

OS 固有の部分を、7 点に分けて入れ替える。

1. 入口で `platform_compat.py` が、`platform_mac.py` と `platform_win.py` に振り分ける。
2. キー・マウス入力の送出は、ctypes の `SendInput`。
3. メニューの操作は、PowerShell の UI Automation。
4. ファイル検索は `os.walk`（Spotlight の代わり）。
5. 常駐はタスク スケジューラ。黒い窓を出さないため、wscript と vbs で起動する。
6. ffmpeg と、導入不要の Python（embeddable）を同梱して、導入作業をなくす。
7. 文字化けは `chcp 65001` で防ぐ。

## 再発防止

- 配布前に、状態確認（`status="ok"`、`problems=[]`）→ カーソル位置の取得 → 検出のみ → リップル削除、の順に試し、失敗したら配布を止める。
- 日本語版のメニュー名は、`(F)` のようなショートカット表記が除かれるが、全角の `（F）` は別扱いになる。

## 出どころ

- Silence Cut の引き継ぎ記録（2026-05-03、Windows / Premiere Pro Beta。実機未テスト）
