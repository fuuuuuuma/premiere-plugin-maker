---
id: uc-xml-invalid-input-fail-closed
title: XML の異常な入力（不正な数値・解決できない link・複数のシーケンス）を黙って通した
kind: usecase
tags: [XML, XMEML, link, 異常入力, fail-closed, トランジション, sequence]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 異常な入力を黙って飛ばすと、音声が欠けたまま成功したり、読み込みが壊れたりする。復元できる正当な値だけ受け、できなければ止める
parts: [fcpxml, silence-cut]
related: [uc-xml-dangling-file, uc-xml-regex-nested-tags, ref-fcp7-xml]
---
## 症状

- 数値が不正なクリップを黙って飛ばすと、音声が欠けたまま字幕作りが「成功」した。
- 解決できない `link` の ID が残ったままだと、Premiere に読み込ませたときに壊れた。
- 1 つの XML に複数の `<sequence>` があると、どれを対象にするのかがあいまいだった。

## 原因

異常な入力を、無言で通していた。ただし、すべての異常が本当の異常とは限らない。クリップの `start` や `end` が `-1` になるのは、トランジション（切り替え効果）の境目を表す正当な値だった。

## 直し方

1. 数値の不正と、解決できない素材の参照は、はっきりしたエラーにする。
2. `start`/`end` が `-1` のクリップは、隣のトランジションから位置を復元できるときだけ受け入れる。
3. 解決できない `link` は、`link` の要素ごと取り除く。
4. 複数の `<sequence>` があるときは、`clipitem` の数が最も多いものを選び、警告を出す。

## 再発防止

- 合成した XML で、リンクの整合・トラックごとのオフセット・連続性を検証する。
- 「復元できなければ止める」を原則にする。複数シーケンスの選び方は、専用のテストが無かったので、増やすときは先にテストを書く。

## 出典

- Cut & SRT と premiere-skills の /cut の記録（2026-07-02、2026-07-14、v0.4.0 より前）
- 合成した XML による機械検証
