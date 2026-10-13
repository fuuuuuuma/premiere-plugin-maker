---
id: uc-verify-skip-is-not-success
title: テストが緑でも、静かに skip されていて走っていなかった
kind: usecase
tags: [検証, テスト, skip, ポート競合, 依存, npm ci]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: skip は成功ではない。走った件数と skip の理由を確認する。配布の最終判定は OS ごとに単独で走らせ、開発の前提の依存（npm ci）を入れてから照合テストを走らせる
parts: [packaging]
related: [uc-verify-clean-env-tiers, uc-verify-env-false-positive, uc-install-dist-zip-gates]
---
## 症状

- Mac と Windows の配布物を同時に Python の統合テストにかけると、実サーバーを使うテストが「環境依存」で skip になった。
- プラグインの直下で `npm ci` をしていないと、部品の照合テスト（5 件）が skip され、全体は緑なのに照合は走っていない。

## 原因

- 2 つのプロセスが、同じ loopback のテスト用ポートを選んでしまった。
- 照合テストは esbuild と jsdom に依存し、その依存は配布物の外にある `package.json` にあった。

## 直し方

1. 配布の最終判定は、OS ごとに単独で実行するか、ポートの予約を分ける。
2. 開発の前提として `npm ci` を実行する。他から写した部品は、同期用のスクリプトで写し直し、照合テストで一致を固定する。

## 再発防止

- skip の件数だけで成否を決めない。たとえば「Windows のインストーラーの静的検査 5 件」が実際に実行されたかを、個別に確かめる。
- skip の理由を読む習慣をつける。件数が記録のたびに違う（6・7・8）のに原因が書かれていないときは、調べる。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-19、09-23。v0.7.3、v0.11.0）。機械検証のみ。
