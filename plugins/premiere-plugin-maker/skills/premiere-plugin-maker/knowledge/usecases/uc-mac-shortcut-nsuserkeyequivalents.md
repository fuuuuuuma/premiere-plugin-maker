---
id: uc-mac-shortcut-nsuserkeyequivalents
title: 統合したあと、ショートカットが 1 つだけ効かない
kind: usecase
tags: [Mac, ショートカット, NSUserKeyEquivalents, メニュー名, 誤診, defaults]
os: [mac]
premiere: ">=26.3"
status: verified
summary: Mac のショートカットの実体は macOS の NSUserKeyEquivalents で、メニュー項目名の完全一致で照合される。プラグイン ID を変えると引き継がれない、は誤判定だった
parts: [packaging]
related: [platform-mac, uc-uxp-shortcut-commands-not-listed, core-versioning-release]
---
## 症状

旧い単体のプラグイン 2 つを、統合版（プラグイン ID が別）に吸収したあと、10 番目のスロットのショートカットだけが効かなかった。

## 原因

最初は「プラグイン ID が変わったので、ショートカットが引き継がれない」と判断したが、これは誤りだった。ショートカットの実体は macOS の `NSUserKeyEquivalents` で、メニュー項目の名前の完全一致で照合される。ID が変わっても名前が一致すれば引き継がれる。10 番目だけが効かなかったのは、メニュー名のタイプミスのためだった。

## 直し方

1. `defaults read <バンドル ID> NSUserKeyEquivalents` で、実際の保存内容を確かめる。
2. `defaults write` で、タイプミスのある側のキーを直す。
3. 数字のキーには、修飾キー（Cmd など）を押しているときは発火しないガードを足す。
4. 再割り当ての手順を README に書く。

## 再発防止

- メニューのショートカットは、ID でなく名前を一致させて、実データで確認する。
- 原因を決める前に、実データを見る。

## 出どころ

- Cut & SRT の失敗記録と引き継ぎ書（Premiere 26.3 / macOS、2026-07-16）。メニューの表示を実機で確認した
- 別の記録は、割り当てが ID とコマンド ID に紐づくとも書く。両者の関係は整理されていない。キットは「名前の一致」を確かめる側に合わせた
