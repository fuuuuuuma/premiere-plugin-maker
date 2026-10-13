---
id: uc-install-udt-connects-once
title: 後から立ち上げたローダーに Premiere はつながらない。UDT 型の読み込みは起動時の一度きり
kind: usecase
tags: [UDT, 読み込み, WebSocket, 起動順, 開発者モード]
os: [mac]
premiere: ">=25.6"
status: verified
summary: 開発者モードの Premiere は、起動時に一度だけ 127.0.0.1:14001 のローダーへつなぎにいき、リトライしない。ローダーは Premiere より先に起動する
parts: [packaging]
related: [uc-install-auto-load-frozen, uc-install-udt-package-stale, core-dev-loop]
---
## 症状

UDT と同じ役目のサーバー（`127.0.0.1:14001` で待ち受け）を、Premiere の起動後に立ち上げた。4 分以上待っても、読み込みの接続が一度も来なかった。

## 原因

開発者モードの Premiere は、起動時に自分から 127.0.0.1:14001 へ接続しにいく（UDT 側は待ち受けるだけ）。接続に失敗してもやり直さない。

## 直し方

1. 読み込み用のサーバーを、Premiere より先に起動する。順序を手順に書く。
2. 状態は設定ファイルで確かめる。開発者モードかどうかは、Mac なら `/Library/Application Support/Adobe/UXP/Developer/settings.json`。過去に読み込みに成功したかは、登録簿（`premierepro.json`）。

## 再発防止

- UDT 型の読み込みは「起動時の一度きり」なので、起動順をガイドに明記する。
- やり取りの形（`ready` → `initRuntimeClient` → `Plugin load` → `reply`）は、非公式のプロトコルで、再現は未検証。当てにして自動化しない。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-28、実機で確認）
