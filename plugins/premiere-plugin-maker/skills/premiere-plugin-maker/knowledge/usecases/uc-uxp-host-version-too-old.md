---
id: uc-uxp-host-version-too-old
title: Premiere が古くてパネルを Load できない・メニューに出ない
kind: usecase
tags: [UXP, minVersion, 26.2, 読み込み, 開発者モード, ProjectConverter, 導入]
os: [mac, windows]
premiere: ">=26.2"
status: unverified
summary: 使う API の Since の最大値が、プラグインの最低版を決める。26.0 では Load に失敗する。導入ガイドの冒頭に最低版を書き、実行時にも版を確かめる
parts: [packaging, ppro-kit]
related: [core-versions, core-manifest-permissions, core-dev-loop, feat-cutsrt-install-update]
---
## 症状

- テスターから「Premiere 26.0 で Load に失敗する」と報告された。
- Load しても一覧に出ない。CCX を入れても、「ウィンドウ → UXP プラグイン」に出ない。
- （まだ起きていない心配として）Premiere の更新で `ProjectConverter` の動きが変わると、カット・テロップ・差分学習が一斉に動かなくなる。

## 原因

Premiere Pro が 26.2 より古い。`manifest.json` の `host.minVersion` を 26.2 にしているのは、`ProjectConverter`（Since 26.2）が下限を決めているため。カットの XML の書き出し、字幕、学習用の書き出しが、すべてこの `ProjectConverter` に依存し、ほかの API は Since 25.6 なので、これが実際の下限になる。26.0 で失敗する仕組みの記述は無い。

開発者モードが未設定、CCX の導入が済んでいない、配布セットの版が違う場合も、同じ「出てこない」症状になる。どれが決定的だったかは、記録に無い。

## 直し方

1. Creative Cloud で Premiere を 26.2 以上に更新して、再起動する。
2. 導入ガイドの冒頭に、「Premiere Pro 26.2 以上が必須」の注意の囲みを置く。「困ったとき」の表に、Load の失敗の行を足す。
3. Load の手順の前に、「環境設定 → プラグイン → 開発者モード」の手順を置く。
4. 起動時に `require("uxp").host.version` を読んで、必要な版より古ければ、警告のバナーを出す。

## 再発防止

- minVersion は、使う API の Since の最大値で決める。核が 1 つの書き出し API に依存するなら、それは単一の障害点なので、最低版を明記して実行時にも検査する。
- 版のチェックの試験を持つ。
- 通常は、UXP 自体がロードを拒否するので、バナーに届かない想定。26.2 未満の実機での表示は確かめていない。

## 出どころ

- Cut & SRT の引き継ぎ書と導入ガイド（2026-07-14〜07-26、v0.9.11）
- 26.0 での失敗はテスターの報告で、26.2 以上での解消の確認は記録に無い。版の下限は、公式リファレンスの Since と Node の試験で確かめた
