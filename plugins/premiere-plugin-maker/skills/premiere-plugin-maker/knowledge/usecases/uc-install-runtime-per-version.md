---
id: uc-install-runtime-per-version
title: 展開した場所に依存した常駐が、移動・削除・同期で壊れる。渡す前に開発機だけの前提も洗い出す
kind: usecase
tags: [配布, 常駐, runtime, 版別, 開発機依存, ロールバック, OneDrive]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 常駐サーバーは展開したフォルダでなく、版ごとのフォルダへ複製して動かし、設定や仮想環境は外に置く。失敗したら以前の物に戻す。渡す前に「開発機にだけある物」を棚卸しする
parts: [packaging, local-server]
related: [uc-install-same-version, uc-install-tcc-protected-folder, platform-cross]
---
## 症状

- 展開した場所を動かすと、常駐が壊れる。
- 導入が途中で止まっても、成功と表示される。
- 更新すると、設定が消える。
- 第三者に渡すと、作者の開発機にだけある前提（外部のリポジトリ、手で入れた依存、自分の辞書、固定の出力先）で動かない。

## 原因

常駐の実体が、配布フォルダの置き場所（保護フォルダ、移動や削除、OneDrive の同期の割り込み）と、開発機の状態に依存していた。

## 直し方

1. サーバーを、利用者のデータフォルダの下の版別フォルダへ複製する（Mac は `~/Library/Application Support/<名前>/runtime/<版>/`、Windows は `%APPDATA%\<名前>\runtime\<版>\`）。そこから常駐（Mac は launchd、Windows はタスク スケジューラ）に登録する。
2. 使っている版を `runtime/current.json` に記録する。
3. 設定・辞書・専用の仮想環境は、runtime の外に置く。
4. 起動確認に失敗したら、以前の runtime に戻す。
5. 開発機依存は、部品の同梱、ワンショットのインストーラ、辞書の書き出しと読み込みで解消する。

## 再発防止

- 同じ版数の runtime は上書きされないので、入れ直す前に uninstall 用のスクリプトで削除する。
- Windows は、OneDrive の管理外（例 `C:\Tools\<名前>\`）で `install.bat` を実行する。
- 渡す前に、「開発機にだけある物」を一覧にして潰す。

## 出どころ

- Cut & SRT の導入ガイドと引き継ぎ記録（v0.4.0 前の棚卸し、v0.10.3〜v0.14.0 の版別 runtime）
