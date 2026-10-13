---
id: uc-verify-panel-reload-only-bugs
title: パネルは読み込み直さないと動かせない。ID の取り違えや起動順の事故が実機まで分からない
kind: usecase
tags: [検証, UXP, パネル, Reload, DOM スタブ, 非同期, unhandled rejection]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: Reload でしか見えない事故は、HTML の ID と JS の参照の照合、評価順を再現する DOM スタブ、稼働中サーバーの実応答で事前に潰す。非同期のボタンは try/catch してパネルのログに出し、画面の作り直しでは ID・保存キー・起動順を変えない
parts: [ui-kit, logger]
related: [core-ui-rules, uc-verify-node-green-device-broken, uc-verify-test-double-defaults, uc-install-reload-layers]
---
## 症状

- UXP のパネルは Premiere で読み込み直して初めて動かせる。ID の取り違えや起動の順序の事故は、実機で見るまで分からない。
- 辞書の行の削除・承認・却下のボタンが失敗しても、画面にもログにもエラーが出なかった。

## 原因

- 検証が実機頼みだった。
- 非同期のボタンの処理で Promise が拒否されても（unhandled rejection）、誰も受け止めていなかった。

## 直し方

1. 非同期のハンドラは `try/catch` で囲み、パネルのログ関数に出す。
2. 読み込み直しの前に、テストで次を機械検査する。
   - JS が参照する ID が HTML に実在するか（文字列の直書き、動的に作る接頭辞、起動時に実際に要求された ID のすべて）。
   - 出力先が未設定のときにサーバーの仕事を呼ばないこと。
   - マーカー 1 点の追加の引数が固定されていること。
3. 稼働中のサーバーの実応答も確かめる（疎通の応答・出力先なしの要求が 400・出力先つきが 202 でその後に綺麗に失敗する）。

## 再発防止

- 13 タブへの画面の作り直しでは、全要素の ID・`data-setting`・保存キーを変えず、起動の処理は JS の末尾から動かさない。タブの順・全ページの実在・初期の表示ページを機械検査で固定した。
- 最終確認は、読み込み直した後の実機で行う。

## 出どころ

- Cut & SRT の引き継ぎ記録（2026-07-16〜07-23、Premiere 26.3）。読み込み直しの前の内部検証で、実機での確認は別。非同期ハンドラの try/catch 化はレビュー指摘による修正で、個別のテストは無い。
