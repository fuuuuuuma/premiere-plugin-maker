---
id: uc-fps-property-missing
title: 60fps なのに 30fps として扱われる（存在しないプロパティを読んで黙って既定値に落ちた）
kind: usecase
tags: [fps, UXP, SequenceSettings, getVideoFrameRate, 既定値, undefined]
os: [mac, windows]
premiere: ">=26.2"
status: partial
summary: シーケンスの fps を「存在しないプロパティ」から読むと常に undefined になり、既定の 30 が実際の値として下流へ流れる。メソッド getVideoFrameRate() を await で呼び、取れなければ失敗として扱う
parts: [ppro-kit, silence-cut]
related: [uc-fps-silent-default-30, uc-fps-conform-rate-trust, core-api-patterns]
---
## 症状

- 60fps のシーケンスを無音カットすると、出てくるシーケンスが 30fps になっている。
- カットのあとの字幕（SRT）作りが、毎回「速度変更またはタイムリマップされた音声クリップは未対応です」で失敗する。
- 59.94fps の素材で、位置が数フレームずれるという別の報告も、同じ原因だと考えられる（推測）。

## 原因

パネルが fps を知るために、`sequence.getSettings()` の結果から `settings.videoFrameRate ?? settings.frameRate` を読んでいた。実機の SequenceSettings には、このような「値のプロパティ」は無い。正しくは `await settings.getVideoFrameRate()` というメソッドで、戻りの `FrameRate` の `value` が数値になる。

プロパティを読んでも例外は出ず、ただ `undefined` になる。そのため `if (fr)` の分岐に入れず、あらかじめ置いてあった既定値（timebase 30）が「検出した実際の値」としてサーバーへ送られた。サーバーはそれを信じて、正しい 60fps の XML を 30fps に張り替え、丸め誤差で区間の長さまでずれ、あとの工程が「速度変更」と誤判定した。

さらに悪いことに、パネルのテストは「実機に無い旧い形」（`getSettings()` が直接プロパティを返す）のスタブを使っていたため、実装の誤りとテストの前提が同じ方向にずれて、テストは全部緑のままだった。

## 直し方

1. `await settings.getVideoFrameRate()` を呼んで、戻りの `value` を使う。
2. 取れなかったときは `detected: false` で返し、ログに出す。fps を送るべき場面（timebase や ntsc）では、何も送らない。
3. NTSC かどうかの判定の許容を 0.1 から 0.01 に狭める（60.00 と 59.94 の差は 0.06 しかない）。
4. 同じ関数の戻り値を使っている箇所を全部洗う。最小無音長の秒への換算など、別の場所にも同じ癖が残っていた。

## 再発防止

- UXP の値が「プロパティ」か「メソッド」かは、思い込まずに公式リファレンスと実機の戻り値で確かめる。
- `if (fr)` を「取得成功」の判定に使わない。取得に失敗した状態を、成功と同じ形で返さない（`uc-fps-silent-default-30`）。
- テストのスタブは、実機で取った戻り値の形に合わせる。テストが緑でも、実機の形とずれていれば意味が無い。
- 旧版を取り出して同じ入力（60fps の XML）を通し、症状（30fps になる、フレーム数が半分になる）を先に再現してから直す。

## 出典

- Cut & SRT の失敗記録（2026-07-24、v0.7.6〜v0.9.1 で発生、v0.9.2 で修正）。実 ffmpeg を使った往復の再現は機械検証。報告した利用者の環境での再確認は記録が無い
- Cut & SRT の作業記録（2026-07-17 に、最小無音長の換算箇所だけ先に対処した）
