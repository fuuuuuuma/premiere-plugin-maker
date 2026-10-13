---
id: uc-uxp-undo-grouping
title: 取り消しをキーや効果の数だけ押さないと戻らない
kind: usecase
tags: [UXP, 取り消し, undo, executeTransaction, ExtendScript, CEP, 設計判断]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: ExtendScript には複数の操作を取り消し 1 回にまとめる手段が無い。実行部を UXP の executeTransaction に移し、取り消しの回数を設計に織り込んで画面に出す
parts: [ppro-kit, cep-helper]
related: [core-transactions, uc-uxp-effect-params-before-commit, feat-ed-overview]
---
## 症状

アニメーションを当てると、元に戻すのに Cmd+Z をキーや効果の数だけ（数十回）押さなければならない。デザインの置き換えも、案内は「Cmd+Z で戻る」だったのに、実際は名前・挿入・削除で 3 回かかった。

## 原因

ExtendScript には、複数の操作を 1 回の取り消しにまとめる公式の手段が無い（Adobe フォーラムの回答でも不可能と明言）。UXP の `executeTransaction` なら、複数の Action を 1 つの履歴にまとめられる。

## 直し方

1. 実行する部分だけを、小さな UXP の補助プラグインに切り出し、`project.executeTransaction` の 1 回の取引で書く。
2. CEP と UXP は、1 つの拡張にまとめられない。別々の拡張にして、ファイルの受け渡し（仕事の JSON を共有フォルダーに置く）でつなぐ。
3. 取り消しの回数は、キーだけのアニメ 1 回、効果を足すアニメ 2 回（複数のクリップでも同じ）。この回数を、画面に表示する。
4. 補助が無い環境では、ExtendScript で当てて、「戻すには Cmd+Z を複数回」と表示する。

## 再発防止

- 表示した回数が実際と合うことを、17 種類で数えて確かめた。数える道具は非公式の ExtendScript の `qe.project.undo()`。
- 「1 操作 = 取り消し 1 回」にしたい設計は、最初から UXP の取引に載せる。

## 出どころ

- Effect & Design の実機の記録（Premiere 26.5、2026-09-18〜09-19）。設計書の「スコープ外」とした判断を覆した記録
- `qe.project.undo()` が消えつつあるという他者の報告は、26.5 では当たらなかった。他の版は未確認
