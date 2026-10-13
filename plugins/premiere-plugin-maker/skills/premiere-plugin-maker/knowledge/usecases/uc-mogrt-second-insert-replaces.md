---
id: uc-mogrt-second-insert-replaces
title: 生成した MOGRT を 2 個目に挿入すると 1 個目が消える（内部 ID の使い回し）
kind: usecase
tags: [MOGRT, UUID, ObjectUID, ClipID, 置換, ドナー, 重なり]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: ドナーの内部 ID を全生成物で使い回すと、Premiere は同じアセットの再挿入と見なして置換する。参照整合を保って毎回振り直し、尺内の続けての挿入は挿入前に検査する
parts: [mogrt-text]
related: [uc-mogrt-first-uuid, uc-mogrt-donor-patch-method, uc-uxp-mogrt-overwrite-unclear, ref-mogrt]
---
## 症状

生成したシェイプの 2 個目を挿入すると、1 個目が消える。最初の実機での挿入では、同時に空のグラフィックも出た。尺（約 5 秒）の内側に続けて挿入すると、先のクリップが潰れた。

## 原因

ドナーの内部 UUID（`ObjectUID`・`ObjectURef`・`<ClipID>`・`<First>`・AudioTrack の `<ID>`）が、すべての生成物で同じだった。Premiere は、ID が同じものを同一のアセットとみなして、再挿入を「置換」として扱った。

## 直し方

1. すべての UUID を、参照整合を保ったまま再生成する（`_regenerate_ids()`）。既知の定数の ID は除く（`<First>` は触らない。`uc-mogrt-first-uuid`）。
2. 出力のファイル名に uuid4 の 8 桁を付ける。
3. パネルが、サーバーから受け取った尺（`durationSeconds`）で、挿入の前に重なりを検査する。

## 再発防止

- 2 回続けて生成し、`ObjectUID`・`ClipID`・`<First>`・`capsuleID`・ファイル名が重複しないことをテストする。
- 「ID で同一性を判定する形式」は、ID を漏れなく振り直し、複数個を続けて挿入する動作を、実機で確かめる。
- 記録の食い違い: Cut & SRT の失敗記録は「すべての ID を再生成」と書くが、`<First>` を振り直すと空描画になる。部品は `<First>` を除く側に合わせた。
- 症状の解消は、v0.9.6 の実機で確認したが、ID の再生成と重なりの検査の合算で、単独の検証ではない。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-25、v0.9.4 で欠陥、v0.9.6 で修正、日本語 UI）
