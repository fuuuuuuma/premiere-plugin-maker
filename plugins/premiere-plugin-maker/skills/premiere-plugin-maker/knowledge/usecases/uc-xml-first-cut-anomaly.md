---
id: uc-xml-first-cut-anomaly
title: 【未解明】カット 1 回目だけ映像トラックが複製される・音声が重複する
kind: usecase
tags: [XML, 未解明, カット, トラック, 再現しない, 診断, Windows]
os: [windows]
premiere: ">=25.6"
status: unverified
summary: やり直すと直る一度きりの異常は、入力の XML と出力の XML の対を一定期間残しておくと、再発のときに自分の変換の責任か切り分けられる。原因は未解明
parts: [silence-cut, fcpxml]
related: [uc-xml-audio-channel-map-lost, uc-xml-dangling-file]
---
## 症状

Windows の利用者で、1 回目のカットだけ、次のことが起きた。

- V2 の画面収録のクリップが複製され、V1 の映像素材が消える。
- 音声が途中から A1 と A2 の両方に複製される。

やり直すと正常になり、再現していない。

## 原因

未解明。文書の見立て（推測）は次のとおり。カットの変換はトラックの構造を保つことを実際の素材で確かめ済みなので、Premiere の `exportAsFinalCutProXML` が、一時的に不正な XML を書いた可能性が濃い。音声チャンネルの問題（`uc-xml-audio-channel-map-lost`）の切り分けと関係するかもしれないが、つながりは確かめていない。

## 直し方

未修正。利用者向けの導入ガイドの「困ったとき」に、もう一度実行すること、そして異常が出たら入力と出力を回収する手順を載せた。

## 再発防止

- Premiere が書いた XML（一時ファイル）と、プラグインが出力した XML を、7 日間残す。再発したら、この対を取り寄せて比べ、自分の変換が原因かを切り分ける。
- 再現しない不具合は、無理に原因を決めない。「未解明」と書いて、資料が集まる仕組みだけ作る。

## 出典

- Cut & SRT の失敗記録（2026-07-19、v0.4.0、Windows、Premiere）
