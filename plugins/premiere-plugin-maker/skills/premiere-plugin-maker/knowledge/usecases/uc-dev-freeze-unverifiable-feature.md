---
id: uc-dev-freeze-unverifiable-feature
title: 検証する手段が無い機能は、削除でなく凍結する
kind: usecase
tags: [開発, 凍結, 撤退, 検証手段, 診断器具, 復活手順, 配布]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 実機で確かめる手段が無い機能は、画面から到達できないようにして凍結する。サーバー側・診断の道具・復活の手順を残し、何を消して何を残したか、残る未検証の点を記録する
parts: [mogrt-text, packaging]
related: [uc-mogrt-empty-graphic-misdiagnosis, uc-mogrt-donor-patch-method, uc-verify-impossible-list-routes, uc-install-dist-zip-gates]
---
## 症状

MOGRT にパッチを当てる方式のシェイプ生成が、3 ラウンドをかけても、実機では「中身が空のグラフィック」しか作れなかった。マルチカムの XML の構造も、未確認のままだった。

## 原因

撤退の理由は「実装が悪い」ではなく「こちらに検証する手段が無い」ことだった。残る未検証の点は、`BinaryHash` が検証されているかどうか。

## 直し方

1. パネルから、シェイプのタブ（`page-shape`、`generateAndInsertShape` など 5 つの関数、ログの帰属、導入ガイドの該当ページ）を撤去して、到達できなくする。
2. サーバー側の `server/shape_mogrt.py`、生成の経路、テスト、診断用のスクリプトは残す。
3. マルチカムは、実物の書き出し XML を見るまで実装しない。

## 再発防止

- 凍結は「どこを消したか」「何を残し、なぜ削除しないか」「残る未検証の点」を記録する。
- 撤去のガードテスト 1 本で、「パネルに痕跡が無い」ことと「サーバー側は存在する」ことを固定する。
- サーバーが先頭で `import shape_mogrt` しているため、配布の ZIP からも外せない（必須の部品の一覧に残す）。
- 復活するときは、まず診断の 0〜8 番で、`BinaryHash` の検証の有無を切り分ける。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-25〜08-02、v0.9.9）。撤去ガードのテストは機械検証。復活の実機検証とマルチカムの方針は未確認。
