---
id: recipe-batch-effect
title: 選んだクリップに一括で効果を足す
kind: recipe
tags: [効果, 一括, 選択, VideoFilterFactory, createComponent, 取引, 取り消し, パネル]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: タイムラインで選んだ映像クリップすべてに効果を足し、足したあとで値を入れる。効果を足す取引と値を書く取引は別にするので、取り消しは 2 回になる
parts: [ppro-kit, ui-kit, probe]
related: [core-transactions, core-api-patterns, uc-uxp-effect-params-before-commit, uc-uxp-action-outside-lock, core-safety]
---
## この型で作れるもの

「選んだクリップに、ぼかし・色の調整・トランスフォームなどの効果を一度に付けるボタン」です。クリップを 1 本ずつ選んで効果を足す手間を、ボタン 1 回にします。値（ぼかしの量など）をパネルの入力欄で決める形にもできます。

効果は「足す」と「値を入れる」の 2 段階で、それぞれ別の取引（取り消し 1 回分のまとまり）になります。この 2 段階が、この型でいちばん大事な点です。

## 前提

- 雛形は `panel`（パネルだけで足ります。ログ・Premiere の操作の型・見た目・診断ボタンが入っています）。
- Premiere 25.6 以上。Mac・Windows どちらでも同じです。
- 足したい効果の matchName（言語に依存しない内部名）を知っていること。分からないときは、診断ボタン（部品 probe）に調べたい名前を足すか、`VideoFilterFactory.getMatchNames()` の一覧から選びます（その API が無い版もあるので、存在を確かめてから呼びます）。
- 利用者のクリップを変える処理なので、一括の前に保存を勧め、件数を伝えます（`core-safety`）。

## 手順

1. 作業フォルダを作る（Mac は `python3`、Windows は `py -3`。`<SKILL>` はこのスキルのフォルダ）。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel --name "Batch Effect" --label "一括エフェクト"
   ```

   既定の場所は Mac `~/PremierePlugins/Batch Effect`、Windows `%USERPROFILE%\PremierePlugins\Batch Effect` です。以降はこの場所を `<作業フォルダ>` と書きます。
2. `index.html` に押すボタン（`id="run"`）と、必要なら値の入力欄を足す。入力欄の値は `PPM.ui.numberValue($("amount"), 既定値)` で読む（空欄でも NaN にならない）。
3. `index.js` の `onRun` に、次の流れで書く。完成サンプル（`<SKILL>/examples/zoom-button/index.js`）が、選択の読み取り・エラーの出し方・結果の表示の見本です。
   - 選択を読む: `const { project, sequence } = await PPM.getProjectAndSequence();` → `(await PPM.getSelectedClips(sequence)).filter((c) => c.kind === "video")`。0 本なら `PPM.err("映像のクリップが選ばれていません", …)` で止める。
   - 効果を足す（取引 1 回目）: クリップごとに `await PPM.addEffect(project, c.item, "AE.ADBE Geometry2")`。部品の生成は取引の外、足すのは取引の中で、ppro-kit がやります。効果はテキストの部品の手前に差します。
   - 値を入れる（取引 2 回目）: 足し終えてから、クリップごとに `const found = await PPM.findParam(c.item, [matchName], ["スケール", "Scale"])` で設定項目を取り直し、全クリップ分を **1 つの** `PPM.transact(project, "値を設定", (add) => { PPM.setValueAction(add, found.param, 値); })` にまとめる。項目名は日本語と英語の両方を並べます。
   - 戻り値を見る: `PPM.transact` は、1 つも受け付けられなければ原因つきのエラーを投げます。`result.warnings` があれば画面に出します。
4. 検査する。誤りが 0 件になるまで直す。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   ```

   取引の中の `await`（J001）や、取引の外で作った Action（J002）は、ここで止まります。
5. UXP Developer Tools の［Add Plugin］で `<作業フォルダ>/manifest.json` を選び［Load］。Premiere の［ウィンドウ］→［UXP プラグイン］からパネルを開く。
6. 診断ボタンを押して、使う API が見つかることを確かめる。結果は AI が次のコマンドで読む。

   ```
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

## 確認

利用者の Premiere で、次を順に見てもらいます。

1. 映像クリップを 3 本ほど選んでボタンを押す。パネルに「◯ 本に付けました」と出る。
2. エフェクトコントロールパネルを開き、選んだ 3 本すべてに効果が並んでいる。1 本だけ付いていない、ということがない。
3. 値を決めたなら、各クリップのエフェクトコントロールで値が入力どおりになっている。
4. 選んでいないクリップには何も付いていない。
5. 付けた効果がテキストの下に隠れていない（テロップを選んだ場合）。

`logs.py` の出力に `warnings` が出ていないことも見ます。

## 戻し方

- 効果を新しく足した場合、取り消し（Cmd+Z / Ctrl+Z）は **2 回**です。1 回目で値が戻り、2 回目で効果が消えます。選んだクリップが何本でも、回数は変わりません。取引の名前を同じにしても、1 回にはまとまりません。
- すでに同じ効果が付いたクリップに、値だけを当て直す場合は **1 回**です。
- パネルの完了の文に、この回数を書いておくと、利用者が迷いません（サンプルの文を参照）。
- 確認の途中で別の操作をすると、取り消しの順が変わります。戻すのは、ボタンを押した直後にしてもらいます。

## 使う部品

- `ppro-kit`: `PPM.getSelectedClips`・`PPM.addEffect`・`PPM.findParam`・`PPM.setValueAction`・`PPM.transact`
- `ui-kit`・`probe`・`logger`: 雛形に最初から入っています。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09）: 足した効果は取引が確定するまで設定項目を持たないこと、取り消しの回数を 17 種類で数えて確かめたこと（`uc-uxp-effect-params-before-commit`）
- Cut & SRT と Effect & Design の API の使用記録（取引の 3 段階の型。`core-transactions`）
- Adobe 公式の変更履歴（26.3 の Action を lockedAccess の中で作る必須化）
