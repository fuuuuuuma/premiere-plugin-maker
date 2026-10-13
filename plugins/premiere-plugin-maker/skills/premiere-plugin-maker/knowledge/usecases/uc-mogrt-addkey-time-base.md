---
id: uc-mogrt-addkey-time-base
title: キーフレームを打った時刻が約 1 時間ずれる（addKey の時刻は素材の入点基準）
kind: usecase
tags: [ExtendScript, addKey, キーフレーム, MOGRT, 入点, pproTicksIn, 時間基準]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: addKey の時刻はクリップ先頭ではなく素材の入点が基準。MOGRT の入点は約 3600 秒なので、先頭からの秒数に入点を足して打つ
parts: [ppro-kit, mogrt-text]
related: [ref-ticktime, ref-keyframe-interpolation, uc-fps-vfr-timebase]
---
## 症状

クリップの ticks 0 と 0.5 秒にキーを打ったのに、10.25 秒のコマで文字が動いていない。FCP XML の中で、MOGRT を `startTicks` で探しても一致しない。

## 原因

`addKey` の時刻は、クリップの先頭ではなく、入点（素材の中での開始位置。素材時間）を基準にしている。MOGRT の入点は 914440114308216 ticks（約 3600 秒）という大きな値なので、キーは「入点の約 1 時間手前」に打たれ、画面に現れなかった。XML の `<pproTicksIn>` も、素材側の入点を指しており、同じドナー（元になる MOGRT）から作った MOGRT なら、どれも同じ値になる。

## 直し方

1. 時刻基準の定数を「入点」として持つ（`ED_KEY_TIME_BASE = "inpoint"`）。
2. クリップの先頭から t 秒の位置に打つときは、`item.inPoint.ticks + t × TPS`（TPS は 1 秒あたりの ticks）で打ち直す。
3. XML の中でクリップを特定するときは、`startTicks` でなく、(`<track>`, `<start>` のフレーム番号) の組を鍵にする。

## 再発防止

- キーの位置は、書き出したコマと FCP XML の `<when>` で確かめる。
- 時刻の基準（クリップ先頭・シーケンス・素材の入点）は API ごとに違いうる。新しい API は、1 つのキーを打って読み戻すところから始める。
- ExtendScript と UXP の両方で同じだった。

## 出典

- Effect & Design の実機の記録（Premiere 26.5、2026-09-17）。書き出したコマと XML の `<when>` で確認
