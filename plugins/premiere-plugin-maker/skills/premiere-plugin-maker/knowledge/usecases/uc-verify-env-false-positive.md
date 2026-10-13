---
id: uc-verify-env-false-positive
title: 環境のせいの誤検出を、原因を特定する前に「無関係」と言わない
kind: usecase
tags: [検証, テスト, 環境依存, PATH, 既存サーバー, 隔離, e2e]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 隔離した環境でだけ落ちるテストは、原因（依存の有無、先客のサーバー）を特定してから「無関係」と判定する。テストは PATH・グローバルな状態・既存のサーバーに依存させない
parts: [local-server, probe]
related: [uc-verify-skip-is-not-success, uc-ai-cli-defaults-env-account, uc-ai-cli-not-on-server-path]
---
## 症状

- 隔離した環境（`uv run --with pytest`、一時的な venv）で、`/jobs/srt` が busy を返すテスト 1 件だけが `400 != 409` で落ちた。
- 別の件で、e2e が別のアプリのサーバーに乗ってしまい、落ちた。

## 原因

- `bridge_server.preflight()` が mlx-whisper / faster-whisper の有無を検査し、無いと mock をかける前に 400 を返す。これはバグではない。
- Playwright の `reuseExistingServer:true` が、同じポートの別アプリを使い回した。

## 直し方

1. テストの実行は `python3.14 -m unittest discover -s server/tests` と `node --test server/tests/*.js` にする（pytest は使わない）。
2. 一時的な venv には、先に `server/install.command` の VENV_PACKAGES を入れる。
3. e2e は、`lsof -nP -iTCP:<ポート> -sTCP:LISTEN` で空きを確認し、`reuseExistingServer:false` にする。

## 再発防止

- 外部の CLI を検出するテストは、`shutil.which` と探索先を mock し、一時フォルダのダミーの実行ファイルで検証する。書き換えた変数は戻す。
- 「無関係」と書くのは、原因を特定した後にする。

## 出どころ

- Cut & SRT の引き継ぎ記録と計画書（2026-07-25〜07-28、v0.9.8、v0.9.19）。2 回起きた。両方の環境で再現した。
