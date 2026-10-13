---
id: uc-ai-login-guide-wrong
title: 画面のログイン案内どおりにしてもログインできない（案内が実態とずれた）
kind: usecase
tags: [AI, ログイン, 案内文, claude, gemini, 公式確認, 一元化]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 「ターミナルで claude /login を実行」は誤りだった。対話内のコマンドとシェルの引数を混同せず、案内文は公式で確かめて 1 か所に集める。外部サービスの認証方式は事業者の都合で変わる
parts: [local-server]
related: [uc-ai-install-login-verify, uc-ai-auth-probe-cache, uc-verify-docs-same-commit]
---
## 症状

- 画面の案内「ターミナルで `claude /login` を実行」に従ってもログインが始まらない。
- gemini は、案内にあった「Google でログイン」では使えず、「API キーが必要」と出る。

## 原因

- `/login` は Claude Code の対話画面の中でだけ使うスラッシュコマンド。シェルの引数として渡すと、「/login という依頼」を 1 回実行するだけになる。
- gemini の無料の Google ログインは終了し、API キー（`GEMINI_API_KEY`）が必須になった。これは外部サービス側の変更で、資料により確認の度合いが違う。
- 誤った案内は計画書で固定され、Windows 向けのガイドにも入った。インストーラは案内の文字列を `eval` で実行していたので、機能上の不具合でもあった。

## 直し方

1. claude は、引数なしの `claude`（初回起動でブラウザ認証）、長期のトークンは `claude setup-token` に直す。直した後はパネルの「設定 → 再接続」を押す。
2. gemini は API キーを環境変数に設定するか、別の CLI（antigravity の `agy`）を使う。grok は `grok login`（契約が必要）。
3. 存在しないコマンド名の案内（`which antigravity`。実体は `agy`）も直す。

## 再発防止

- 案内文は各エンジンの定義の 1 か所（`login_hint`）に持ち、ガイドの「困ったとき」の表を、コードの実際のエラー文言と 1 対 1 で突き合わせる。
- 案内は公式の文書で確かめてから書く。

## 出どころ

- Cut & SRT の引き継ぎ記録と計画書（2026-07-19〜07-28）。claude の誤りは公式の文書で確認した。実機でのログイン動作の確認は記録が無い。
