---
id: uc-mogrt-xml-synthesis-experiment
title: スタイル済みテロップを XML で作れるか分からず、機能が止まっていた（実験の進め方）
kind: usecase
tags: [実験, XMEML, Source Text, PNG, ドナー, 判定基準, 設計判断]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 実機でしか分からない前提は、結果の場合分けと判定の手順を先に決め、道具を作ってから 1 往復で実験する。この方式は PNG 合成を経て、ドナー MOGRT のパッチに置き換わった
parts: [fcpxml, mogrt-text]
related: [uc-mogrt-donor-patch-method, uc-mogrt-source-text-unreadable, ref-mogrt]
---
## 症状

「スタイル付きのテロップが入った XML から、文字だけ差し替えて読み込み直せば、成立するか」が分からず、箇条書きの生成と、SRT の自動配置の機能が止まっていた。

## 原因

XMEML の書き出しには、Source Text の BinaryData が含まれる。それを差し替えて取り込めるかは、実機でしか分からなかった。

## 直し方

1. 差し替えの道具を先に作る（`replace_source_text(encoded, new_text)`。末尾に最も近い「u32 リトルエンディアンの長さ + UTF-8」だけを差し替える）。
2. 結果の判定を、実験の前に決める。
   - A: 文字だけが変わり、スタイルは保たれる
   - A': 一部のスタイルが欠ける
   - B: XML に本文が入っていない
   - C: 取り込みに失敗する
3. 10 分の 1 往復で試す。

## 再発防止

- 差し替えは、差し替えたあとの XML を読み直して、指定した位置だけが変わったかを自分で検証する形にする。
- 経緯: この方式は、ffmpeg の drawtext で合成した PNG（フォントを直接指定し、straight alpha に変換）を経て、v0.9.4 でドナー MOGRT のパッチ（`uc-mogrt-donor-patch-method`）に置き換わった。判定 A/A'/B/C の結果は、資料に残っていない。実機では「生成そのものは成功」という記録のみ（2026-07-24）。

## 出典

- Cut & SRT の実験の記録と作業記録（2026-07-23〜24、v0.8.0〜v0.9.1、Premiere Pro 2026）。合成した XMEML の往復と PNG の実ファイル検証まで
