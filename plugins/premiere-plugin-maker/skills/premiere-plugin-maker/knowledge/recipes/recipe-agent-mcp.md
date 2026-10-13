---
id: recipe-agent-mcp
title: AI からプラグインを操作できるようにする
kind: recipe
tags: [MCP, Claude Code, Codex, 登録, 待ち行列, ポーリング, 安全規約, パネル, 開発中の確かめ]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: AI（Claude Code・Codex）が道具として呼べる入口を、プラグインに付ける。登録は CLI の命令に任せ、変更系の命令は利用者の指示があるときだけ・取り消し 1 回の作りにし、パネルを開いておく
parts: [mcp-bridge, local-server, probe, ppro-kit]
related: [ref-mcp, ref-local-server, feat-cutsrt-mcp, feat-premiere-agent-kit, uc-server-mcp-long-job, uc-server-stale-handshake-403, core-safety, core-transactions]
---
## この型で作れるもの

AI（Claude Code・Codex など）が「選んでいるクリップを読む」「マーカーを打つ」のような操作を、プラグインに頼めるようにする型です。人が画面を触らなくても Premiere が動くので、**開発中の確かめ**（診断を呼ぶ、ログを読む）にも、利用者向けの機能にも使えます。

仕組みは次のとおりです（詳しくは `ref-mcp`）。

```
AI ─ 標準入出力 ─► MCP のアダプタ ─► 手元のサーバーの待ち行列 ◄─ パネルが 2 秒ごとに取りに来る
```

サーバーからパネルへ「押し込む」ことはできません。パネルが取りに来る方式なので、**パネルを閉じていると命令が届きません**。

## 前提

- 雛形は `panel-server`。部品 `mcp-bridge`（`local-server` と `probe` が一緒に入る）を足す。
- AI の側に Claude Code か Codex が入っていること（入っている方にだけ登録します）。
- 設計のうえで先に決めること:
  - 公開する命令の一覧。**読み取りの命令**（選択・概要・診断・ログ）と、**変更する命令**（マーカー・効果など）を分けて考える。
  - 変更する命令は、利用者が「やって」「実行して」と言ったときだけ AI が使う、と**命令の説明文に書く**。提案と実行を混ぜさせない。
  - 一括で変える命令には、1 回の上限を決める（例: マーカー 50 か所）。
- 登録は利用者の環境の設定を変えることなので、**何をするかを見せて許可を取ってから**実行します。

## 手順

1. 作業フォルダと部品。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-server --name "Agent Panel" --label "AI から操作"
   python3 <SKILL>/scripts/add_part.py mcp-bridge --project <作業フォルダ>
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Agent Panel`、Windows `%USERPROFILE%\PremierePlugins\Agent Panel` です。
2. パネルの `index.js` の起動処理（`boot()`）の中で `PPM.agent.start()` を呼ぶ。最初から `probe`（診断）・`get_selection`・`sequence_overview`・`log_tail` の命令が入っています。
3. 命令を足す。

   ```js
   PPM.agent.register("add_marker", "再生ヘッドの位置にマーカーを打つ。利用者の実行の指示があるときだけ使う。取り消しは 1 回", async (args) => {
     const { project, sequence } = await PPM.getProjectAndSequence();
     await PPM.addMarkers(project, sequence, [{ seconds: Number(args.seconds), name: String(args.name || "") }]);
     return { ok: true };
   });
   ```

   画面のボタンと**同じ関数**を呼ぶ（処理を二重に書かない）。Premiere を変える命令は `PPM.transact` の 1 回の取引にする。
4. サーバーを入れる（`recipe-local-server-heavy` の手順 4）。
5. **登録する。まず試し実行で、何が登録されるかを利用者に見せる。**

   ```
   python3 <作業フォルダ>/server/setup_mcp.py
   ```

   見せた内容に利用者が同意したら、`--apply` を付けて実行する。

   ```
   python3 <作業フォルダ>/server/setup_mcp.py --apply
   ```

   内部では `claude mcp add <名前> --scope user -- python3 <アダプタの絶対パス>` と `codex mcp add <名前> -- python3 <アダプタの絶対パス>` を、先に `remove` してから呼びます。入っている方にだけ登録します。**AI の設定ファイルを手で書き換えません。**
6. **新しいセッションを開き**、`ppm_health`（つながっているかの確認）を 1 回呼ぶ。続けて `ppm_panel_commands` で命令の一覧を見る。
7. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

## 確認

利用者の Premiere で次を見てもらいます。

1. パネルを開いたまま、AI に「つながっているか調べて」と頼む。`ppm_health` が成功する。
2. AI に「選んでいるクリップを教えて」と頼む。Premiere で選んだクリップの名前と位置が返る。
3. 変更する命令は、**1 クリップ、または 1 か所だけ**で最初に試す。Premiere に変化が出て、その場で取り消し 1 回で戻る。
4. パネルを閉じてから頼むと、「パネルが応答しません」と理由つきで返る（黙って固まらない）。
5. 全部の道具で 403 が続くときは、古い接続情報を読んでいる疑いがあります。接続情報は「環境変数 → アプリのデータフォルダの `server.json` → 隣のファイル」の順に探す作りにします（`uc-server-stale-handshake-403`）。接続情報の中身（合言葉）は、画面やチャットに貼りません。

## 戻し方

- 変更した結果は、**取り消し 1 回**（Cmd+Z / Ctrl+Z）。一括の変更の前に、AI がプロジェクトの保存と件数の確認をする規約にしておく。
- 登録を外す:

  ```
  claude mcp remove <名前> --scope user
  codex mcp remove <名前>
  ```

  名前は `<アプリ名の小文字>-premiere`。
- サーバーごと外す: `python3 <作業フォルダ>/server/install.py --uninstall`

## 使う部品

- `mcp-bridge`: `ppm_mcp.py`（アダプタ）、`setup_mcp.py`（登録。既定は試し実行）、`panel_queue.py`（待ち行列）、`PPM.agent`（パネル側の受け口）
- `local-server`: 手元のサーバー
- `probe`: 診断の命令

## 出どころ

- Cut & SRT の MCP の実装と記録（36 個の道具、2026-08 の 403 の計測）
- Premiere Agent Kit の登録の仕組み・安全規約（試し実行・CLI に任せる・疎通の確認）
- 実機で確かめたのは Mac の Claude Code 側の元の実装です。このキットの形の登録の本実行（`--apply`）、Codex 側、Windows のアダプタは確かめていません
