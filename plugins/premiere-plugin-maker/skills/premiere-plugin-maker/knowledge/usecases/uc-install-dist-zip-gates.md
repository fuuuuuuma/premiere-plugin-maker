---
id: uc-install-dist-zip-gates
title: 作業ツリーをそのまま固めると、認証トークンやテストが配布物に混ざる
kind: usecase
tags: [配布, ZIP, ゲート, git ls-files, 検査, 再生成]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 配布 ZIP は 1 コマンドで再生成し、git で追跡しているファイルを基準に組む。「含めるもの」と「含めてはいけないもの」の両方をゲートで検査し、展開した実物で確かめる
parts: [packaging]
related: [uc-install-secret-name-dropped, uc-install-zip-japanese-names, uc-install-personal-info-leak, core-versioning-release]
---
## 症状

作業ツリーをそのまま固めると、追跡していない認証トークン（`server/ready`）、`__pycache__`、内部の文書、テストが混ざりうる。実行権限が欠けたり、Windows のスクリプトの文字コードが不備だったり、古い版の ZIP を誤って配ったりもありうる。ZIP を作るスクリプトが一時領域にしか無く、消えてしまったこともあった。

## 原因

中身の確認と生成の手順が、人手と一時領域に任されていた。Windows 専用のファイルは git の外にある重ね合わせ用の場所（overlay）に置かれていて、それが無いと Windows 版は作れない。

## 直し方

1. `python3 scripts/make_dist_zip.py` で、Mac 用と Windows 用の ZIP を 1 コマンドで生成する。
2. `git ls-files` を基準にして、引き継ぎ文書・README・メモ・設計文書・スクリプト・サーバーのテストを除く（Mac 版は 81 本から 74 本になった）。
3. Mac 版は `.command`/`.plist`、Windows 版は overlay の 8 本を合成した `.bat`/`.ps1` だけを入れる。
4. 生成後のゲートで、次を検査する。トークン・pycache・内部文書・`test_*` が無いこと、必須ファイルがあること、manifest の版数が一致すること、UTF-8 のフラグ、実行権限 0755、`.ps1` の UTF-8 BOM、`.bat` が ASCII のみであること。1 つでも落ちたら異常終了にする。
5. 古い版の ZIP は削除する。生成スクリプトは、リポジトリの `scripts/` に常設する。

## 再発防止

- 展開した後に、版数・初期辞書の件数・実行権限・BOM を確かめる。
- ダウンロードフォルダへ展開して実行すると、保護フォルダの検出で、常駐の登録の前に止まるので、既存の環境を壊さない。
- 再利用するスクリプトは、最初から git の管理下に置く。

## 出どころ

- Cut & SRT の引き継ぎ記録と作者の開発メモ（2026-07-19〜07-28、ゲート通過と展開後の確認まで。配布先の実機ではない）
