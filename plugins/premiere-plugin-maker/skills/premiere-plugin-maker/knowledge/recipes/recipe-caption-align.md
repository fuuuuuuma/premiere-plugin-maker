---
id: recipe-caption-align
title: テロップをカットの境目にそろえる
kind: recipe
tags: [整列, テロップ, 字幕, カット点, 許容コマ数, createSetStartAction, createSetEndAction, グラフィック, 取引]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: テロップ（グラフィック）の開始と終了を、別のトラックのクリップの境目に、許容コマ数の内で寄せる。グラフィックには setIn/setOut を使わず、開始側と終了側の境目を別の一覧にし、全体を 1 つの取引にする
parts: [ppro-kit, ui-kit]
related: [feat-caption-align, feat-cutsrt-align, ref-ticktime, uc-uxp-ticktime-ticks-zero, uc-uxp-get-track-items-args, uc-uxp-action-outside-lock, uc-uxp-init-tdz, uc-uxp-require-relative, core-transactions, recipe-silence-cut]
---
## この型で作れるもの

無音カットのあとに字幕を置くと、テロップの端が映像のカット点から数コマずれます。この型は、テロップのクリップの開始と終了を、基準にしたトラックのクリップの境目へ、**許容コマ数の内で**自動で寄せるパネルです。基準トラックは映像でも音声でも選べます。

## 前提

- 雛形は `panel`（最小の形で足ります。サーバーは要りません）。
- テロップは**グラフィックのクリップ**（文字のクリップ）としてタイムラインに置かれていること。
- 基準のトラックには、境目になるクリップが並んでいること。
- シーケンスのフレームレートが取れること。**取れなかったら黙って 30 と見なさず、止めて理由を出す**（コマ数をティックに直す計算が狂うため）。`await PPM.getFrameRate(sequence)` は `{ fps, detected }` を返すので、`detected` が false なら止めます。
- 利用者のテロップの位置を変える処理です。実行の前に、対象のトラックと許容コマ数を画面で確認させ、プロジェクトの保存を勧めます。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Caption Align" --label "テロップ整列"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Caption Align`、Windows `%USERPROFILE%\PremierePlugins\Caption Align` です。
2. 画面は縦に 3 段: 基準トラック（種類と番号）・テロップのトラック番号・許容コマ数（`−` `＋` で増減）。主ボタンと、結果の「そろえた／飛ばした／失敗した」の 3 つの数、折りたたみのログ。トラック番号は画面では 1 始まり、API には 0 始まりで渡します。
3. 処理の順（`onRun`）:
   1. `const { project, sequence } = await PPM.getProjectAndSequence();` と `const fr = await PPM.getFrameRate(sequence);`（`fr.detected` が false なら止める。コマ数 × `PPM.TICKS_PER_SECOND` ÷ `fr.fps` でティックに直す）。
   2. 基準トラックの全クリップ（`await PPM.listTrackClips(sequence, kind, index)`）から境目を集める。**開始側の境目（クリップの開始）と終了側の境目（クリップの終わり）は、別々の一覧にする。** 1 本にまとめると、終了が次のクリップの開始に吸い寄せられて、2 コマずれる事例があります。
   3. テロップの各クリップについて、開始は開始側の一覧から、終了は終了側の一覧から、許容コマ数の内でいちばん近い点を探す。近い境目どうしが重ならないようにする（テロップの長さが 0 以下になる動かし方はしない）。この「探す」部分は**純関数**にして、画面や Premiere から切り離す。
   4. 全部の変更を **1 つの取引**にまとめる。

      ```js
      PPM.transact(project, "テロップを整列", (add) => {
        for (const m of moves) {
          if (m.newStart) add("開始", () => m.item.createSetStartAction(m.newStart));
          if (m.newEnd)   add("終了", () => m.item.createSetEndAction(m.newEnd));
        }
      });
      ```

      **グラフィックのクリップには `createSetStartAction` と `createSetEndAction` だけを使い、入点・出点（`setIn`/`setOut`）には触れません。** グラフィックの入点は 0 付近の小さな値しか持たず、早い方向にずらすと負の時刻になり、カット点を数コマ飛び越えて反対側に着地した事例があります。映像クリップで通った書き方を、そのまま写さないでください。
   5. 新しい位置の TickTime は、境目のクリップから取った TickTime をそのまま使う。比率から作り直すと数百ティックの誤差が出る。引き算は必ず「大きい方 − 小さい方」にする。
   6. 適用後、各クリップの位置を読み戻し、期待した位置との差をログに出す（検証ログ。差が 0 でなければ警告）。
4. 初期化の全体を try/catch で包み、失敗は画面のログ欄に出す。小さな関数を別の JS ファイルに分けない（UXP の相対 `require` は使えず、読み込み順も不安定。1 つの `index.js` に置く）。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンのあと `logs.py` で、検証ログを読む。

## 確認

利用者の Premiere で次を見てもらいます。**テスト用のシーケンス**（カット点が数か所あり、テロップが数個）で試します。

1. 基準トラックと許容コマ数（例 10）を入れて押す。結果の数字が「そろえた N・飛ばした M・失敗した 0」のように出る。
2. テロップの端の近くまで再生ヘッドを動かし、矢印キーでコマ送りする。テロップの開始・終了が、基準のカット点とぴったり同じコマに揃っている。
3. 許容コマ数の外にあったテロップは動いていない（「飛ばした」に数えられている）。
4. 検証ログ（`logs.py`）の「期待との差」が、すべて 0。
5. シーケンスのフレームレートを 30 以外（24・60 など）にしても、揃う。フレームレートが取れないときは、止まって理由が出る。

## 戻し方

全部を 1 つの取引にしているので、**取り消し 1 回**（Cmd+Z / Ctrl+Z）でテロップの位置が元に戻ります。元に戻らなかったときは、実行の前にプロジェクトを保存しておいたものを開き直します。

## 使う部品

- `ppro-kit`: `PPM.getProjectAndSequence`・`PPM.listTrackClips`・`PPM.describeClip`・`PPM.getFrameRate`・`PPM.transact`・`PPM.ticksOf`
- `ui-kit`: ステッパー・結果の数・ログの折りたたみ

## 出どころ

- 小型プラグイン caption-align の引き継ぎ文書と修正履歴（版 1.0.0〜1.0.6、2026-04-29）。整列の処理は、Mac の Premiere で 7 件・許容 10 コマの実機検証に通っている
- Cut & SRT の整列タブの記録。Windows の実機では整列が動いた報告がある
- このキットの形（`ppro-kit` を使う書き方）は、Premiere 実機で通していません
