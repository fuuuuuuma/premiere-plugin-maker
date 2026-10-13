---
id: uc-mogrt-telop-text-not-greppable
title: テロップの本文が XML を検索しても見つからない
kind: usecase
tags: [XML, テロップ, 本文, FlatBuffer, base64, GraphicAndType, 書き戻し]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: 本文の置き場は、MOGRT なら effect の name、旧来のテロップなら base64 の中の FlatBuffer の末尾にある。置き場は書き出した XML で実測して決め、別種のクリップに同じ方式が通じると決めつけない
parts: [fcpxml, mogrt-text]
related: [uc-mogrt-source-text-unreadable, ref-prtextstyle, ref-fcp7-xml]
---
## 症状

XMEML（FCP7 XML）にテロップを 139 枚置いて書き出し、`grep` で本文を探しても、見つからない。

## 原因

本文の置き場が、クリップの種類によって違う。観測では 2 通りあった。

- MOGRT のグラフィック 7 件は、FCP XML の `<effect><name>`（`GraphicAndType`）が本文そのもので、BinaryData は無い。
- 旧来の XMEML のテロップは、`<name>ソーステキスト</name>` の隣の `<value>` に、base64 で符号化された FlatBuffer が入っており、本文はその末尾の「4 バイトの長さ + UTF-8」として入っている。

## 直し方

1. 対象の XML で置き場を実測して決める。
2. BinaryData は、末尾から走査し、UTF-8 として読め、かつ長さが `len(decoded.encode())` と一致する部分を本文とする。

## 再発防止

- 書き戻すときは、3 つを同時に更新する。先頭の u32 リトルエンディアン（全体の長さ − 12）、`<hash>` の末尾 4 バイト（全体の長さ + 12）、文字列（バッファの末尾。全体の長さ = `align4(文字列の位置 + 4 + バイト数 + 1)`）。この不変条件は、139 個のバッファで確かめた。
- 別の機能で実証できた方式が、別の種類のクリップで通じるとは限らない。
- 未確認: XMEML では name 側が 147 種あり、本文 139 件と一致しなかった。`name` を優先する方式が、編集後の本文で通じるかは分からない。`<hash>` の先頭 12 バイトの意味も不明。実機への読み込みは確かめていない。

## 出典

- Effect & Design の記録（2026-08-20 の XMEML、2026-09-17 の FCP XML）。抽出は実際の XML で確認、書き戻しの不変条件は 139 個のバッファで確認
