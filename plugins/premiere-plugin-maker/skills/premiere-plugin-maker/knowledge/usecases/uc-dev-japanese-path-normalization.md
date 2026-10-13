---
id: uc-dev-japanese-path-normalization
title: 日本語のパスの罠（NFC / NFD の混在、URL のパーセントエンコード、git の 8 進エスケープ）
kind: usecase
tags: [開発, 日本語, パス, NFC, NFD, URL.pathname, git, quotepath, macOS]
os: [mac]
premiere: ">=25.6"
status: verified
summary: 日本語のパスは、見た目が同じでもバイト列が違う。鍵にする前に NFC に正規化し、URL とパスの変換経路を揃え、git は core.quotepath=false で動かす
parts: [fcpxml, packaging]
related: [ref-fcp7-xml, uc-install-zip-japanese-names, platform-mac]
---
## 症状

- 同じスキルが 2 件に数えられる（文字数が 62 と 63）。
- `fs.existsSync(new URL(...).pathname)` が、いつも false になる。
- `git subtree push` が、573 コミットを処理した後に `fatal: assertion failed` で止まる。

## 原因

- macOS は、経路によって日本語のファイル名を NFD（濁点を分けた形）か NFC で返す。
- `new URL().pathname` は、日本語をパーセントエンコードする。
- git は既定（`core.quotepath` が true）で、非 ASCII の文字を 8 進のエスケープにする。

## 直し方

1. パスを鍵にする前に、`.normalize('NFC')` をかける。
2. `fs` には、URL のオブジェクトのまま渡す（`.pathname` を取り出さない）。
3. git は `git -c core.quotepath=false` を付ける（subtree、`diff --cached --name-only` も）。

## 再発防止

- 着手時に、「同じ実体が 2 件出ていないか」「上書きの設定が効くか」を 1 回測る。
- FCP XML の `pathurl` でも同じ注意が要る（推測）。

## 出どころ

- 作者の開発メモと Cut & SRT 周辺の失敗記録（2026、統合は 2026-10-04）。Mac の実機で確かめた。
