---
id: uc-uxp-api-doc-vs-device
title: 公式の文書にある API が、実機では動かない・曖昧
kind: usecase
tags: [UXP, API, 公式リファレンス, 存在確認, typeof, プローブ, 可否表]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 文書にあることと、その素材・その版で動くことは別。typeof で存在を確かめ、無ければ原因つきで止める。未確認の呼び出しは 1 つずつ実機で確かめる
parts: [ppro-kit, probe]
related: [core-api-patterns, core-verification, uc-uxp-new-trackitemselection, uc-uxp-sequence-inout-missing]
---
## 症状

- 公式リファレンスで実在を確かめた API でも、実機で動かないことがある。たとえば `createSetSpeedAction` は実機で見つからず、`createMoveAction` は動かす方向の説明が曖昧だった。
- 2026 年 5 月の実測では、無音カットを UXP の API だけで作ろうとして、多くが失敗した。

## 原因

「文書に書いてある」は「実装済み」を意味しない。2026 年 5 月の実測（無音カットの試作）の結果は次のとおり。

- 動く: `Sequence.createSetInPointAction` と `createSetOutPointAction`（範囲の設定）、`getTimebase()`（フレームレートの検出に向く）。
- 「Illegal Parameter type」になる: 引数なしの `clearSelection()`、配列渡しの `createRemoveItemsAction([item])`。
- 「Script action failed to execute」になる: `TrackItem.createSetEnd/Start/InPoint/OutPointAction`。
- 「Connection to object lost」になる: `TrackItemSelection.addItem`。

同じ API が、グラフィックのクリップでは動き、映像のクリップでは動かないこともあり、素材の種類や版による差があるとみられる。

## 直し方

1. 採用する前に、公式リファレンスと公式サンプルで実在を確かめる。
2. 呼ぶときは `typeof` で存在を確かめ、無ければ縮退するか、「症状・なぜ・次の一手」の 3 点のエラーで止める。
3. 名前が不確かな API（遷移の生成など）は、候補を 2 つ試すプローブを作る。
4. 動きが曖昧な API は、「初回は 1 クリップで確かめる」と明記して使う。
5. フレームレートは `getTimebase()` から逆算する。TickTime を作る関数は、数値・TickTime・秒の 3 段で試す。

## 再発防止

- API ごとに、版と素材の種類を変えて実機で探る（probe）。
- API のガード（存在確認・3 点のエラー）を Node の試験で固定する。ただし実機での発火は別に確かめる。
- 実機で未確認の呼び出しは、UXP のログを grep して確かめる。

## 出どころ

- 無音カット小型プラグインの実機探査（2026-05、v2.x）
- Cut & SRT の引き継ぎ書（2026-07-19〜09-23、v0.4.1〜v0.11.0）
- `createSetSpeedAction` は「リファレンスに無い」とも「あるが実機で見つからない」とも書かれ、記録が食い違う。キットの部品はどちらにも賭けず、存在を確かめる側に合わせた
