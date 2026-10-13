---
id: uc-server-launchd-log-rotation
title: 常駐サーバーのログを truncate すると、巨大な空白ができる（launchd）
kind: usecase
tags: [macOS, launchd, ログ, truncate, kickstart, ローテーション, 常駐]
os: [mac]
premiere: ">=25.6"
status: verified
summary: launchd が握るログのファイルは稼働中に truncate せず、リネームしてからジョブを再起動して世代を作る。確かめられない前提に頼らない手順を選ぶ
parts: [local-server, logger]
related: [platform-mac, uc-mac-bash-variable-japanese, ref-local-server]
---
## 症状

8 MB のログを truncate（中身を空にする）で整理したら、8 MB 分の NUL（空のバイト）の空洞ができた。または、ログが欠ける恐れがあった。

## 原因

`StandardOutPath` のファイルのハンドルを握っているのは launchd で、`O_APPEND`（常に末尾へ追記する）で開かれているかは、確かめられない。開かれていなければ、truncate のあとも元のオフセットへ書き続け、間が空洞になる。

## 直し方

次の 2 行を順に実行する。

```
mv "${LOG_FILE}" "${LOG_FILE}.1"
launchctl kickstart -k "gui/$(id -u)/com.<label>"
```

古いプロセスは `.1` に書き続けて終了し、launchd が再起動のときにログを新しく作る。どちらのハンドルの仕様でも壊れず、世代は 2 つで頭打ちになる。

## 再発防止

- 自動のローテーションはサーバーには入れない。ジョブを再起動できる保守の入口（`doctor.command` のようなもの）に置く。サーバーは `/doctor` で、肥大を知らせるだけにする。
- 試験は、`launchctl` の代役（stub）を PATH に置いて、本物の bash でスクリプトを実行し、退避したファイルの実在を見る。
- 確かめられない前提（`O_APPEND` かどうか）に頼らず、前提の要らない手順（リネーム + 再起動）を選ぶ。8 MB のログで実測した。

## 出典

- Mac のシェルと常駐に関する作者の実測の記録（2026、記憶の統合は 2026-10-04、macOS の launchd）
