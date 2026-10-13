---
id: uc-uxp-get-track-items-args
title: getTrackItems が空・例外になる（引数が 2 つ要る）
kind: usecase
tags: [UXP, Track, getTrackItems, 引数, 選択]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: Track.getTrackItems は (type, includeEmpty) が必須。無引数は空配列か例外になる。選択オブジェクトの getTrackItems は別物で引数なし
parts: [ppro-kit]
related: [core-api-patterns, uc-uxp-action-outside-lock]
---
## 症状

トラック上のクリップを集めようとして `track.getTrackItems()` を呼ぶと、空の配列が返る、または例外になる。古い Premiere では同じ書き方で動いていたため、更新後に突然「クリップが見つからない」になる。

## 原因

`Track.getTrackItems(type, includeEmpty)` は引数が必須の API になっている。`type` は 1 が「クリップ」で、`includeEmpty` を true にするとクリップの間の空き（ギャップ）も返る。無引数の呼び出しは古い版でだけ通っていた。

一方、`sequence.getSelection()` が返す選択オブジェクトの `getTrackItems()` は、別のクラスの別の書き方で、引数を取らない。名前が同じなので混同しやすい。

## 直し方

1. トラックから集めるときは `track.getTrackItems(1, false)` のように、種類と空きを含めるかを必ず渡す。
2. `includeEmpty` を true にしたときは、返ってきた要素が null のことがあるので、null を除く。
3. 選択から集めるときは、選択オブジェクトの `getTrackItems()` を引数なしで呼ぶ。トラックの方と書き分ける。
4. 版によって通る書き方が違うかもしれないと疑うなら、複数の引数の組を順に試す防御を、1 か所にまとめて持つ。

## 再発防止

- `check.py` の J003 が、引数なしの `getTrackItems()` を止める。止まったときは、呼び出し元がトラックか選択かを確かめる。
- 取り出したクリップのハンドルは保存せず、使う直前に取り直す。

## 出どころ

- Cut & SRT の小型プラグインの実装と作者の実測メモ（2026-07、Premiere 26.x）
- 「現行版は空配列か例外」は作者の実測メモによる。版ごとの切り替わりの境目を測った記録は無いので、status は partial
