---
id: ref-mogrt
title: MOGRT の中身とドナー差し替え
kind: reference
tags: [MOGRT, mogrt, ドナー, Basic Title, prgraphic, definition.json, importMGT, insertMogrtFromPath, テロップ, locale, UUID]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: .mogrt は zip。Premiere 同梱の Basic Title.mogrt をドナーにして文字のデザインだけ差し替える。ID の振り直しで <First> を触らない・尺は locale ごとに読む・転植版は使わない
parts: [mogrt-text]
related: [ref-prtextstyle, ref-ticktime]
---
## 仕様

MOGRT（モーショングラフィックステンプレート）は、テロップなどの動くグラフィックを 1 つのファイルにしたものです。Premiere に「文字のデザインを丸ごと差し替える」公式の API は無いので、**Premiere に同梱の `Basic Title.mogrt` を「ドナー」（部品の提供元）にして、中のデザインだけ差し替えた MOGRT を作り、挿入する**、という方式を使います。

**層の構造**（Premiere 26.5.2 と Beta 27.1.0 の同梱ドナーで確認）

```
Basic Title.mogrt            ← zip
 ├ definition.json           ← 言語ごとの定義（カプセルの名前・使う書体・各言語の識別子・尺）
 ├ project.prgraphic         ← en_US
 ├ project_ja_JP.prgraphic   ← ja_JP（ko_KR・ru_RU・zh_CN も同様）
 └ thumb.png / thumb.mp4 ほか（サムネイル）
```

- `.prgraphic` ＝ **zip（gzip（XML））の二重包み**です。読むときは zip から 1 ファイルを取り出して gzip を戻し、UTF-8 の XML にします。書くときは逆に、gzip した XML を 1 ファイルの zip に入れます。
- 作る MOGRT には、`definition.json`・すべての `.prgraphic`・`thumb.png`（あれば）だけを入れます。ほかのサムネは落としても読み込めました。
- ドナーの探し方：Mac は `<アプリ>/Contents/Essential Graphics/Basic Title.mogrt`、Windows は `%ProgramFiles%\Adobe\Adobe Premiere Pro <版>\Essential Graphics\Basic Title.mogrt`（platform-mac・platform-windows）。年の新しい版を選び、Beta は後回しにします。名前を文字の順に並べて最後を選ぶ方法は、`(Beta)` と数字の並びの偶然に頼るので避けます。

**差し替える箇所**（各 `.prgraphic` に同じ変更を当てる）

1. ソーステキストの blob：テキスト部品（`AE.ADBE Text`）の 1 番目のパラメータの値を、新しい blob に差し替え、`BinaryHash` を計算し直す（blob の作りは ref-prtextstyle）。**ドナーの部品を残したまま** blob だけ替えます。
2. 位置：3 番目のパラメータ（ParameterID 3 ＝ 位置）。ドナー形式（`time,x,y,…`）か 2026 形式（`time,x:y,…`）かを見て、同じ形で書く。
3. レイヤー名（`InstanceName`）：本文の先頭 40 文字ほど。
4. グラフィック本体の名前：`SubClip` が参照する `MasterClip` の `<Name>` だけ。
5. 尺（指定したとき）：`<End>`、`<OriginalDuration>`（2 件）、アクティブな `VideoClip` と予備の `VideoClip` の `<OutPoint>`。想定の件数と違えば止める。
6. UUID の振り直し：`ObjectUID`・`ObjectURef` 属性と、`<ClipID>`・`<ID>` タグ。**世代ごとに別の UUID にしないと、2 個目が 1 個目を置き換えます。**
7. `definition.json`：`capsuleID` を新しい UUID に、名前・本文・使う書体（言語ごとの PostScript 名）・尺（`{"scale":12000,"value":秒×12000}`）を更新。**`sourceInfoLocalized.<言語>.id` は、その言語の `.prgraphic` の新しい `Sequence` の `ObjectUID` に合わせます**（連結が必須）。
8. 自己検査：XML が整形式／`ObjectID` が重複しない／`ObjectRef` がすべて解決する／テキスト部品が 1 個／blob が復号できる／`definition` の id と Sequence の UID が一致する。1 つでも外れたら MOGRT を出さずに止めます。

