---
id: uc-dev-stay-uxp-not-cep
title: 導入が面倒だから CEP に移るべきか
kind: usecase
tags: [設計判断, UXP, CEP, 移行, 導入, 二重保守]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: CEP に移る利点は導入の簡単さだけで、移ると取引と OTIO の書き出しを失い、作り直しになる。UXP のまま、導入の経路を直す
parts: [cep-helper, local-server]
related: [core-capabilities, ref-cep-extendscript, uc-dev-cep-end-date-unverified, uc-uxp-undo-grouping]
---
## 症状

UXP のプラグインを入れるために UDT（UXP Developer Tool）を挟む手順が面倒だとして、CEP の拡張に移すべきかを調べた。

## 原因

CEP の利点は、導入の簡単さだけだった。移ると次の損がある。

1. `project.executeTransaction`（複数の操作を取り消し 1 回にまとめる）と OpenTimelineIO の書き出しを失う。
2. パネルとホスト（ExtendScript、ES3）が別のプロセスで、`CSInterface.evalScript()` による非同期のメッセージでしか通信できない。Adobe 自身も「移行でなく再構築」と明言している。見積もりでは、7,800 行のうち Premiere の API に触れるのは約 265 行でも、書き換えは関数単位で 2〜3 割に及ぶ。
3. 1 つの manifest での併用はできず、別々に配ると二重保守になる。

## 直し方

1. CEP へは移行せず、UDT を介さない導入の経路（サイドロードの自動配置、署名済みの `.ccx` の配布）で解決する。
2. ロジックは手元の HTTP サーバー（Python）に置き、パネルは `fetch()` で呼ぶだけにする。技術を替えても、中身が無傷で残る。

## 再発防止

- 新しい Premiere のプラグインは UXP で作る。CEP が必要になるのは、UXP に無い操作（分割など）を補助するときだけ。
- 「別の基盤に移れば簡単」は、移る前に、失うものを表にする。

## 出どころ

- Cut & SRT の CEP 移行の検討書（Premiere 26.3.0 / 25.6.6、2026-07-25）。UXP の正式版は 25.6
- CEP 拡張 4 件の稼働は実機で確認した。書き換えのコストは見積もり。当初の「CEP は 2026 年 9 月まで」という前提は、確定日としては裏付けられなかった（uc-dev-cep-end-date-unverified）
