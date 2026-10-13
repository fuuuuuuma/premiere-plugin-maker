---
id: feat-ed-overview
title: Effect & Design の全体（CEP パネル＋UXP 補助＋Python のエンジン・4 つの実行場所）
kind: feature
tags: [Effect & Design, CEP, UXP, ExtendScript, Python, 補助プラグイン, 構成, テロップ, デザイン, アニメ, ハイブリッド]
os: [mac]
premiere: ">=25.6"
status: partial
summary: テロップのデザインとアニメを 1 クリックで当てる拡張。画面は CEP、Premiere の操作は ExtendScript、見た目づくりは Python、取り消し 1 回で書く部分だけ UXP の補助。役割を 4 つに割り、後で UXP へ差し替えられる形にした
parts: [cep-helper, mogrt-text, motion-bake]
related: [feat-ed-design-apply, feat-ed-motion, feat-ed-import-styles, feat-ed-catalog-previews, feat-ed-packaging, feat-cutsrt-design, ref-cep-extendscript, core-versions, core-transactions]
---
## 何をする機能か

Effect & Design は、動画編集者が「選んだテロップに、テレビ番組のようなデザインとアニメーションを 1 クリックで当てる」ための Premiere Pro 用の拡張です。見本つきのカタログから選ぶと、選択中のテロップの見た目を差し替えたり、出入りや強調の動きを付けたりします。結果は Premiere の純正のテキストになるので、あとから文字を直せます。

Premiere の公式 API には「選んだテロップの見た目を別のデザインに替える」手段がありません。この拡張は、その穴を「同梱の土台から作った MOGRT で差し替える」やり方で埋めています（`feat-ed-design-apply`）。

## 作り方

一つの拡張を、役割の違う 4 つの実行場所に分けています。

| 実行場所 | 言語と作り | 受け持ち |
|---|---|---|
| CEP パネル | HTML と JavaScript（Chromium 上、Node が使える） | 画面、カタログの並び、選択の状態、手順の流れ |
| ExtendScript | ES3 の 1 ファイル。Premiere の DOM と QE DOM を触る | シーケンス・トラック・クリップ・キーフレームの操作 |
| Python のエンジン | 標準ライブラリだけ（3.9 互換） | スタイルから MOGRT を作る、本文を読む、検査する、取り込む |
| UXP の補助プラグイン | 画面を持たない常駐の補助。起動時に読み込まれる | 取り消し 1 回で動き（キーフレーム）を書く |

つなぎ方の決まりは次のとおりです。

- パネルから ExtendScript へは、関数名と JSON の引数を文字列で渡し、JSON の文字列で返事をもらう。
- パネルから Python へは、`python3 -m engine.xxx` を同期で呼ぶ。標準出力は JSON 1 行、終了コードは常に 0（失敗は JSON の `ok:false` と日本語の理由で伝える）。
- パネルから UXP の補助へは、公式の通信手段が無いので、フォルダを介したファイル渡しにする（`feat-ed-motion`）。
- カタログ（デザインとアニメの定義）はデータだけで、何も実行しない。

役割の線引きは「見た目を作る・カタログを読む・見本を作る」を Python に、「Premiere を触る」を ExtendScript の 1 ファイルに閉じ込める、というものです。こうしておくと、将来 CEP が使えなくなっても、画面と ExtendScript の部分だけを UXP に置き換えれば済みます。

### なぜ CEP と UXP の併用なのか

- 当時の判断では、UXP にはテキストレイヤーやテキストスタイルを扱う API が無く、デザインの差し替えは MOGRT を作る方式でしか成り立ちませんでした。画面とカタログは、実績のある CEP で作りました。
- ExtendScript には、複数の操作を取り消し 1 回にまとめる手段がありません。キーフレームを打つと、1 つごとに Cmd+Z が要りました。UXP の `executeTransaction` なら 1 回で戻せます。
- 一つの manifest に CEP と UXP を同居させることはできません。そこで「別々の 2 製品として並べて入れる」形にしました。代わりに、導入と更新が二重になります（`feat-ed-packaging`）。

## 使った API と道具

