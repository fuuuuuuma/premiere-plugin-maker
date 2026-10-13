---
id: uc-verify-regression-fails-when-broken
title: 新しいテストが、本当にバグを捉えているか分からない（「壊すと落ちる」を確かめる）
kind: usecase
tags: [検証, 回帰テスト, fail-first, 構造検査, assert, 二重管理, 機械照合]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 回帰テストは、修正を無効にしたときに落ちることを確かめて初めて信用できる。「無いこと」は構造で確かめ、置換は assert でガードし、二重に持つ表は片方を直すと落ちる形で結ぶ
parts: [probe]
related: [uc-verify-stub-wrong-shape, uc-verify-test-double-defaults, uc-ai-engine-registry, uc-server-bridge-contract-drift]
---
## 症状

- 新しいテストが、本当にバグを捉えているか分からない。
- `not.toContain("onerror=alert")` は、エスケープ後の出力にも残るので、正しい実装でも落ちた。
- `str.replace` は、アンカー（置換の目印）が合わなくても、黙って元のまま書き戻した。

## 原因

値が正しいことだけを見るテストは、空振りも通してしまう。「無いこと」を部分文字列で確かめるのは、構造を見ていない。

## 直し方

1. 修正を無効にして、新しいテストが落ちることを確認する（例: `SNAP_MAX_EXTEND_S=0` で 3 件落ちる）。
2. 選択肢の距離を測る（RGB の距離が 30 以下のものを落とす）。「無いこと」は、タグごと構造で確かめる。
3. 置換の前に `assert old in s` を置き、`tsc --noEmit` も走らせる。
4. 二重に持つ表は機械で照合する（MCP のツール 17 種の宣言と実装、レジストリの label と HTML の option）。
5. 整理（リファクタ）は、現行のコードで先に緑になる特性化テストで固定してから置換する。

## 再発防止

- 修正のコミットごとに、fail-first の確認を記録する。

## 出どころ

- Cut & SRT の引き継ぎ記録、計画書、作者の開発メモ（2026-07-19〜08-14、v0.7.5〜v0.8.0。一部は Premiere 以外のツール）。機械検証のみ。特性化テストは計画書の手順で、実際に走らせたかは未確認。
