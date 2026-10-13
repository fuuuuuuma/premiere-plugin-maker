---
id: uc-uxp-remove-items-4-args
title: 削除の Action が「Not Enough Parameters」になる
kind: usecase
tags: [UXP, 削除, createRemoveItemsAction, 引数, 26.3, エラー]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: createRemoveItemsAction は 26.3 で 4 引数（選択・ripple・メディア種別・shiftOverLapping）が必須。少ない引数は Not Enough Parameters になる
parts: [ppro-kit]
related: [core-api-patterns, uc-uxp-new-trackitemselection]
---
## 症状

クリップを削除する処理が「Not Enough Parameters」というエラーで落ちる。以前は選択だけを渡して動いていた。配列でクリップを渡すと、別のエラー「Illegal Parameter type」になる。

## 原因

Premiere 26.3 の `createRemoveItemsAction` は、4 つの引数 `(選択, ripple, メディア種別, shiftOverLapping)` を必須にしている。2 つ以下の引数だと足りないと判断される。また、第 1 引数に配列 `[item]` を渡す書き方は型が違うとして拒否される（選択オブジェクトを渡す）。

## 直し方

1. 第 1 引数にはライブな選択オブジェクト（`getSelection()` から作ったもの）を渡す。配列は渡さない。
2. 4 つの引数を揃えて渡す。メディア種別の列挙値は版で違いうるので、存在を確かめて使う。
3. 古い Premiere も支える必要があるときは、4 引数 → 2 引数 → 1 引数の順に試す関数を 1 か所に作る。ただし 1 引数は「通常の削除（リップルなし）」にしかならないので、意図と違う結果にならないか確かめる。
4. 削除は元に戻せない操作に近いので、実行前に対象の数を確かめ、取り消しの案内を出す。

## 再発防止

- 削除の Action は 1 か所の関数に閉じ込め、引数の数を単体で試験する。
- 選択の作り方は uc-uxp-new-trackitemselection に従う。

## 出どころ

- Cut & SRT の実装のコメント（2026-07-19 の実機ログ、Premiere 26.3）
- 同じ小型プラグインの引き継ぎ書には、同じ API が配列渡しで失敗した記録もある。版や使い方で結果が変わっていると推測されるが、実行ログそのものは残っていないので partial
