---
id: uc-server-preflight-light
title: 事前の確認や診断が、ログイン確認のプローブで最大 60 秒止まる
kind: usecase
tags: [プリフライト, 診断, doctor, サブプロセス, CLI, ログイン確認, 設計判断]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 事前の確認と診断は、「入っているか・設定されているか」までの軽い判定に絞る。重い確認は、既存の工程か、利用者が押す再検査のボタンに分ける
parts: [local-server]
related: [uc-server-cli-exit-zero-path, feat-cutsrt-ai-engines, feat-cutsrt-settings-diagnostics]
---
## 症状

転換前の設計書は、開始の直後にエンジンが使えるかを、プローブ（実際に試し打ちして確かめること。結果は一定時間キャッシュ）で確かめて、だめなら即停止する案と、診断で各エンジンのログイン済みをプローブで点検する案だった。

## 原因

HTTP の経路や診断の画面で、ログイン確認のサブプロセスを走らせると、最大で 60 秒ブロックする。

## 直し方

判定を次の 4 つだけにする。

1. バイナリが解決できるか（`llm_engine.resolve_engine_binary`）
2. 環境変数（gemini は `GEMINI_API_KEY`）
3. ローカルエンジンの準備ができているか（`local_engine_status().ready`）
4. すでに持っているプローブのキャッシュ

事前の確認を、新しい関数（`llm_engine.preflight_linebreak(engine, local_only)`、`bridge_server.preflight(kind, ...)`）にまとめ、診断（`doctor_report` と `GET /doctor`）も同じ確認を使う。深い確認は、実際に改行を行う工程か、「再検査」ボタン（`/engines/recheck`）に任せる。

## 再発防止

- バイナリの有無とローカルの準備の組み合わせごとの判定を、`shutil.which` などをモックしたテストで固定する。
- 注意点: CLI が入っていれば、未ログインでも事前の確認は通る。ログインの確認は、深い確認の側で行う。
- 端末版の doctor と、深い点検は、初版では見送った。計画書の記述の段階（確度は未確認）。

## 出典

- Cut & SRT の計画書（2026-07-21、v0.8.0）。2026-07-20 の設計書の案を覆した
