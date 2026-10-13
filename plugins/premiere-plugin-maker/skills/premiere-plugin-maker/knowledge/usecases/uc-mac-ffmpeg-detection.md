---
id: uc-mac-ffmpeg-detection
title: ffmpeg の案内文が実装と食い違い、PATH の先頭の Intel 専用ビルドで起動に失敗する
kind: usecase
tags: [ffmpeg, Mac, PATH, Intel, Homebrew, 診断, インストーラ]
os: [mac]
premiere: ">=25.6"
status: partial
summary: ffmpeg は同梱せず、案内文は実装と一致させる。有無は PATH ではなく「-version を実行」して判定する。PATH の先頭にある Intel 専用ビルドに注意する
parts: [media-tools, packaging]
related: [platform-mac, uc-install-support-pack, uc-mac-intel-degraded]
---
## 症状

- 「ffmpeg の導入方法が分からない」という利用者の声があった。Mac 版は、無いと 1 行のエラーを出すだけだった。エラー文は「自動で導入します」と書いていたが、実装は無かった。サーバーが止まっていると、診断も有無を表示できなかった。
- 別件として、PATH の先頭にある `~/.local/bin/ffmpeg` が Intel 専用（x86_64）だった。`/bin/bash`、`shell=True`、`shutil.which` が返す絶対パスでの起動は、終了コード 126（Bad CPU type）で失敗した。zsh と、リスト形式の subprocess だけは次の候補に進んで成功した。

## 原因

ffmpeg は、ライセンスと容量の問題で同梱しない。Windows は winget で自動導入できるが、Mac は未実装で、文言だけが先に書かれていた。`which` は「起動できないバイナリ」のパスも返す。

## 直し方

1. インストーラは、Homebrew があれば `brew install ffmpeg`、無ければ Homebrew の導入コマンドを示して止める。導入後も見つからなければ、仮想環境を作る前に止める。
2. 有無の判定は、`-version` を実行して、有無・版・実際のパスを返す関数にする。
3. 診断コマンドは、サーバーが止まっていても表示する。
4. 呼ぶ側は、`/opt/homebrew/bin/ffmpeg` を先に試す。

## 再発防止

- 壊れたバイナリ、タイムアウト、キャッシュ、案内文の内容、`bash -n` の構文検査を確かめるテストを置く。
- 「ffmpeg が起動しない」と出たら、まず PATH の先頭の Intel 専用ビルドを疑う。
- エラー文が約束する自動処理は、実装と一致させる。外部ツールは、PATH でなく実行して確かめる。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の環境メモ（2026-07-25、2026-09-30。Intel 専用ビルドの現象は実機で確認。Mac の自動導入の通しは未確認）
