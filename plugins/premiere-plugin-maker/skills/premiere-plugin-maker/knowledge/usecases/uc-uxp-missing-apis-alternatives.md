---
id: uc-uxp-missing-apis-alternatives
title: CEP や本体にある操作が UXP から呼べない（できる・できないの表）
kind: usecase
tags: [UXP, CEP, ExtendScript, 差分表, 代替, 設計, リンク, ターゲット]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: リンク・ターゲット・分割・速度変更・名前の変更などは UXP に無い。企画の最初に公式リファレンスで可否を表にし、案内・代替の画面・自前の実装で補う
parts: [ppro-kit, cep-helper]
related: [core-capabilities, ref-cep-extendscript, uc-uxp-no-razor-api, uc-dev-stay-uxp-not-cep]
---
## 症状

CEP / ExtendScript や Premiere 本体にある操作が、UXP からは呼べない。たとえば、リンク・リンク解除のボタンがいつもエラーになる、トラックが「ターゲット」かどうかを読めない、本体の生成メディアのツールやオブジェクトマスクを呼べない。

## 原因

UXP に該当する API が無い。

- UXP に無いもの: `Sequence.linkSelection / unlinkSelection`、`track.isTargeted()`、SRT をキャプショントラックにする機能（文字起こし系の API だけある）、`TrackItem.createSetSpeedAction`、クリップ単体の名前の変更、クリップの分割（razor）、メニューコマンドの実行、トラック間の移動、マルチカム、「グラフィックにアップグレード」（メニュー専用）。
- ExtendScript に無いもの: `project.executeTransaction`（複数の操作を取り消し 1 回にまとめる）、OpenTimelineIO の書き出し、matchName による指定。
- どちらにも無いもの: 図形の新規生成。

## 直し方

1. 設計の最初に、公式リファレンスで可否を表にして確定する。
2. 無い操作は、案内（「右クリックメニューで」）、代替の画面（パネル内で対象のトラックを選ぶチップ）、自前の実装、で補う。
3. SRT は、プロジェクトに読み込むところまで（`project.importFiles`）。MOGRT の挿入は `SequenceEditor.insertMogrtFromPath` でできる。
4. UXP に無い機能が核なら、CEP を主に、UXP を補助にする組み合わせを考える（同じ manifest での併用はできない）。
5. 画面を操作して補う案は、先に画面の構造を 10 分ほどの試しで測ってから決める。

## 再発防止

- 「別の基盤なら解けるのでは」と移る前に、移った先でも本当にできるかを調べる。
- 「不可能」の結論は調査した時点のもの。あとで覆ることがある（図形の生成は、ドナー方式で一度できた）。

## 出どころ

- Cut & SRT の引き継ぎ書と Effect & Design の設計書（2026-07-16〜10-05）
- Adobe 公式リファレンス（UXP の API 一覧）
- 公式リファレンスでの不在確認が中心で、実機での探査は記録に無いので unverified
