---
id: uc-server-atomic-output
title: 失敗やキャンセルで、前回の成果物や保存データが壊れる
kind: usecase
tags: [staging, atomic, os.replace, 成果物, キャンセル, 保存形式, 0件]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 成果物は同じフォルダの staging に書き、後処理が済んでから os.replace で公開する。0 件や部分成功を成功にせず、旧い保存データは消さない
parts: [local-server, silence-cut, transcribe-srt]
related: [uc-server-lock-order-cancel, uc-server-transcript-cache-fingerprint, core-safety]
---
## 症状

- 最終の SRT や XML に直接書いていたため、失敗やキャンセルで、前回の成功した成果物が壊れた。
- 範囲を指定したのに字幕が 0 件でも「成功」と扱われ、前回の SRT を 0 件で置き換えた。
- 辞書の保存が、設定ファイル（`settings.json`）を壊した例もあった。

## 原因

書き込みの順序と保存の方式が、機能ごとにばらばらだった。「一度に置き換える（atomic）」という約束が、後から作った保存の機能に伝わらなかった。

## 直し方

1. 同じフォルダの staging（仮の場所）に書く。
2. QA と後処理が済んでから、はじめて `mkstemp → os.replace` で公開する。
3. キャンセルの受付と置き換えは、ジョブ管理（`JobStore`）の同じロックで、どちらが先かを裁定する。
4. 範囲を適用したあとが 0 件なら、はっきりしたエラーにする。翻訳は、失敗した部分が残れば、部分的な成果物を作らない。
5. localStorage の保存形式を上げるときは、新しいキー（例: `clipClipboard_v2`）に保存し、旧いキーは読み取り専用で残す。

## 再発防止

- 保存の機能の棚卸しは、`grep -n 'open(.*"w"' server/*.py` で行う。
- 0 件や部分成功を成功にしない。旧いデータは消さない。
- 修正の適用は記録にあるが、個別の検証の記録は無い。

## 出典

- Cut & SRT の失敗記録と作業記録、設計書（2026-07-14〜08-02、v0.7〜v0.8.0）
