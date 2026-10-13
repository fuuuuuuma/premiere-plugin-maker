---
id: uc-windows-daemon-process-paths
title: Windows では常駐・プロセスの停止・通知・パスの扱いが Mac と違う
kind: usecase
tags: [Windows, 常駐, pythonw, taskkill, 通知, パス, EncodedCommand, file URL]
os: [windows]
premiere: ">=25.6"
status: unverified
summary: pythonw で動く常駐はログが残らないので、ログの出力先を自前で付け替える。子プロセスはグループ生成フラグと taskkill で止め、パスはサーバーから受け取る
parts: [local-server, logger]
related: [platform-windows, uc-windows-port-local-server, uc-windows-cp932]
---
## 違いの一覧

| 項目 | Mac で使ったもの | Windows での置き換え |
|---|---|---|
| 子プロセスの独立 | `start_new_session=True` | `CREATE_NEW_PROCESS_GROUP \| CREATE_NO_WINDOW`（`popen_group_kwargs()` にまとめる） |
| プロセス群の停止 | グループへの kill | `taskkill /T` の次に `/F` |
| 通知 | osascript | NotifyIcon（PowerShell） |
| PowerShell へ渡す命令 | そのまま | `-EncodedCommand`（UTF-16LE） |
| 常駐のログ | ターミナルかログファイル | `pythonw` は出力が残らないので、`%LOCALAPPDATA%\<名前>\Logs` に自前でリダイレクト |
| 一時フォルダ | `/tmp` | サーバーが `ready` で渡す `tmpDir` を、パネルが使う |
| ファイルの URL | `file://` で始まる Mac のパス | `file:///C:/...` |

## 症状

`start_new_session=True`、プロセスグループへの kill、osascript による通知が、Windows では使えない。`pythonw` で動かした常駐は、ログが残らず、失敗の原因が分からない。

## 原因

OS の違い（プロセスグループ・通知・コンソールの有無・パスの表記）。

## 再発防止

- Mac 上から、OS を判定する属性を差し替えて、Windows の分岐をテストする。
- Premiere の API が、区切り文字の混ざったパスを受け付けるかは、未検証。Windows 実機の確認もまだ。
- 常駐の Python のログ先は自前で付け替える。子プロセスはグループ生成のフラグと taskkill で止める。パスはサーバーから受け取る。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-17、v0.4.0 以前の移植）
