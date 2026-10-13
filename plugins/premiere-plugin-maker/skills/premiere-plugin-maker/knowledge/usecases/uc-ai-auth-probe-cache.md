---
id: uc-ai-auth-probe-cache
title: ログインしたのにパネルは未認証のまま。認証確認の失敗が固まって残る
kind: usecase
tags: [AI, 認証, キャッシュ, TTL, 再接続, Windows, claude]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 認証の確認結果を、特に失敗を長く覚えていると、ログイン後も直らない。失敗の保持時間は短くし、利用者が押せる再確認の経路を用意する。単体の CLI の資格はアプリとは別
parts: [local-server]
related: [uc-ai-which-not-usable, uc-ai-login-guide-wrong, uc-ai-cli-not-on-server-path, uc-windows-daemon-process-paths]
---
## 症状

- ログインを済ませても、パネルは未認証の表示のまま。サーバーか PC を再起動するまで回復しない。
- Windows で、アプリにはログイン済みなのに、単体の CLI（`claude -p`）が「Not logged in · Please run /login」で終わる。

## 原因

- 実応答での確認結果（特に失敗）を、プロセスが生きている間ずっと覚えていて、捨てる手段が無かった。
- Windows の単体 CLI の認証は、デスクトップのアプリとは別の資格だった。

## 直し方

1. 結果に保持時間を付ける（成功は 300 秒、失敗は 15 秒）。
2. 明示的に捨てる経路を作る（サーバーの再確認の窓口と、設定タブの「再接続」ボタン）。
3. Windows では、単体 CLI で別にログインしてもらう。常駐サーバーの PATH にも、単体 CLI の置き場所（`~\.local\bin`）を足す。PATH が反映されないときだけ、常駐のタスクを停止して開始し直す。

## 再発防止

- 保持時間と再判定の動きを、単体テストで固定する。
- 案内には「単体の CLI の資格はアプリと別」と書く。

## 出どころ

- Cut & SRT の引き継ぎ記録と失敗記録（2026-07-14〜07-19）。症状は Windows 実機、ログイン後の回復は利用者の報告。PATH に置き場所が無かったのは、補強を足したことからの推測。
