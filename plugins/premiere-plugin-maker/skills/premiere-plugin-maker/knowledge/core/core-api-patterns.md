---
id: core-api-patterns
title: Premiere の API の正しい使い方の型（用途別）
kind: core
tags: [API, premierepro, シーケンス, 選択, getTrackItems, マーカー, 書き出し, 効果, MOGRT, TickTime, localStorage]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 読み取りは await、変更は取引の中。getTrackItems は引数 2 つ、選択は getSelection を使い、TickTime は ticksNumber から読む。公式の文書にあっても実装済みとは限らないので存在を確かめてから呼ぶ
parts: [ppro-kit]
related: [core-transactions, core-verification, core-versions, ref-ticktime, ref-mogrt]
---
## 要点

- Premiere の機能は `const ppro = require("premierepro")` で取る（`require("premiere")` は存在しない）。ブラウザの下見で落ちないよう try/catch で包む。
- 読み取りは `await`。変更は Action を取引の中で作る（`core-transactions`）。
- よく間違える 3 つ: `track.getTrackItems(種類, 空を含むか)` は引数が必須、選択は `sequence.getSelection()` で取り `new TrackItemSelection()` を作らない、時刻は `ticksNumber` から読む。
- クリップのハンドルは長く持たない。使う直前に取り直す。保存するのは名前・開始位置・トラック番号などの情報だけ。
- 「公式の文書にある」は「この Premiere に実装されている」ではない。存在を確かめ、無ければ理由つきで止める。

## 詳しく

### プロジェクト・シーケンス・タイムラインを読む

```js
const project  = await ppro.Project.getActiveProject();
const sequence = await project.getActiveSequence();      // 無ければ null。「アクティブなシーケンスがありません」と言う
const n = await sequence.getVideoTrackCount();
const track = await sequence.getVideoTrack(0);           // トラック番号は 0 始まり
const clips = await track.getTrackItems(1, false);       // 1 は「クリップ」。引数 2 つが必須
```

- `getTrackItems` を引数なしで呼ぶと、今の版では空配列か例外になる。種類は `ppro.Constants.TrackItemType.CLIP`（取れなければ 1）。別クラスの `TrackItemSelection.getTrackItems()` は引数なしで正しい。混同しない。
- クリップ名・開始・終了・入点・出点は `getName()` `getStartTime()` `getEndTime()` `getInPoint()` `getOutPoint()`。
- `getMediaType()` は Premiere 26 系では Guid を返し、`=== 1` のような比較は常に偽になる。映像か音声かは、クラスの名前（`VideoClipTrackItem` / `AudioClipTrackItem`）で見分ける（`check.py` の J015）。
- フレームレートは `sequence.getSettings()` の `getVideoFrameRate()`（26.2 以降）で取る。`settings.videoFrameRate` のようなプロパティは存在せず、黙って `undefined` になって 30fps に落ちる事故が実際に起きた。取れなかったら 30 を詰めずに「不明」を返す。

### 選択

- `const sel = await sequence.getSelection(); const items = await sel.getTrackItems();` で選択中のクリップを取る。
- 選択を変えるときも、この `sel` に `addItem` / `removeItem` して `sequence.setSelection(sel)` に渡す。`new ppro.TrackItemSelection()` は 26.3 で後続の呼び出しが `Connection to object lost` になるため使わない（`check.py` の J004）。
- `setSelection` は 26.3 から同期で、成功の boolean を返す。古い版では Promise の可能性があるので、戻りが Promise でも通る書き方にする。
- プロジェクトパネルの選択は `ppro.ProjectUtils.getSelection(project)`（25.6 以降）。

### クリップの操作

`SequenceEditor.getEditor(sequence)` から、挿入・上書き・複製・削除の Action を作る。

| やりたいこと | 呼び出し | 気を付けること |
|---|---|---|
| 素材を挿入 | `createInsertProjectItemAction(item, 時刻, 映像トラック, 音声トラック, false)` | 挿入はリップル。既存クリップが後ろへ押し出される |
| 素材を上書き | `createOverwriteItemAction(...)` | 存在を確かめてから。無ければ挿入に切り替える |
| 複製 | `createCloneTrackItemAction(...)` | `isInsert=true` で後続の音声クリップの長さが 0 になった報告（26.3.2）。1 クリップで試してから |
| 削除 | `createRemoveItemsAction(選択, ripple, 種類, shiftOverLapping)` | 26.3 は 4 引数が必須（2 引数以下は `Not Enough Parameters`） |
| 開始・終了の変更 | `item.createSetStartAction` / `createSetEndAction` | 文字や図形のグラフィックのクリップには入点・出点（`createSetInPointAction`）を呼ばず、開始と終了だけにする。負の時刻の事故がある |
| 有効・無効 | `createSetDisabledAction` | |
| 移動 | `createMoveAction(TickTime)` | 説明が曖昧。初回は 1 クリップで確かめる |

### マーカー

`const markers = await ppro.Markers.getMarkers(sequence)` で取り、`markers.createAddMarkerAction(名前, 種類, 開始, 長さ, コメント)` で追加する（取引の中）。長さ 0 で 1 点のマーカー。色は 26.5 で `MAGNETA` が非推奨になり `MAGENTA` へ。色の設定 API は実機未検証なので、存在を確かめてから使う。

### 書き出し

- コマの画像: `ppro.Exporter.exportSequenceFrame(sequence, 時刻, ファイル名, 保存先, 幅, 高さ)`。**呼び出しが戻っても、画像はまだ書き終わっていないことがある**。ファイルができるのを待ってから読む。描画が欠けたら、プレイヘッドをその時刻に置いて出し直す。
- シーケンス: `ppro.EncoderManager.getManager().exportSequence(...)`（Adobe Media Encoder 経由）。
- FCP XML・OTIO: `ppro.ProjectConverter.exportAsFinalCutProXML(sequence, パス, true)`（26.2 以降）。

