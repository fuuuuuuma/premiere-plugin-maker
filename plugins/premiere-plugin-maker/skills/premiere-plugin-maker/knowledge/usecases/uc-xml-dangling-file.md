---
id: uc-xml-dangling-file
title: XML を読み込んでも新しいシーケンスが出てこない（ぶら下がった file の参照）
kind: usecase
tags: [XML, XMEML, file, pathurl, 部分複製, 読み込み, fail-closed]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: XMEML は file の完全な定義を文書中で最初の 1 回しか書かない。一部のクリップだけを複製すると定義が落ち、Premiere はエラー無しで XML を無視する。書き出す前に全参照を検査して止める
parts: [fcpxml, silence-cut]
related: [uc-xml-nested-multicam, uc-xml-invalid-input-fail-closed, ref-fcp7-xml]
---
## 症状

ショート動画の候補を解析して、その区間だけの新しいシーケンスを XML で作って読み込ませたら、「インポート後の新規シーケンスを特定できませんでした」と出た。シーケンスは 0 件で、Premiere はエラーも何も出さない。

## 原因

XMEML（FCP7 XML）では、素材の定義 `<file>` を、文書全体で最初に出てきたクリップにだけ完全な形で書き、あとのクリップは `<file id="..."/>` と参照だけを書く。候補の区間だけを切り出して複製すると、完全な定義を持っていたクリップ（通常は先頭のもの）が区間の外に出てしまい、残ったクリップはすべて「定義の無い参照」だけになる。`pathurl`（素材の場所）が 0 個になる。Premiere は、解決できない参照を含む XML を、エラー無しで無視する。

## 直し方

1. 元の文書から `<file>` の完全な定義を集めておく（`_collect_file_definitions()`）。
2. 複製した文書で、各 `file id` が最初に出てくる場所に、集めた完全な定義を入れる。
3. 書き出す前に、すべての参照が解決できるかを検査し（`_validate_file_references()`）、解決できないものがあれば XML を書かず、エラーで止める（fail-closed、危ないときは進まず閉じる）。

## 再発防止

- 検査は「`pathurl` があるか」でなく「`<file>` が子要素を持つか」で判定する。字幕やグラフィックの素材には `pathurl` が無いので、前者だと誤って弾く。
- 同じ型の危険は、無音カットにもある。先頭の定義を持つクリップがカットで消えると、同じ種類の壊れた XML ができうる。当時は未対応で、解消は未確認だった。XML を部分的に作る処理は、すべて同じ検査を通す。
- 機械検証は済ませたが、実際の Premiere での読み込み成功は確かめていない。

## 出典

- Cut & SRT の失敗記録（2026-07-25、v0.9.4 で機能追加、v0.9.6 で修正）
