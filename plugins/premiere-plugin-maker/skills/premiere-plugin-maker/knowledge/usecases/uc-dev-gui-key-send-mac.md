---
id: uc-dev-gui-key-send-mac
title: API で範囲を削除できず、macOS でキー送信に頼った経路の実測
kind: usecase
tags: [開発, macOS, キー送信, Quartz, CGEvent, アクセシビリティ, キャリブレーション, 最終手段]
os: [mac]
premiere: ">=25.6"
status: verified
summary: Premiere は画面の部品の階層をアクセシビリティに出さない。キー送信の自動操作は、フォーカス・座標・権限に依存するので最終手段にする。使うなら Quartz でクリックしてフォーカスを移し、キーの押下に間を置く
parts: [commands]
related: [uc-uxp-no-razor-api, uc-uxp-shortcut-commands-not-listed, uc-mac-shortcut-nsuserkeyequivalents, uc-uxp-api-doc-vs-device]
---
## 症状

UXP の API では範囲を削除できないので、キー送信でリップル削除を起こしたい。しかし AppleScript の keystroke は、キーを奪う、メニューのクリックは focused panel に依存する、cliclick はアクセシビリティの問題がある、といずれも使えなかった。

## 原因

Premiere は、アクセシビリティにパネルの階層を公開しない（AXLayoutArea の子の数が 0）。ウィンドウの一覧も単一のウィンドウしか見えない。そのため、タイムラインへのクリックは絶対座標になり、キャリブレーション（位置の較正）が必須になる。

## 直し方

1. Python の Quartz（CGEventPost）で、タイムラインのタブをクリックしてフォーカスを移す。
2. F キーを送り、ショートカットに割り当てた「リップル削除」に、in / out の範囲を削除させる。
3. Python にアクセシビリティの権限と `pyobjc-framework-Quartz` を入れる。
4. `kCGEventSourceStateHIDSystemState` で IME の影響を避ける。キーの押下は、down → 30ms 保持 → up にする。
5. Undo は、区間数 × 2 回の Cmd+Z。

## 再発防止

- 区間は後ろから順に処理する。
- GUI の自動操作は最終手段にする。のちに XML の往復の方式へ移り、キー送信は使わなくなった（推測）。

## 出どころ

- Cut & SRT の初期の作業記録（2026-05-01、v2.2〜v2.6、Mac / Premiere 2026 / Python 3.14）。実機で確かめた。
