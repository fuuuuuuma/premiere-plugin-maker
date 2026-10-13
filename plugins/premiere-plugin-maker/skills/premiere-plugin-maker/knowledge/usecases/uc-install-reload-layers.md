---
id: uc-install-reload-layers
title: サーバーを再起動してもパネルは古いまま。変更の反映は層ごとに手段が違う
kind: usecase
tags: [開発, 反映, Reload, UDT, 再起動, トークン]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: パネルだけの変更は UDT の Reload、サーバーの変更は常駐の再起動、再起動でトークンが変わるならパネルも Reload。層ごとの反映手段を手順の冒頭に書く
parts: [local-server, packaging]
related: [core-dev-loop, uc-install-edit-vs-running-copy, uc-install-stale-panel-version-chip]
---
## 症状

パネルの JS（`index.js`）を書き換えてサーバーを再起動しても、動いているパネルは古いコードのままで、新しい命令を「unknown action」と拒否した。

## 原因

動いている UXP パネルには、ファイルを保存すれば自動で反映される機能（ライブリロード）が無い。常駐サーバーも、起動した時点のコードで動き続ける。さらに、サーバーが起動するたびに認証用のトークン（`server/ready`）が変わるので、Reload していないパネルはトークンが合わなくなる。

## 直し方

| 変えたもの | 反映の手段 |
|---|---|
| パネルだけ（`index.*`・`panel.css`） | UDT（UXP Developer Tool）の Reload |
| `server/*.py`（サーバーが import するモジュールも） | 常駐を再起動（Mac は `launchctl kickstart -k gui/$(id -u)/<ジョブ名>`）し、パネルも Reload |

更新のたびに Remove してから Load し直すと、トークン不一致のループに入りやすい。必要なのは Reload だけ、と設計書は書いている（実機での再現は未確認）。

## 再発防止

- 手順書の各節の冒頭に、「Reload で足りるか・再起動が要るか」を書く。
- 層（パネル・サーバー・トークン）ごとに反映手段を書いておかないと、古い版で試した誤報告が起きる。

## 出どころ

- Cut & SRT の引き継ぎ記録と設計書（2026-07-21〜07-28、Premiere 26.3）
