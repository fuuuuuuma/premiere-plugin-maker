---
id: uc-install-cc-signin-wipes
title: Creative Cloud にサインインし直したら、導入した補助プラグインが消えた
kind: usecase
tags: [UXP, UPIA, 登録簿, Creative Cloud, サインイン, PluginsInfo]
os: [mac]
premiere: ">=26.5"
status: verified
summary: Creative Cloud が「ユーザーが変わった」と判断した瞬間に、UXP の登録簿が空に書き換わる。一覧コマンドには残って見えるので気づけない。もう一度 install すれば、再起動なしで戻る
parts: [packaging, probe]
related: [uc-install-udt-package-stale, core-versions, platform-mac]
---
## 症状

Premiere を開き直すと、UXP の補助プラグインが読み込まれない。起動ログに "Zero plugins found in user's PluginsInfo file" と出る。UPIA の `--list` には残って見えるので、気づきにくい。

## 原因

UPIA で入れたプラグインは、登録簿（Mac では `~/Library/Application Support/Adobe/UXP/PluginsInfo/v1/premierepro.json`）に載る。Creative Cloud が「User has changed」（ユーザーが変わった）と判断した瞬間に、この登録簿が `{"plugins":[]}` に書き直される。サインアウトとサインインで起きる。作者の環境では、Adobe Fonts の件と登録簿の件で 2 回起きた。

## 直し方

1. もう一度 `UPIA --install <ccx>` を実行する。`--remove` は status -406 で失敗するが、無視してよい。登録簿が戻り、再起動なしで読み込まれる。
2. 製品側の対処（予定。未確認）: 補助プラグインの .ccx を同梱し、補助の心拍（生きている合図）が無ければ UPIA で入れ直す。

## 再発防止

- 診断（doctor）で、登録簿の実体（`premierepro.json`）を確かめる。一覧コマンドが「ある」と言っていても、実体を見る。
- 心拍で補助の死活を検知して案内し、無ければ従来の経路（ExtendScript）に切り替える。

## 出どころ

- Cut & SRT と Effect & Design の実測（2026-09-19〜09-20、Premiere 26.5・Mac で確認。製品側の対処は未確認）
