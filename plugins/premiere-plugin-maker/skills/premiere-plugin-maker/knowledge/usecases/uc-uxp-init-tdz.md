---
id: uc-uxp-init-tdz
title: 起動で ReferenceError が出る（宣言前の const）
kind: usecase
tags: [UXP, 起動, TDZ, const, readyState, 初期化]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 起動の処理が const の宣言より前に残ると、UXP が readyState を complete にした状態で評価するため、未初期化の const に触れて落ちる。起動の処理はファイルの最後に置く
parts: [ui-kit]
related: [core-ui-rules, uc-uxp-require-relative]
---
## 症状

別のプラグインの機能を、タブとして取り込んだあと、取り込んだタブだけが使えなくなり、ログが 2 重に出た。取り込んだタブのイベントの配線が全部だめになった（本体のタブは配線済みで無事に見えるので、気づきにくい）。エラーは `Cannot access 'ccSlots' before initialization`。

## 原因

起動の処理（`if (document.readyState !== "loading") init()`）が、取り込んだ機能の `const` の宣言より前に残っていた。追記のコードをファイルの末尾に足したため、起動の処理より後ろに `const` が来てしまった。

UXP は、スクリプトを評価する時点で、すでに readyState が「loading」でないことがある。その場合、`init()` が評価の途中で同期的に実行され、まだ初期化されていない `const` に触れて、TDZ（宣言前に触れる禁止の区間）のエラーになる。

## 直し方

1. 起動の処理を、ファイルの一番最後に移す。
2. `init()` は、二重にイベントを登録しないよう、必ず一度だけ実行する。
3. 取り込み元の画面をそのままコピーすると二重になるので、画面は統合先の共通部品に任せ、ロジックだけを移す。
4. document 全体のキー入力のショートカットは、修飾キー（Cmd / Ctrl / Alt）つきを除外する。除外しないと、本体の Cmd+数字を奪う。

## 再発防止

- `check.py` の J012 が、起動の処理がファイルの末尾にないことを警告する。
- readyState を complete にした DOM の偽物で評価順を再現する試験を持つ。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ書（2026-07-16、v0.4.0 より前、Premiere 26.3）
- 偽物の DOM で再現して直し、同日の実機でパネルが 8 つのタブで表示されたことを確認した。そのため partial
