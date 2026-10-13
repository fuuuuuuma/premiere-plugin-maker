---
id: core-versions
title: Premiere と UXP の版の歴史と、最低版（minVersion）の決め方
kind: core
tags: [版, minVersion, 25.6, 26.2, 26.3, 26.5, 27.0, CEP, 終了予定, 変更履歴]
os: [mac, windows]
premiere: ">=25.2"
status: partial
summary: UXP の正式版は 25.6 から。26.3 で取引の規則が厳しくなった。minVersion は「使う API の最低版」で決める。CEP は 2028-12 に既定で無効の予定
related: [core-transactions, core-manifest-permissions, ref-cep-extendscript]
---
## 要点

- Premiere の UXP プラグインが「正式版」になったのは 25.6（2025 年 11 月）。それより前の 25.2〜25.5 はベータ版だけの機能だった。
- 版が上がると API の決まりが変わる。特に 26.3 から、タイムラインを変える Action は `project.lockedAccess` の内側で作ることが必須になった。
- `minVersion`（manifest の最低版）は、プラグインが使う API の中で一番新しいものに合わせる。感覚や「最新だから」で決めない。
- CEP（古い方式の拡張）は 2027-12 に新規受付停止、2028-12 に既定で無効、2029-12 に同梱終了の予定。ExtendScript はこの予定の対象外。
- 確認日は 2026-10-13。27.0 はまだベータで、正式版の日付や内容は確かめられていない。

## 詳しく

### 版の歴史（確認日 2026-10-13）

| 時期 | 版 | できごと |
|---|---|---|
| 2024-12 | 25.2（ベータ） | UXP の最初の公開ベータ。Spectrum Web Components などが未完成 |
| 2025-11 | 25.6 | UXP が正式版（GA）に。API が CEP / ExtendScript にかなり近づき、配布の文書も整った |
| 2026-01 | 26.0 | 製品名が「Adobe Premiere Pro」から「Adobe Premiere」に短縮された（時期は資料で割れる）。manifest の `host.app` は `premierepro` のまま |
| 2026-04 | 26.2 | `ProjectConverter`（FCP XML・OTIO の書き出し）、`SequenceSettings.getVideoFrameRate`、`Project.isProject`、C++ を使う Hybrid プラグインに対応 |
| 2026-06 | 26.3 | 破壊的変更。`Sequence.setSelection` が同期（boolean を返す）になり、`create*Action` は lockedAccess の内側で作ることが必須に |
| 2026-09 | 26.5 | `WorkAreaUtils`、`MediaManager`、`C2PAService`、`Media.getDuration()` などが追加 |
| 2026-08〜 | 27.0（ベータ） | クリップ分割（razor）系の API の試作、`MogrtText`、ドラッグ＆ドロップなどが見える。ベータ限定の可能性が高く、仕様は未確定 |

25.6 には長期サポート系列があり、`minVersion` を 25.6.0 にするとその系列の利用者にも届く。

### minVersion の決め方

1. プラグインが使う API を全部書き出す。
2. 各 API の「最低版（Since）」を調べる。キットには `knowledge/reference/api-since.json` があり、`check.py` の J014 が、使った API の最低版が manifest の `minVersion` より新しいときに知らせる。
3. その中で一番新しい版を `minVersion` にする。例えば FCP XML を書き出す機能は 26.2 以上が必要なので、`minVersion` は `26.2`。
4. 何も特別な API を使わない小さなプラグインは `25.6` にする（正式版の最小）。25.6 未満にするとベータ版だけで動く状態になり、`check.py` の M006 が注意する。

公式は `minVersion` の推奨値を示していない。公式の例も 25.1.0・25.2.0・25.6.0・26.2.0 とばらばらなので、「使う API の最低版」で決めるのがもっとも確実。

### 版ごとに気を付けること

- 26.3 以降で動く作り（Action を lockedAccess の中で作る）は、25.6 でも動く。迷ったら 26.3 以降の作法に揃える。詳しくは `core-transactions`。
- 新しい API を古い Premiere で呼ぶとエラーになる。`typeof x === "function"` で存在を確かめてから呼ぶ（`core-api-patterns`）。
- 「公式の文書に載っている」と「その版に実装されている」は別。使う前に診断ボタンで確かめる（`core-verification`）。
- UXP のランタイムは Premiere の版ごとに同梱される（25.6 は UXP 8.1、26.2 は 9.2、26.3 は 9.3）。Premiere の版が分かれば UXP の版も決まる。

### CEP の予定（Adobe 公式ブログ 2026-09）

| 区切り | 時期 |
|---|---|
| 新規の CEP を Marketplace に出せなくなる | 2027-12 |
| CEP が既定で無効になる（利用者は簡単にオンに戻せる） | 2028-12 |
| 旗艦アプリに CEP が同梱されなくなる | 2029-12 |

既に Marketplace にある CEP は、同梱が外れるまで動作し、更新もできる。Marketplace の外で配る CEP は 2027 年の区切りの影響を受けない。ExtendScript は今回の移行の対象外と明記されている。新しい機能は UXP にだけ追加される。

CEP に頼る作り（再生・分割の補助など）は期限つきの手段として扱う。`ref-cep-extendscript` を参照。

## やってはいけないこと

- `minVersion` を最新の版に上げっぱなしにして、古い版の利用者を理由なく外すこと。
- `minVersion` を使う API より古くすること。読み込めても、実行時に API が無くて止まる。
- 27.0 ベータで見えた API を、正式版でも使える前提で作ること。
- 「CEP は 2026 年 9 月で終わる」「ExtendScript は終わる」といった古い・出所の弱い話を、そのまま利用者に伝えること。公式ブログの日付は上の表。

## 出どころ

- Adobe 公式の変更履歴と、API リファレンスの各メンバーの Since 表記（25.2〜26.5）
- Adobe 公式ブログ「CEP から UXP への移行スケジュール」（2026-09）と UXP の対応表（2026-07）
- Adobe 公式フォーラムの 26.3 / 26.5 の API 更新の投稿
- Cut & SRT の記録（minVersion を 26.2 にした根拠と、26.0 で読み込みに失敗した利用者の報告）
- 実機で確かめた範囲は 26.3〜26.5（Mac）。27.0 ベータは公式資料の読み取りだけで、実機では試していない
