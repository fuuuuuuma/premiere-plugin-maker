---
id: uc-mac-bash-variable-japanese
title: Mac のインストーラが途中で止まる。「$変数」の直後の日本語が変数名に混ざる
kind: usecase
tags: [Mac, bash, シェル, インストーラ, 日本語, ロケール, set -u]
os: [mac]
premiere: ">=25.6"
status: partial
summary: Mac 標準の bash 3.2 は、UTF-8 の環境で「$VAR」の直後の日本語の先頭バイトを変数名に取り込む。変数は ${VAR} と書き、候補の列挙は while read で回す
parts: [packaging]
related: [platform-mac, uc-windows-cp932, core-verification]
---
## 症状

- 利用者の Mac で、インストーラが途中で止まった（未定義の変数を禁止する `set -u` のエラー）。
- pip は導入済みと表示するのに、再検証が「未導入」と言い、矛盾した（全員）。
- 非対話で実行すると、最後の `read` が EOF で終了コード 1 になった。`set -e` の下で `launchctl load` が失敗しても、無言で終わった。

## 原因

- bash 3.2（Mac 標準）は、UTF-8 のロケールで `$VAR・` の次の日本語の先頭バイトを、変数名の一部として取り込む。
- 候補を `for cand in $(…)` で回すと、空白を含むパス（`Application Support`）が分割されて、実行可能かの検査を通らない。
- どちらも、開発機では通らない分岐で、一度も実行されなかったので気づかなかった。ロケールの違いが原因ではない。

## 直し方

1. 変数の展開は `${VAR}` に統一する。各スクリプトの先頭で `export LC_ALL=C` を入れる。
2. 候補の列挙は `while IFS= read -r c; do …; done < <(関数)` で回す（パイプにすると変数が親に戻らない。`mapfile` は bash 4 以降なので使えない）。
3. 成功の判定は、pip の終了コードでなく、import できるかで見る。
4. 最後の待機は、端末（TTY）のときだけにし、成功の経路には明示の `exit 0` を置く。

## 再発防止

- 静的な検出と、日本語のロケールでの実際の bash 起動を行うテスト、空白入りのパスを使うテストを置く。直す前の状態に戻すと失敗することを確かめる。
- 日本語を含む配布用の shell は、`${VAR}` と `while read` を徹底する。開発機で通らない分岐は、強制的に通すテストで見張る。
- 利用者の環境での最終確認は、まだ。

## 出どころ

- Cut & SRT の引き継ぎ記録と失敗記録（2026-07-14〜07-28、macOS 標準の bash 3.2）
