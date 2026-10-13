---
id: uc-verify-impossible-list-routes
title: 「不可能」と結論した後に、別の経路で実現できた
kind: usecase
tags: [検証, 不可能, 経路, 誤診, シェイプ, 選択補助, 未検証]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 「A はできないから X は不可能」は、A 以外の経路が無いことを示して初めて成立する。「不可能」と書くときは、試した経路と、未検証の経路を並べて書く
parts: [probe, mogrt-text]
related: [uc-uxp-missing-apis-alternatives, uc-uxp-cannot-measure-or-write-anywhere, uc-mogrt-donor-patch-method, uc-dev-freeze-unverifiable-feature]
---
## 症状

- 「UXP にシェイプを作る API は無く、XMEML にも現れない（702 クリップ中 0 件）」から「不可能」と結論し、PNG の画像で代替した。
- 選択の補助も、`isTargeted` やリンクの API が無いので「統合は不可」と判定した。

## 原因

調べたのは UXP の直接の API と XMEML の 2 経路だけだった。.mogrt を同梱してパッチを当て、`insertMogrtFromPath` で挿入する経路が、未検証だった。選択補助も、別の設計で実現できた。

## 直し方

- シェイプ: Classic Live Overlay.mogrt をドナーに、内部の .prproj の 3 つのブロブ（Source Text・Path・Appearance）をバイナリでパッチして挿入し、PNG の方式をやめた（ただし実機で成立せず、のちに凍結した）。
- 選択補助: 対象トラックの選択（全体・映像・音声）と、実証済みの `TrackItemSelection` + `addItem` + `createRemoveItemsAction` で作り直した。

## 再発防止

- 「不可能」と書くときは、試した経路を並べ（UXP API、XMEML、OTIO、.mogrt、.prproj の断片、QE DOM）、未検証を明示する。
- 未実証の API は、存在を確かめて、原因つきのエラーにする。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-16、07-23〜07-25、v0.9.4）。機械検証のみで、新しい方式の描画は実機で成立せず凍結した。
