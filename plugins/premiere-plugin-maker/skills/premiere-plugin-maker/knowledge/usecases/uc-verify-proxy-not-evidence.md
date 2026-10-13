---
id: uc-verify-proxy-not-evidence
title: 似た経路・模擬素材・単体テストで通っても、本物の証拠にならない
kind: usecase
tags: [検証, 代理, 模擬素材, 実クライアント, 認証, Sec-Fetch, 実送信]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 代わりのもので通ったことは、本物の証拠にならない。壊れている画面と同じ経路・実素材・実際の送信で確かめ、代わりのもので確かめた範囲は「ここまで」と書く
parts: [local-server]
related: [core-verification, uc-verify-probe-same-path, uc-verify-node-green-device-broken, uc-server-bridge-contract-drift]
---
## 症状

- curl では `/auth/login` が 302 を返すのに、ブラウザは編集画面を出した。診断用の窓口で「認可は通る」と判断して「直りました」と言い、2 回外した。
- ピンマイクの切り替えは、模擬素材で全件一致したが、音響の精度は測れていなかった。

## 原因

- Cloudflare Workers の静的アセットは、ブラウザの遷移（`Sec-Fetch-Mode: navigate`）を Worker より先に受け取る。curl はこのヘッダーを送らない。
- 模擬素材は、元が同じ音なので、実際のマイクの混ざり方を再現しない。

## 直し方

1. curl に `-H "Sec-Fetch-Mode: navigate" -H "Sec-Fetch-Dest: document"` を付ける。診断用のコードは、壊れている画面と同じ種類のファイルに置く。
2. ピンマイクは、正解表つきの合成した対談（87 秒）を、実機の前に解析して 3 点を直した。
3. 通知は、使い捨てのトピックを使って実際に送信し、受信するところまで確かめた。

## 再発防止

- 認証が要る経路は、ログイン済みのブラウザで、報告された操作そのものを踏んで確かめる。
- 模擬素材で確かめたのは「しきい値と配線」までと書く。

## 出どころ

- 作者の開発メモと Cut & SRT の引き継ぎ記録（2026-07-16〜09-30、v0.13.0）。Workers と通知の実送信は実機で確かめた。ピンマイクの音響の精度、切る処理・リンク音声・取り消し・Windows は未確認。
