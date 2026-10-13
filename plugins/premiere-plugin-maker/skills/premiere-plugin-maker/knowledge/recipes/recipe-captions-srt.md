---
id: recipe-captions-srt
title: 文字起こしして字幕（SRT）を作る
kind: recipe
tags: [字幕, SRT, 文字起こし, Whisper, mlx-whisper, faster-whisper, 意味区切り, 改行, 日本語]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 素材の音声を手元で文字起こしして SRT にし、プロジェクトへ読み込む。SRT のタイムラインへの配置は手作業か別の処理。意味で区切る改行は AI の文脈判断で行う
parts: [ppro-kit, local-server, media-tools, transcribe-srt, ui-kit]
related: [feat-cutsrt-telop-srt, feat-premiere-skills, core-capabilities, uc-xml-audio-shorter-than-video, uc-windows-cuda-dll, uc-windows-cp932, uc-mac-ffmpeg-detection]
---
## この型で作れるもの

「選んだ素材（または再生範囲）を文字起こしして、時刻つきの字幕ファイル（SRT）を作り、プロジェクトに取り込むボタン」です。

注意点が 2 つあります。

- 取り込まれた SRT は、プロジェクトパネルの項目になるだけで、**シーケンスへは自動で並びません**（配置は利用者の手か別の処理）。
- 1 行の長さを機械で切る簡単な改行は付きますが、「意味の切れ目で改行する」のは AI の仕事です。この型は、そこまで求めないなら文字数での改行で十分、求めるなら下の「意味で区切る改行」を足す、という構成です。

## 前提

- 雛形は `panel-server`、部品は `transcribe-srt`（`media-tools` が一緒に入ります）。
- 文字起こしの部品は、Mac（Apple Silicon）は `mlx-whisper`、Windows は `faster-whisper` です。**初回に約 1.5GB のモデルをダウンロード**します。入れる前に、何をどれだけ入れるかを利用者に見せ、許可を取ります。
- Windows で GPU を使うときは、CUDA の DLL が見つからない（`cublas64_12.dll`）失敗が起きやすいので、先に `uc-windows-cuda-dll` を読みます。日本語が文字化けする場合は `uc-windows-cp932`（あらゆる境界で UTF-8 を指定する）。
- Intel の Mac では `mlx` 系が動きません。入れる前に確かめます。
- 音声の取り出しに ffmpeg が要ります（`media-tools` が場所を探して、実際に起動して確かめます）。

## 手順

1. 作業フォルダを作って部品を足す。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-server --name "Caption Maker" --label "字幕づくり"
   python3 <SKILL>/scripts/add_part.py transcribe-srt --project <作業フォルダ>
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Caption Maker`、Windows `%USERPROFILE%\PremierePlugins\Caption Maker` です。
2. `index.js` の `onRun` で、素材の実ファイルのパスを取る。選んだクリップの `getProjectItem()` で素材の項目を取り、`ppro.ClipProjectItem.cast(項目).getMediaFilePath()` で実ファイルのパスを読む（25.6 以降。取引の外で読む。`cast` や `getMediaFilePath` が無い版では存在を確かめて理由つきで止める）。取れなければ「素材がオフラインです」と止める。
3. ジョブを呼ぶ:

   ```
   const r = await PPM.server.runJob("transcribe",
     { mediaPath, language: "ja", maxChars: 18 },
     { onProgress: (p, m) => PPM.ui.showInfo(out, `${m}（${p}%）`) });
   ```

   範囲だけ起こすなら `start`（秒）と `duration`（秒）を足す。戻りの `srtPath` が SRT のパスです。
4. プロジェクトに読み込む（取引の外で単独に呼ぶ）:

   ```
   const root = await project.getRootItem();
   await project.importFiles([r.srtPath], true, root, false);
   ```

   完了の文に「プロジェクトパネルに SRT を入れました。タイムラインへは自分で置いてください」と書く。
5. 意味で区切る改行を足す場合（任意）。文字数での改行を、AI の文脈判断に置き換える。
   - 機械の形態素解析（MeCab など）は使いません。複合動詞やカタカナ語を途中で割るためです。AI に「意味の切れ目で 1 行 25 字以内に」と頼みます。
   - AI が整えた行と、文字起こしの単語の列を、`difflib` で **全体合わせ**して時刻を割り当てます。「少し先を探して進む」やり方は、終盤ほどずれます。
   - 組み立てたあと、1 行の長さ（25 字超）と、行頭に来てはいけない文字を機械で検査し、該当行だけ AI に直させます。AI の改行は実行ごとに出来が違うため、この直しの輪は省けません。
   - 手順の詳細は `feat-premiere-skills` と `feat-cutsrt-telop-srt`。
6. サーバーを入れる（依存を入れるので許可を取る）。

   ```
   python3 <作業フォルダ>/server/install.py --dry-run
   python3 <作業フォルダ>/server/install.py --with-deps
   ```
7. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

## 確認

利用者の Premiere で、**30 秒ほどの短い素材**から試してもらいます。

1. 初回は、モデルの準備で時間がかかる。パネルに進み具合が出る。
2. プロジェクトパネルに `.srt` が増える。
3. SRT を開くか、タイムラインに置いて、字幕の文が音声と合っている（固有名詞は誤りやすい。辞書で直す機能は `feat-cutsrt-dictionary`）。
4. 時刻が最後までずれていない。終盤のずれは、文字起こしの合わせ方が原因のことが多い。
5. 音声が映像より短い素材では、「音声が不足」と全滅しない（`uc-xml-audio-shorter-than-video`）。

## 戻し方

SRT を作って読み込むだけで、シーケンスは変えません。**取り消しは要りません**。不要なら、プロジェクトパネルの SRT の項目を選んで消し、手元の SRT のファイル（一時フォルダ）を消します。

## 使う部品

- `transcribe-srt`: ジョブ `transcribe`（音声の取り出し → 文字起こし → SRT）
- `media-tools`: ffmpeg、音声の取り出し
- `local-server`: ジョブの受け渡し
- `ppro-kit`: プロジェクトとシーケンスの取得

## 出どころ

- premiere-skills の `/srt`・`/srt-fast` の実測（Mac。意味で区切る改行、全体合わせ、検査の輪）
- Cut & SRT の字幕の生成の記録（`feat-cutsrt-telop-srt`）と Windows の失敗記録（CUDA・文字コード）
- このキットの部品 `transcribe-srt` の説明書き（SRT は読み込めるが、配置は手作業か別の処理）
