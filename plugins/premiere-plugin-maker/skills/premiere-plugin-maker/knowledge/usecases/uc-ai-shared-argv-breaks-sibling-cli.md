---
id: uc-ai-shared-argv-breaks-sibling-cli
title: 共有の引数の組み立てを直したら、差分に名前の出ない兄弟の CLI が壊れた
kind: usecase
tags: [AI, CLI, 引数, stdin, 回帰, 総当たり, Windows]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 複数の AI CLI が使う引数の組み立てを 1 つ直すと、stdin を読めない別の CLI だけ本文が空になった。直した対象だけでなく、実際に渡る引数と標準入力の層で全エンジンを総当たりして確かめる
parts: [local-server]
related: [uc-windows-cmd-argv, uc-ai-cli-invocation-traps, uc-ai-engine-registry, uc-verify-probe-same-path]
---
## 症状

Antigravity の CLI（`agy`）で応答確認をすると、ヘルプの全文と「flag needs an argument: -p」（終了コード 2）が返る。明示的に選んでも、改行処理の工程が完走しない。

## 原因

別の CLI（claude）の不具合を直すため、本文を標準入力（stdin）で渡すように共有の関数 `_probe_argv` の最終行を書き換えた。ところが `agy` は標準入力を読めず、本文ゼロの引数だけが残った。差分に `agy` の名前は出ないので、レビューでも気づけなかった。

## 直し方

1. 共有の関数に CLI ごとの分岐を足し、`agy` には本文が届く形にする。
2. Windows で cmd.exe を経由する `agy` に、改行・`| & < > ^ %`・6,000 字超の危険な本文を渡すときは、黙って壊さず「使えない」と原因つきで止める。

## 再発防止

- 旧テストは、応答確認の関数ごと偽物に差し替えていて層が高すぎた。実際に渡る引数・標準入力・プロンプトのファイルを捕まえるテストにし、登録した全エンジンについて「本文が届く」を検査する。
- 共有の部品を直したときは、その部品を使う全員を機械で回す。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-08-25）。実際の `agy` で再現と完走を確かめた。Windows の cmd.exe による拒否は実機未確認。
