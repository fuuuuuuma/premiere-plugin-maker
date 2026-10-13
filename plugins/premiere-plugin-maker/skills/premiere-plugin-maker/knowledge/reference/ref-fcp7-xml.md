---
id: ref-fcp7-xml
title: FCP7 XML（xmeml）の決まり
kind: reference
tags: [FCP7 XML, xmeml, file, timebase, ntsc, ネスト, マルチカム, GraphicAndType, ダングリング, 書き出し, 読み込み]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 完全な定義は 1 回だけ。ぶら下がりを書く前に検査し、子要素で判定。換算は宣言 timebase。マルチカムの映像は書き出されない。テロップ本文は GraphicAndType から読む
parts: [fcpxml, silence-cut]
related: [ref-ticktime]
---
## 仕様

Premiere は［ファイル］→［書き出し］→［Final Cut Pro XML］で、タイムラインを FCP7 XML（正式には xmeml という形式）として書き出せます。カットや字幕の自動処理は、これを読んで作り直し、読み込み直す流れで作れます。次は、Cut & SRT の実際の書き出しファイルで確かめた決まりです。

**1. 完全な定義は文書に 1 回だけ**

- 同じ素材（`<file>`）を何百のクリップが参照しても、中身（`pathurl`・`media`・`rate`）を持つ完全な定義は文書全体で 1 つだけです。残りは `<file id="file-12"/>` のような空の参照です。ネストしたシーケンス（`<sequence>`）も同じ書き方です。
- 完全な定義かどうかは、**子要素を持つか**で判定します。`pathurl` の有無で判定してはいけません。テロップのような「グラフィック」は実体のファイルを持たず、`pathurl` が無い完全な定義だからです。`pathurl` で判定すると、正常なグラフィックを全部「壊れた参照」と誤検出します。
- 定義は、その id が最初に出てくる場所に置きます。後ろに定義があって前が空の参照だと、Premiere は解決できません。

**2. ぶら下がりの検査（書く前に必ず）**

タイムラインの一部だけを複製して XML を作り直すと、唯一の完全な定義を落とすことがあります。そうなると Premiere は**エラーを出さずに XML を無視し**、新しいシーケンスが増えないだけです。書き出す前に、すべての参照に定義があるかを調べ、足りなければ止めます（キットでは `ppm_fcpxml.dangling()` と `ensure_first_definition()`）。

**3. 読むときは XML パーサで**

`clipitem` の中に `<file><media><video>` が入れ子になるので、正規表現で `<video>` を切り出すとトラックの途中で止まります。`xml.etree.ElementTree` などで辿ります。外部から来た XML は、DOCTYPE を落とすか、`<!ENTITY` を含むものを拒否します（実体展開攻撃の対策）。

**4. 時間の換算は宣言の timebase で**

- シーケンスの速さは、`<sequence>` の**直下**の `<rate>` から読みます（文書の先頭付近にある別の `<rate>` を掴まない）。
- 秒とフレームの換算は、宣言された `timebase` と `ntsc` で行います（ntsc が真なら 1000/1001 を掛ける）。実際の fps（29.998 など）は、終端のはみ出しを抑える上限にだけ使います。
- `in`・`out`・`start`・`end` はクリップ自身の宣言レートの単位です。フレームの値と `pproTicks` は、**同じ基準で**書きます。要素ごとに基準や単位が違う XML を混ぜると、位置に比例してずれが開きます。
- 記録されている流れ：「実 fps で換算する」→（累積のずれが出て）「宣言 timebase に統一」→ さらに規則が変わりました。古い記述に引っ張られず、キットの実装（`ppm_fcpxml.py`）に合わせます。

**5. ネストとマルチカム**

