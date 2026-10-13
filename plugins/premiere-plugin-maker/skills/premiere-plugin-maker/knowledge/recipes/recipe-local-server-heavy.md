---
id: recipe-local-server-heavy
title: 重い処理を手元のサーバーに任せる
kind: recipe
tags: [サーバー, ジョブ, Python, 127.0.0.1, 常駐, launchd, タスク スケジューラ, 依存, 同意, 進み具合]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: UXP のパネルでは持てない重い処理（音声解析・動画の処理など）を、同じ PC の Python のサーバーのジョブとして動かす。ジョブの書き方、導入、依存を入れる前の同意まで
parts: [local-server, logger, ppro-kit, ui-kit, probe]
related: [ref-local-server, uc-server-localhost-network-all, uc-server-launchd-log-rotation, uc-install-same-version, uc-server-atomic-output, recipe-silence-cut, recipe-ai-integration, core-safety]
---
## この型で作れるもの

「パネルのボタンを押すと、手元のサーバーが時間のかかる処理をして、進み具合がパネルに出て、結果が戻る」プラグインです。UXP のパネルは、重い計算や外部のプログラム（ffmpeg など）を自分では動かせません。そこで、同じ PC の中に小さな Python のサーバーを置き、パネルが頼みに行きます。無音カット（`recipe-silence-cut`）も、この型の上にあります。

## 前提

- 雛形は `panel-server`。サーバー（`server/` フォルダ）と、パネル側の窓口（`PPM.server`）が入ります。
- 利用者の PC に Python 3.9 以上が要ります。導入の前に `python3 --version`（Windows は `py -3 --version`）で確かめます。
- パネルの権限は、サーバーにつなぐため `network` が `domains: "all"`、接続情報を読むため `localFileSystem: "fullAccess"` になります。権限が広いので、**入れる前に利用者に説明します**（`core-manifest-permissions`）。
- サーバーが待ち受けるのは `127.0.0.1` だけです。外の機械からは届きません。
- 外部の部品（Python のライブラリ、ffmpeg など）を入れる必要があるときは、**何をどれだけ入れるかを利用者に見せ、許可を取ってから**入れます。勝手に入れません。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-server --name "Heavy Job" --label "重い処理"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Heavy Job`、Windows `%USERPROFILE%\PremierePlugins\Heavy Job` です。
2. ジョブを書く。`<作業フォルダ>/server/jobs/<名前>.py` に、`NAME` と `run(params, ctx)` を置く（見本は同じ場所の `echo.py`）。
   - 必須の引数は `need(params, "キー", 型)` で取り出す。足りなければ、理由つきで止まる。
   - 進み具合は `ctx.progress(パーセント, "いま何をしているか")`。長いループの中で、`ctx.cancelled()` を見て、止められたら速やかに終わる。
   - 失敗は `JobError("症状", "なぜ", "次の一手")` を投げる。パネルには「症状・なぜ・次の一手」の 3 つで出ます。
   - 成果物は、一時フォルダに書いてから置き換える（失敗しても前回の成果物を壊さない。`uc-server-atomic-output`）。
3. パネルから呼ぶ（`index.js` の `onRun`）。

   ```js
   await PPM.server.connect({ tries: 2, intervalMs: 1000 });
   const result = await PPM.server.runJob("名前", { /* 引数 */ }, { onProgress });
   ```

   `onProgress` に画面の進み具合の更新を渡す。起動の直後はサーバーよりパネルが先に立つので、`connect` が数回やり直します。
4. サーバーを入れる。まず試し実行で、何をするかだけ見る。

   ```
   python3 <作業フォルダ>/server/install.py --dry-run
   python3 <作業フォルダ>/server/install.py
   ```

   - Python の部品が要るときは、入れる内容を利用者に見せて許可を取ってから `--with-deps` を付ける。
   - 状態は `--status`、外すときは `--uninstall`。
   - **同じ版が既にあると、導入は写し直しません**。サーバーのコードを直したあとは、サーバーの版（`server/config.json` の `version`）を上げるか、`--force` を付けます（`uc-install-same-version`）。
   - Mac は launchd、Windows はタスク スケジューラで常駐します。Windows のサインイン時の自動起動は、実機で確かめていません。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンのあと、`logs.py` で結果を読む。

## 確認

利用者の Premiere で次を見てもらいます。

1. 最初は `echo` ジョブ（値をそのまま返す）で、つながりだけを確かめる。パネルに「受け取りました」と戻る。
2. 自分のジョブを押す。進み具合の数字と文が動き、終わると結果が出る。
3. 途中で止めるボタン（あれば）を押すと、「失敗」でなく「中止」と表示される。
4. サーバーを止めた状態で押すと、「サーバーにつながっていません」と理由と次の一手が出る（黙って固まらない）。
5. ジョブが失敗したとき、「通信が切れた」ではなく、ジョブの失敗の理由が出る（ジョブの失敗は通信としては成功で返ります。`ref-local-server`）。

## 戻し方

- Premiere の中身を変えないジョブなら、**取り消しは要りません**。
- 成果物が増えたら、一時フォルダや出力先のファイルを消すだけです。
- サーバーそのものを外す: `python3 <作業フォルダ>/server/install.py --uninstall`。常駐の登録と、版ごとの置き場所が片付きます。
- Premiere を変えるジョブ（読み込みなど）は、1 回の取引にまとめて、取り消し 1 回で戻る作りにします。

## 使う部品

- `local-server`: `server/ppm_server.py`（127.0.0.1・起動ごとの合言葉・ジョブ）、`ppm_jobs.py`（`JobError`・`need`）、導入スクリプト、`PPM.server`
- `logger` / `probe`: ログと診断
- 追加の口（MCP・CEP）が要るときは、別の部品が `server/ext/` に足されます

## 出どころ

- Cut & SRT の通信・導入の記録（握手のファイル・ジョブ・ポーリング・版ごとの runtime・常駐。2026-07〜10）
- 完成サンプル `silence-cut`（この型を使う。このキットの形での Premiere 実機の通し確認はまだです）
