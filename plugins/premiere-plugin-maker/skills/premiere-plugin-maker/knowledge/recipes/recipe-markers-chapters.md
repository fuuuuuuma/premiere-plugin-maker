---
id: recipe-markers-chapters
title: マーカーを打つ・チャプターの一覧を作る
kind: recipe
tags: [マーカー, チャプター, 概要欄, YouTube, タイムスタンプ, createAddMarkerAction, パネル]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: シーケンスにマーカーをまとめて打ち、同じ一覧を YouTube の概要欄用の「0:00 題」の形で出す。マーカーの追加は取引 1 回・取り消し 1 回。色の指定は実機で確かめていない
parts: [ppro-kit, ui-kit]
related: [core-api-patterns, core-transactions, ref-ticktime, core-capabilities, feat-premiere-agent-kit]
---
## この型で作れるもの

- 入力欄に「秒（または 分:秒）と題」を並べて押すと、シーケンスにマーカーが一度に打たれる。
- 今あるマーカーを読み出して、YouTube の概要欄に貼れる `0:00 題` の一覧にする。

チャプターの題を AI が考える場合は、パネルは「題の案をもらって打つ」役に徹し、案の作成は別（AI のスキルや MCP）に任せると、小さく作れます（`feat-premiere-agent-kit` にチャプター用の手順があります）。

## 前提

- 雛形は `panel`。部品は雛形に入っている `ppro-kit`（`PPM.addMarkers`）で足ります。
- マーカーは **シーケンスの**マーカーです（クリップのマーカーではありません）。
- 時刻は秒で渡します（`PPM.addMarkers` が TickTime に直します）。マーカーの種類は、列挙値が無い版でも動くよう、ppro-kit が `"Comment"` に落とします。
- YouTube のチャプターの決まり: 1 行目は `0:00`、3 つ以上、各チャプターは 10 秒以上。一覧を作るときに、この条件を満たしているか画面で知らせます（YouTube 側の仕様は変わることがあるので、公開前に利用者が確かめます）。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Chapter Markers" --label "チャプター"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Chapter Markers`、Windows `%USERPROFILE%\PremierePlugins\Chapter Markers` です。
2. `index.html` に複数行の入力欄（`id="list"`）と、「マーカーを打つ」「概要欄用の一覧を作る」の 2 つのボタンを置く。
3. 「打つ」の `onRun`:
   - 入力を 1 行ずつ読み、`{ seconds, name }` の配列にする。`1:23 はじめに` と `83 はじめに` の両方を受ける。読めない行は、行番号つきで画面に出して止める（黙って飛ばさない）。
   - `const { project, sequence } = await PPM.getProjectAndSequence();`
   - 既存のマーカーと同じ時刻・同じ名前が無いか調べる（二重に打たない）。調べ方は `await ppro.Markers.getMarkers(sequence)` で取った一覧を読む。
   - `await PPM.addMarkers(project, sequence, markers)`。全部を **1 つの取引**で足します。
   - 完了の文に「◯ 個打ちました（取り消しは 1 回）」と書く。
4. 「一覧を作る」のボタン: 入力の配列から、秒を `分:秒`（1 時間を超えたら `時:分:秒`）に直して `0:00 はじめに` の形に並べ、結果の欄に出す。コピーは `navigator.clipboard.writeText`（無ければ `clipboard.setContent`）。先頭が 0:00 でない、3 つ未満、間が 10 秒未満、のいずれかなら、その旨を添える。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   `check.py` が誤り 0 件になってから、UXP Developer Tools で［Load］。診断ボタンのあと `logs.py` で結果を読む。

## 確認

利用者の Premiere で次を見てもらいます。

1. 3 行ほど入れて押す。タイムラインの上の目盛りの帯に、マーカーが 3 つ出る。
2. 再生ヘッドをマーカーに合わせて、位置が入力した時刻と合っている（コマ単位のずれは、シーケンスのフレームレートによる丸めです）。
3. マーカーパネルを開き、名前（題）が入力どおり。
4. もう一度同じ入力で押しても、マーカーが倍にならない。
5. 「一覧を作る」の出力が、`0:00 …` で始まり、時刻が昇順である。

## 戻し方

マーカーの追加は取引 1 回なので、取り消し（Cmd+Z / Ctrl+Z）は **1 回**です。打つ個数が多くても同じです。マーカーを選んで消す操作は、Premiere の画面（マーカーパネル）から行います。

## 使う部品

- `ppro-kit`: `PPM.addMarkers`・`PPM.getProjectAndSequence`・`PPM.transact`・`PPM.time`
- `ui-kit`: 複数行の入力、結果の表示

## 注意（確かめていないこと）

- マーカーの **色**を付ける API は、実機で確かめていません。色は、マーカーを足す取引のあとに実体を取り直して、別の取引で付ける形になる見込みです（足した直後のものは設定を持たない、という効果と同じ型）。使う前に診断ボタンで存在を確かめます。26.5 では色の名前の綴り（`MAGNETA` → `MAGENTA`）が変わっています。
- クリップのマーカーや、マーカーの一括削除は、この型では扱いません。

## 出どころ

- Cut & SRT の API の使用記録（`createAddMarkerAction` の呼び出し。Mac の Premiere 26.3〜26.5）
- premiere-agent-kit のチャプターの手順（題は 12 字以内・体言止め、実行前に案の表を見せる、概要欄用の一覧も返す）
- Adobe 公式の API リファレンスと 26.5 の変更履歴（マーカーの色の綴り）