## 例

最小の手順（新しいプラグインで MOGRT を作って入れる）：

1. ドナーを探す。zip を開き、`definition.json` と `project*.prgraphic` を読む。
2. 各 XML で、テキスト部品が 1 個あることを確認 → blob を差し替え → 位置 → レイヤー名 → `MasterClip` の名前 → 尺 → UUID（`<First>` を除く）の順に直す。
3. `definition.json` を更新し、各言語の識別子を新しい Sequence の UID に結びつける。
4. 自己検査に通ってから出力する。
5. Premiere では UXP の `insertMogrtFromPath`、または ExtendScript の `importMGT` で入れる。**最初の挿入の試験は 1 本ずつ、診断のボタン経由で**（固まる可能性があるため）。
6. 入れたあとで、クリップの終わりを尺に合わせ、名前を本文に付け直す。
7. 見た目は、書き出したコマの画を自分で見て確かめる。

## 注意

- **罠 1：`<First>` は振り直さない。** 振り直すと、挿入はされても層の無い空のグラフィックになり、文字が描かれません（実機、2026-09-17）。トラックグループの `<First>` は、メディアの種類ごとの**固定の UUID**（映像と音声の 2 つ）で、`<MediaType>` の値と一致していなければなりません。振り直す対象は `ClipID`・`ID` のタグと、`ObjectUID`・`ObjectURef` の属性だけです。
- **罠 2：尺の ticks は言語ごとに違う。** `<End>` を英語版の値で決め打ちして置換すると、日本語版などでは置換が 0 件になり、必ず失敗します。各ファイル自身の `<End>` を読み、それと一致する `<OriginalDuration>` の 2 件だけを書き換えます（3 件目は無関係な巨大な値）。尺を省略したときの既定値も、ドナーの現在の値を測って使い、固定の数を書きません。
- **罠 3：`MasterClip` が 2 つある。** 「Proxy Sequence」と「Graphic」（日本語版は「グラフィック」）です。名前で最初のものを掴むと、Proxy を改名してしまいます。`SubClip` から辿って、アクティブな方を特定します。
- **罠 4：転植版は使わない。** ドナーの部品を 2026 形式の部品にまるごと差し替えた MOGRT を `importMGT` に渡すと、「Loading Motion Graphics Template… 30%」から戻らず、Premiere ごと固まりました（キャンセル不可、強制終了）。使うのは「ドナーの部品を残して blob だけ替える」版です。
- **`importMGT` と `insertMogrtFromPath` の違い**：`importMGT`（ExtendScript）は、**無いトラックを指定すると作らず、一番上の既存のトラックに丸めて、そこにあった元のクリップを上書き**します（利用者の実機で判明）。先にトラックを足してから入れます。UXP の `insertMogrtFromPath` も、同じトラックの重なる区間を上書きするかについて記録が割れています（Shape のテンプレートでは上書きを確認、テキストのスタイルでは「元が残ったまま追加された」という実機の報告）。**上書きに賭けず**、挿入の前に元のクリップを明示的に外すか、重なりを調べて中止します。
- 挿入後のテキスト部品は、ドナーが 2018 形式（21 項目）でも 22 項目と読めます。Premiere が読み込み時に現行の形に上げていると考えられます（推測）。文字は問題なく描かれることを、黄色の文字・赤と白の二重の縁・影で確認しました。
- 読めないもの：After Effects で作った MOGRT の見た目と、`getMGTComponent()` による差し替えは、実機で確かめていません。

## 出どころ

- Effect & Design の実機の記録（2026-09-17〜20：空のグラフィック、固まった転植版、`importMGT` のトラックの丸め）と、Premiere 同梱ドナーの観測（2026-10-13：構造、言語ごとの尺、`MasterClip` が 2 つ）
- Cut & SRT の MOGRT 生成の実機の記録（2026-07-25）、`insertMogrtFromPath` の上書きの記録の食い違い
- キットの部品 mogrt-text（`build_mogrt.py`）
