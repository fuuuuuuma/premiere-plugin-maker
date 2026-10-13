---
id: recipe-import-bins
title: 素材のフォルダを読み込んでビンに整理する
kind: recipe
tags: [取り込み, ビン, importFiles, createBinAction, フォルダ, 素材, 整理, プロジェクトパネル]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 選んだフォルダの素材を project.importFiles で取り込み、種類ごとのビンに整理する。ビンを作る Action はビンを返さないので、名前で探し直す。ビンの作成は実機で確かめていない
parts: [ppro-kit, ui-kit, probe]
related: [core-api-patterns, core-transactions, feat-cutsrt-assets, core-safety, platform-cross]
---
## この型で作れるもの

「撮影素材のフォルダを選ぶと、映像・音声・画像などの種類ごとにビン（プロジェクトパネルのフォルダ）を作り、そこへ取り込むボタン」です。毎回の案件で同じ整理をする人向けです。

## 前提

- 雛形は `panel`。専用の部品はなく、`ppro-kit` と UXP の `fs` で組みます。
- フォルダの中を読むには、manifest の `localFileSystem` の権限が要ります。雛形のままではフォルダの読み取りが足りないことがあるので、足りないときは `core-manifest-permissions` を読み、必要な最小の権限にします。
- 取り込みは `project.importFiles([パス…], suppressUI, 取り込み先のビン, 連番画像として扱うか)`。**取引の外**で、単独で呼びます。
- ビンの作成は `FolderItem.createBinAction(名前, 重複を避けるか)` で、**取引の中**で作ります。この Action は **ビンそのものを返しません**。作ったあと、名前でプロジェクトの項目を探し直します。同じ名前のビンが既にあるかも、先に調べます。
- ビンの作成は、Cut & SRT で初めて使った API で、**実機での確認が残っています**。失敗しても取り込み自体は進める作りにします。
- Windows のパスは、UXP の API によっては `file:///C:/...` の形に直す必要があります（`core-api-patterns`）。

## 手順

1. 作業フォルダを作る。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Import Bins" --label "素材をビンに整理"
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Import Bins`、Windows `%USERPROFILE%\PremierePlugins\Import Bins` です。
2. 診断の項目に `FolderItem.createBinAction` と `Project.importFiles` を足しておく（`PPM.probe.run([...])`）。
3. `onRun`:
   1. フォルダを選んでもらう: `await require("uxp").storage.localFileSystem.getFolder()`。キャンセル（偽の値）なら何もしない。
   2. 中のファイルを読み、拡張子で種類に分ける（映像: mp4・mov など、音声: wav・mp3 など、画像: png・jpg など）。**数と内訳を先に画面に出し、利用者が「取り込む」を押してから**進める（大量の取り込みで固まる既知の問題があるので、数百件を超えるときは分割する）。
   3. 種類ごとのビンを作る（取引 1 回）:

      ```
      const root = await project.getRootItem();
      PPM.transact(project, "ビンを作る", (add) => {
        for (const name of 必要なビンの名前) add("ビン", () => root.createBinAction(name, false));
      });
      ```

      既にある名前のビンは作らず、そのまま使う。
   4. ビンを名前で探し直す: `await root.getItems()` を読み、名前が一致する `FolderItem` を取る。見つからなければ「ビンを作れませんでした」と警告し、ルートに取り込む。
   5. 取り込む（取引の外）: `await project.importFiles(その種類のファイルのパス, true, ビン, false)`。戻りの真偽を見て、偽なら失敗として数える。
   6. 結果の文: 「映像 12・音声 8・画像 3 を取り込みました。取り込めなかったもの: ◯ 件」。
4. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断のあと `logs.py` で、`createBinAction` が found かを読む。

## 確認

利用者の Premiere で、**素材が数本入った試し用のフォルダ**から試してもらいます。

1. 押す前に、数と内訳が出る。
2. 取り込むと、プロジェクトパネルに種類ごとのビンができ、中に素材が入っている。
3. 同じフォルダでもう一度押しても、ビンが倍にならず、素材が二重に入らない（二重の取り込みを避ける作りか確認する）。
4. 取り込めなかった素材があれば、名前つきで一覧に出ている。
5. 既存のビン・素材・シーケンスが動いていない。

## 戻し方

- ビンの作成は取引 1 回なので、取り消し（Cmd+Z / Ctrl+Z）の **1 回分**です。ただし `importFiles` は取引の外の操作で、取り消しの扱いを実機で数えていません。押した直後に、取り消しが何回で戻るかを一度確かめてから配ってください。
- 確実に戻す方法は、プロジェクトパネルで、増えたビンと取り込まれた素材を選んで削除することです（元のファイルはディスクに残ります。プロジェクトの参照だけが消えます）。
- 大量に取り込む前は、プロジェクトの保存を勧めます（`core-safety`）。

## 使う部品

- `ppro-kit`: `PPM.getProjectAndSequence`（プロジェクトの取得）・`PPM.transact`・`PPM.err`
- `probe`: API の有無
- `ui-kit`: 結果の表示

## 出どころ

- Cut & SRT の素材タブの実装（`project.importFiles`、`createBinAction`、名前での探し直し。取り込みは Mac で作者が確認済み。ビンの作成は実機未検証）
- Cut & SRT の API の使用記録（`importFiles` は取引の外、`createBinAction` は取引の中、`getItems` でたどる）
- Adobe 公式の API リファレンス（`FolderItem`）
