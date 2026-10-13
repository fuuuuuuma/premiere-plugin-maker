---
id: uc-uxp-action-outside-lock
title: 「The script object is no longer valid」で変更が失敗する
kind: usecase
tags: [UXP, 取引, Action, エラー, lockedAccess, executeTransaction, await]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: Action を取引の外で作ったか、取引の中で await した。非同期の取得は先に済ませ、Action は lockedAccess と executeTransaction の中で同期的に作る
parts: [ppro-kit]
related: [core-transactions, core-api-patterns, uc-uxp-get-track-items-args, uc-uxp-effect-params-before-commit]
---
## 症状

ボタンを押すと「The script object is no longer valid」というエラーが出て、タイムラインが変わらない。値を読むだけの処理（開始時刻を読むなど）は外でも通り、Action を作る処理（キーフレームの追加、効果の追加など）だけが落ちる。「前は動いたのに Premiere を更新したら急に」という形で出ることも多い。

## 原因

`project.lockedAccess()` と `project.executeTransaction()` に渡す関数（コールバック）は、完全に同期でなければならない。Action を取引の外で（`await` を挟んで）作ってから中で足すだけにすると、Action が別のアクセスの文脈のものになり、無効になる。「急に」の正体は、Premiere の更新で API が厳しくなったことが多い。Premiere 26.3 からは、Action を取引の中で作ることが必須になった。

## 直し方

1. 非同期の取得（クリップのハンドル、`getMatchName()`、`VideoFilterFactory.createComponent`、`getProjectItem`）は、すべて取引の前、ロックの外で済ませる。
2. Action を作る処理と `addAction` は、`project.lockedAccess(() => project.executeTransaction((ca) => { ca.addAction(...) }, "操作名"))` の中で、同期的に書く。
3. 足したあとにもう一度取り直す必要があるもの（効果を足してから値を書く、など）は、別の取引にする。
4. クリップのハンドルは長く持たない。使う直前に、名前・開始位置・トラック番号から取り直す。

## 再発防止

- `check.py` の J001（取引の中の await）と J002（取引の外で作った Action）が止める。
- 部品 `ppro-kit` の `PPM.transact` を使えば、3 段階の型が守られる。
- あわせて起きやすい別の失敗として、`Track.getTrackItems()` の引数忘れがある（uc-uxp-get-track-items-args）。

## 出どころ

- Cut & SRT・Effect & Design の実機の記録（Premiere 26.x）。正しい型を適用した 3 つのプラグインが稼働している
- 「外で作ると失敗する」側の再現は単独実験ではなく、Adobe フォーラムの回答とコードのコメントによる
