---
id: uc-server-mcp-long-job
title: MCP ツールの設計と保守（長時間のジョブ・宣言と実装のずれ・200 の中の失敗）
kind: usecase
tags: [MCP, 長時間ジョブ, ポーリング, 機械照合, ツール定義, 通信エラー, AST]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 長い処理は「開始」と「状態確認」の二段にし、ツールの宣言と文書の対応は実装を読んで機械で照合する。通信の成否とジョブの成否は別の層で判定する
parts: [mcp-bridge, local-server]
related: [ref-mcp, feat-cutsrt-mcp, feat-premiere-agent-kit, uc-server-boundary-validation]
---
## 症状

- 長時間かかるジョブを、MCP の 1 回の呼び出しの中で待たせられない。
- ツールを足すたびに、別のリポジトリにあるスキルの記述が古くなる。
- ジョブの状態を返す API が、HTTP 200 で `{status: "error"}` を返すと、ポーリングの層が通信断だと誤認し、同じエラーを 3 回表示した。

## 原因

- 長時間の処理を、1 回の呼び出しに載せる前提で作っていた。
- 2 つのリポジトリに別々に書いた取り決めが、非同期に古くなった。
- 汎用の fetch の層が、`error` のキーがあるだけで例外を投げており、通信の成否とジョブの成否を、同じ層で判定していた。

## 直し方

1. 開始の呼び出し（`start-srt`）は、開始の通知だけを返す。進み具合は、状態を見る別のツール（`premiere_job_status`。内部は `JobStore.snapshot`）で確かめる。
2. パネルの橋渡しに、実行系 11 種の入口（`/agent/panel/<key>`）を足し、パネル側は、すでに実戦で使われている関数を呼ぶだけにする。
3. `tool_coverage` テストが、`mcp_premiere.py` のツール定義（36 件）を `ast` で読み、`premiere-ops` の記述と双方向に照合する。
4. 通信の成否とジョブの成否は、別の層で判定する。

## 再発防止

- `_PANEL_TOOLS` と `PANEL_AGENT_ACTIONS` のキーの一致を、テストで保証する。
- MCP の設定のコピーや `.mcp.json` は持たない（二重登録と版のずれを避ける）。登録は `bin/setup_mcp.py`（dry-run が既定、`--apply` で実行）が `claude mcp add` と `codex mcp add` で行う。
- 実機で確定した点: `current.json` のキーは version・bridgeProtocol・runtimeDir・serverDir（pythonBin は無い）。`premiere_pick` の op は 6 値（ripple を含む）。
- 実行確認は、Python のテスト 365 件と tool_coverage の 44 件まで（機械検証）。AI のタブからの実行と、Premiere 実機のプローブは未実施。

## 出典

- Cut & SRT の記録（2026-07-19〜09-07、v0.5.0 で MCP 17 種）と、Premiere Agent Kit の記録（v0.1.0、36 種）
