---
id: uc-verify-clean-env-tiers
title: 開発機と違う配布先を、段階を分けて検証し、未検証の範囲を書く
kind: usecase
tags: [検証, 配布, クリーン環境, fake HOME, PATH, check-only, 新規ユーザー]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 未導入の環境は、危険度の低い順に 3 段階（自動テスト、PATH を絞った確認、新規ユーザー）と、偽の HOME での合成の通し検証で調べる。偽装の限界と、どの段階まで済んだか（未検証）を正直に書く
parts: [packaging, local-server]
related: [uc-verify-other-os-without-machine, uc-install-dist-zip-gates, uc-install-verify-hijacks-agent, core-verification]
---
## 症状

開発機は Homebrew・ffmpeg・Python・各 CLI・常駐の登録がすべて済んでいて、配布先の「何も入っていない環境」を再現できない。受け取り側でしか出ない不具合（words の時刻が未シフト）があった。ブラウザで確かめた辞書の書き出し・読み込みや、`.srt` の自動取り込みは、UXP 実機では未確認のままだった。

## 原因

開発機の状態が配布先と違いすぎる。ブラウザでの検証は、UXP の `getFileForSaving` / `getFileForOpening` の動作を保証しない。

## 直し方

1. 段階 0: 全自動テスト（`python3 -m unittest discover -s tests -p "test_*.py"`）と、PATH を絞った `install.command --check-only` の実プロセスでの実行。書き込みをしないことも検査する。
2. 段階 1: `env -i HOME=<偽の HOME> PATH=/usr/bin:/bin ... bash .../install.command --check-only`。複製先の `server/ready`（認証の合言葉）は消しておく。
3. 段階 2: 新規の macOS ユーザーで、実際に導入する（30〜60 分）。
4. 偽の HOME では、同梱部品へのフォールバックと、音声合成の音声に実際の codex と文字起こしを通す合成の通し検証を実走した。

## 再発防止

偽装の限界を文書に書く。
- Python の候補は絶対パスを直接調べるので、「Python が無い」状態は再現できない。
- `launchctl list` は HOME を偽装しても、常駐の PID を拾う。
- Intel / Apple Silicon の判定は、起動時に決まる。

新規ユーザーでの Premiere の起動には Adobe ID のサインインが要る。Homebrew は全ユーザー共有なので、段階 2 の導入は既存ユーザー側にも影響する。

## 出どころ

- Cut & SRT の導入の検証手順書と引き継ぎ記録（2026-07-14〜07-26、Premiere 26.3）。段階 0・1 は実測済み、段階 2 は手順書のみ。UXP の 3 点（辞書の書き出し・読み込み、`.srt` の自動取り込み）は未確認。
