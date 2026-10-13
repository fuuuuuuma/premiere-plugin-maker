---
id: uc-ai-cli-not-on-server-path
title: ターミナルでは動く CLI が、常駐サーバーからは「見つかりません」になる
kind: usecase
tags: [AI, CLI, PATH, 常駐, nvm, 探索, フルパス]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: ターミナルの PATH と常駐サーバーの PATH は別物。導入先の候補を 1 つの関数で探してフルパスで実行し、見つからないときは探した場所を見せる。同じ探索を持つ入口を全部そろえる
parts: [local-server]
related: [uc-ai-which-not-usable, uc-dev-duplicate-logic-entries, uc-windows-daemon-process-paths, uc-mac-ffmpeg-detection]
---
## 症状

codex をターミナルでは使えるのに、「codex CLI が見つかりません」と出て字幕の処理が始まらない。「claude は動くが codex は動かない」のように、機械ごとの差も出た。

## 原因

常駐サーバーは、`which` と固定の 3 か所（`~/.local/bin`、`/opt/homebrew/bin`、`/usr/local/bin`）しか探さなかった。nvm・asdf・bun・npm の別の prefix に入れたものを見つけられない。状態確認・実行・診断で、それぞれ別の `which` を使っていたことも原因の一部。

## 直し方

1. 探す場所の候補を 1 つの関数にまとめる（`~/.bun/bin`、`~/.asdf/shims`、`~/.nvm/versions/node/*/bin`、`NPM_CONFIG_PREFIX`、Windows は nvm-windows、のちに `~/.claude/local` と `~/.volta/bin` を追加）。
2. 「which、だめなら候補のフルパス」で解決する 1 つの関数を作り、`which` を使っていた 8 か所・状態確認・AI タブをそれに統一する。
3. 見つからないときのエラーは、症状・理由・次の一手の 3 点にし、探した場所を書く。

## 再発防止

- 診断は「未発見」「未ログインの可能性」「古い CLI で機能が縮んだ」に分けて出す。
- `which` が何も返さないよう固定し、ダミーの実行ファイルが候補から見つかる統合テストを置く。
- 直しを反映するにはサーバーの再起動が要る。再起動すると認証の合言葉が変わるので、パネルも読み込み直す。

## 出どころ

- Cut & SRT の計画書と引き継ぎ記録（2026-07-20〜07-23）。ダミーの CLI を使った単体・統合テストで確かめた。テスターの環境での解消確認は記録が無い。
