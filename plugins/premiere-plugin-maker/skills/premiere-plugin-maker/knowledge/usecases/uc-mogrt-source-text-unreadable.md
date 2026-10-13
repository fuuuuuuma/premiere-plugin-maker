---
id: uc-mogrt-source-text-unreadable
title: テロップの本文（Source Text）が API で読めない
kind: usecase
tags: [UXP, ExtendScript, Source Text, getValue, OTIO, BinaryData, ComponentParam]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: Source Text は複合型で、ExtendScript の getValue は 1 文字の文字化けを返し、UXP の ComponentParam は拒否する。OTIO の書き出しから BinaryData を取って読む。書き込みは setValue で効く
parts: [ppro-kit, fcpxml, mogrt-text]
related: [uc-mogrt-telop-text-not-greppable, uc-mogrt-binary-rule-without-data, uc-mogrt-otio-track-pick, ref-prtextstyle]
---
## 症状

- ExtendScript の `getValue()` が、本文でなく "Ƥ" の 1 文字だけを返す。
- UXP の `ComponentParam.getValueAtTime()` が、Source Text を「複合型なので扱えない」と拒否する。

## 原因

Source Text は、文字・書体・装飾が 1 つの blob（かたまりのバイト列）に入った複合型。`getValue` の戻りは、そのバイト列を文字列として見せたもので、"Ƥ" は blob の長さ（0x01A4）が文字として出たものだった。UXP の公開 API は、複合型を扱わない。

設計書は当初「getValue で読む」としていたが、実機で覆った。

## 直し方

1. `ProjectConverter.exportAsOpenTimelineIO()` で OTIO（OpenTimelineIO。タイムラインの交換形式）を書き出す。
2. OTIO の中の BinaryData を Base64 から復号し、blob の末尾の「リトルエンディアンの長さ + UTF-8 の本文」を読む。FCP XML 経由でも同じ読み方ができる。
3. 書き込みは `setValue()` が効く。「書けるが読めない」型だと分かった。
4. 書き出した OTIO の一時ファイルは数十 MB になるので、書き出した側が `finally` で必ず消す。

## 再発防止

- 複合型は「書けるが読めない」ことがある。読み取りが要る機能は、最初から OTIO や FCP XML 経由で設計する。
- 未確認: 「API 自体が無い」こと、スタイルの書き換えができないことは、確かめていない。AI によるスタイルの書き換えは、提案までにとどめた。

## 出典

- Effect & Design の実機の記録（Premiere 26.3 の UXP、26.5 の ExtendScript）
- Cut & SRT の失敗記録と作業記録（2026-07-14〜09-17）
