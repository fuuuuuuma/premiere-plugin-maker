---
id: recipe-silence-cut
title: 無音をカットする
kind: recipe
tags: [無音カット, FCP7 XML, ジェットカット, 閾値, 新しいシーケンス, ffmpeg, 終了コード, パネル, サーバー]
os: [mac, windows]
premiere: ">=26.2"
status: verified
summary: シーケンスを XML で書き出し、手元のサーバーが無音を詰めた XML を作り、読み込んで新しいシーケンスとして開く。元のシーケンスには触らない。カット 0 件は成功にしない
parts: [ppro-kit, local-server, fcpxml, media-tools, silence-cut, ui-kit]
related: [feat-cutsrt-cut, feat-premiere-skills, ref-fcp7-xml, uc-xml-silence-asymmetric, uc-xml-nested-multicam, uc-xml-fit-scale-lost, uc-fps-vfr-timebase, uc-uxp-no-razor-api, recipe-razor-workarounds]
---
## この型で作れるもの

「ボタン 1 回で、しゃべっていない区間を詰めた新しいシーケンスを作る」プラグインです。トーク動画の編集で、いちばん手間のかかる作業を自動化します。

UXP にはクリップを切る API がないので、「切る」のではなく、**XML を作り直して読み込む**方式です。そのため元のシーケンスはそのまま残り、結果は新しいシーケンスとして増えます。完成サンプル `<SKILL>/examples/silence-cut` が、この型そのものです。

## 前提

- 雛形は `panel-server`、部品は `silence-cut`（`fcpxml` と `media-tools` が一緒に入ります）。
- Premiere 26.2 以上（XML の書き出し API が 26.2 から）。
- 音声の解析に ffmpeg と Python の `numpy` が要ります。入っていなければ、何をどれだけ入れるかを利用者に見せて、許可を取ってから入れます。
- 無音の検出は、既定では声が入っているトラック（`A1`）の音声だけで行います。ピンマイクで人ごとにトラックが分かれているときは、対象のトラックを明示します。BGM が常に鳴るトラックを対象にすると、無音がなくなり、カットが 0 件になります。
- マルチカメラのシーケンスは、XML に映像が書き出されません。平らにした（またはネストした）シーケンスで試します。

## 手順

1. 作業フォルダを作って部品を足す。

   ```
   python3 <SKILL>/scripts/new_plugin.py --template panel-server --name "Silence Cut" --label "無音カット"
   python3 <SKILL>/scripts/add_part.py silence-cut --project <作業フォルダ>
   ```

   Windows は `py -3`。既定の場所は Mac `~/PremierePlugins/Silence Cut`、Windows `%USERPROFILE%\PremierePlugins\Silence Cut` です。
2. `index.html` に入力欄を置く: 無音とみなす音量 `threshold`（既定 -48 dB）、最小の無音の長さ `minSilence`（既定 0.2 秒）、前後に残す余白 `padding`（既定 2 コマ）。
3. `index.js` の `onRun`（サンプルのとおり）:
   1. `await PPM.server.connect({ tries: 2, intervalMs: 1000 })`
   2. `const xmlPath = await PPM.fcpxml.exportActiveSequence("ppm-cut-….xml")`
   3. `const result = await PPM.server.runJob("silence_cut", { xmlPath, threshold, minSilence, padding }, { onProgress })`
   4. `await PPM.fcpxml.importAndOpen(result.outputXml)`。新しいシーケンスができて開く。
   5. 完了の文: 「新しいシーケンス『…』を開きました（元のシーケンスはそのままです）」。
4. サーバーの部品の約束（`silence_cut` のジョブ）:
   - 終了コード 3 はカット 0 件。成功にしない。原因は 1 つではないので、しきい値・基準トラック・余白（前後の余白の合計が最小の無音以上だと、すべて余白に食われる）を順に案内する。
   - 終了コード 4 は音声を取り出せない（トラックに音声が無い、素材がオフライン）。5 は XML に映像が無い。どちらも XML を書かない。
5. サーバーを入れる。

   ```
   python3 <作業フォルダ>/server/install.py --dry-run
   python3 <作業フォルダ>/server/install.py --with-deps
   ```

   `--with-deps` は Python の部品（numpy など）を入れる指定なので、入れる内容を見せて許可を取ってから付けます。
6. 検査と読み込み。

   ```
   python3 <SKILL>/scripts/check.py <作業フォルダ>
   python3 <SKILL>/scripts/logs.py --project <作業フォルダ>
   ```

   誤り 0 件を確かめてから［Load］。診断ボタンのあと、結果を `logs.py` で読む。

## 確認

利用者の Premiere で、まず 1〜2 分の短いシーケンスで試してもらいます。

1. 押して数十秒〜数分待つ（長い素材ほどかかります。進み具合がパネルに出る）。
2. プロジェクトに「…カット済み」のようなシーケンスが増え、自動で開く。
3. 元のシーケンスは、そのままの長さで残っている。
4. 新しいシーケンスを再生して、間が詰まっている。言葉の頭や語尾が切れていない（前後の余白と、無音の前後の測り方が偏っていないか）。
5. 映像と音声がずれていない。終わりに近いほどずれる場合は、素材のフレームレートの扱いが原因のことが多い（`uc-fps-vfr-timebase`）。
6. 画面の大きさが変わっていない（「フレームサイズに合わせてスケール」の設定が XML で落ちる事例があります。`uc-xml-fit-scale-lost`）。
7. カット 0 件のときは、数字つきの理由が出る。

## 戻し方

元のシーケンスを変えないので、**取り消しは要りません**。気に入らなければ、増えた新しいシーケンスを削除するだけです（プロジェクトパネルで選んで消す）。XML の取り込みでプロジェクトに入った素材の参照も増えている場合は、その項目も選んで消せます。

しきい値を変えてやり直すと、新しいシーケンスがもう 1 つ増えます。試す回数が多いと混乱するので、名前に時刻が付くことを案内します。

## 使う部品

- `silence-cut`: ジョブ `silence_cut`（音声の包絡で前後を同じ基準で測り、XML を作り直す。終了コードの約束つき）
- `fcpxml`: `PPM.fcpxml.exportActiveSequence` / `importAndOpen`、ぶら下がった参照の検査、宣言の timebase での換算
- `media-tools`: ffmpeg の場所探し・音声の取り出し
- `local-server`: ジョブの受け渡し、常駐（Mac は launchd、Windows はタスク スケジューラ）

## 出どころ

- Cut & SRT の無音カットの実機の記録（Premiere 26.2〜26.5。XML の往復・終了コード・前後の余白の規則。`feat-cutsrt-cut`）
- premiere-skills の `/cut` の作りと終了コードの契約（`feat-premiere-skills`）
- 完成サンプル `silence-cut`（このキットが生成し、`check.py` を通したもの。このキットの形での Premiere 実機の通し確認はまだです）
