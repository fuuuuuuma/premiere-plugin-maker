---
id: uc-install-stale-panel-version-chip
title: 「直っていない」と報告されたが、古いパネルで試されていた
kind: usecase
tags: [版, パネル, 診断, サポート, バージョン表示]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: パネルとサーバーは別々に更新されるので、画面に版が出ないと切り分けられない。版の表示を「panel X / server Y」の併記にし、起動ログにも版を出す
parts: [ui-kit, local-server]
related: [uc-install-reload-layers, uc-install-version-scattered, uc-install-protocol-not-version]
---
## 症状

直したあとの最初の報告が「直っていない」だった。ログを見ると、パネルの起動を示す行が一つも無く、古いパネルで試された可能性が高かった。画面に「v0.3」のような静的な版の表示が残っていた事故や、古い版の利用者からの報告もあった。

## 原因

UXP パネルは Reload するまで古いコードのままで、パネルとサーバーが別々に更新される。画面に版が出ていないと、どちらが古いのか切り分けられない。

## 直し方

1. パネルのビルド番号を持つ定数（例: `PANEL_BUILD`）を作る。
2. 画面の版の表示を、サーバーの状態確認から取った値と並べて「panel X / server Y」にする。
3. 起動時に `[bootstrap] panel build <版>` のようなログを出す。
4. 利用者には、再インストールと Reload を案内する。

## 再発防止

- 実機で確かめる前に、Reload 後の画面の版数を見る。
- 動的にした版の表示でも、あとから静的な表示が HTML に戻ってくることがあるので、版の一致を調べるテストに HTML も含める。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-19〜07-25、旧パネルでの報告は推定で、解消の記録は無い）
