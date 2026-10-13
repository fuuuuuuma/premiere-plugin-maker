---
id: uc-ai-cli-defaults-env-account
title: AI CLI の既定・環境変数・アカウントの種別で、モデルと認証の結果が変わる
kind: usecase
tags: [AI, CLI, モデル, 環境変数, アカウント, 401, 検証環境]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 外部 CLI はモデルと思考の深さを明示して呼ぶ。モデルの名前はアカウントの種別で変わるので、実応答で確かめてから選択肢に入れる。検証のときは、開発機の設定やシェルに残った API キーの環境変数が結果を変えていないか疑う
parts: [local-server]
related: [uc-ai-old-cli-rejects-flags, uc-ai-cli-invocation-traps, uc-verify-env-false-positive]
---
## 症状

- 字幕の処理で claude を使うと、ひどく遅い。
- ChatGPT のアカウントで使う codex に、素の `gpt-5.6` を指定すると拒否される。
- 開発機のシェルで claude の CLI を試すと 401 になり、約 3 分リトライしてから失敗する（確認のプログラムは 60 秒で時間切れ）。

## 原因

- CLI の既定に任せたため、開発機の重い設定（高性能のモデルに最大の思考量）を引きずった。
- ChatGPT のアカウント経由の codex では、モデルの名前がアカウントの種別で違い、`gpt-5.6-sol` だった。
- シェルに残っていた `ANTHROPIC_API_KEY` を claude の CLI が使い、401 になった。なぜ 401 になるかの仕組みは未解明。

## 直し方

1. モデルと思考の深さを明示する（字幕の claude の既定は `sonnet` と `low`。実測で 5.7 秒）。
2. codex の選択肢は、実際に応答を確かめた 3 つにする。
3. 手元で検証するときは `env -u ANTHROPIC_API_KEY` を付ける。ログイン時に環境変数を持たない常駐（launchd）は影響を受けない。

## 再発防止

- 選択肢に入れる前に、選択肢ごとに実 CLI の実応答を確かめる。
- 検証の結果がおかしいときは、プラグインより先に、手元の環境変数・設定ファイル・アカウントの種別を疑う。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の開発メモ（2026-07-19〜07-25）。実際の応答時間と 401 は実機で観察した。
