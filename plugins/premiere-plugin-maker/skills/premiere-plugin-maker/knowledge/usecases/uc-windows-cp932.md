---
id: uc-windows-cp932
title: Windows で日本語が文字化けする・落ちる。あらゆる境界で UTF-8 を指定する
kind: usecase
tags: [Windows, cp932, UTF-8, 文字化け, PowerShell, BOM, subprocess]
os: [windows]
premiere: ">=25.6"
status: partial
summary: Windows の既定の文字コードは cp932。.bat・PowerShell・パイプ・ファイル入出力・常駐プロセスの、どの境界でも UTF-8 を明示する。.bat は ASCII だけにして、日本語は BOM 付きの .ps1 に置く
parts: [packaging, local-server]
related: [platform-windows, uc-windows-mac-only-path, uc-windows-cmd-argv, uc-mac-bash-variable-japanese]
---
## 症状

- .bat や .ps1 の警告文、同梱した部品の入出力で文字化けする。
- 常駐プロセスが絵文字を `print` した時や、ある経路（`/design/run`）で、クラッシュする。
- 5 回以上、場所を変えて再発した（.bat、ps1、常駐の絵文字、Codex の経路、`/design/run`）。

## 原因

- Windows の既定の文字コードは cp932。
- Python の `Popen(text=True)` に `encoding` を指定していないと、cp932 で読み書きする。
- 環境変数 `PYTHONUTF8` が、常駐プロセスに伝わらない。
- PowerShell 5.1 は、BOM（先頭の目印）が無い `.ps1` を CP932 として読む。

## 直し方

1. 全ての `Popen` に `encoding="utf-8", errors="replace"` を付ける。`read_text`/`write_text` も `encoding="utf-8"` を指定する。
2. 常駐の Python は `-X utf8` で起動する。
3. `.bat` は ASCII だけで書く。日本語を出す処理は、UTF-8 の BOM 付き `.ps1` に移す。
4. 本家の別リポジトリへの移植も忘れずに行う。

## 再発防止

- 配布 ZIP の検査で、`.ps1` の BOM（EF BB BF）と、`.bat` が ASCII のみであることを確かめる。
- Mac 上で cp932 を模擬してテストする。Windows 実機での再確認は待ち。

## 出どころ

- Cut & SRT の失敗記録・引き継ぎ記録・作者の開発メモ（v0.1〜v0.12.0、PowerShell 5.1）
