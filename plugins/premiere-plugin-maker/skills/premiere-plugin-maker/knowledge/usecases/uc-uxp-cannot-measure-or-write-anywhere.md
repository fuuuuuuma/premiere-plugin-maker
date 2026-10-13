---
id: uc-uxp-cannot-measure-or-write-anywhere
title: 描画後の大きさが取れない・好きなパスに読み書きできない
kind: usecase
tags: [UXP, 制約, ローカルサーバー, ファイル入出力, 整列, selectionStart]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 取れない量は「取れる量 + 構造の取り決め」で、許されない操作は手元のサーバーで補う。不確かな API には確実な代わりの入力を用意する
parts: [local-server, ui-kit]
related: [core-capabilities, ref-local-server, uc-uxp-missing-apis-alternatives]
---
## 症状

- 箇条書きの行間と位置を数値でそろえたいが、文字や下地の描画後の高さを、API から取れない。
- 字幕の分割の画面で、好きなパスのファイルを読み書きしたい（ファイル選択の画面が無い）。また、入力欄の `selectionStart`（カーソル位置）が使えない環境がある。

## 原因

UXP に、描画後の高さを返す API が無い。パネルは、任意のパスのファイルを自由に読み書きできない。

## 直し方

1. 取れない高さは、「一番下の映像トラックを下地とみなす」という構造の取り決めで補う。その上で、X をそろえ、Y を等間隔にし、位置を `createKeyframe` と `createAddKeyframeAction` の 1 取引で書く。
2. ファイルの入出力だけ、手元のサーバーの `/srt/read` と `/srt/write` にやらせる（`.srt` だけ、10MB まで、書くときは一時ファイルから置き換える）。
3. 分割の位置は、`/` の記号 → `selectionStart` → 中央、の順に決める。確実な代わりの入力を最後に用意する。

## 再発防止

- 整列の計算、分割の画面、サーバーの経路それぞれの試験を持つ。
- 実機での確認はまだ。

## 出どころ

- Cut & SRT の引き継ぎ書（2026-07-23〜07-24、v0.8.0 / v0.9.2）。Node の試験のみで、実機は未確認
