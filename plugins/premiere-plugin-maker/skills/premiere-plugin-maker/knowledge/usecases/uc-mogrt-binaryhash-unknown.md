---
id: uc-mogrt-binaryhash-unknown
title: blob を書き換えたときの BinaryHash の規則が割れない
kind: usecase
tags: [MOGRT, BinaryHash, ハッシュ, blob, 総当たり, 診断, 効かなかった試み]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: 内容のハッシュは解読に固執せず、触らない版と代用値の版を対にして実機で判定する。「実害なし」は検証するまで推定にとどめる
parts: [mogrt-text]
related: [uc-mogrt-empty-graphic-misdiagnosis, uc-mogrt-first-uuid, ref-mogrt]
---
## 症状

MOGRT の blob を書き換えたとき、Premiere が `BinaryHash` を検証して、書き換えた blob を黙って捨てるのかどうかが分からなかった。空のグラフィックの、最後に残った容疑だった。

## 原因

未確定。`BinaryHash` の末尾 8 桁（16 進）は「blob の長さ + 12」で、1,059〜1,318 件で反例が無かった。先頭の 24 桁（96 ビット）の規則は解けなかった。ダイジェスト（内容から計算した値）なのか、単なる一意のキーなのかも、分からない。

総当たりで調べたが、md5・sha 系・blake2・murmur3・xxhash・cityhash・crc32 などは、すべて一致しなかった。

## 直し方

1. 先頭の 24 桁は、`md5(新しいデータ)` の先頭 24 桁で代用する。
2. 切り分けの手順: 診断用のスイッチ（`CUTSRT_SHAPE_PROBE=1`）で、blob を一切書き換えない MOGRT を作る。元の絵が出れば、BinaryHash は無罪とみなせる。
3. ハッシュだけを違えた対を実機に挿す診断の梯子（7・8 番）で、検証の有無を切り分ける。

## 再発防止

- 割れない検証値は、割ろうとせず、対を作って実機で判定する。
- 当時の「実害なし」は、推定でしかなかった。検証するまで、結論として書かない。
- Premiere 側のハッシュ検証の有無は、実機で確かめていない。

## 出典

- Cut & SRT の失敗記録と作業記録（2026-07-25、v0.9.4〜v0.9.9、Classic Live Overlay）
