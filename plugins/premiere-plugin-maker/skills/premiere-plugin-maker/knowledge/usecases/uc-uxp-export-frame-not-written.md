---
id: uc-uxp-export-frame-not-written
title: 書き出したコマの画像がまだ無い
kind: usecase
tags: [UXP, 書き出し, exportSequenceFrame, exportAsMediaDirect, コマ, 待ち]
os: [mac, windows]
premiere: ">=26.5"
status: verified
summary: exportSequenceFrame は画像を書き終わる前に戻る。ファイルが現れるまで待つ。描画が欠けたらプレイヘッドを置いて出し直し、exportAsMediaDirect の出点は含まれない前提で長さを見る
parts: [ppro-kit]
related: [core-api-patterns, feat-cutsrt-direct-zoom, feat-cutsrt-direct-stamp, core-verification]
---
## 症状

次の 3 つが起きた。

1. `exportSequenceFrame` で書き出したはずの画像が、直後に読もうとすると存在しない。画面ズームが「一時フォルダの外」で失敗したり、顔の位置の測定が失敗したりした。
2. 連続で 5 枚書き出したところ、重ねた図形（MOGRT）が欠けたコマがあった。プログラムモニターでその時刻を表示してからだと映った。
3. 3 秒の指定で `exportAsMediaDirect` した動画が 2.97 秒（89 コマ）しかなかった。

## 原因

1. `exportSequenceFrame` は、画像の書き込みが終わる前に完了を返す。完了の通知は、画像が読める状態を保証しない。
2. 描画が欠ける原因は特定できていない。1 と同じ原因かも分からない。
3. 書き出しの範囲の出点は含まれない。`exportAsMediaDirect` 自体は同期で、返ってきた時点で終わっている（ここでは 381 ミリ秒、結果は "No Error"）。

## 直し方

1. 画像を使う側（手元のサーバーなど）が、ファイルが現れるのを最大 15 秒ほど待つ。
2. 描画が欠けるときは、プレイヘッドを対象の時刻に置いてから書き出す。
3. 動画の長さを確かめるときは、「3 秒ちょうど」でなく許容を付ける（2.95 秒以上なら通す）。終わりを待つポーリングは要らない。

## 再発防止

- 24 コマを 1/8 秒ごとに並べて、頭と末尾の背景を目で確かめる。
- 完了通知と「成果物が読める」は別と考え、ファイルの出現・大きさを確かめてから次へ進む。

## 出どころ

- Cut & SRT の演出タブ（v0.14.0 開発中）と Effect & Design の実機の記録（Premiere 26.5、macOS、2026-09-17〜10-05）
- 描画欠けの原因は未特定
