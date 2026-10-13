---
id: uc-mogrt-importmgt-track-rounding
title: 上のトラックが無いと、元のクリップを上書きしてしまう（importMGT のトラック指定）
kind: usecase
tags: [ExtendScript, importMGT, トラック, 丸め, 0始まり, addTracks, 上書き]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: importMGT のトラック番号は 0 始まりで、指したトラックが無いとトラックを作らず最上段へ丸める。挿入の前に上のトラックを足し、挿入後に入り先を確かめる
parts: [ppro-kit, mogrt-text]
related: [uc-uxp-mogrt-overwrite-unclear, uc-mogrt-design-apply-replaces, ref-cep-extendscript, feat-ed-design-apply]
---
## 症状

- 「元のクリップを残す」つもりで、元の 1 つ上のトラックに MOGRT を入れたのに、元のテロップが最上段（V2）にある実際のシーケンスでは、新しいクリップが V3 でなく V2 に入り、元を上書きした。
- `seq.importMGT(path, startTicks, 2, 0)` を V2 を選んだ状態で呼ぶと、V3 に入った。
- 置いたクリップの名前が、MOGRT の中の名前を変えても、「グラフィック」のままだった。

## 原因

- トラックの引数は 0 始まり。1 始まりのトラック番号を渡すと、そのまま「1 つ上」になる。
- 指したトラックが無い（上に空きが無い）と、`importMGT` はトラックを作らず、一番上の既存のトラックへ丸めて入れる。同じトラックの重なる区間は黙って上書きするのが、API の既定の動き。
- 最初に確認したシーケンスは、V3 が空のトラックとして既にあり、この場合を踏んでいなかった。
- クリップの表示名は、MOGRT の内部の名前の欄（SubClip・MasterClip の Name、ClipName、Title）とは別のもの。

## 直し方

1. 元のクリップは消さず、`disabled = true` にして残す。
2. 新しいクリップは、1 つ上のトラックへ入れる。上が無ければ、QE の `addTracks(1, 既存の本数, 0, 0, 1, 0, 0, 1)` で先に 1 本足す。足せなければ、何も変えずに失敗として止める。
3. 上の同じ時間に別のクリップがあれば、理由を出して止める。
4. 挿入のあと、入ったトラックを確かめ、予定と違えば失敗として扱い、取り消しを案内する。
5. 戻りの TrackItem の終わりは、`ti.end = Time` の代入で伸ばせる。名前は、置いたあとに `ti.name = 本文` で付け直す。

## 再発防止

- 最初の「合格」は、利用者の確認で穴が見つかって取り消し、再修正した。トラックが足りない実際のシーケンスで試す。
- 足したテストは、直す前のコードで落ちることを確かめてから通す。
- UXP 版の同じ問題は、`uc-uxp-mogrt-overwrite-unclear` に書いてある。

## 出典

- Effect & Design の実機の記録（2026-09-17〜09-18、Premiere 26.5 の ExtendScript）。2026-09-18 12:24 に、別の実シーケンスで再確認した
