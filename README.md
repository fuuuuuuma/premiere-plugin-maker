# premiere-plugin-maker

AI（Claude Code / Codex）に頼むだけで、Premiere 用のプラグインを作れるスキルです。要望を聞き取り、これまでのプラグイン作りで分かった知識・失敗事例・部品を使って組み立て、Premiere で動くことを確かめてから完成にします。

- Mac と Windows の両方に対応（最初にどちらかを聞きます）
- パネルのボタン・メニューのコマンド・手元のサーバーでの重い処理（無音カット・文字起こし・テロップの生成）・CEP 補助（再生・分割）・AI から操作する口まで
- 作った物は機械の検査（過去に実機で起きた失敗の型）を通してから、Premiere で確かめます
- 配る準備（.ccx と「はじめにお読みください」）までできます

これは Adobe の公式のものではありません。

## 入れ方

Claude Code:

```bash
claude plugin marketplace add fuuuuuuma/premiere-plugin-maker
claude plugin install premiere-plugin-maker@premiere-plugin-maker
```

Codex:

```bash
codex plugin marketplace add fuuuuuuma/premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

入れた後は、新しいセッション（新しいタスク）で使えます。ターミナルを使わない人は、[導入用の文](docs/prompts-ja.md) をデスクトップアプリに貼ってください。

## 頼み方の例

> Premiere で、選んだクリップにボタン一つでゆっくりズームを付けるプラグインを作りたい

> 無音の所を自動でカットするパネルを作って（Windows です）

> 作ったプラグインが Premiere に出てこないので見てほしい

## 必要なもの

| もの | 必須か | 入れ方 |
|---|---|---|
| Premiere 25.6 以降（推奨 26.x） | 必須 | Creative Cloud デスクトップ |
| UXP Developer Tools | 必須（作っている間） | Creative Cloud デスクトップ →［すべてのアプリ］ |
| Python 3.9 以上 | 必須（スキルの道具） | Mac: 入っていなければ python.org、Windows: Python install manager |
| ffmpeg | 音声を扱うとき | Mac: `brew install ffmpeg`、Windows: `winget install --id Gyan.FFmpeg -e` |
| mlx-whisper / faster-whisper | 文字起こしをするとき | 使うときにスキルが案内します（入れる前に確認します） |

スキルは、これらを勝手には入れません。足りない物は、入れ方を見せて確認してから進みます。

## できないこと

Premiere の UXP の API に無い操作は作れません。代わりの手（FCP XML の作り直し・CEP 補助・手作業）を提案します。

- クリップの分割（CEP 補助で試せますが期限つき・Mac だけ）
- 再生速度の変更、字幕（キャプション）の本文の書き換え
- プログラムモニターの再生（CEP 補助で可能）、メニューのコマンドの実行
- Premiere のキーボードショートカットへの割り当て（Mac はシステム設定で可能）
- C++ を使うプラグイン（Hybrid）

## 確かめた範囲

- 道具のテスト（Python 217 件・JS 55 件）: GitHub Actions の macOS と Windows の両方で通っている（0.1.0 の公開時）。Windows の鍵の保管（DPAPI）の往復もここで確かめた
- Premiere の実機: このキット（道具・部品・完成サンプル）自体は、まだ Premiere の実機で通して確かめていません（0.1.0 の時点）。部品の多くは、元になったプラグイン（Cut & SRT・Effect & Design など）が Mac の Premiere で実際に使っていた書き方を写したもので、知識の各項目に「確かめたか（verified / partial / unverified）」を書いてあります。テロップの部品は、この Mac の Premiere 26.5.2 に入っている Basic Title.mogrt から MOGRT を作るところまでテストで通しています
- Windows の Premiere の実機では確かめていません。手順と検査は Windows 向けにも用意してあり、確かめていない所は知識に「未確認」と書いてあります

## 中身

- `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/SKILL.md` — 手順
- `knowledge/` — 知識の棚（版・API の型・失敗事例・過去の機能の記録・OS の違い）
- `parts/` — 部品、`templates/` — 雛形、`examples/` — 完成サンプル、`scripts/` — 道具（Python の標準ライブラリだけ）

## 更新のしかた

```bash
claude plugin marketplace update premiere-plugin-maker
claude plugin update premiere-plugin-maker@premiere-plugin-maker
```

```bash
codex plugin marketplace upgrade premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

## ライセンス

MIT（[LICENSE](LICENSE)）。Adobe の配布物（CSInterface.js・Premiere の中の Basic Title.mogrt など）は同梱していません。MOGRT の生成は、利用者の Premiere の中にある Basic Title.mogrt を使います。
