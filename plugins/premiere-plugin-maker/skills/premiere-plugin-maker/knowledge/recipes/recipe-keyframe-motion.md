---
id: recipe-keyframe-motion
title: キーで動きを付ける（ズーム・スライド・フェード）
kind: recipe
tags: [キーフレーム, ズーム, スライド, フェード, 補間, 焼き込み, 取り消し, モーション, スケール]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 選んだクリップのスケール・位置・不透明度に、時刻と値のキーを打つ。補間は 1 コマごとの直線キーに焼き込むので、取引 1 回・取り消し 1 回で済む
parts: [ppro-kit, motion-bake, ui-kit]
related: [ref-keyframe-interpolation, core-transactions, uc-uxp-interp-same-transaction, uc-uxp-keyframe-extra-and-wrapped, uc-mogrt-addkey-time-base, uc-uxp-keyframe-curve-overshoot, feat-ed-motion]
---
## この型で作れるもの

「選んだ映像クリップを、ゆっくり 100% から 110% に拡大する」「左から滑り込む」「ふわっと現れる」といった動きを、ボタン 1 回で付けるプラグインです。動きは、時刻と値の組（キー）を並べたものとして表します。

完成サンプル `<SKILL>/examples/zoom-button` が、この型そのものです（開始の大きさ・終了の大きさ・秒数を入力して押すと、ゆっくりズームが付きます）。

## 前提

- 雛形は `panel`、部品は `motion-bake`（雛形に入る `ppro-kit` の上に乗ります）。
- Premiere の補間（イーズ）は、同じ取引の中では設定できません（無言で効きません）。そこで `motion-bake` が、イーズの曲線を **1 コマごとの直線のキー**に変換（焼き込み）します。この方式なら取引 1 回で終わり、取り消しも 1 回です。
- キーの時刻は **素材時間**（クリップの入点からの位置）で渡します。タイムライン上の時刻で渡すと、入点の分だけずれます（約 1 時間ずれた事例があります）。
- フレームレートはシーケンスから読みます。読めなかったときに 30 を詰めません（警告を出して、既定で焼くなら理由を表示します）。

## 手順

1. 作業フォルダを作って、部品を足す。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン"
   python3 <SKILL>/scripts/add_part.py motion-bake --project <作業フォルダ>
   ```

   Windows は `py -3` に置き換えます。作業フォルダの既定の場所は Mac `~/PremierePlugins/Zoom Button`、Windows `%USERPROFILE%\PremierePlugins\Zoom Button` です。
2. `index.html` に入力欄（開始・終了の大きさ、秒数）とボタンを足す。入力は `PPM.ui.numberValue($("from"), 100)` で読む。
3. `index.js` の `onRun` に書く。サンプルの流れは次の 5 つです。
   1. 選んだ映像クリップを取る（`PPM.getSelectedClips`）。0 本なら止める。
   2. キーの計画を作る: `PPM.motion.bakeTrack([{ t: 0, value: 100, interp: "bezier" }, { t: 2, value: 110, interp: "linear" }], 1 / fps)`。`t` は秒、`interp` は `linear`・`bezier`・`hold`。
   3. 動かす項目を探す（取引の前）: `PPM.findParam(c.item, ["AE.ADBE Motion"], ["Scale", "スケール"])`。位置は `["Position", "位置"]`、不透明度は不透明度の部品（`AE.ADBE Opacity`）で探す。入点も `PPM.secondsOf(await c.item.getInPoint())` で先に読む。
   4. 1 つの取引で打つ: `PPM.transact(project, "ゆっくりズームを付ける", (add) => { PPM.keyframeActions(add, 項目, 入点, キー列); })`。
   5. 完了の文に「取り消しは 1 回」と書く。
4. 位置を動かすときは、値を 0〜1 の正規化座標の `[x, y]` で渡す（`PPM.toValue` が `PointF` に直します）。スライドが設計の約 2 倍行き過ぎる事例があるので、イーズの種類は短い動きから試します（`ref-keyframe-interpolation`）。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   ```

   誤り 0 件を確かめてから、UXP Developer Tools の［Add Plugin］→［Load］。診断ボタンのあと `python3 <SKILL>/scripts/logs.py --project <作業フォルダ>` で結果を読む。

## 確認

利用者の Premiere で次を見てもらいます。

1. 映像クリップを 1 本選んで押す。クリップのエフェクトコントロールの「モーション」→「スケール」に、キーを示す印が並ぶ（1 コマごとなので、細かく並ぶのが正しい姿です）。
2. 再生ヘッドを動かして、開始が設定した値、終わりが設定した値になっている。
3. 再生して、動きが滑らかで、始まりと終わりで跳ねない。
4. 入点が 0 でないクリップ（前を切ったクリップ）でも同じ動きになる。キーがクリップの途中から始まっていたり、余分なキーが 1 つ増えていたりしない。
5. 複数のクリップを選んだときも、全部に付く。

見た目を確かめるときは、`PPM.exportFrame` で動きの始まりと終わりのコマを書き出して比べます。

## 戻し方

取り消し（Cmd+Z / Ctrl+Z）は **1 回**です。選んだクリップが何本でも同じです。ただし、そのクリップに対象の項目が最初から無く、効果を新しく足してから打つ作りにした場合は 2 回になります（`recipe-batch-effect` を参照）。モーションの「スケール」「位置」は最初からあるので、この雛形の例では 1 回です。

## 使う部品

- `ppro-kit`: `PPM.keyframeActions`（キーを消す → 時間変化をオン → キーを打つ → 入点より前の余分なキーを消す、までを 1 つにした型）・`PPM.findParam`・`PPM.transact`・`PPM.getFrameRate`
- `motion-bake`: `PPM.motion.bakeTrack`（曲線を 1 コマごとの直線に変換）。エフェクトプリセット（`.prfpset`）の生成も持っています。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09）: 補間は同じ取引で効かないこと、キーの時刻が素材時間であること、余分なキーの扱い、取り消しの回数（`feat-ed-motion`、`uc-uxp-interp-same-transaction`、`uc-uxp-keyframe-extra-and-wrapped`）
- Premiere の補間の実測式（`ref-keyframe-interpolation`）
- 完成サンプル `zoom-button`（このキットが雛形と部品から生成し、`check.py` を通したもの。Premiere の実機で通した記録はまだありません）
