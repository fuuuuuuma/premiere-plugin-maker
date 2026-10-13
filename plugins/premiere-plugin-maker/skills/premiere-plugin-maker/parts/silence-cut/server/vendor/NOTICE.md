# silence_cut.py について

- 出どころ: premiere-skills（fuuuuuuma/premiere-skills）の silence_cut.py を、Cut & SRT が実機で使っている上位版から写したもの。ライセンスはこのリポジトリと同じ MIT。
- 無音の判定は 20ms の RMS の包絡で前後を同じ基準で測る（silencedetect の前後の偏りをなくした版）。
- 終了コード: 3 = カットする所が無い（成功扱いにしない）、4 = 基準の音声を解析できない、5 = 書き出した XML に映像が無い（マルチカム）。
- このキットで変えたこと（Windows で文字化けして止まらないため）:
  - 1247 行目（映像のストリームを読む ffprobe の呼び出し）: `subprocess.run(..., text=True)` に `encoding="utf-8", errors="replace"` を追加
  - 1284 行目（音声のチャンネル数を読む ffprobe の呼び出し）: 同じく `encoding="utf-8", errors="replace"` を追加
  - 写した元: Cut & SRT の server/vendor/premiere_skills/scripts/silence_cut.py（2026-10-13 時点、3306 行）。ほかの行は 1 文字も変えていない
