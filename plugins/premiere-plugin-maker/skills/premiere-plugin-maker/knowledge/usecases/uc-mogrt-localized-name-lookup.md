---
id: uc-mogrt-localized-name-lookup
title: 日本語の Premiere でだけ MOGRT のパラメータが見つからない（翻訳される表示名で引いた）
kind: usecase
tags: [MOGRT, prgraphic, ObjectID, ロケール, 日本語UI, 表示名, ドナー]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 表示名は言語ごとに翻訳される。アセットの部品は ObjectID や ClassID など、言語に依らない識別子か構造上の位置で引く
parts: [mogrt-text]
related: [uc-mogrt-empty-graphic-misdiagnosis, uc-mogrt-binary-rule-without-data, ref-mogrt]
---
## 症状

日本語版の `.prgraphic` では、パラメータの `<Name>` が翻訳されている（"Source Text" が「ソーステキスト」になる）。名前でパラメータを引くと、見つからずに失敗する。同じ種類の失敗が、2 回起きた（2026-07-25 の `.prgraphic` の `<Name>`、翌日の OTIO のバイリンガル表示で本文が 0 件）。

## 原因

要素を、表示名（言語によって翻訳される欄）をキーに特定していた。回避策として、英語版の XML を全言語に上書きしたところ、フォントの欠落と、言語別の ID の不一致（空のグラフィックの原因の候補。`uc-mogrt-empty-graphic-misdiagnosis`）を招いた。

## 直し方

1. 役割は、英語版（en_US）の英語の名前で 1 度だけ確定する（`_build_donor_index`）。
2. 以降は、全言語で同じ値の ObjectID で引く（Source Text = 88、Path = 109、Appearance = 110）。
3. 実際のドナーの 5 言語で、ObjectID・ClassID・要素の並びが一致することを構造の確認で確かめた。

## 再発防止

- 言語を変えたドナーの試験（ja_JP のとき英語のパラメータ名が現れないことなど）と、実際のドナーの試験を置く。
- 多言語のアセットは、表示名で特定しない。言語に依らない識別子（ObjectID・ClassID・matchName）か、構造上の位置で引く。

## 出典

- Cut & SRT の作業記録（2026-07-25、v0.9.7、日本語 UI を含む多言語環境）。5 言語のドナーでの構造確認まで（機械検証）
