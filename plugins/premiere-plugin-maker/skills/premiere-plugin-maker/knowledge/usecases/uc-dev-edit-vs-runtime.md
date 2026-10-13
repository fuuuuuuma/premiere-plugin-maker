---
id: uc-dev-edit-vs-runtime
title: 直したのに Premiere の動きが変わらない（編集した物と、動いている物は別）
kind: usecase
tags: [開発, 反映, Reload, 再起動, 稼働コピー, 層, 切り分け]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 動いているのは、編集したファイルそのものとは限らない。パネル・サーバー・補助・導入先のコピーの 4 つの層のどれが古いかを、版と応答で確かめ、層ごとの反映の手段で入れ直す
parts: [packaging, local-server, cep-helper]
related: [core-dev-loop, uc-install-edit-vs-running-copy, uc-install-reload-layers, uc-install-same-version, uc-install-stale-panel-version-chip, uc-cep-unknown-command]
---
## 症状

コードを直し、テストも通ったのに、Premiere の中の動きが変わらない。古いエラー文言がそのまま出る。新しい命令が「unknown action」と拒否される。

## 原因

プラグインは、複数の層でできていて、それぞれ別の場所で、別の方法で読み込まれる。直した層が、動いている層と違うことが多い。

| 層 | 動いている物 | 古いままになる理由 |
|---|---|---|
| パネル（UXP） | UDT が読み込んだフォルダ | 保存しても自動では反映されない。Reload が要る |
| 常駐サーバー | 導入先に複製したコピー | 起動した時点のコードで動き続ける。再起動すると認証の合言葉が変わり、パネルも Reload が要る |
| 補助（CEP など） | Premiere が起動時に読んだもの | Premiere を再起動するまで入れ替わらない |
| 導入先のコピー | リポジトリや配布 ZIP とは別 | 同じ版数だと「既にあるので上書きしない」。ZIP 展開物は更新日時が固定で、差分を取りこぼす |

## 直し方

1. まず、動いている物を特定する。プロセス一覧と、状態確認の応答の版、UDT の読み込み先を見る。
2. 古い層を見つけたら、その層の反映の手段で入れ直す。
   - パネル: UDT の Reload。manifest を変えたときは Unload してから Load。
   - サーバー: 導入先をチェックサム比較（`rsync -avc`）で同期し、常駐を再起動。その後パネルも Reload。
   - 補助: Premiere を再起動する。
3. 状態確認の応答の `version` が期待どおりかで、届いたことを確かめる。

## 再発防止

- 手順書の冒頭に、「どの層を変えたか、その層は何で反映するか」を書く。
- 画面に「panel X / server Y」の版を併記し、版の食い違いが見えるようにする。
- 「直したのに変わらない」の第一容疑は、「編集した場所と、動いている実体が違う」。
- 詳しい手順は、関連する 3 つの事例（稼働コピー、Reload の層、同じ版数の入れ直し）に分けて書いてある。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の開発メモ（2026-07-21〜09-30、Premiere 26.3 / 26.5）。実機で確かめた。
