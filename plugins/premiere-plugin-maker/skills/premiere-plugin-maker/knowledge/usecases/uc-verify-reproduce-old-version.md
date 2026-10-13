---
id: uc-verify-reproduce-old-version
title: 「単体版では壊れない」は、呼び出し方の差。旧版を実際に動かして再現する
kind: usecase
tags: [検証, 再現, 旧版, 呼び出しの差, fps, XML の宣言]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 「A では壊れず B では壊れる」は、まず呼び出しの差を疑う。旧版を取り出して実行し、症状を再現する。Premiere に任せる工程は、XML の宣言で確かめられる範囲と、実機でしか確かめられない範囲に分ける
parts: [silence-cut]
related: [uc-fps-property-missing, uc-fps-conform-rate-trust, uc-verify-reproduce-with-real-data, uc-verify-show-used-value]
---
## 症状

視聴者から「60fps で無音カットすると、生成されたシーケンスが 30fps になる。単体版（/cut）では 60fps のままだった」との報告があった。

## 原因

単体版の `silence_cut.py` はプラグイン版と同じ中身だった。単体版は `--sequence-timebase` を渡さないので、レートを合わせる処理が発動しなかっただけ。カット後のシーケンスは、`project.importFiles([出力 XML])` で Premiere が作り、レートは出力 XML の `<rate>` で決まる。

## 直し方

1. 旧版を `git show <旧版のタグ>:<ファイル>` で取り出して実行する。
2. `--sequence-timebase 30` を渡すと、60fps の入力が timebase 30、長さが 246 フレームから 123 フレームになる症状を再現する（原因は別項目の fps の取り違え）。
3. 検証を 2 つに分ける。「再現」は旧版の実行、「再発防止」は 5 つのレート × 検出の成功・失敗・誤検出のテスト。安全網を外すと落ちる形にし、出力 XML の `<rate>` も機械で検証する。

## 再発防止

- Premiere が宣言どおりにシーケンスを作ることは、XML の宣言だけでは保証できない。実機でしか確かめられない範囲を明記して残す。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ記録（2026-07-25。欠陥は v0.7.6〜v0.9.1、修正は v0.9.2 以降）。旧版を実際に動かした再現と、現行版の HTTP 往復は機械検証。別の fps の事例で「ずれ 0」の結論が後に訂正されており、この結論への影響は未確認。
