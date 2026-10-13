---
id: recipe-commands-shortcuts
title: メニューのコマンドとショートカット
kind: recipe
tags: [コマンド, ショートカット, メニュー, manifest, NSUserKeyEquivalents, Mac, panel-commands]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: パネルを開かずに実行できるメニューのコマンドを足し、Mac ではシステム設定の「アプリのショートカット」でキーを割り当てる。Premiere のショートカット画面には出ない。Windows の割り当ては未確認
parts: [commands, ui-kit]
related: [uc-uxp-shortcut-commands-not-listed, uc-mac-shortcut-nsuserkeyequivalents, core-manifest-permissions, core-capabilities, feat-cutsrt-clip-slots, platform-mac]
---
## この型で作れるもの

- ［ウィンドウ］→［UXP プラグイン］の下に出る「メニューのコマンド」。パネルを開いていなくても、選ぶだけで処理が走ります。
- Mac では、そのコマンドにキーボードのショートカットを割り当てられます（割り当ては macOS 側の設定で行います）。

向く場面: 「選んだクリップに決まった効果を付ける」「再生ヘッドの位置にマーカーを打つ」のように、ボタン 1 回で終わる処理を、キー 1 つで呼びたいとき。

## 前提

- 雛形は `panel-commands`（`panel` に部品 `commands` を足した形）。
- **Premiere の［キーボードショートカット］の画面には、UXP のコマンドは出ません**（版によっては出ない、という記録です。`uc-uxp-shortcut-commands-not-listed`）。ですから「Premiere の中で割り当てる」手順は書きません。
- Mac だけ、macOS の仕組みで割り当てられます。ショートカットの実体は macOS の `NSUserKeyEquivalents` で、**メニューの項目名が 1 文字でも違うと、黙って効きません**。
- Windows で同じことができるかは、確かめていません。Windows の利用者には、パネルを表示している間だけ効くキー入力（パネル内のボタンや数字キー）を代わりに用意します。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-commands --name "Quick Marker" --label "クイックマーカー"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Quick Marker`、Windows `%USERPROFILE%\PremierePlugins\Quick Marker` です。
2. コマンドは 2 か所に書きます。
   - `manifest.json` の `entrypoints` に、`{ "type": "command", "id": "addMarker", "label": { "default": "クイックマーカー: マーカーを打つ" } }` の形で 1 つ足す。雛形には `runMain`（「…: 実行」）が最初から入っています。
   - `index.js` で `PPM.commands.define("addMarker", async () => { … })` と書く。中身は、パネルのボタンと同じ関数を呼ぶだけにします（処理を二重に書かない）。
3. 失敗は `PPM.commands.define` が受け止めてログに残します（コマンドは画面が無いので、利用者に伝える方法は、ログとマーカーなど目に見える結果だけです）。画面に出したいときは、Premiere を変える処理の最後に、結果が見える形（マーカー・クリップ名など）にします。
4. Premiere を変える処理は、必ず `PPM.transact` の 1 回の取引にまとめます（`core-transactions`）。取り消し 1 回で戻ります。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから UXP Developer Tools で［Load］。
6. 【Mac】キーを割り当てる（利用者の操作です。AI は設定を書き換えません）。
   1. 「システム設定」→「キーボード」→「キーボードショートカット」→「アプリのショートカット」→［＋］。
   2. アプリケーションは Adobe Premiere Pro。
   3. メニュータイトルは、Premiere の［ウィンドウ］→［UXP プラグイン］の下に**実際に出ている名前**をそのまま（manifest の `label` と同じ文字）書く。
   4. 好きなキーを押す。他のアプリや Premiere のキーとぶつからないよう、Cmd+Shift+Option など修飾キーを重ねたものを勧めます。
7. 割り当てが効かないとき（Mac）は、保存の中身を見ます。

   ```
   defaults read <Premiere のバンドル ID> NSUserKeyEquivalents
   ```

   バンドル ID は `mdls -name kMDItemCFBundleIdentifier <Premiere のアプリのパス>` で分かります。保存された名前と、メニューの名前を 1 文字ずつ比べます（全角・半角の空白、コロンの種類の違いに注意）。

## 確認

利用者の Premiere で次を見てもらいます。

1. ［ウィンドウ］→［UXP プラグイン］の下に、コマンド名が出ている（出なければ Premiere を再起動し、manifest の書き方を `check.py` で見直す）。
2. パネルを閉じたまま、メニューからコマンドを選ぶ。効果やマーカーなど、目に見える変化が起きる。
3. 【Mac】割り当てたキーを押して、同じことが起きる。Premiere の他の操作と干渉していない。
4. 診断ボタン（パネル）のあと `logs.py` で、コマンドが呼ばれた行と、エラーが無いことを確かめる。

## 戻し方

- 処理の結果は、**取り消し 1 回**（Cmd+Z / Ctrl+Z）で戻ります（`PPM.transact` を使った場合）。
- ショートカット: システム設定の「アプリのショートカット」で該当の行を選んで［−］。
- コマンドそのものを外すときは、`manifest.json` の `entrypoints` と `index.js` の `define` を消して、［Reload］します。

## 使う部品

- `commands`: `PPM.commands.define(id, handler)` と `PPM.commands.table()`。manifest の `commands` に渡す表を返す。
- `ppro-kit`: `PPM.transact` など（雛形に入っている）。
- `ui-kit`: パネル側のボタン。コマンドと同じ関数を呼ぶ。

## 出どころ

- Cut & SRT のショートカットの記録（Premiere 26.3 / macOS、2026-07-16。Mac のメニュー名の完全一致は実機で確認）
- Cut & SRT の導入ガイドと設計書（UXP のコマンドを Premiere の画面から割り当てられない、という記述。実機での確認は無い）
- このキットの形でのコマンドは、Premiere 実機で通していません。Windows の割り当ては未確認です
