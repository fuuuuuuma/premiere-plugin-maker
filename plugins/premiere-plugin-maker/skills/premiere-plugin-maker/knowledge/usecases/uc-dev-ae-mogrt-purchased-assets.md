---
id: uc-dev-ae-mogrt-purchased-assets
title: After Effects で作られた MOGRT の見た目は取り出せない。購入した素材の可否は形式と規約で決まる
kind: usecase
tags: [開発, MOGRT, After Effects, 購入素材, 規約, 取り込み, 凍結]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: AE 製の .mogrt の見た目は、Premiere のテキストの部品でなく AE のレイヤーの中にあるので、スタイルとして取り出せない。外部の素材を取り込むときは、技術より先に形式と規約を確かめ、購入素材を配布物に同梱しない
parts: [mogrt-text]
related: [ref-mogrt, ref-prtextstyle, uc-mogrt-source-text-unreadable, uc-mogrt-style-import-keep-blob]
---
## 症状

AE で作られた .mogrt は、スタイルとして取り出せなかった。購入した素材を、そのまま使えるかも分からなかった。

## 原因

見た目が、Premiere のテキストの部品でなく、AE のレイヤーの中にある。素材を使えるかは、技術でなく、形式と規約で決まる。

## 直し方

- AE 製の .mogrt は、「テキストの見た目が見つかりません」と伝え、取り込まない。文字単位のアニメーションは凍結する。
- `.prtextstyle` は取り込める。PNG の連番は取り込めない。
- 拡張ごとの配布・販売は不可。「自動化」「AI」の利用や逆解析を禁じる条項に注意する。

## 再発防止

- 素材ごとに、形式と、商品ページの規約を確かめてから取り込む。
- 購入した素材を、配布物に同梱しない。
- AE 製の .mogrt に文字を差し替えて挿入できるかは、「見込み」のままで未検証。

## 出どころ

- Effect & Design の実機の受け入れの記録と調査の要約（2026-09-18〜09-19、Premiere 26.5）。結論のみの記述で、確かめた手順の記録は無い。
