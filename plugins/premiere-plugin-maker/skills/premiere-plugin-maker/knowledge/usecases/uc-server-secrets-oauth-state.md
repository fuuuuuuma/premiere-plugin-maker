---
id: uc-server-secrets-oauth-state
title: 設定の取得で秘密の値が流れる・OAuth のコールバックをどう守るか
kind: usecase
tags: [秘密情報, API, OAuth, state, コールバック, MCP, トークン, 設定]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 外部の AI 向けの設定取得は、値そのものでなく「設定済みか」だけを返す。ヘッダ認証のサーバーで OAuth のコールバックを受けるときは、ヘッダ検査の外に置いた分を state の一致で守る
parts: [local-server, mcp-bridge, keychain]
related: [uc-server-stale-handshake-403, uc-install-secret-name-dropped, ref-mcp, core-safety]
---
## 症状

- MCP 経由で外部の AI が設定を読むと、API キーや Webhook の値がそのまま流れうる。
- OAuth のコールバックを、独自のヘッダ（`X-CutSRT-Token`）で認証するサーバーで受ける必要があったが、ブラウザのリダイレクトはカスタムヘッダを付けられない（推測）。

## 原因

設定の取得 API が、値そのものを返していた。また、ヘッダでの認証を、リダイレクトで来る OAuth の戻り先にも要求すると、通れなくなる。

## 直し方

1. 設定の取得は、「設定済みか」だけを返す。値は返さない。
2. OAuth のコールバックの経路（`/frameio/oauth/callback`）は、ヘッダの検査の外に置き、その代わりに、開始時に作った `state` の一致で保護する。
3. 取得したトークンは、別のファイル（`frameio_auth.json`）に分け、権限を 600 にして、リポジトリの外に置く。

## 再発防止

- 外部のエージェント向けの API は、秘密の値を返さない。
- 該当の送信機能の試験（`test_send_frameio.py`）を置く。実際のログインを通した確認は、未実施。

## 出典

- Cut & SRT の README と作業記録（2026、v0.10.3 と v0.11.0、2026-09-24）
