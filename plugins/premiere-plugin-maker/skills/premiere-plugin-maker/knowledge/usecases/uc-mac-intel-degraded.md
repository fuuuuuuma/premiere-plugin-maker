---
id: uc-mac-intel-degraded
title: Intel Mac で mlx 系が動かず導入が失敗する。縮退構成を作るなら wheel の提供を先に測る
kind: usecase
tags: [Intel Mac, x86_64, wheel, mlx, faster-whisper, 縮退, fail-closed]
os: [mac]
premiere: ">=25.6"
status: unverified
summary: 古い CPU 向けの縮退構成は、依存全体の wheel 提供を PyPI で先に実測する。画面とバックエンドの両方で fail-closed にして、静かな代替を防ぐ。実機が無い項目は一覧にして、未測定の速度などはガイドに書かない
parts: [transcribe-srt, packaging]
related: [platform-mac, uc-mac-ffmpeg-detection, uc-windows-guide-python-limit]
---
## 症状

Intel Mac（x86_64）では、環境の検査（`check_os_arch`）が NG になって導入できず、`mlx` 系は動かない。以前のインストーラは、他の修復を続けた後に、失敗の数が 1 以上で終了コード 1 になった。

## 原因

PyPI で実測すると、`mlx`・`mlx-whisper`・`mlx-lm` に macOS の x86_64 用 wheel が無かった。`onnxruntime` も、最新の 1.28.0 には無く、1.23.2 までだった。`faster-whisper` の指定は `<2,>=1.14` と緩かった。

## 直し方

1. Intel だけに限定して、`faster-whisper` と `onnxruntime<1.24` を入れる。検査は「縮退構成として続行」にする。
2. 完全にローカルで動かす構成は非対応にする。画面は、状態確認の `macIntelDegraded` で無効（disabled）にする。
3. 実行側も、`mlx_lm` の import の前に `EngineUnavailable` を投げる。モデルの準備のジョブも、すぐエラーにして、静かな代替（黙って別の動きになること）を防ぐ。

## 再発防止

- Intel に見せかけて分岐を強制するテスト（`IS_MAC_INTEL` を差し替える 15 件）を置く。このテストを書いている途中で、関数内の変数 `messages` がモジュール名 `messages` を隠して `UnboundLocalError` になる潜在バグが見つかった。変数を改名して直した。
- 実機でしか確認できない項目は一覧にする。例: faster-whisper の CPU 実行の完走、ピンの解決（将来の yank の可能性）、mlx の import 失敗の文言、画面の崩れ、Homebrew なしでの導入の完走。
- 未測定の速度などは、ガイドに書かない。

## 出どころ

- Cut & SRT の引き継ぎ記録と整理の記録（2026-07-26）。Intel 実機は無く、PyPI の実測とモック付きテスト 15 件のみ
