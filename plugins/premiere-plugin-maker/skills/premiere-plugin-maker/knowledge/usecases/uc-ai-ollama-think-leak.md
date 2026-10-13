---
id: uc-ai-ollama-think-leak
title: Windows のローカル LLM（Ollama）で、思考の文章が応答に混ざり、途中でやめられない
kind: usecase
tags: [AI, Ollama, Windows, qwen3, 思考モデル, think, キャンセル]
os: [windows]
premiere: ">=25.6"
status: unverified
summary: 思考モデルは API の think=False だけでは思考が漏れる個体がある。プロンプトの /no_think も併用し、非ストリームは途中キャンセルできないと割り切って上限時間で守る
parts: [local-server]
related: [uc-ai-engine-registry, uc-ai-prompt-no-system-no-session, uc-windows-guide-python-limit]
---
## 症状

- ローカルで動かす qwen3 の「考えている過程」の文章が、応答の本文に混ざる個体がある。
- 生成を途中でキャンセルできない。

## 原因

- API の `think=False` だけでは思考を止めきれない個体がある。
- 応答を一度に受け取る（ストリームにしない）方式で呼んでいるため、途中で中断する手段が無い。上限はタイムアウト（900 秒）だけだった。

## 直し方

1. API のフラグに加えて、プロンプト側のソフトスイッチ `/no_think` も併用する。
2. 生成する長さの上限（`num_predict`）を入力の大きさに連動させる。
3. キャンセルは据え置き（できない）と割り切り、画面にもそう書く。
4. 選べるモデルは小さな一覧（既定は qwen3:4b）にし、取得済みかどうかは `/api/tags` の完全一致で判定する。
5. 「Ollama に接続できません」は、未起動かモデル未取得を意味すると案内する。

## 再発防止

- Ollama の状態確認・生成・経路選択のテストを、Windows 向けの移植のテストに入れる。

## 出どころ

- Cut & SRT の Windows 対応の記録（2026-07-17〜07-19）。テスターの環境から出た修正を取り込んだもので、作者の実機では未確認。
