---
id: recipe-export-automation
title: 決まった設定で書き出す
kind: recipe
tags: [書き出し, EncoderManager, exportSequence, Media Encoder, AME, プリセット, epr, H.265, 作業エリア, キュー]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: アクティブなシーケンスを、書き出しプリセット（.epr）を指定して Adobe Media Encoder のキューへ送る。H.265 のプログラム書き出しは意図的に無効、作業エリアバーが出ていると In/Out が無視される。実機での確認は少ない
parts: [ppro-kit, ui-kit, probe]
related: [core-api-patterns, core-versions, core-safety, uc-uxp-export-frame-not-written, core-capabilities]
---
## この型で作れるもの

「ボタン 1 回で、いつもの設定のとおりにシーケンスを書き出す（または Media Encoder のキューに入れる）プラグイン」です。YouTube 用・確認用の軽い版、のように、プリセットを切り替える形にもできます。

この型は、キットの部品にまだ専用の道具がありません。`EncoderManager` を直接呼ぶ書き方で作ります。実機で通した記録が薄いため、status は未確認（unverified）です。使うときは「未確認です」と伝え、診断ボタンと 1 回の試し書き出しで確かめてから採用します。

## 前提

- 雛形は `panel`（`ppro-kit` と診断ボタンが入ります）。
- 書き出しは **Adobe Media Encoder（AME）経由**です。`ppro.EncoderManager` の `exportSequence(シーケンス, 書き出しの種類, 出力ファイルのパス, プリセットファイルのパス, 全体か)`（Premiere 25.6 以降、種類は `ppro.Constants.ExportType` の `IMMEDIATELY` / `QUEUE_TO_AME` / `QUEUE_TO_APP`）。
- 呼び出しの形は、公式の文書では `EncoderManager.getManager()` で取ってから呼ぶ書き方です。Cut & SRT の実装は、取得したものから呼ぶ形で組まれています。どちらで通るかは版で違う可能性があるので、診断ボタンで「`EncoderManager` と `exportSequence` が存在するか」を先に調べます。
- 列挙値は存在を確かめてから使い、無ければ生の値に落とします（`QUEUE_TO_AME` が無ければ 1、`IMMEDIATELY` が無ければ 0。Cut & SRT がこの形）。
- **H.265（HEVC）のプログラム書き出しは、Adobe が意図的に無効にしています**（Adobe 公式フォーラムの回答、2026-06）。H.265 のプリセットを指定して失敗しても、プラグイン側の誤りではありません。H.264 や ProRes など、別のプリセットを案内します。
- **作業エリアバーが表示されていると、シーケンスの In/Out が無視される**既知の問題があります（Adobe の追跡番号あり）。範囲を指定して書き出したいときは、作業エリアバーを消してから試してもらいます。
- プリセットなしの書き出しは、書き出しモードの開閉の状態に挙動が左右される報告があります。プリセット（`.epr`）は必ず指定する形にします。
- 利用者のファイルを書き換える操作なので、出力先に同じ名前のファイルがあれば上書きしない（別名にする）か、確認します（`core-safety`）。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Export Preset" --label "決まった設定で書き出し"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Export Preset`、Windows `%USERPROFILE%\PremierePlugins\Export Preset` です。
2. 診断ボタンの調べる項目に、使う API を足す（`index.js` の起動の所で `PPM.probe.run(["EncoderManager.exportSequence", "EncoderManager.isAMEInstalled"])` のように）。
3. `index.html` に、プリセットのパス（`.epr`）と出力先のフォルダの入力欄、［AME のキューに入れる］ボタンを置く。フォルダの選択は `require("uxp").storage.localFileSystem.getFolder()`（キャンセルで偽の値が返るので、その場合は何もしない）。
4. `onRun`:
   1. `const { project, sequence } = await PPM.getProjectAndSequence();`
   2. 出力のファイル名を決める（シーケンス名と日時。使えない文字を除く）。同名があれば別名にする。
   3. `ppro.EncoderManager` を取り、`isAMEInstalled` が使える版ならそれで AME の有無を確かめる。無ければ「Media Encoder が見つかりません」と止める。
   4. 種類を決める（キューなら `QUEUE_TO_AME`）。
   5. `let ok = manager.exportSequence(sequence, 種類, 出力のパス, プリセットのパス, true);` 戻りが Promise なら `await` する。偽ならエラー（症状・理由・次の一手の 3 点）にする。
   6. 完了の文に「キューに入れました。書き出しは Media Encoder で進みます」と書く。**書き出しの完了ではありません**。完了の通知は `EncoderManager` のイベント（`EVENT_RENDER_COMPLETE` など）で受けられますが、この型では使っていません。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンで `exportSequence` が found になっているかを、`logs.py` で読む。

## 確認

利用者の Premiere で、**短いシーケンス（10 秒ほど）**で試してもらいます。

1. 診断で `EncoderManager` / `exportSequence` が「ある」と出る。無い場合は、その版では使えないので、手で書き出す案内に切り替える。
2. 押すと、Media Encoder が起動し、キューに 1 件入る。
3. 書き出しが終わったら、出力先に指定した名前のファイルができている。
4. ファイルを再生して、長さ・画質・音が設定どおり。
5. 作業エリアバーを出した状態で試した場合は、その範囲だけが書き出されるのか、全体が書き出されるのかを確認して、結果を記録する。

## 戻し方

プロジェクトは変わりません（取り消しは要りません）。次のどちらかで戻します。

- Media Encoder のキューから該当の項目を取り除く（書き出し前なら）。
- 書き出されたファイルを、出力先のフォルダから削除する（書き出し後）。

## 使う部品

- `ppro-kit`: `PPM.getProjectAndSequence`、`PPM.err`（原因つきのエラー）
- `probe`: 使う API の有無の確認
- 専用の部品はありません。`EncoderManager` は直接呼びます。

## 出どころ

- Cut & SRT の書き出しの実装（`exportSequence` を AME のキューまたは即時で呼ぶ形。実機での通し確認の記録は見つかっていません）
- Adobe 公式の API リファレンス（`EncoderManager`、26.3 での `launchEncoder`・`startBatchEncode` の追加）
- Adobe 公式フォーラムの回答（H.265 のプログラム書き出しが意図的に無効、2026-06。作業エリアバーで In/Out が無視される問題）
