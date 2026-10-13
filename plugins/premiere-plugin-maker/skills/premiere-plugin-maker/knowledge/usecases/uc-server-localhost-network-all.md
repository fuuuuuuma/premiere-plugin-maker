---
id: uc-server-localhost-network-all
title: パネルから手元のサーバーにつながらない（network.domains の個別許可では fetch が発生しない）
kind: usecase
tags: [UXP, manifest, network.domains, fetch, loopback, ローカルサーバー, 127.0.0.1]
os: [mac]
premiere: ">=26.3"
status: verified
summary: manifest の許可リストに http://127.0.0.1:3850 のような個別の loopback を書いても fetch が発生しなかった。network.domains を all にし、安全性はサーバー側（loopback だけで待ち受ける・起動ごとのトークン）で担保する
parts: [local-server, ppro-kit]
related: [core-manifest-permissions, ref-local-server, uc-server-stale-handshake-403, core-safety]
---
## 症状

Premiere 26.3（macOS）で、パネルから手元のローカルサーバーへの通信が一切起きない。`fetch` がそもそも発生しない。manifest の許可リストに、`http://127.0.0.1:3850` のような個別の loopback の HTTP を書いていた場合。

## 原因

個別のドメインの許可リストでは、fetch が発生しなかった。観測した事実だけで、UXP 側の理由、再現の条件、検証の手順は記録に残っていない。

## 直し方

1. manifest.json の `network.domains` を `all` にする。
2. 安全性は、サーバー側で担保する。サーバーは `127.0.0.1` だけで待ち受け（bind）、外部のホストから接続できる構成にはしない。
3. 起動ごとに作り直す ready トークンを、すべての API で要求する。

## 再発防止

- ローカルサーバーとの連携は、「`network.domains: all` + loopback bind + 起動ごとのトークン」の 3 点で作る。
- 通信が実際に発生するかは、実機で確かめる。別のバージョンや OS で同じとは限らない（今回の観測は Premiere 26.3、macOS）。
- 未確認: 外部のカタログ JSON（約 10 MB）を、パネルから直接 fetch する設計は、「UXP の fetch は相手の CORS 許可ヘッダを要らないはず」（根拠は Web タブが任意のページの本文を読めていること）を、最初に実機で確かめ、だめならサーバー経由にする、という方針だった。結果は記録に残っていない。

## 出典

- Cut & SRT の失敗記録と README（2026-07、v0.10.3、Premiere 26.3、macOS）
