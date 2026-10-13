---
id: uc-uxp-new-trackitemselection
title: 26.3 で選択の反映が「Connection to object lost」になる
kind: usecase
tags: [UXP, 選択, TrackItemSelection, setSelection, 26.3, エラー]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: new TrackItemSelection() は作れても、続く setSelection で失敗する。getSelection() のライブな選択を空にして、対象だけ足す置き換え式にする
parts: [ppro-kit]
related: [core-api-patterns, core-versions, uc-uxp-remove-items-4-args, uc-uxp-api-doc-vs-device]
---
## 症状

クリップの選択や解除をする処理が、Premiere 26.3 の実機で「Connection to object lost」というエラーになる。暫定の回避策では、元の選択が残ったまま追加選択になってしまい、そのまま削除の処理に渡すと、元の選択ごと消してしまう恐れがあった。

## 原因

26.3 では、`new ppro.TrackItemSelection()` で選択オブジェクトを作るところまでは通るが、そのあとの `setSelection` などで「Connection to object lost」になる。同じ 26.3 で `Sequence.setSelection` は、同期で boolean を返す形に変わった（公式の変更履歴）。記録どうしが食い違っていて、古い版や別の機能では「作って使えた」とも書かれている。版や使い方（作る・ライブの選択を使う・配列を渡す）で結果が変わっている可能性が高い。

## 直し方

1. 選択は新しく作らず、`await sequence.getSelection()` で取った「ライブな選択」を使う。
2. その選択を `removeItem` で全部外して空にし、対象のクリップだけ `addItem` する（置き換え式）。
3. `setSelection` の戻り値が false なら、反映に失敗したとして扱う。
4. 削除など、元の選択ごと巻き込む処理は、置き換えができないときは実行しないで止める。

## 再発防止

- `check.py` の J004 が `new TrackItemSelection()` を止める。
- 使う API は実行時に存在を確かめ、無ければ原因を書いたエラーで止める。
- 部品 `ppro-kit` の選択の関数を使う。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ書（2026-07-16〜07-19、Premiere 26.3）
- Adobe 公式の変更履歴（26.3）
- 最初の記録は「コンストラクタが失敗」、07-17 に「setSelection で失敗」へ訂正された。ほかの記録は 25.6 系ですでに失敗していたと書き、時期が食い違う。キットの部品は、ライブな選択を再利用する側に合わせた
- 最終形の `removeItem` の動きは実機で確かめていないので partial
