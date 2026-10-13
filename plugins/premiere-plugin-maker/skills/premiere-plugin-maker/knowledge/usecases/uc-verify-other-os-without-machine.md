---
id: uc-verify-other-os-without-machine
title: 手元に Windows 機が無いとき、Windows 向けの分岐をどう検証するか
kind: usecase
tags: [検証, Windows, OS 判定, テスト, 関数内参照, チェックリスト]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: OS の判定を関数の中で毎回参照するようにし、テストで属性を差し替えて Mac から他 OS の分岐を通す。OS の条件でスキップされるテストは実機でしか効かないので、未検証の範囲を明記して実機のチェックリストで確かめてもらう
parts: [local-server, packaging]
related: [uc-verify-clean-env-tiers, uc-windows-powershell-traps, uc-windows-port-local-server, platform-windows]
---
## 症状

実際の Windows 機が無く、Windows 向けの分岐（常駐・通知・文字起こし・パス）を検証できない。

## 原因

検証する環境が手元に無い。

## 直し方

1. OS ごとの違いを 1 つのファイル（`server/osplat.py`）に集め、`IS_WINDOWS` / `IS_MAC` を関数の中で毎回参照する（読み込み時に固定しない）。
2. テストで属性を差し替え、Mac の上で Windows の分岐を通す。
3. PowerShell のスクリプトは、Mac の `pwsh` で構文を検査する。
4. 実機は、「導入（Windows）」の 6 項目のチェックリストで確かめてもらう。

## 再発防止

- Windows の移植のテスト（23 件）を置く。
- CUDA での実際の文字起こし・常駐・トースト通知・UXP の動作・混在したパス区切りは、未検証と明記する。
- nvm-windows の `%APPDATA%\nvm` のような Windows 固有の探索先は、検証のテストが計画に無かった。

## 出どころ

- Cut & SRT の引き継ぎ記録と計画書（2026-07-17、pwsh 7.6.3）。機械検証のみで、実機はテスターの回答待ちだった。
