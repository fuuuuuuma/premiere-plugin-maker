---
id: recipe-telop-restyle
title: テロップのデザインを一括で差し替える
kind: recipe
tags: [テロップ, MOGRT, デザイン, 一括, 差し替え, 本文の読み取り, FCP7 XML, ドナー, 取り消し]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: 選んだテロップの本文を XML で読み、デザインを変えた MOGRT を作って同じ位置に入れ直す。位置と動きは引き継がれず、取り消しは 1 本あたり 2〜3 回
parts: [ppro-kit, local-server, fcpxml, mogrt-text, ui-kit]
related: [feat-ed-design-apply, ref-mogrt, uc-mogrt-donor-patch-method, uc-mogrt-design-apply-replaces, uc-uxp-mogrt-overwrite-unclear, uc-mogrt-source-text-unreadable, uc-mogrt-telop-text-not-greppable, uc-mogrt-adobe-fonts-signout, uc-mogrt-second-insert-replaces]
---
## この型で作れるもの

「選んだテロップを、すべて白文字に黒縁のデザインにそろえる」ボタンです。本文は元のまま、見た目だけが変わります。

完成サンプル `<SKILL>/examples/telop-restyle` が、この型そのものです（デザインを選ぶ欄と［差し替える］ボタン）。

## 前提

- 雛形は `panel-server`（パネル＋手元のサーバー）。部品は `mogrt-text`（`fcpxml` が一緒に入ります）。
- UXP からは、テロップの本文（Source Text）が読めません。そこで、シーケンスを FCP7 XML として書き出し、サーバーが XML から本文を取り出します（`uc-mogrt-source-text-unreadable`）。
- UXP にはグラフィックを新しく作る API がありません。そこで、サーバーが、Premiere に入っている標準の `Basic Title.mogrt` を **ドナー**（部品取り用の元）にして、文字のデザインだけを差し替えた MOGRT を作ります（`uc-mogrt-donor-patch-method`）。
- 最低版は 26.3 です（Action は取引の中で作る必須化と、XML の書き出しの API のため）。
- 書体は Creative Cloud にサインインして Adobe Fonts が有効なときだけ使えます。サインアウトすると全部が「書体なし」になる事例があります（`uc-mogrt-adobe-fonts-signout`）。
- 手元のサーバーを入れる前に、利用者の許可を取ります。

## 手順

1. 作業フォルダを作って、部品を足す。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-server --name "Telop Restyle" --label "テロップ一括デザイン"
   python3 <SKILL>/scripts/add_part.py mogrt-text --project <作業フォルダ>
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Telop Restyle`、Windows `%USERPROFILE%\PremierePlugins\Telop Restyle` です。
2. デザインを選ぶ欄を作る。デザインの定義は `<作業フォルダ>/server/mogrt/styles/*.json`（見本は `white-black`・`news-band`・`yellow-red-white`）。増やすときは、見本の JSON をコピーして書体・色・縁を書き換える。選ぶ欄は `PPM.ui.protectSelect($("style"))` で、ホイールで値が変わる事故を防ぐ。
3. `index.js` の `onRun` の流れ（サンプルのとおり）:
   1. 選んだ映像クリップを取る。0 本なら「テロップが選ばれていません」で止める。
   2. `await PPM.server.connect(...)` で手元のサーバーにつなぐ。
   3. `PPM.fcpxml.exportActiveSequence(...)` で XML を書き出し、`PPM.server.runJob("read_texts", { xmlPath, clips })` で本文を読む。読めないクリップ（テロップではない）は飛ばして、数を画面に出す。
   4. `PPM.server.runJob("build_mogrt", { styleName, items })` で、本文ごとの MOGRT を作る。
   5. クリップごとに `PPM.mogrt.replaceClip(project, sequence, clip, mogrtのパス)`。元を外してから新しいものを入れ、長さを合わせる。戻り値の `undoSteps` を足して、完了の文に「取り消しは ◯ 回」と書く。
4. サーバーを入れる。依存が無いか、あるなら何をどれだけ入れるかを利用者に見せて、許可を取ってから進める。

   ```
   python3 <作業フォルダ>/server/install.py --dry-run
   python3 <作業フォルダ>/server/install.py
   ```

   Mac では `server/install_mac.command`、Windows では `server\install_windows.bat` をダブルクリックしても同じです。
5. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンのあと、`logs.py` で結果を読む。

## 確認

利用者の Premiere で次を見てもらいます。まずテロップを **2 本だけ** 選んで試します。

1. パネルの文に「2 本を差し替えました」と出て、飛ばした数も出ている。
2. タイムラインのテロップが、選んだデザイン（文字の色・縁・書体）に変わっている。
3. 本文が元と一字も違わない。改行と、日本語の字がそろっている（豆腐になっていない）。
4. 長さ（始まりと終わり）が元と同じ。
5. 元の位置や動きは **引き継がれない**。標準の位置（画面の下寄り）に置かれる。この点を、押す前に画面で警告している。
6. 上のトラックが空だったテロップが、元のクリップを上書きして消していない。

## 戻し方

- 取り消し（Cmd+Z / Ctrl+Z）は、**1 本あたり 2 回**（元を外す・新しく入れる）です。長さを合わせる操作が入った本は **3 回**です。選んだ本数 × この回数が合計です。パネルは完了の文でこの回数を正直に出します。
- MOGRT の挿入は、取引に入れられず、取り消しが別の項目になります。回数は実機で数え直すのが確実です。
- 一括で押す前に、プロジェクトを保存してもらいます。取り消しの途中で迷ったら、保存した状態に戻せます。
- 回数が多くなるときは、先にシーケンスの複製を作ってから試す方法もあります（元はそのまま残ります）。

## 使う部品

- `mogrt-text`: ドナーからの MOGRT の生成（`build_mogrt`）、`PPM.mogrt.insertAt` / `replaceClip`
- `fcpxml`: XML の書き出し・本文の読み取り（`read_texts`）
- `local-server`: サーバーとのジョブのやり取り（`PPM.server`）
- `ppro-kit`: 選択の読み取り、取引

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09）: ドナー方式、MOGRT の 2 個目の挿入、アニメ付きテロップ、`importMGT` のトラック指定（`feat-ed-design-apply`）
- Cut & SRT の失敗記録: 本文が XML でしか読めないこと、デザインを当てると位置と動きが消えること（`uc-mogrt-design-apply-replaces` は実機の確認待ち）
- 完成サンプル `telop-restyle`（このキットが生成し、`check.py` を通したもの。Premiere の実機で通した記録はまだありません）
