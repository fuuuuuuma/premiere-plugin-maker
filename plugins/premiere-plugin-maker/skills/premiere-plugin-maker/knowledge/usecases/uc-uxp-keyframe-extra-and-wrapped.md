---
id: uc-uxp-keyframe-extra-and-wrapped
title: キーフレームが余分に付く・消せない・値が包まれて返る
kind: usecase
tags: [UXP, キーフレーム, createSetTimeVaryingAction, 範囲削除, 戻り値]
os: [mac, windows]
premiere: ">=26.0"
status: verified
summary: キーを打つと時刻 0 に余分な 1 本が付く。同じ取引で足したキーは消せない。値は { value } と一段包まれて返る
parts: [ppro-kit]
related: [core-transactions, uc-uxp-interp-same-transaction, ref-keyframe-interpolation, uc-uxp-transition-duration-ticks]
---
## 症状

- キーを 3 つ打ったのに 4 つ付き、余分な 1 本が時刻 0（クリップの入点の約 3600 秒前）にある。
- 同じ取引で足したキーを消そうとすると失敗する（"keyframe doesn't exist"）。
- 読んだ値が `{ value: 値 }` と一段包まれて返る（位置は PointF）。

## 原因

1. キーを打つには `createSetTimeVaryingAction(true)`（時間で変化する、をオンにする）が要る。再生ヘッドが 0 の位置にあるとき、オンにしたはずみで時刻 0 にキーが 1 本増える。途中にあれば増えない。オンにしないとキーが付かない。
2. `createRemoveKeyframeAction` は、Action を作る時点でキーの存在を確かめる。同じ取引で足すキーは、作る時点でまだ無いので消せない。
3. `getStartValue` もキーの value も、値を包んだ形で返る。

## 直し方

1. 入点より前を `createRemoveKeyframeRangeAction`（範囲で消す、これは通る）で消す。既存のキーも、範囲で消してから打ち直す。
2. 消すキーが「同じ取引で足したもの」にならないように、足す取引と消す取引を分ける。
3. 値を読むときは、包みを外して取り出す関数を 1 か所に作る。
4. 書いたあとにキーの数と値の形を確かめる。

## 再発防止

- UXP のキーの API は「同じ取引の中の整合」に厳しいと考え、取引を分けて書く。
- 書いたキーは `getValueAtTime` で読み返して確かめる。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09-18〜09-19）
- 値の包みを外す直し方は、読む側の推測を含む
