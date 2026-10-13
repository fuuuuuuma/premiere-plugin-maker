---
id: uc-install-cep-python-upia-home
title: 配布版を仮のホームで試しても再現しない。CEP から見える python3 と UPIA の書き込み先の罠
kind: usecase
tags: [CEP, python3, UPIA, HOME, xcode-select, 配布, AGENTS.md]
os: [mac]
premiere: ">=25.6"
status: verified
summary: Premiere の CEP から使える python3 は /usr/bin/python3 だけ。UPIA と defaults write は HOME を偽装しても本物のホームに書く。配布 ZIP に AI 向けの指示を入れるなら、開発リポジトリの同名ファイルと衝突しないよう、配布時に生成する
parts: [packaging, cep-helper]
related: [ref-cep-extendscript, platform-mac, uc-install-udt-package-stale]
---
## 症状

- 仮のホームフォルダで配布版を試しても、現象が再現しない。
- Premiere の拡張から `python3` が使えない。
- 配布 ZIP に入れた指示ファイル（AGENTS.md）を、作業中の AI が自分への指示として読んでしまう。

## 原因

- Premiere（CEP）から見える `python3` は `/usr/bin/python3` だけで、コマンドライン・デベロッパ・ツールが入っていない Mac では、見かけだけあり、起動すると失敗する。
- UPIA（.ccx の導入）と `defaults write` は、HOME 環境変数を偽装しても、本物のホームに書く。そのため、HOME を変えたテストは、これらの書き込み先に効かない。
- 同じ名前の AGENTS.md / CLAUDE.md は、作業中の AI が読む。

## 直し方

1. インストーラが `xcode-select -p` で確かめ、無ければ `xcode-select --install` を開く。ガイドは「bash と打ってドラッグ」の形にする。
2. 配布用の指示は `packaging/AGENTS.package.md` に置き、ZIP を作るときに、AGENTS.md と、`@AGENTS.md` だけを書いた CLAUDE.md を生成する。
3. ZIP は `python3 tools/make_package.py` で作る（同じ内容なら同じバイト列になる）。

## 再発防止

- 配布先で未確認なのは、Intel Mac、Windows（非対応）、コマンドライン・デベロッパ・ツールが無い Mac。`xcode-select --install` の経路は、作者の Mac では試せていない。
- 同梱する書体が足りないときは、インストーラが日本語名で列挙する。

## 出どころ

- Effect & Design の作業記録（2026-09-19、v0.3.0〜v0.4.0）
