---
id: platform-cross
title: Mac と Windows の両方で動かす書き方
kind: platform
tags: [Mac, Windows, パス, 文字コード, 改行, NFC, NFD, cp932, 実行ビット, check.py, W規則, 日本語]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: パスは環境変数と相対で、文字コードは明示、OS の分岐は 1 か所に。Mac 専用の場所だけを探して Windows で失敗した事故と check.py の W 規則
related: [platform-mac, platform-windows]
---
## 違いの表

両方の OS で動かすための書き方の対応表です。

| 項目 | Mac で起きること | Windows で起きること | 書き方 | 確度 |
|---|---|---|---|---|
| 設定・データの置き場 | `~/Library/Application Support/<アプリ名>` | `%APPDATA%\<アプリ名>` | 置き場の決め方を 1 つの関数にまとめ、環境変数（`HOME`・`APPDATA`・`LOCALAPPDATA`）から作る。ログも同じ（`~/Library/Logs/...` と `%LOCALAPPDATA%\...\Logs`） | キットの部品で両 OS 用に実装。Windows は実機未確認の部分あり |
| 文字コード | 既定は UTF-8 | Python 3.14 以前は cp932 | `open(..., encoding="utf-8")`、`subprocess.run(..., text=True, encoding="utf-8", errors="replace")` を必ず書く | Windows の利用者の PC で事故を確認（5 回以上） |
| 改行 | LF | CRLF のことがある | 読むときは両方を受け入れる。ハッシュの一覧のような機械で照合するファイルは LF に決める | 案件の記録 |
| パスの区切り | `/` | `\` | 文字列をつなげず `pathlib`（Python）か `path.join`（JS）。URL にするときは Windows を `file:///C:/...` の形にする | 案件の記録 |
| 空白・日本語のパス | `Application Support`、日本語のフォルダ | `Program Files`、日本語のユーザー名 | コマンドに渡すときは引数を配列で渡す（文字列を連結してシェルに渡さない）。表示用の文にも引用符を付ける | 案件の記録 |
| 日本語の正規化 | Finder の展開で NFD になることがある | 通常 NFC | パスを鍵にする前、一覧どうしを比べる前に NFC にそろえる | Mac で事故を確認 |
| 実行ビット | `chmod +x` が必要。zip 経由では失われがち | 概念が無い | 実行ビットに頼らず、`python3 script.py` や `bash script.sh` と明示して呼ぶ | 案件の記録 |
| 起動の入口 | `.command`（ダブルクリックは Gatekeeper で止まることがある） | `.bat` → `.ps1` | Mac は `bash` ＋ドラッグの案内。Windows は ASCII だけの .bat で .ps1 を呼ぶ | 案件の記録（Windows は導入まで確認） |
| 常駐 | launchd | タスク スケジューラ | 起動・停止・再起動の操作を OS ごとの小さな関数に分け、呼ぶ側は OS を知らない | Mac は実機。Windows は起動まで確認、自動起動は未確認 |
| 外部コマンドの探索 | Homebrew の場所、`/usr/bin/python3` | winget のリンク、`py -3.13` | 候補の場所を順に試し、**実際に起動して確かめてから使う**（名前があるだけでは使えない） | 実機で確認 |

## 気を付けること

- **OS の分岐は 1 か所に**：`if sys.platform == ...` をあちこちに書かず、場所を決める関数（置き場・ログ・探索の候補）に集めます。ほかの所はその関数を呼ぶだけにします。
- **Mac 専用の場所だけを探さない**：Effect & Design（Mac だけの拡張）から写したエンジンは `/Applications/...` だけを探しており、Windows では必ず失敗しました。Windows 向けに配る前に、`/Applications`・`~/Library` と `text=True` だけの `subprocess` を探します。Windows では `%ProgramFiles%` と `%ProgramW6432%` の両方、`%APPDATA%` も探します。
- **文字コードは常に明示**：Windows の事故は「Mac では動いていたコード」で起きました。Python の版が 3.15 になって UTF-8 が既定になっても、明示は残します。Mac 上でも cp932 を真似て再現できるので、テストに入れておきます。
- **bash 3.2 の罠（Mac）**：`.command` や `.sh` で `$変数` の直後に日本語が続くと、Mac の古い bash が日本語の一部を変数名と読んで、`set -u` で止まります（新しく入れた人のほぼ全員が踏みました）。必ず `${変数}` と書きます。
- **正規表現や日本語の判定**：日本語の否定表現（「〜くない」と、裸の「ない」が「切ない」「危ない」に当たる誤爆）は、文脈で判断します。文字列検索だけで済ませません。
- **相手の OS で確かめるまで「動く」と言わない**：片方の OS で動いたことは、もう片方で動く証拠になりません。実機で確かめていない所は、利用者向けの案内にも「未確認」と書きます。
- **版数を上げる基準**：Mac と Windows の両方に関わる変更のときだけ版を上げます。片方だけの細かい修正は、同じ版のまま配布物を作り直します（ただし同じ版では入れ直しても更新されないので、入れ直しの手順を添えます。core-versioning-release を見てください）。

## check.py の W 規則

`check.py` は、次のような Windows で壊れる書き方を見つけます。

| 規則 | 見つけるもの |
|---|---|
| W001 | 日本語を含む .ps1 に BOM が無い |
| W002 | .bat / .cmd に英数字以外が入っている |
| W003 | `subprocess` の `text=True` なのに `encoding` が無い／テキストの `open` に `encoding` が無い |
| W004 | `/Applications` など Mac 専用の場所だけを書いている（OS の分岐が無い） |
| W005 | `.command` / `.sh` で `$変数` の直後に日本語が続く |
| Y001 | Python の構文の誤り |

## 出どころ

- Cut & SRT の失敗記録：cp932 の事故（2026-07〜09）、Mac 専用の場所を写して Windows で失敗した事故（v0.12.0、2026-09-27）、bash 3.2 の変数名の誤認（インストーラ）
- 作者の記憶に残した日本語の扱いの罠（NFC/NFD、日本語パスと git のエスケープ、否定表現の検索）
- Windows 側の事実確認の調査資料（2026-10-13）
