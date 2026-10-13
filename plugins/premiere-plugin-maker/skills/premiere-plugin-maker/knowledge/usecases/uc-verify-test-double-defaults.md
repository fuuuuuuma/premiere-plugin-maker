---
id: uc-verify-test-double-defaults
title: Node の VM・DOM スタブ・タイマーのスタブのテストは、本番を再現しない
kind: usecase
tags: [検証, テスト, スタブ, Node VM, DOM, タイマー, 既定値, 待ち時間]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: スタブが本番と同じ既定値・型・遅延を持つかは、別に固定しないと、緑は信用できない。待ち時間の改善は実時間で確かめる
parts: [probe, ui-kit]
related: [uc-verify-stub-wrong-shape, uc-verify-node-green-device-broken, uc-verify-regression-fails-when-broken]
---
## 症状

- 一括置換のテストが、実装と無関係に赤になったり緑になったりした。
- ジョブの完了を調べる間隔を、最初の 5 回だけ 300ms にしたが、Node のテスト 258 本が緑のままで、効果を検証できなかった。

## 原因

1. VM（Node の仮想環境）の中で作ったオブジェクトのリテラルは、`assert.deepStrictEqual` がプロトタイプまで比べるので、不一致になる。
2. `const` は VM のグローバルに現れない。
3. 要素のスタブは HTML の属性を解釈しないので、`<input type="checkbox" checked>` が `checked:false` になる。
4. `waitForJob` のテストは、`setTimeout` の遅延の値を無視する。

## 直し方

1. 比べる前に、`{...result}` で、テストを書く側のオブジェクトに写す。
2. 定数は、index.js の原文を正規表現で読み取る。
3. HTML の既定値をテストの冒頭でスタブに反映し、`checked` 属性の有無そのものを、別のテストで固定する。

## 再発防止

- 待ち時間の改善は、実機の体感か実時間で確かめる。
- スタブで検査しにくい描画は、`box.appendChild` の呼ばれた回数で確かめる。
- HTML の ID と JS の参照を照合するテストは、動的に描画する形にしても通るようにしておく。

## 出どころ

- Cut & SRT の失敗記録と計画書（2026-07-21、07-25、09-23。v0.9.9 / v0.11.0）。機械検証のみで、待ち時間の短縮の体感は未確認。
