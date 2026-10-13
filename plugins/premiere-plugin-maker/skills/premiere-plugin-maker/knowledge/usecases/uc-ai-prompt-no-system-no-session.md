---
id: uc-ai-prompt-no-system-no-session
title: system 引数もセッションも持たない AI CLI に、指示と質問を一緒に渡すと混乱する
kind: usecase
tags: [AI, プロンプト, system, セッション, 履歴, 知識の注入, CLI]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: system 相当を持たない CLI には、規則と質問の境界を文で明示する。セッションを持たない CLI には、直近の履歴を字数の上限つきで毎回渡す。大きな知識は索引だけを常に入れ、本文は必要なときに読ませる
parts: [local-server, mcp-bridge]
related: [uc-ai-cli-invocation-traps, uc-ai-headless-permissions, uc-windows-cmd-argv]
---
## 症状

- codex や gemini に、規則（`<システム指示>…</システム指示>`）と質問を同じメッセージで渡すと、「システム指示の内容を送ってください」と返ってくる。
- 非 claude の AI タブでは、会話が続かない。

## 原因

- 指示と質問が 1 つの文に入っていたので、AI は指示そのものを質問だと受け取った。
- codex・gemini・grok は、1 回の呼び出しが 1 つのプロセスで、会話のセッションを持たない。

## 直し方

1. 内部の規則を「これは質問ではない。黙って適用する」と明記し、規則と会話を見出しで分ける。正式な system の引数を持つ CLI（grok・claude）ではそれを使い続ける。
2. セッションを持たない CLI には、直近 12 件（利用者と AI の発言のみ。合計 12,000 字まで）を毎回プロンプトに付ける。claude はセッション ID を正本にする。
3. 大きな知識は、索引（絶対パスと見出し 1 行）だけをシステム指示に入れ、本文は必要なときに Read で読ませる。約 1KB の小さなものは全文を入れる。
4. 履歴は画面の復元だけのために、ブラウザの保存領域（上限 40 件）に置く。

## 再発防止

- 履歴の永続化と、知識の索引の生成をテストで固定する。
- 長い指示を引数で渡す経路は、別の罠（Windows の cmd.exe による再解釈）にも当たりうる。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-19、v0.6.0〜v0.7.2）。機械検証のみで、外部の AI への実際の依頼と Premiere 実機は未実施。
