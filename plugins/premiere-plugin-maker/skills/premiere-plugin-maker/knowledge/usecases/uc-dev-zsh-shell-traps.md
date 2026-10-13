---
id: uc-dev-zsh-shell-traps
title: Mac で AI が使うシェルは zsh。環境変数の束が分割されず、`=` で始まる語が展開され、timeout が無い
kind: usecase
tags: [開発, macOS, zsh, bash, 環境変数, 語分割, timeout, シェル]
os: [mac]
premiere: ">=25.6"
status: verified
summary: AI が Mac で実行するシェルの操作は zsh 前提で書く。複雑な環境変数の組み立ては bash のスクリプトにして /bin/bash で実行し、待ちは perl の alarm で作る
parts: [packaging]
related: [uc-mac-bash-variable-japanese, uc-ai-cli-invocation-traps, uc-windows-powershell-traps, platform-mac]
---
## 症状

- `env $envs …` で、空白で区切った環境変数の束が 1 つの語になった。画面の写しを 3 枚撮ったのに、すべて同じ md5 になり、Chrome を疑って 15 分を失った。
- `echo ======` が止まった。
- `timeout` が exit 127（コマンドが見つからない）になった。

## 原因

- zsh は、クォートしていない `$var` を語に分割しない。
- zsh は、`=` で始まる語を、コマンドのパスに置換する。
- macOS には `timeout` コマンドが無い。

## 直し方

1. ループは `#!/bin/bash` のスクリプトにして、`/bin/bash` で実行する（zsh のまま使うなら `env ${=envs}`）。
2. 待ちは `perl -e 'alarm N; exec @ARGV'` で作る。
3. 区切りの行は `echo "-----"` のように、クォートする。

## 再発防止

- 画面の写しを撮ったら、md5 が重なっていないかを先に見る。
- zsh の予約変数（`status`・`path`）を変数名に使わない。
- 同じ系統の罠: `python -c` の f-string の中の引用符のエスケープは SyntaxError になる。二重引用符の中のバッククォートは、コマンドの置換になる。

## 出どころ

- 作者の開発メモ（2026、統合は 2026-10-04）。Mac の実機で確かめた。