- CEP: `CSXS/manifest.xml`、`CSInterface.js`（Adobe 配布のまま）、`.debug`（開発用の確認口。配布物には入れない）、未署名拡張を許可する `PlayerDebugMode`。
- ExtendScript: `importMGT`、QE DOM の `addVideoEffect` と `addTracks`、キーフレームの `addKey`、`exportAsFinalCutProXML`、`exportAsMediaDirect`。
- UXP: `project.lockedAccess` と `project.executeTransaction`、`VideoFilterFactory`、`TransitionFactory`。manifest は v5、最低版 25.6。
- Python: `zipfile`・`gzip`・`xml.etree`、FlatBuffer を自前で読み書きする部品。
- 観測の道具: `.debug` のポートに接続してパネルの内部を読む方法（画面を触らずに確かめられる）。

## つまずきと直し方

この拡張で実際に踏んだ、全体に効く落とし穴です。個別の話は各機能の記録にあります。

- **テストが全部緑なのに、実機だけ止まる**。CEP の Node は、普通の Node と違って、ページに `module` が生えていたり、`child_process` の非同期コールバックが届かなかったりします。→ 「実機のログを確かめるまで動くと言わない」を決まりにし、実機で分かった性質をテスト用の偽物に取り込んだ。詳しい症状は `ref-cep-extendscript`。
- **UMD の読み込みで画面が固まる**。`module` があるかだけで分岐すると、`window` に載らない。→ `module.exports` と `window` の両方に載せる。
- **Python の返事が来ない／画面が永久に待つ**。→ 同期呼び出しにして `timeout` を必ず付ける。ExtendScript 側にも見張り（45 秒）を付け、時間切れ後に届いた返事は捨てる。
- **Python が見つからない、あっても動かない**。Premiere から見える PATH は最小で、Apple のコマンドライン・デベロッパ・ツールが無い Mac の `python3` は中身の無い見かけだけのものです。→ 候補を順に試し、見かけだけのものは次へ回す。導入時に確かめる。
- **ExtendScript を直してもパネルを開き直すまで反映されない**。→ 毎回、ExtendScript の本文ごと渡す（重いので、版の印が合っていれば本文を省く工夫は別ブランチの実験にある）。
- **日本語の Premiere では、英語の効果名で効果が付かない**。→ `feat-ed-design-apply` と `feat-ed-motion` を参照。

### 記録が食い違う所

| 話題 | 記録 A | 記録 B | キットの部品が合わせた側 |
|---|---|---|---|
| CEP の終わる時期 | 設計時の資料に「2026-09 に終了」と「UXP の正式版から 1 年並行」 | 後の調査で「確定した終了日は無い」 | Adobe 公式ブログ（2026-09）の新しい予定に合わせた。2027-12 に新規受付停止、2028-12 に既定で無効、2029-12 に同梱終了（`core-versions`）。部品 `cep-helper` は期限つきの補助にだけ使う |
| UXP で `<video>` が使えるか | 設計時の記録は「使えない」 | 後の調査では根拠も反証も確定できない | 未確認のまま。見本は静止画を基本にし、動画は使えない前提で作る |
| 1 つの取引にまとめる範囲 | 設計時は「ExtendScript のまま 3 回」を想定 | 実測では、キーだけなら 1 回、効果を足すと 2 回 | 実測に合わせた（`core-transactions` の T4）。デザイン差し替え（MOGRT の挿入）は取引に入らず、複数回になる |

## 結果と今の状態

- Mac（Apple シリコン）の Premiere 26.5 系で、画面が立ち上がり、デザインを当て、アニメを当て、取り消しで戻る、という通し確認ができています。受け入れの一覧は全項目が合格しました。
- 確かめていないこと: Intel Mac、Windows（非対応）、コマンドライン・デベロッパ・ツールが無い Mac、Premiere 24 系、英語など日本語以外の UI、Beta 版での動作。
- 版の扱い: 画面の最低版は manifest 上 24、UXP の補助は 25.6 以上。補助が無い場合も、パネル本体は使えます（取り消し回数が増えます）。
- この記録の時点で、別ブランチにだけある性能改善（選択の見張りの高速化）は、本体には取り込まれていません。

## 出どころ

- Effect & Design の設計書・実機の判定表・受け入れの記録（2026-09-17〜09-21）
- 作者の実測メモ（UXP の取引、CEP の Node の罠、補助プラグインの導入）
- Cut & SRT の CEP と UXP の比較調査（2026-07-25）
- Adobe 公式ブログ（CEP の予定、2026-09）
