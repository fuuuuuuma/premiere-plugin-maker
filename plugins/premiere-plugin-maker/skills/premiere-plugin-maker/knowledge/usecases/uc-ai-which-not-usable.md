---
id: uc-ai-which-not-usable
title: 「CLI が見つかる」と「使える」は別。画面は利用可なのに実行で失敗する
kind: usecase
tags: [AI, CLI, 認証, 可否判定, 実応答, 縮退, which]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: バイナリがあることしか見ていないと、未ログインや未課金でも「利用可」と出る。LLM を呼ばない軽い確認か短い実応答で可否を判定し、別のエンジンに切り替わったことを利用者に見せる
parts: [local-server]
related: [uc-ai-auth-probe-cache, uc-ai-cli-not-on-server-path, uc-ai-install-login-verify, uc-server-preflight-light]
---
## 症状

画面は「接続中・利用可」なのに、実行すると失敗する。codex を指定したのに、改行の品質だけ落ちる例もあった。完了ログの「エンジン:」欄を見て初めて気づく状態だった。

## 原因

可否を `which`（実行ファイルがあるか）だけで判定していた。未ログイン・認証切れ・未課金でも `which` は通る。失敗した部分は、自動選択が黙ってローカルの LLM に切り替わっていた。

## 直し方

1. 起動時に 1 回、LLM を呼ばない軽い確認で判定する。
   - claude: `claude auth status` の `loggedIn`
   - codex: `codex login status`（結果は標準エラー出力に出る）
   - 実応答の確認: 短い文（例: 「ok とだけ返して」）を投げ、末尾の行が `ok` か見る
2. 未ログインのエンジンは黙って飛ばし、次のエンジンへ回す。
3. 処理の完了時に、実際に使ったエンジンと、切り替わったことを画面に出す。

## 再発防止

- 標準出力と標準エラー出力をつなげてから判定する。「Not logged in」は「logged in」に部分一致するので、`not logged in|logged out` を先に弾く。
- 判定を毎分繰り返すと利用枠を消費する。
- Grok のように、ログインしていても課金が無いと実行時に 401 になるものがある。確認が通っても、最後は実際の呼び出しの結果を信じる。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の開発メモ（2026-07-19〜08-16）。判定コマンドの出力と、確認にかかる時間は実機で確かめた。「codex の未ログインが品質低下の原因」は仮説。
