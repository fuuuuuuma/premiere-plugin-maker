---
id: uc-mogrt-first-uuid
title: 作った MOGRT が空のグラフィックになる（First の UUID まで振り直した）
kind: usecase
tags: [MOGRT, UUID, First, MediaType, ドナー, 描画, insertMogrtFromPath]
os: [mac, windows]
premiere: ">=26.3"
status: verified
summary: ID の振り直しで、メディア種別を示す定数の UUID（First）まで変えると、挿入はできるのに描画が空になる。アセット固有の ID と、型を示す定数を区別し、後者は触らない
parts: [mogrt-text]
related: [uc-mogrt-second-insert-replaces, uc-mogrt-empty-graphic-misdiagnosis, ref-mogrt, feat-ed-design-apply]
---
## 症状

ドナー（元になる MOGRT）から作り変えた MOGRT が、挿入は成功するのに、描画が空になる。

## 原因

ID を振り直す処理（`_regenerate_ids`）が、`<First>` まで振り直していた。`<First>` は、アセット固有の ID ではなく、メディアの種別を示す定数の UUID（映像は `228cda18…`、音声は `80b8e3d5…`）で、対になる `<MediaType>` と一致していなければならない。別の値にすると食い違い、描画が空になった。

## 直し方

1. ID の再生成から、`<First>` を除外する。それで描画が正しくなり、`insertMogrtFromPath` と `importMGT` の両方で挿入できた。
2. 実機で、変数を 1 つずつ元に戻して、どこで空になるかを切り分ける。
3. 単体テストで、blob の復号と、UUID の一意性を確かめる。

## 再発防止

- ID を機械的に振り直すときは、「そのアセット固有の ID」と「型を示す定数」を区別する。
- 記録の食い違い: Cut & SRT の失敗記録には「`<First>` も振り直す」と書かれている。Effect & Design の実機の検証では、`<First>` を振り直すと空になった。キットの部品は、振り直さない側に合わせた。
- 2026 形式の Text 部品へ移植した版は、`importMGT` が「Loading… 30%」で固まったため、blob だけを差し替える版を既定にした。

## 出典

- Effect & Design の実機の記録（2026-09-17、Premiere 26.5、macOS）。修正の前後を、書き出したコマで確認した
