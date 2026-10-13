---
id: uc-windows-cuda-dll
title: Windows の文字起こしが「cublas64_12.dll is not found」で失敗する
kind: usecase
tags: [Windows, CUDA, cuBLAS, cuDNN, faster-whisper, GPU, フォールバック]
os: [windows]
premiere: ">=25.6"
status: verified
summary: faster-whisper は CUDA のランタイムが無くてもモデルのロードは通り、最初の推論で失敗する。実行時のエラーで CPU に切り替えて知らせ、ランタイムの DLL はインストーラで入れる
parts: [transcribe-srt, packaging]
related: [platform-windows, uc-mac-intel-degraded, uc-windows-guide-python-limit]
---
## 症状

Windows で文字起こしが `cublas64_12.dll is not found` で失敗する。

## 原因

`device=auto` は、GPU のドライバがあるだけで CUDA を選ぶ。ところが cuBLAS・cuDNN のランタイムが未導入でも、モデルのロードは成功し、最初の `encode` の時に初めて落ちる。ロードの時点で CPU に切り替える処理（ロード時フォールバック）が、効かない。

## 直し方

1. nvidia の wheel が持つ `bin` フォルダを、`os.add_dll_directory` に登録する。
2. 文字起こし時の `RuntimeError`（メッセージに cublas / cudnn / cuda を含む）を捕まえて、CPU の int8 で再度文字起こしする。画面には「注意:」で知らせる（`CUTSRT_WARN:` の印）。環境変数で GPU の試行を省略できるようにする。
3. `install_windows.ps1` が、`nvidia-smi` で GPU を見つけたら、`nvidia-cublas-cu12` と `nvidia-cudnn-cu12` を導入する。

## 再発防止

- 実行時のエラーで CPU に切り替えるテストと、DLL の登録のテストを置く。
- GPU が使えるかどうかは、最初の推論で分かることがある。ロードの成功を、GPU が使える証拠にしない。
- 移植したロード時の CPU フォールバックは、構文の検査のみで、実機では未確認。

## 出どころ

- Cut & SRT の導入ガイドと引き継ぎ記録（2026-07-19、テスターの報告。Windows 10・11 / CUDA 12）
