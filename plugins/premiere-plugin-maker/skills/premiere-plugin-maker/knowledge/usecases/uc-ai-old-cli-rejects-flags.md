---
id: uc-ai-old-cli-rejects-flags
title: 古い AI CLI が、新しいフラグや新しいモデルの指定を拒否して失敗する
kind: usecase
tags: [AI, CLI, フラグ, 縮退, モデル, effort, 診断]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 外部 CLI の新しいオプションと新世代のモデルは、古い版が拒否する前提で作る。外して 1 回だけやり直し、縮んだことを診断に出す。共通の設定でも、CLI ごとに引数の名前も有無も違う
parts: [local-server]
related: [uc-ai-cli-defaults-env-account, uc-ai-engine-registry, uc-ai-cli-invocation-traps]
---
## 症状

思考の深さ（effort）の指定や、新世代のモデルの指定をすると、古い CLI は知らないので実行に失敗することがある。

## 原因

CLI の版の差。さらに、思考の深さの渡し方が CLI ごとに別で、codex は設定名 `model_reasoning_effort`、claude や grok は専用のフラグ、gemini は指定する手段が無い。

## 直し方

1. フラグを拒否されたら、外して 1 回だけ実行し直す。
2. 縮んだことを記録し、診断に「モデルと思考の深さの指定は無視されます」と出す。
3. 新世代のモデルが使えないときも、ジョブを止めず、前の世代で 1 回やり直す。動作チェックに「CLI を更新すると解消します」と出す。
4. 思考の深さは、対応する CLI だけに渡す。gemini には渡さず、画面の選択欄を無効にする。

## 再発防止

- フラグが拒否されたときの縮退を、テストで固定する。
- 無条件に全 CLI へ同じ引数を渡さない。

## 出どころ

- Cut & SRT の引き継ぎ記録と計画書（2026-07-19〜09-23）。縮退は単体テストで確かめ、通常の経路の実応答は実機で確かめた。各 CLI での拒否の実際の挙動は記録が無い。
