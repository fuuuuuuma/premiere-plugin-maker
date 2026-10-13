---
id: uc-install-secret-name-dropped
title: 配った先でサーバーが起動しない。名前に secret を含む部品が、配布から落ちた
kind: usecase
tags: [配布, ビルド, 除外, secret, token, credentials, import, 部品名]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 配布ビルドは「秘密の混入防止」で名前に secret / token / credentials を含むファイルを黙って外す。部品の名前にこれらの語を使わず、配布物を展開して全部品を import できるか検査する
parts: [keychain, packaging]
related: [uc-install-dist-zip-gates, uc-install-version-scattered]
---
## 症状

鍵の置き場の部品（`secret_store.py`）が配布物から落ち、配った先でサーバーが、起動時の import で止まるところだった。新しく足したパネルのファイル（`direct_tab.js`）も、一覧に載せないと配布物に入らなかった。

## 原因

配布物を作る処理は、秘密の混入を防ぐために、名前に `secret`・`token`・`credentials` を含むファイルを外す。配布する対象は、3 か所に別々に列挙されている（パネルの根のファイル一覧、パネルだけの一覧、ZIP 生成の一覧）。1 か所だけに足すと、配布物に入らない。

## 直し方

1. 部品を `keychain_store.py` に改名する。
2. 新しいパネルのファイルは、3 か所すべての一覧に追加する。

## 再発防止

- 作った配布物の ZIP を展開し、隔離したホームフォルダで、全モジュールを import するテストを置く（開発用の診断スクリプトだけは、意図的に除外する）。
- 配布物と一覧を突き合わせるテストで、漏れを止める。
- 配布ビルドは名前で除外するので、部品の名前に、この種の語を使わない。

## 出どころ

- Cut & SRT の作者の開発メモ（2026-10-05、配布前にテストが検知した）
