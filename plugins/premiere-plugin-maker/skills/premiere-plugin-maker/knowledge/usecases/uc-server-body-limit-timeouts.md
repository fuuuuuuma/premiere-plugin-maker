---
id: uc-server-body-limit-timeouts
title: 画像が送れない・接続が間欠的に切れる（受信上限と Node の既定タイムアウト）
kind: usecase
tags: [Node, ローカルサーバー, タイムアウト, keepAliveTimeout, 受信上限, https, Failed to fetch]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 受信の上限は最大のケースで決めて画面側で収め、Node の既定のタイムアウトは上書きする。1 回の失敗で切断と決めつけない
parts: [local-server]
related: [uc-server-bridge-contract-drift, uc-server-localhost-network-all, ref-local-server]
---
## 症状

- 画像が `body too large` で弾かれる。
- 接続が間欠的に切れて、画面には `Failed to fetch` としか出ない。
- https の公開サイトから、手元の常駐サーバーへ届かない。

## 原因

- 受信の上限（`readBody`）が 1 MB に固定されていて、画像が収まらなかった。
- Node の既定のタイムアウトは、`keepAliveTimeout` が 5 秒、`requestTimeout` が 300 秒。使い回した接続が、間を置いて切られた。
- https の件は推測: Chrome の「ローカルネットワークアクセス」の制限による（UXP のパネルには当てはまらない）。

## 直し方

1. 画面側で、PNG を JPEG に変えて、寸法と品質を落とし、上限の予算に収める。
2. サーバー側は、`readBody(req, maxBytes)` の上限を用途ごとに設ける。
3. `keepAliveTimeout = 120_000`、`headersTimeout = 125_000`、`requestTimeout = 0` に上書きする。
4. https の件は、画面ごと `127.0.0.1` から配信して、同じオリジンにした。

## 再発防止

- タイムアウトの確認は、同じソケットで 10 秒以上空けて 2 回リクエストして行う。
- 上限は、最大のケースを見積もって決める。1 回の失敗だけで「切断」と決めつけない。
- https のページ（Chrome 154）では、Playwright で確認したのみ。

## 出典

- ローカルブリッジの落とし穴の記録（2026-07-31〜10-01、Node 22、Chrome 154）
