---
id: uc-uxp-interp-same-transaction
title: キーの補間がイーズにならない
kind: usecase
tags: [UXP, キーフレーム, 補間, イーズ, 焼き込み, 取引]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 同じ取引の中ではキーの補間を変えられず、無言で効かない。別の取引にすると取り消しが 2 回になるので、補間の結果を 1 コマごとの直線キーに焼き込む
parts: [ppro-kit, motion-bake]
related: [core-transactions, ref-keyframe-interpolation, uc-uxp-effect-params-before-commit, uc-uxp-keyframe-extra-and-wrapped, feat-ed-motion]
---
## 症状

UXP の 1 取引（取り消し 1 回）でキーフレームを書くと、補間（イーズ）が効かず、直線に動く。従来の ExtendScript の経路と並べて書き出すと、動きが違う（色ずれの分かれ幅、スライドの速さなど）。

## 原因

同じ取引の中では、補間を変えられない。`createSetInterpolationAtKeyframeAction` も `kf.setTemporalInterpolationMode` も、エラーにならずに無言で効かない（足したキーがまだ存在しないため）。別の取引に分ければ効くが、そうすると取り消し（Cmd/Ctrl+Z）が 2 回必要になる。

## 直し方

Premiere が描く曲がり方を、先に自分で計算して、1 コマごとの直線キーにして書く（焼き込み、`bake`）。

1. 数値の直線区間は両端のキーだけでよい。
2. hold（次のキーまで一定）は、次のキーの直前のコマに同じ値を置く。
3. ベジェ曲線と位置（道筋が曲がる）は、1 コマごとにキーを置く。
4. キーは 1 本のプロパティに 1200 個までにする。長い繰り返しは、何コマおきかに間引く。

曲線の式は ref-keyframe-interpolation に実測式がある。

## 再発防止

- 従来の経路と UXP の経路で、同じアニメを書き出し、全コマを比べて確かめた。
- キーが増えると負荷が増えるので、重さは実機で見る。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09-19）
- Cut & SRT の画面ズームも同じ方法で焼く。ただしそちらは計算の機械試験のみで、キーの重さと見た目は実機で確かめていない
