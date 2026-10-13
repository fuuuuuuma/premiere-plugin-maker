---
id: uc-mogrt-empty-graphic-misdiagnosis
title: 生成した MOGRT が「空のグラフィック」になる（誤診が 3 回続いて凍結）
kind: usecase
tags: [MOGRT, 空グラフィック, 誤診, Sequence ID, Keyframes, 凍結, 検証]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 挿入は成功するのにレイヤーが空になる。不透明度 0 説と Sequence ID 不一致説は 2 つとも直しても実機で直らなかった。実在の欠陥を直したことと症状が消えたことは別で、根治は実機の前後確認まで宣言しない
parts: [mogrt-text]
related: [uc-mogrt-first-uuid, uc-mogrt-binaryhash-unknown, uc-mogrt-localized-name-lookup, ref-mogrt, feat-cutsrt-shapes]
---
## 症状

パッチで作った MOGRT を挿入すると、挿入そのものは成功するのに、クリップが空になる。レイヤーの一覧が完全に空で、不透明度は 100%。エラーは出ない。日本語 UI の Premiere で起きた。

## 原因

確定していない。2 つの説が出て、どちらも外れた。

1. 「空の `<Keyframes>` は不透明度 0 を意味する」説。実測で否定された。
2. 「`definition.json` の言語別の ID と、`.prgraphic` の `<Sequence ObjectUID>` が一致していない」説。これは実在の欠陥だったが、直しても空のままだった。

残った容疑は、blob のハッシュ（`uc-mogrt-binaryhash-unknown`）。また、のちに別の件で分かった、`<First>` まで振り直していた問題（`uc-mogrt-first-uuid`）が、本当の原因だった可能性がある（推測）。

## 直し方

1. 言語別の `.prgraphic` をパッチして、Sequence UID を `definition.json` へ書き戻し、リンクを検査する関数（`_assert_sequence_ids_linked`）で確かめた。
2. それでも実機で空は直らず、シェイプのタブは撤去した（v0.9.9）。

## 再発防止

- ID を振り直すときは、外部の参照（`definition.json`）まで同期して検査する。
- 合成した試験用のドナーで 43 件が緑でも、実機は空だった。実際のドナーを使った検証を置く。
- 実在の欠陥を直したことと、症状が消えたことは別。根治は、実機での前後の確認まで宣言しない。「根治」の報告が 3 回連続で外れた。
- 記録の食い違い: 引き継ぎ文書の旧い記述（空の Keyframes による静止化など）を原因そのものとしているが、あとの訂正と合わない。キットは訂正の側に合わせた。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-25、v0.9.4〜v0.9.9、日本語 UI、Classic Live Overlay）。出力 XML の実測とテストまで（機械検証）
