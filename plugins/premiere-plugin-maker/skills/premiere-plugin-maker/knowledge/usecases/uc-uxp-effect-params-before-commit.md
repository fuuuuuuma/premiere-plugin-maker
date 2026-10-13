---
id: uc-uxp-effect-params-before-commit
title: 足した効果の値を設定できない
kind: usecase
tags: [UXP, 効果, VideoFilterFactory, createComponent, 取引, getParamCount]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 足す前の効果は設定項目を持たず、取引が確定してから現れる。効果を足す取引と、値やキーを書く取引を分ける
parts: [ppro-kit]
related: [core-transactions, uc-uxp-action-outside-lock, uc-uxp-interp-same-transaction]
---
## 症状

`VideoFilterFactory.createComponent` で作った効果に、同じ取引の中で値やキーを入れようとすると、`getParamCount is not a function` というエラーになる。効果を足す操作だけが通り、取り消しを 1 回すると消える。

## 原因

作っただけの効果（部品）は、まだ設定項目（パラメーター）を持っていない。設定項目は、取引が確定してから現れる。

## 直し方

1. 効果を足す取引と、値やキーを書く取引を分ける。取り消しの名前（undoString）を同じにしても、1 回にはまとまらない。
2. 足したあとは、クリップから効果を取り直して、その設定項目に書く。
3. 取り消しの回数は、キーだけなら 1 回、効果を新しく足すなら 2 回になる。すでに同じ効果が付いたクリップに当て直すときは、既存の効果を使い回して 1 回で済む。複数のクリップでも同じ。
4. 画面には、取り消しに必要な回数を正直に表示する。

同じ形の例（公式の文書でだけ確認）として、マーカーの色は、マーカーを追加する取引のあとに、実体を取り直して別の取引で色を付ける。

## 再発防止

- 表示した回数と実際の取り消し回数が合うことを、17 種類の動きで数えて確かめた。
- 偽物を使う試験と、実機の確認項目に「動きの適用と取り消し 1 回」を入れる。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09-18〜09-23）
- Cut & SRT への移植の設計書（同じ落とし穴を既知として記載）
