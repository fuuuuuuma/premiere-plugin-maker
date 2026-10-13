---
id: uc-mogrt-adobe-fonts-signout
title: 全デザインが「書体なし」になる（Creative Cloud のサインアウトで Adobe Fonts が空）
kind: usecase
tags: [フォント, Adobe Fonts, Creative Cloud, サインアウト, E_FONT, 書体探索]
os: [mac]
premiere: ">=26.2"
status: verified
summary: Adobe Fonts は Creative Cloud のサインアウトで空になる。書体の探索は Adobe Fonts だけでなく、利用者が入れた書体の置き場も見て、全件が欠けたらサインアウトを疑う
parts: [mogrt-text]
related: [feat-ed-catalog-previews, feat-ed-import-styles, platform-mac]
---
## 症状

検査をかけたら、すべてのデザインが `E_FONT`（書体が無い）になった。計測すると、100 種の Adobe Fonts のうち 55 種が消えていた。

別の場面では、利用者が自分で入れた書体（`~/Library/Fonts`）を、「入っていない」と判定してしまった。

## 原因

- Creative Cloud が、ある時刻に認証を取り消してサインアウトしており、Adobe Fonts の置き場（`~/Library/Application Support/Adobe/CoreSync/plugins/livetype/`）が空になっていた。
- 別件は、書体の探索が Adobe Fonts の置き場しか見ていなかった。

## 直し方

1. 検査で `E_FONT` が全件のときは、CoreSync のログ（`~/Library/Logs/CreativeCloud/CoreSync/`）でサインアウトの記録（signout）を探す。
2. 実機での作業の前に、Creative Cloud にサインインしているかを確かめる。
3. 書体の探索は、Adobe Fonts の次に、`~/Library/Fonts`、`/Library/Fonts`、`/System/Library/Fonts` も探す（ファイルを mmap で読むと、914 書体を 0.04 秒で探せた）。

## 再発防止

- 書体の置き場の更新時刻を、検査結果のキャッシュの印に入れる。Adobe Fonts を有効にしたあとに、検査し直すため。
- フォントに頼るプラグインは、探索先を OS と利用者の置き場まで広げ、無いときは隠さず利用者に見せる。
- 書体が全部欠けたときは、プラグインの不具合でなく、サインイン状態の問題かもしれないと考える。

## 出典

- Effect & Design の実機の記録（2026-09-18〜09-21、Creative Cloud、Premiere 26.5、macOS）
