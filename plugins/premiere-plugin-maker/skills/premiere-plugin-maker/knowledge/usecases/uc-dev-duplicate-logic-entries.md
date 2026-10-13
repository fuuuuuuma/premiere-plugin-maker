---
id: uc-dev-duplicate-logic-entries
title: 同じ探索の処理を別のモジュールも持っていて、1 か所を直しても別の入口で同じ症状が残った
kind: usecase
tags: [開発, 重複, リファクタ, 共通関数, 呼び出し箇所, 洗い出し]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 同じ処理を複数のモジュールが別々に持つと、直し漏れが出る。直す前に、呼び出し箇所を全数洗い出して、共通の関数に一本化する
parts: [local-server]
related: [uc-ai-cli-not-on-server-path, uc-ai-engine-registry, uc-server-bridge-contract-drift]
---
## 症状

字幕の経路で「CLI が見つからない」を直しても、AI タブで同じ「見つかりません」が起きた。計画書のレビューで、計画の漏れとして見つかった。

## 原因

AI タブの `server/agent_job.py` が、独自の `_which`（実体は `shutil.which`）と `_require_binary` を持っていて、候補のパスで探す救済も、症状・理由・次の一手のエラー文も受けていなかった。洗い出しが、`llm_engine.py` と `bridge_server.py` だけだったことが原因とみられる（推測）。

## 直し方

1. エラー文を作る関数（`llm_engine.cli_not_found_message(eng)`）を切り出す。
2. `agent_job._which` を共通の解決関数（`llm_engine.resolve_engine_binary(name)`）に置き換える。
3. `_require_binary` を、共通のエラー文を持つ例外 `AgentUnavailable` を投げる形にする。

## 再発防止

- `test_agent_job_which_uses_resolve` など 3 本のテストを足す。
- `shutil.which` の取りこぼしを探す機械検査は無い。直す前に、その処理の呼び出し箇所を全数 grep する。

## 出どころ

- Cut & SRT の計画書（2026-07-20）。計画書のみで、実機での確認は無い。
