---
id: uc-windows-powershell-traps
title: PowerShell スクリプトが、環境変数の未設定や 1 行の出力で落ちる
kind: usecase
tags: [PowerShell, Windows, null, 配列, Parser, 構文検査, grep]
os: [windows]
premiere: ">=25.6"
status: partial
summary: 別の OS のスクリプトは、grep でなく構文解析で検査し、実行まで確かめる。Bash からの移植では、配列と単独の値の暗黙の変換を疑う
parts: [packaging]
related: [platform-windows, uc-windows-cp932, uc-windows-cmd-argv]
---
## 症状

- 環境変数 `$env:LOCALAPPDATA` が未設定のとき、`Join-Path` がエラーになる。
- 応答が 1 行だけ（"ok"）だと、`.ToLower()` がクラッシュする。

## 原因

- null の場合を考えない書き方を、中身の文字列を grep するだけのテストが通してしまった。
- 出力が 1 行だけのパイプラインは、配列でなく文字列に変わる。そのため `$lines[-1]` が、最後の 1 行でなく最後の 1 文字になる。

## 直し方

1. null に強い書き方に直す。
2. 構文を `Parser::ParseFile` で検査するゲートを置く（pwsh が無い環境ではスキップする）。
3. パイプライン全体を `@(...)` で包み、いつも配列にする。

## 再発防止

- 構文のゲート、pwsh での両方の分岐の実行、判定ロジックの単体テスト 10 件。
- 別の OS のスクリプトは、grep でなく、パーサで検査して実行まで確かめる。Bash から移したスクリプトでは、配列と単独の値の暗黙の変換を疑う。
- 検査は、Mac の pwsh 7.6.3 で行った。Windows 実機（PowerShell 5.1）での確認はまだ。
- 同じスクリプトのログイン案内（`claude /login`）は、別件で誤りと分かった（正しくは、引数なしの `claude` で起動して対話の中で行う）。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-21、07-25）