### プロジェクトの項目とビン

`project.getRootItem()` から `getItems()` をたどる。取り込みは `project.importFiles([パス], true, 取り込み先のビン, false)`（取引の外）。ビンの作成は `FolderItem.createBinAction`（取引の中。作ったビンは戻らないので名前で探し直す）。

### 効果とキーフレーム

```js
const filter = await ppro.VideoFilterFactory.createComponent("AE.ADBE Geometry2"); // 取引の外
const chain  = await item.getComponentChain();
```

- 効果は matchName（言語に依存しない内部名）で探す。設定項目（パラメータ）は表示名で探すため、日本語と英語の両方を候補に並べる（例: 「位置」と `Position`）。
- 値は `param.createKeyframe(値)` で作る。位置は `new ppro.PointF(x, y)`（0〜1 の正規化座標）。読み取った値は `{ value: 値 }` で 1〜2 段包まれていることがある。
- Premiere のオブジェクト（`PointF` など）は JSON にできない。`localStorage` に保存するときは `{x, y}` の素の形に直す。

### トランジション

`ppro.TransitionFactory.createVideoTransition(内部名)` と `new ppro.AddTransitionOptions()` で作り、`item.createAddVideoTransitionAction(...)` で足す。長さは ticks（`core-transactions` の T9）。

### MOGRT

`editor.insertMogrtFromPath(パス, 時刻, 映像トラック(0 始まり), 音声トラック)`。取引に入れられない（T10）。挿入前に重なりを調べ、挿入後に実際に入ったトラックを確かめる（`ref-mogrt`）。

### UXP の host・ファイル・クリップボード・保存・ネットワーク

- `require("uxp").host` に `name` / `version`。`require("uxp").versions.uxp` で UXP の版。
- ファイル: 絶対パスは `require("fs")`（`localFileSystem` が `fullAccess` のとき）。フォルダの選択は `storage.localFileSystem.getFolder()`（キャンセルで偽の値）。プラグイン同梱は `plugin:/`、書き込める置き場は `getDataFolder()`（`plugin-data:/`）。Windows の絶対パスは `file:///C:/...` の形に直す。
- クリップボード: `navigator.clipboard.writeText`。無ければ `clipboard.setContent({"text/plain": 文})`。
- 保存: `localStorage` は try/catch で包み、保存できなくても機能を生かす。
- ネットワーク: `fetch` は manifest の権限が要る（`core-manifest-permissions`）。手元のサーバーへは `network.domains: "all"`。

### TickTime（時刻）

1 秒 ＝ 254016000000 ticks。`TickTime.createWithSeconds(秒)`、`createWithTicks("文字列")`。読むときは **`ticksNumber`（数値）を先に**、無ければ `ticks`（文字列）、最後に `seconds`。`ticks` を直接信用しない。詳しくは `ref-ticktime`。

### 存在を確かめてから呼ぶ

```js
if (typeof sequence.setInPoint !== "function") {
  throw new Error("この Premiere には setInPoint がありません（症状・なぜ・次の一手）");
}
```

列挙値も `X.CLIP !== undefined ? X.CLIP : 1` のように守る。エラーの文は「症状 ／ なぜ ／ 次の一手」の 3 点を入れる。

### 記録が割れている所と、部品の選んだ側

| 話題 | 記録 A | 記録 B | 部品（ppro-kit）の選択 |
|---|---|---|---|
| `TickTime.ticks` | 実機（26.3）で常に 0 を返した。`ticksNumber` が正 | 別の機能（26.5）では `ticks` を文字列として比較して動いていた | `ticksNumber` を先頭にした防御の連鎖 |
| `insertMogrtFromPath` は重なる区間を上書きするか | する前提（図形の機能では実証、帯のテロップでも潰す事例） | 実際に使うと元のクリップが残り上書きされなかった（実機報告） | どちらにも賭けず、挿入前に重なりを調べて止める |
| `Sequence.setInPoint` / `setOutPoint` | 公式の文書に無い（再調査） | 存在ガードつきで呼ぶ実装がある | 使わない。範囲指定は別の手段にし、使うなら存在を確かめる |
| 選択オブジェクトの作り方 | 「新規作成して使える」と書いたコメント（古い） | 26.3 で `Connection to object lost`（新しい） | `getSelection()` を再利用する側 |

## やってはいけないこと

- `getTrackItems()` を引数なしで呼ぶ。
- `new ppro.TrackItemSelection()` を作る。
- `settings.videoFrameRate` のようなプロパティを読む。メソッドで取る。
- 取得に失敗したフレームレートを 30 で埋めて先へ進める。
- `getMediaType()` の戻りを数値や文字列と比べる。
- クリップのハンドルを保存して、後で使い回す。
- 公式の文書にあるだけの API を、確かめずに「動く」と言う。

## 出どころ

- Cut & SRT（v0.14.0）の API の使用記録（実機で確かめた箇所と、公式文書だけの箇所を区別して集めた）
- 小型 UXP プラグイン 4 本と Effect & Design の補助プラグインの実機の記録
- Adobe 公式の API リファレンス、型定義（`@adobe/premierepro`）、公式サンプル
- Adobe 公式フォーラムの 26.3 / 26.5 の API 更新の投稿
- 実機で確かめた範囲は主に Mac の 26.3〜26.5。Windows の実機での API 検証は少ない
