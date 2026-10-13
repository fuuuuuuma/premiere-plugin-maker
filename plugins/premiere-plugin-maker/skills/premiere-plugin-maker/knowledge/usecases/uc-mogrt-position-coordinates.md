---
id: uc-mogrt-position-coordinates
title: シェイプの位置がずれる（Position は正規化値で、基準辺が符号で変わる）
kind: usecase
tags: [MOGRT, Position, 正規化, StartKeyframe, IsTimeVarying, アニメーション, 静止化]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: レイヤーの Position は正規化値で、0 以上は左/上辺基準、負は右/下辺基準。アニメ付きパラメータの StartKeyframe は捨て値で、静止化は Keyframes の削除と IsTimeVarying=false で行う
parts: [mogrt-text]
related: [uc-mogrt-donor-text-font-align, uc-mogrt-empty-graphic-misdiagnosis, ref-mogrt]
---
## 症状

パッチして作ったシェイプで、帯と文字の位置を誤った。また、ドナーに入っているフェードのアニメを、止める必要があった。

## 原因

- アンカーの定数を、アニメ付きのパラメータの `<StartKeyframe>`（アニメが始まる前の「捨て値」）から取っていた。
- 座標が、ピンの設定によって原点の辺が変わることを見落としていた。

## 直し方

1. Position は正規化値。0 以上のときは左/上辺が基準（px = 正規化値 × サイズ）、負のときは右/下辺が基準（px = サイズ + 正規化値 × サイズ）。基準の辺は、ドナーの静止時の値（レスト値）の符号で判定する。`AE.ADBE Motion` は 0.5, 0.5 のまま。
2. 定数は、アニメの開始値でなく、レスト値で確かめる。
3. アニメを止める（静止化）には、`<Keyframes>` を削除し、`<IsTimeVarying>false</IsTimeVarying>` を `<Name>` の直後に置く。無効にする書き方は、アプリ自身が書く「無効状態」の実物をまねる。

## 再発防止

- Position を px へ戻して要求値と照合し、サムネイルの実測と、ドナー 2 種で二重に確認する。
- 「空の `<Keyframes>` は値 0」という機序は未検証で、空グラフィックの原因としては否定済み（`uc-mogrt-empty-graphic-misdiagnosis`）。
- 描画と、ベースラインの係数（0.36）は実機で確かめていない。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-25、v0.9.4 で誤り、v0.9.5〜v0.9.6 で確定、Classic Live Overlay と Modern Web Caption）
