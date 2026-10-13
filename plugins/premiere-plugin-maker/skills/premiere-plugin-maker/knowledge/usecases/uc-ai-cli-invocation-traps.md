---
id: uc-ai-cli-invocation-traps
title: AI CLI の呼び出しの罠（標準入力・作業ディレクトリ・フラグの位置・タイムアウト）
kind: usecase
tags: [AI, CLI, stdin, cwd, タイムアウト, 並列, stderr, デッドロック]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 外部 AI CLI は、依頼の渡し方・作業ディレクトリ・フラグの位置を実際に動かして確かめる。別の所から流用したタイムアウトは測り直し、ローカルの CLI は並列にしても速くならない
parts: [local-server]
related: [uc-windows-cmd-argv, uc-ai-shared-argv-breaks-sibling-cli, uc-ai-prompt-no-system-no-session, uc-ai-cli-defaults-env-account]
---
## 症状

- 「no stdin data received in 3s」で止まる。
- `claude -p --allowedTools "A,B" "頼み"` が「Input must be provided…」で何もしない。
- codex が、大きなフォルダで実行すると 240 秒でも終わらない。
- 別のプロジェクトから流用した 150 秒のタイムアウトに毎回当たる。2 本同時に投げると、両方 420 秒で 0 件。

## 原因

- Node の `execFile` には標準入力を渡す手段が無い。
- `--allowedTools` は可変長で、後ろの依頼の文まで道具の名前として読んでしまう。
- codex は作業ディレクトリの中身を読みにいく。
- 流用した定数は、流用元の所要時間に合わせた値だった。ローカルで動く CLI は、並列にしても速くならない。

## 直し方

1. `spawn` で起動して `child.stdin.write()` で依頼を渡す。`echo "$PROMPT" | claude -p --allowedTools WebSearch WebFetch` の形にする。
2. codex は空のディレクトリを作業ディレクトリにし、`codex --search exec --skip-git-repo-check --output-last-message <file>` で呼ぶ。`--search` は exec の前に置くグローバルなフラグ。claude は作業ディレクトリを指定しない。
3. ストリーム形式の出力を行ごとに読むときは、標準エラー出力を別のスレッドで読み捨てて、詰まり（デッドロック）を避ける。
4. タイムアウトは 420 秒に測り直し、同時に走らせる本数は既定を 1 本にする。

## 再発防止

- AI の生の失敗文は画面に出さず、利用枠の上限・レート制限・認証切れ・時間切れを一言に直して出す。
- 依頼の渡し方（引数・標準入力・ファイル）は CLI ごとに違う。新しいエンジンは、実物で 1 往復させてから採用する。
- zsh のテスト用ラッパーでは、変数名 `status` が読み取り専用の予約語なので使わない。

## 出どころ

- 作者の開発メモと Cut & SRT の引き継ぎ記録（2026-07-19〜09-29）。標準入力・作業ディレクトリ・フラグの位置は各 CLI で実測した。
