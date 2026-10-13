---
id: uc-uxp-getmediatype-guid
title: 映像か音声かの判定がいつも外れる
kind: usecase
tags: [UXP, TrackItem, getMediaType, Guid, 映像, 音声, リンク]
os: [mac, windows]
premiere: ">=26.0"
status: unverified
summary: getMediaType() は Premiere 26.x で Guid を返し、数値や文字列と比べると必ず false。クラス名で判定し、再取得の照合キーには媒体の種別も入れる
parts: [ppro-kit]
related: [core-api-patterns, uc-uxp-action-outside-lock, uc-uxp-ticktime-ticks-zero]
---
## 症状

クリップを棚に保存して貼り付ける機能で、音声トラック A1 のクリップだけが保存も貼り付けもできない（A2 は動く）。保存データを見ると、画面収録の動画なのに「映像ではない」と記録されていた。

## 原因

2 つの原因が重なっていた。

1. `TrackItem.getMediaType()` が、Premiere 26.x では Guid（識別子のオブジェクト）を返す。`mt === 1` や `mt === "Video"` のような比べ方は、常に false になる。
2. クリップを取り直すときの照合が「名前 + 開始位置 + トラック番号」だけで、映像か音声かを見ていなかった。映像と音声がリンクした素材は、V1 と A1 で名前・開始位置・番号が同じになる。映像トラックを先に調べるので、音声のつもりが映像のクリップに一致し、音声が貼られなかった。

もとの試験は `getMediaType: async () => 1` という偽物で書かれており、コードと同じ誤った前提を焼き付けたまま、緑のままだった。

## 直し方

1. 映像か音声かは Guid に頼らず、クラスで判定する関数にする（`constructor.name` が `VideoClipTrackItem` か `AudioClipTrackItem` か）。判定できなければ null を返し、従来の動きに縮退して診断ログを出す。
2. 取り直すときは、調べたトラックの種別を各クリップに印として付けておき、保存側の種別が真偽値のときだけ、種別の一致を必須にする。
3. 試験の偽物は、実機の戻り値の型（Guid は空のオブジェクト `{}`）に合わせる。

## 再発防止

- `check.py` の J015 が、`getMediaType()` を数値と比べる書き方を止める。
- API の戻り値の型は、公式リファレンスで裏を取ってから試験の偽物を作る。
- リンクされた映像と音声の素材は、名前・開始・番号がぶつかるので、同一性のキーに媒体の種別を含める。

## 出どころ

- Cut & SRT の失敗記録（2026-07-21、v0.7 系）
- `constructor.name` が実機で期待どおりの名前を返すかは、診断ログによる再確認を待っていた記録なので unverified
