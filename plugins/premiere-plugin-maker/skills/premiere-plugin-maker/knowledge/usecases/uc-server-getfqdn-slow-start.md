---
id: uc-server-getfqdn-slow-start
title: 手元のサーバーが起動の合図（server.json）を書くまで何十秒も止まる
kind: usecase
tags: [サーバー, 起動, 遅い, server.json, getfqdn, DNS, HTTPServer, Mac]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: Python の標準の HTTPServer は待ち受けの前に socket.getfqdn で自分の名前を DNS に聞く。ネットの設定によってはそこで長く止まる。127.0.0.1 だけで待つなら、server_bind で名前を聞かない
parts: [local-server]
related: [ref-local-server, uc-server-localhost-network-all]
---
## 症状

- 手元のサーバーを起動しても、パネルが「サーバーが動いていません」と出し続ける。しばらくすると（数十秒後）つながることがある。
- サーバーは落ちていない（プロセスは動いている）のに、起動の合図のファイル `server.json` ができない。

## 原因

Python の標準の `http.server.HTTPServer`（`ThreadingHTTPServer` も同じ）は、待ち受けを始める `server_bind` の中で `socket.getfqdn(host)` を呼び、自分の名前を DNS に問い合わせる。ネットの設定（DNS の応答が遅い・名前の逆引きが引けない）によっては、ここで長く止まる。GitHub Actions の Mac で 20 秒を超えて止まり、テストが全部落ちた（2026-10-13・このキットの CI）。手元の Mac では一瞬で終わったので、利用者の環境によって出たり出なかったりする型。

## 直し方

127.0.0.1 だけで待つサーバーは、自分の名前が要らない。`server_bind` を上書きして、名前を聞かないようにする（キットの部品 local-server の `ppm_server.py` の `_Server`）。

```python
class _Server(ThreadingHTTPServer):
    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port
```

## 再発防止

- テストで `socket.getfqdn` を「呼んだら失敗」に差し替え、サーバーを作れることを確かめる（`tests/test_review_fixes.py`）。
- 起動を待つ側は、時間切れのときにサーバーのエラー出力を捨てずに見せる（理由が分かるように）。

## 出どころ

- このキットの GitHub Actions（macos-latest）での失敗と直し（2026-10-13）。Windows の CI では起きなかった。
