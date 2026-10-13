---
id: uc-windows-guide-python-limit
title: Windows の導入ガイドの空欄（Python の上限・ログの場所）を、確かめずに前提で埋めそうになった
kind: usecase
tags: [Windows, Python, wheel, ガイド, 一次情報, PyPI, ログ]
os: [windows]
premiere: ">=25.6"
status: partial
summary: 対応する Python の範囲は、全ての依存について Windows 向けの wheel の提供で決める。ガイドの前提やログの場所は、一次情報で確かめる。「別の作業が確定した」という前提は、差分やコミットで裏取りする
parts: [packaging]
related: [platform-windows, uc-mac-intel-degraded, uc-install-support-pack]
---
## 症状

Windows 版の導入ガイドの「Python の上限」と「インストーラのログの保存先」が、TODO のまま埋まらなかった。

## 原因

「互換性の調査が Python の上限を確定済み」という前提が誤っていた。その調査の範囲は、Premiere 側の API だけだった。Windows のインストーラは、`Write-Host` で画面に出すだけで、ログを保存していなかった。

## 直し方

1. PyPI の JSON API で、`ctranslate2`・`onnxruntime`・`av`・`tokenizers`・`numpy` の `win_amd64` の wheel が 3.14 までそろっていることを確かめる。実用の範囲を 3.10〜3.14 にした。
2. ログは、サーバーが書く場所（`%LOCALAPPDATA%\<名前>\Logs\...err.log`）を案内する。

## 再発防止

- 新しい Python が出たら再確認する。
- 「別の作業が確定した」という前提は、差分とコミットで裏取りする。
- 実機での pip の実行は未実施で、PyPI のメタデータとスクリプトの読解だけで決めた。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-26、プラグイン 0.9.10〜0.9.11）
