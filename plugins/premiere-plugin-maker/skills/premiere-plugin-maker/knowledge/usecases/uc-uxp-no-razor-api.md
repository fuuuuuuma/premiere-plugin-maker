---
id: uc-uxp-no-razor-api
title: クリップを切る（分割）API が UXP に無い
kind: usecase
tags: [UXP, 分割, razor, QE, CEP, チャンネル割り当て, XML]
os: [mac]
premiere: ">=25.6"
status: unverified
summary: UXP に razor / split も音声チャンネルの割り当て API も無い。破壊的な擬似実装はせず、限られた用途だけ CEP の QE で補う（Mac のみ・前後を照合）
parts: [cep-helper]
related: [uc-uxp-missing-apis-alternatives, ref-cep-extendscript, feat-cutsrt-pinmic, feat-cutsrt-playback-helper]
---
## 症状

- 無音カットで XML を往復すると、音声のチャンネルの割り当てが壊れる。これを避けたいが、UXP で直す手段が見つからない。
- 同じクリップの中で話す人が入れ替わる所を切りたいが、分割の API が無い。リンクした音声を `createSetDisabledAction` で無効にすると、映像まで巻き込まれる心配もあった。

## 原因

- 公式の型定義（`types.d.ts`、4263 行）を split / razor / channel / mapping で全文検索しても、該当が 0 件だった。
- QE DOM の `razor()` は CEP 専用で、Adobe は公式にサポートしていない。
- `ClipProjectItem`、`FootageInterpretation`、`AudioTrack` にも、チャンネルの割り当てを読み書きする API が無い（ExtendScript には `getAudioChannelMapping / setAudioChannelMapping` がある）。

## 直し方

1. XML の往復で壊れる件は、根本の対策を凍結し、被害は警告で小さくする。CEP への全面移行（取引と OTIO の書き出しを失う）や、複製して両側を削る擬似分割（欠落の恐れ）は採らない。
2. 音声トラックの数か所だけ切りたいときは、同梱の CEP の補助に「razor」の命令を足し、QE DOM の `track.razor` で切る。時刻は `getFormatted(フレームレート, 表示形式)` の書式で、位置は 1/4 コマ内側にする。Mac だけで、Windows ではマーカーを置くだけにする。
3. 切れないところは、両方を有効のままにして、マーカー「話す人が入れ替わる」を置く。
4. 切る前後で、映像クリップの状態を照合し、変わっていれば、パネルが止めて取り消しを案内する。

## 再発防止

- UXP でできないこと（分割・チャンネル割り当て）は、設計の最初に型定義を全文検索して洗い出す。
- 挙動が実機でしか分からない補助には、前後の照合・取り消しの案内・Mac のみの明示をセットで入れる。
- 偽の QE オブジェクトで、命令の動きを Node で試験する。

## 出どころ

- Cut & SRT の引き継ぎ書（2026-07-25〜07-27 の凍結、2026-09-30〜10-01 の v0.13.0）
- QE の `track.razor` の挙動は実機で確かめていない（10-01 の実機試験でも、切る処理は実行されなかった）。そのため unverified
- 「ExtendScript にも無い」という記述は、QE DOM の razor を使う実装と食い違う。キットの部品は、QE を非公式の補助として使う側に合わせた
