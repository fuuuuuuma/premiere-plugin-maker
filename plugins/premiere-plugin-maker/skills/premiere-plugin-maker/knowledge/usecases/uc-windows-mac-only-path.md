---
id: uc-windows-mac-only-path
title: Windows でだけ「見つかりません」になる。Mac 専用の探索とエンコーディングを持ち込んだ
kind: usecase
tags: [Windows, 流用, /Applications, パス, MOGRT, text=True, エンコーディング]
os: [windows]
premiere: ">=25.6"
status: partial
summary: Mac 用に作った部品を Windows に流用するときは、固定のパスとエンコーディングの既定を、OS をまたいで grep する。画面が捨てていた失敗の理由は、結果に添える
parts: [mogrt-text, ppro-kit]
related: [platform-windows, uc-windows-cp932, uc-uxp-mogrt-overwrite-unclear]
---
## 症状

Windows の画面で、デザインを当てるボタンだけが「Basic Title.mogrt が見つかりません」と言う。

## 原因

Mac 専用の拡張から写した処理が、手本になる MOGRT（ドナー）を `/Applications` の下でしか探していなかった。Windows では、Premiere は `%ProgramFiles%\Adobe\Adobe Premiere Pro *\Essential Graphics` にある。さらに、`subprocess.run(text=True)` は cp932 で絵文字を書けず、落ちた。

「本文を読めなかった」という報告の真因は、確定していない。元の設計書は、Windows をスコープ外として凍結し、`/usr/bin/python3` を前提にしていた。

## 直し方

1. ハッシュの検査で「元と同一」を保つ写しは、改変しない。その代わりに、呼び出す側の別ファイルで、探す関数を差し替える。
2. 差し替えた関数は、Windows の場所（`%ProgramFiles%\Adobe\Adobe Premiere Pro *\Essential Graphics`）も探す。
3. 結果を受け取る経路を、UTF-8 に固定する。
4. 画面が捨てていた失敗の理由を、結果に添えて表示する。

## 再発防止

- 配布の前に、`/Applications`・`~/Library`・`text=True` を grep する。
- Mac 製の部品を流用するときは、固定のパスとエンコーディングの既定を、OS をまたいで点検する。
- Windows 実機での再確認は待ち。

## 出どころ

- Cut & SRT の作者の開発メモと Effect & Design の設計書（2026-09-27、v0.12.0）
