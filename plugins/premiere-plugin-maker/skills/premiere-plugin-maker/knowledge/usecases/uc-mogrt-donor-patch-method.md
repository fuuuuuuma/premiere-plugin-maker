---
id: uc-mogrt-donor-patch-method
title: UXP にグラフィックを作る API が無い（同梱 MOGRT をパッチして挿入する方法）
kind: usecase
tags: [MOGRT, ドナー, バイナリパッチ, insertMogrtFromPath, prgraphic, FlatBuffer, UXP]
os: [mac, windows]
premiere: ">=26.3"
status: partial
summary: 生成の API が無くても、同梱した MOGRT の blob を局所的にパッチして insertMogrtFromPath で入れれば、再編集できるグラフィックが作れる。尺の ticks は言語ごとに違い、MasterClip は 2 つある
parts: [mogrt-text, ppro-kit]
related: [ref-mogrt, uc-mogrt-first-uuid, uc-mogrt-second-insert-replaces, uc-mogrt-xml-synthesis-experiment, feat-cutsrt-shapes]
---
## 症状

UXP には、図形やテキストのグラフィックを新しく作る API が無い。PNG にして入れる方式では、あとから図形やテキストを再編集できない。

## 原因

ドナー（元になる MOGRT）は、言語ごとに違う構造を持つ。

- 尺の ticks は言語ごとに違う（en_US は 1250160912000 など）。固定値で書くと、en_US 以外で失敗する。
- `<MasterClip>` が 2 つある（Proxy Sequence と Graphic）。名前で引くと、取り違える。

## 直し方

1. 同梱した MOGRT（zip。`definition.json` と、言語別の `project*.prgraphic`）の、`ArbVideoComponentParam` の 3 つの `StartKeyframeValue` だけを、全言語にパッチする。
   - Source Text: u64 リトルエンディアンの長さ + UTF-16LE の JSON
   - Appearance
   - Path
   値は base64 で入った blob。FlatBuffer のマジック（0x11223344）は `blob[8:12]` にある。
2. パッチした MOGRT を、`SequenceEditor.insertMogrtFromPath` で挿入する。
3. 尺の ticks は、各ファイルから動的に検出する。固定値にしない。

## 再発防止

- 言語の差と、同名の要素は、実際のドナーの全言語を使った試験で確かめる。
- blob の規則は、1,059 個の blob で照合した（機械検証）。
- 注意: この方式は、凍結した経緯がある（`uc-mogrt-empty-graphic-misdiagnosis`）。挿入の落とし穴（ID の使い回し、`<First>`、フォントと文言）は、関連の事例を先に読む。

## 出典

- Cut & SRT の作業記録（2026-07-25、Classic Live Overlay と Basic Title）
- Effect & Design の実機の記録（2026-09-17、Premiere 26.5）
