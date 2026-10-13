---
id: recipe-clip-slots
title: クリップや効果をコピーして貼る
kind: recipe
tags: [クリップ棚, スロット, コピー, 貼り付け, 複製, localStorage, 効果, キーフレーム, ショートカット, 取り直し]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 選んだクリップを番号つきの棚に保存し、あとで再生ヘッドの位置に貼る。保存は名前・開始・トラック・種類だけ、貼る直前に取り直す。複製の Action は取引の中で作り、取り消しは 1 回
parts: [ppro-kit, commands, ui-kit]
related: [feat-cutsrt-clip-slots, feat-clip-clipboard, feat-cutsrt-fx-slots, feat-effect-shortcut, uc-uxp-copy-keyframes-lost, uc-uxp-keyframe-extra-and-wrapped, uc-uxp-shortcut-commands-not-listed, uc-uxp-get-track-items-args, uc-uxp-action-outside-lock, core-transactions, recipe-commands-shortcuts]
---
## この型で作れるもの

- よく使う素材の組み合わせ（ロゴと効果音、枠つきの映像など）を、番号つきの「棚」に保存し、ワンキーで再生ヘッドの位置に貼る。
- 複数のクリップを選んで保存すれば、トラックの並びとクリップどうしの相対的な位置を保ったまま貼れる。
- 発展: 付いていた効果とキーフレームも一緒に写す（難しいので、最初は「クリップの複製」だけで始めるのを勧めます）。

## 前提

- 雛形は `panel-commands`（メニューのコマンドを足せる）。部品は `ppro-kit` と `commands` が入っている。
- 保存してよいのは**素の値だけ**です。Premiere のクリップのオブジェクト（ハンドル）は寿命が短く、パネルを読み込み直すと使えなくなります。名前・開始位置（ティック）・トラック番号・種類（映像か音声か）だけを書きます。
- 棚の保存先は、パネルの保存領域（`localStorage`）。**読み書きは try/catch で包み**、使えなくても画面は出るようにする（消えることがある、と利用者に伝える）。
- 時間はティック（`ref-ticktime`）。計算は文字列でなく数値にしてから。
- ショートカットは、Premiere の画面からは割り当てられません。パネルを表示している間の数字キー（1〜9 と 0 を棚 1〜10）を入口にし、Cmd・Ctrl・Alt を押しているときは反応させません（`uc-uxp-shortcut-commands-not-listed`）。メニューのコマンドを足せば、Mac ではシステム設定から割り当てられます（`recipe-commands-shortcuts`）。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-commands --name "Clip Slots" --label "クリップ棚"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Clip Slots`、Windows `%USERPROFILE%\PremierePlugins\Clip Slots` です。
2. 画面: 棚を 10 行（番号・内容の要約・［保存］［貼り付け］［消去］）と、折りたたみのログ。
3. **保存**（［保存］）:

   ```js
   const { sequence } = await PPM.getProjectAndSequence();
   const clips = await PPM.getSelectedClips(sequence);   // 選択が空なら「クリップを選んでから」と案内して止める
   slots[n] = clips.map((c) => ({ name: c.name, startTicks: c.startTicks, trackIndex: c.trackIndex, kind: c.kind }));
   ```

   棚の状態を書き換える処理は、現在の状態を受け取って新しい状態を返す**純関数**にして、画面や Premiere から切り離す（Node で試せる）。
4. **貼り付け**（［貼り付け］）:
   1. 棚の各クリップを、ライブのタイムラインから**取り直す**: `await PPM.findClip(sequence, kind, trackIndex, startTicks)`。見つからないものは、理由つきで数えて飛ばす（黙って飛ばさない）。
   2. 取り直せた中でいちばん早い開始位置を基準に、`再生ヘッドの位置 − 基準` をすべてのクリップに同じだけ足す（相対位置が保たれる）。再生ヘッドは `await sequence.getPlayerPosition()`。
   3. **取引の中で**複製の Action を作る:

      ```js
      const editor = ppro.SequenceEditor.getEditor(sequence);
      PPM.transact(project, "棚から貼り付け", (add) => {
        for (const p of plan) add("複製", () => editor.createCloneTrackItemAction(p.item, p.offsetTime, 0, 0, false, false));
      });
      ```

      引数の意味は `createCloneTrackItemAction(trackItem, timeOffset, 映像トラックのずらし, 音声トラックのずらし, alignToVideo, isInsert)`。トラックの番号は 0 始まり。複製が全部失敗したときは、`createInsertProjectItemAction`（素材の挿入）に切り替える方法がありますが、**素材をそのまま挿入すると元の効果が付かない**ので、効果を付けたいときは複製を使います（`uc-uxp-copy-keyframes-lost`）。
   4. 完了の文に「◯ 個貼りました（取り消しは 1 回）」と書く。
5. （発展）効果とキーフレームも写す: 複製（クローン）は効果を引き継ぎます。素材の挿入で貼ったときだけ、保存しておいた効果を別の取引で適用します。キーフレームは「時刻・値・補間」の列で持ちます。**足す取引と消す取引は分ける**（同じ取引で足したキーは、単独では消せません。`uc-uxp-keyframe-extra-and-wrapped`）。
6. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンのあと `logs.py` で結果を読む。

## 確認

利用者の Premiere で、**テスト用の別シーケンス**に素材を置いて試してもらいます。

1. ロゴと効果音など 2〜3 個を選び、棚 1 に［保存］。棚の表示に内容の要約が出る。
2. 再生ヘッドを別の位置に動かして［貼り付け］。クリップがその位置から、元と同じトラックの並び・同じ間隔で並ぶ。
3. 取り消しを 1 回押すと、貼った分が全部消える。
4. パネルを読み込み直して（［Reload］）も、棚の内容が残っている。貼り付けも動く。
5. 元のクリップを削除してから貼ろうとすると、「元のクリップが見つかりません」と理由つきで案内される（落ちない）。
6. （効果を写す場合）貼ったクリップの効果コントロールに、元と同じ効果とキーが付いている。

## 戻し方

- 貼り付けは 1 つの取引なので、**取り消し 1 回**（Cmd+Z / Ctrl+Z）で全部戻ります。効果を別の取引で足した場合は、**もう 1 回**押します（取引の数だけ）。
- 棚の内容を消す: ［消去］。保存領域の全消去は、棚の画面の設定に用意するか、Premiere を閉じたあとでプラグインのデータフォルダを消す。
- 別のシーケンスへ貼る: 元のクリップを取り直せないので、素材の ID と素材の中の始点・終点を保存しておき、素材を挿入してから始点・終点を設定する方法になります。Cut & SRT では計画までで、実機で確かめていないため、最初は「同じシーケンスの中」で使うと案内します。

## 使う部品

- `ppro-kit`: `PPM.getSelectedClips`・`PPM.findClip`・`PPM.transact`・`PPM.timeFromTicks`
- `commands`: メニューのコマンド（棚 1〜10 の貼り付け）
- `ui-kit`: 棚の行・ログの折りたたみ

## 出どころ

- Cut & SRT のクリップ棚の設計書と開発記録（2026-07〜08）、小型プラグイン clip-clipboard のコードの説明と修正（2026-07-06）。保存領域への保存は実機で観測済み。同じシーケンス内の貼り付けは、実機の利用を前提に作り直したもの
- 別シーケンスへの貼り付けと再起動後の復元は、計画書の段階で、実機では未確認です
