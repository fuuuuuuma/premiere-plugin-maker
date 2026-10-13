---
id: uc-install-zip-japanese-names
title: 日本語名を含む配布 ZIP の罠。文字化け・実行権限の消失・拡張属性・OS の混入物
kind: usecase
tags: [配布, ZIP, UTF-8, 実行権限, 拡張属性, zsh, 日本語]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: ZIP は「開ける」だけでなく、ファイル名のフラグ・実行権限・拡張属性・OS ごとの混入物を全エントリで検査する。OS 標準の zip 作成は UTF-8 のフラグを立てない
parts: [packaging]
related: [uc-install-dist-zip-gates, uc-install-unsigned-os-protection, platform-cross]
---
## 症状

- macOS の `ditto -c -k` や zip で作ると、日本語のファイル名（導入ガイド）が文字化けする。UTF-8 のフラグ（bit 11 = 0x800）が立たない。`unzip -t` は通ってしまう。
- ZIP で転送すると、`.command` の実行権限が消える。隔離の印（`com.apple.quarantine`）が付くと、起動に失敗する。

## 原因

- OS 標準の ZIP 作成は、UTF-8 のフラグを立てない。
- OS が作る不要なファイル（ランチャーなど）の混入を調べる検査が、`server/` の直下だけを見ていて、深い階層（`server/vendor/…`）の物を見逃した。
- zsh の小文字の変数 `path` は、`PATH` と連動する。検査のループで `path` を使うと、次の反復から `unzip` や `shasum` が `command not found` になる。

## 直し方

1. `scripts/make_dist_zip.py` のように、Python の `zipfile` で ZIP を作る（日本語名には 0x800 が自動で付く）。
2. `.command` には `external_attr` で 0755 を設定する。生成後に `xattr -c` で拡張属性を消す（`com.apple.provenance` は許容）。トップフォルダは固定の名前にする。
3. シェルのループ変数は `path` や `status` を避け、`entry_name` のような名前にする。

## 再発防止

- `ZipInfo.flag_bits & 0x800`、正しいパスでの `getinfo()`、`testzip()` を確かめる。
- Windows 向け ZIP に `.command`/`.plist` が 0 件、Mac 向け ZIP に `.bat`/`.ps1` が 0 件であることを、全エントリで検査する。
- 別の場所へ展開して、実行権限と隔離の印が付いていないことを確かめる。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-20〜07-25、機械検証のみ）
