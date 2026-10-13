---
id: uc-server-cli-exit-zero-path
title: 画面が呼ぶ CLI が失敗で終了すると画面が止まる・常駐側で ffmpeg が見つからない
kind: usecase
tags: [CLI, 終了コード, JSON, PATH, 常駐, ffmpeg, Python, doctor]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 画面が呼ぶ CLI は、失敗でも終了コード 0 で JSON を返し、失敗は本文で伝える。常駐やパネルは対話シェルの PATH を引き継がないので、絶対パスの候補を探す
parts: [local-server, ppro-kit]
related: [uc-server-preflight-light, core-dev-loop, platform-cross]
---
## 症状

- 検査に落ちた項目が 1 つでもあると、カタログの画面が永久に「読み込んでいます…」のままになる。
- パネルだけ、`ffmpeg` が「見つかりません」と表示される。ターミナルでは動く。

## 原因

- 検査の CLI が、不合格が 1 件でもあると終了コード 1 を返し、それを呼ぶ側の `execFileSync` が例外を投げて、画面の処理が止まっていた。
- CEP や常駐サーバーが受け取る PATH は最小限で、Homebrew の場所（`/opt/homebrew/bin`）が含まれない。

## 直し方

1. 画面から呼ばれる CLI は、常に終了コード 0 で JSON を返し、失敗は `{"ok": false, "error": "…"}` で伝える。
2. Python は、`/usr/bin/python3` など、絶対パスの候補を順に探す。
3. PATH の問題が起きたときの案内: Mac は `server/install.command` を再実行する。Windows は黒い画面（コマンドプロンプト）を開き直して `install.bat` を実行する。`which`（Windows は `where`）で場所を確かめる。

## 再発防止

- 自分の環境以外（第三者の環境）で確かめ、診断画面（ドクター）に、ffmpeg の版と場所を出させる。
- 「終了コード 0 + JSON」の約束を、画面から呼ぶ CLI すべての決まりにする。
- 終了コード 1 の件は、修正後に実機で確認した。Python の探索はテストまで。

## 出典

- Effect & Design の記録（2026-09-18、v0.3.0）と Cut & SRT の導入ガイド（v0.9.10 以降）
