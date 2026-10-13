---
id: uc-server-transcript-cache-fingerprint
title: 辞書やモデルを更新しても古い文字起こしが使われる（キャッシュの判定が足りない）
kind: usecase
tags: [キャッシュ, 転写, fingerprint, モデル, 辞書, VAD, ハッシュ]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: キャッシュの再利用は、結果を変えるすべての要素の指紋と、内容のハッシュの両方が一致したときだけにする。書き込みに失敗したときは、古い派生ファイルを消す
parts: [transcribe-srt, local-server]
related: [uc-fps-vfr-timebase, uc-server-atomic-output, feat-cutsrt-telop-srt]
---
## 症状

辞書・ランタイム・モデルを更新しても、fps を変えても、古い文字起こしが再利用される。生の結果の書き込みに失敗したあとは、前回の `raw.json` が残り、誤ったマーカーを出し続けた。

## 原因

キャッシュを識別する材料が、辞書とモデル名くらいしか無かった。書き込みに失敗したときに、古い `raw.json` を消していなかった（`whisper_wrapper.py`）。

## 直し方

1. 次の要素の指紋（fingerprint）と、segments の SHA-256 を、メタ情報に保存する。
   - 辞書の prompt
   - モデル
   - 依存するランタイム
   - デコーダと VAD（無音検出）の設定
   - シーケンスのレート
   - 素材のファイル情報（stat）
2. 両方が一致したときだけ再利用する。
3. 生の結果の書き込みに失敗したときは、古い raw を `unlink` で消す。

## 再発防止

- 指紋と中身のハッシュの二重の照合を、試験で固定する。
- 重い処理のキャッシュは、入力・設定・モデルの指紋と、内容のハッシュで判定する。派生ファイルの書き込みに失敗したら、古いものを消す。
- 更新後の「直っていない」という報告は、古いキャッシュが再利用されている可能性を疑う。

## 出典

- Cut & SRT の失敗記録と README（2026-07〜07-23、v0.7〜v0.10.1）。機械検証まで