- ネストしたシーケンスは、完全な定義が動画トラック側のクリップに付き、音声トラック側は空の参照だけを持つことがあります。`file` と同じ「id → 完全な定義」の索引を作らないと、中身に届きません。
- マルチカムの外側と内側でレートが違います（外側 59、内側 4、さらに素材が 29 など）。フレーム数のまま比を掛けると後半ほどずれるので、**秒を経由して**換算します。
- **マルチカムの映像クリップは書き出されません。** Premiere 自身が「マルチカメラシーケンスがサポートされていないため、トラックアイテムがスキップされました」と報告します。XML には、音声クリップの `<link mediatype=video>` だけが残り、参照先の `clipitem` が無い状態になります。映像と音声は同じネストシーケンスを同じ時間で参照している（A/V リンク）ので、音声クリップの `start`・`end`・`in`・`out`・`rate` と、参照先のネストの定義を写せば、映像クリップを作り直せます（30 分の素材で 762 クリップが全て一致）。`sourcetrack` のような音声だけのタグは写しません。
- どのカメラの音を使っているかは、XML から分かりません。`<sourcetrack><trackindex>` の 0/1 は出力の左右で、カメラの選択ではありません。

**6. テロップ（グラフィック）の本文**

UXP や ExtendScript では、テロップの本文（ソーステキスト）が読み取れません（値は本文でなく内部データの生の列になります）。**FCP XML から読みます。** `<filter><effect>` の中の `<effectid>GraphicAndType</effectid>` を持つ要素の `<name>` が本文です。クリップの特定は（トラック番号, `<start>` のシーケンスフレーム番号）で行います。`pproTicksIn` は素材側の入点で、同じ元の MOGRT から作ったクリップは全部同じ値になるので、鍵にできません。

## 例

```xml
<!-- 最初の出現が完全な定義、以降は空の参照 -->
<clipitem id="clipitem-1">
  <file id="file-1"><name>a.mp4</name><pathurl>file:///.../a.mp4</pathurl><rate>...</rate><media>...</media></file>
</clipitem>
<clipitem id="clipitem-2"><file id="file-1"/></clipitem>
```

```python
# 読み取りの骨組み（キットの ppm_fcpxml より）
root = ppm_fcpxml.load(path).getroot()
bad = ppm_fcpxml.dangling(root)            # 定義より前に出る空の参照の id
if bad: raise SystemExit("参照が壊れています: " + ", ".join(bad))
tb, ntsc = ppm_fcpxml.rate_of(seq)         # sequence 直下の rate
sec = ppm_fcpxml.frames_to_seconds(start, tb, ntsc)
```

## 注意

- **往復で失われる設定がある**：「フレームサイズに合わせてスケール」はクリップ単位の暗黙の設定で、XML に保存されず、カット後に画面が大きくなります。カスタムのオーディオチャンネル割り当ても往復で失われます。書き出し側で明示した値に直して補い、手で設定された値には触りません。自分のコードを疑う前に、プラグインを通さず「書き出して読み直す」だけで再現するかを確かめます。
- 「素材のフレームレートの上書き（Interpret Footage）」は、素材側の `<file>` に載りません。
- 部分複製・不正な値・解決できない `link`・複数の `sequence` を黙って通さず、復元できなければ止めます。
- 読み込みは `importXmlAndOpen` などを使います。Premiere で読み込めたかどうかは、プロジェクトの項目数の増減を before/after で数えて確かめます（件数が増えないなら読み込み失敗、増えたのに見つからないなら探し方の問題）。
- 書き出す作者側の手順（案内用）：［ファイル］→［書き出し］→［Final Cut Pro XML］。

## 出どころ

- Cut & SRT の失敗記録（2026-06〜07：部分複製で `pathurl` が全滅した件、VFR 素材の timebase、正規表現で切った件、`GraphicAndType` の本文）
- ネストとマルチカムの実書き出し 2 本での実測（2026-08-02）、Windows の利用者の SRT ずれの報告
- Effect & Design の実機の記録（2026-09：本文の読み取り、フレーム番号を鍵にする理由）
- キットの部品 fcpxml（`ppm_fcpxml.py`）
