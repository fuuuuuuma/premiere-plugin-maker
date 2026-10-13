# premiere-plugin-maker 設計書

- 日付: 2026-10-13
- 状態: 利用者の確認待ち
- 作業場所（予定）: `projects/常時運用/premiere-plugin-maker/`（このワークツリー内の独立した git。channel-pv-maker と同じ扱い）
- 材料: このセッションの調査資料 7 本（付録 A）

---

## 0. 要約

作者がこれまで作った Premiere 用プラグイン（Cut & SRT、Effect & Design、小型 UXP 4 本、KAZARU、premiere-skills、premiere-agent-kit）の部品・知識・失敗の記録を一つにまとめ、Claude Code と Codex の両方で使えるスキル「premiere-plugin-maker」にする。

視聴者や編集者がこのスキルを AI に使わせると、AI はまず「Windows か Mac か」を聞き、要望を聞き取り、知識の棚から関係する知識と部品を選び、雛形と部品を組み合わせてプラグインを作る。作った物は機械の検査に通し、利用者の Premiere で動くことを確かめてから完成とする。

公開 GitHub から 2 行で導入でき、スキルの文書だけを持っている人には、発動時に一式を GitHub から取ってくる。

---

## 1. 目的と成功の基準

### 1.1 目的

視聴者・編集者が、Claude Code または Codex にこのスキルを使わせるだけで、要望に合った Premiere プラグインを、Mac でも Windows でも、同じ手順・同じ品質で作れるようにする。これまでの機能・失敗・版の情報を知識として持ち、要望に合わせて選んで使う。

### 1.2 成功の基準（公開前に全部を満たす。S3 と S5 は公開後）

| # | 基準 | 確かめ方 |
|---|---|---|
| S1 | 視聴者役の AI が、典型的な要望（§13.2 の一覧）で手順どおりに進み、作った物が機械の検査で誤り 0 件になる | Sonnet に利用者役と作り手役をさせるリハーサル（Mac 想定・Windows 想定の両方）。つまずいた点は全部直す |
| S2 | 完成サンプル 3 本が、この Mac の Premiere 26.5.2 で読み込め、目的の操作が動く | UDT で読み込み → 操作 → UXP のログと書き出したコマで確認。.ccx にして入れ直しても動く |
| S3 | キットの道具のテストが macOS と Windows の両方で通る | GitHub Actions の macos-latest / windows-latest（公開後） |
| S4 | 要望の言い回し 30 件それぞれで、関係する知識が検索の上位 5 件に入る | 評価表を使った機械判定 |
| S5 | 公開 GitHub から Claude Code と Codex の両方に 2 行で入る | 隔離した設定フォルダ（CLAUDE_CONFIG_DIR / CODEX_HOME）で導入（公開後） |
| S6 | 公開物に個人のパス・鍵・利用者名・取引先の情報・有料素材が 0 件 | 衛生検査のテスト |

---

## 2. 使う人と前提

- 使う人: 作者の視聴者・編集者。プログラミングには詳しくない想定。AI はデスクトップアプリの Claude Code または Codex を使う。
- OS: Mac（Apple シリコンが主。Intel も考慮）と Windows 10/11。スキルの最初の質問で確定する。
- Premiere: UXP の正式版が入った 25.6 以降。推奨は 26.x。ベータ版（27.x）は任意。
- 利用者の PC に要るもの（スキルが案内し、勝手には入れない）: Premiere、Creative Cloud デスクトップ、UXP Developer Tools（以下 UDT）、Python 3.9 以上（キットの道具を動かすため）。部品によっては ffmpeg などが加わる。

---

## 3. 合意した方針（会話の記録）

| 日付 | 決めたこと | 出どころ |
|---|---|---|
| 2026-10-13 | 公開 GitHub で配る。これまでの機能も部品として全部入れる | 利用者の回答（選択肢「公開GitHub・機能も全部入り」） |
| 2026-10-13 | Windows でも再現度をなるべく上げる。最初に Windows か Mac かを聞く | 利用者の指示 |
| 2026-10-13 | Cut&SRT にしか要らない機能も、知識として積み上げる | 利用者の指示 |
| 2026-10-13 | ほかの知識も積み上げ、要望に合わせて使い分けながら作る | 利用者の指示 |
| 2026-10-13 | 進め方は「組み立てキット方式」に完成サンプルを足す形（案 A） | 設計案に対する利用者の返答 |

---

## 4. 全体構成

### 4.1 リポジトリの形

docu-video-maker・after-effects-agent と同じ「入れ子の形」にする。利用者の PC に入るのは `plugins/premiere-plugin-maker/` の中だけで、テストや開発用の文書は入らない（調査 F の実測）。

```
premiere-plugin-maker/                      GitHub リポジトリ（独立した git）
├─ .claude-plugin/marketplace.json          Claude Code 用の目録
├─ .agents/plugins/marketplace.json         Codex 用の目録
├─ README.md   LICENSE（MIT）   CHANGELOG.md
├─ docs/
│   ├─ prompts-ja.md                        デスクトップアプリに貼る「導入用」「制作用」の文
│   └─ superpowers/                         この設計書の写しと実装計画
├─ tests/                                   キット自体のテスト（利用者の PC には入らない）
├─ .github/workflows/ci.yml                 macOS / Windows でテストを回す（公開後に有効）
└─ plugins/premiere-plugin-maker/           利用者の PC に入る部分
    ├─ .claude-plugin/plugin.json
    ├─ .codex-plugin/plugin.json
    └─ skills/premiere-plugin-maker/
        ├─ SKILL.md                          手順の本体（200 行以内）
        ├─ agents/openai.yaml                Codex での表示
        ├─ knowledge/                        知識の棚（§6）
        ├─ parts/                            部品（§7）
        ├─ templates/                        雛形（§8）
        ├─ examples/                         完成サンプル（§8）
        └─ scripts/                          道具（§9。Python 標準ライブラリだけ）
```

- 名前はリポジトリ・目録・プラグイン・スキルとも `premiere-plugin-maker` にそろえる。公開後は変えない（受け取った人の導入が壊れるため）。
- スキルの中から道具を呼ぶときは「このスキルのフォルダから見た相対パス」を使う。既存の公開スキルが使っている `${CLAUDE_PLUGIN_ROOT:-…}` は Claude Code でも置き換わらないと分かったため（調査 F §3.1）、使わない。
- `plugin.json` は Claude 用と Codex 用で name と version を必ず一致させ、テストで縛る。

### 4.2 導入のしかた（README に載せる）

```bash
claude plugin marketplace add fuuuuuuma/premiere-plugin-maker
claude plugin install premiere-plugin-maker@premiere-plugin-maker
```

```bash
codex plugin marketplace add fuuuuuuma/premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

ターミナルを使わない人のために、デスクトップアプリに貼れば AI が導入してくれる文を `docs/prompts-ja.md` に置く（after-effects-agent の方式）。

---

## 5. スキルの流れ（発動から配布まで）

### 5.0 準備

1. **最初の質問**: 「お使いのパソコンは Windows と Mac のどちらですか？」と聞く。選択式で聞ける環境では選択式にする。答えに合わせて、以降のコマンド・パス・導入方法を OS 別の表から出す。後で診断の結果と食い違ったら、利用者に確認する。
2. **キットの確認**: このスキルのフォルダに `knowledge/` `parts/` `templates/` `scripts/` がそろっているかを見る。無ければ GitHub から取ってくる（§11）。
3. **環境の診断**: `doctor.py` で、Premiere の版（安定版とベータ版）、UDT の有無、開発者モード、Creative Cloud、プラグインの導入ツール（UPIA）、Python、ffmpeg（部品で要るときだけ）を調べる。足りない物は直し方を見せ、入れる前に許可を取る。

### 5.1 聞き取り

1 問ずつ、選択肢をつけて聞く。

1. 何をしたいか（1 文で）
2. 何に対してか（選んだクリップ／シーケンス全体／プロジェクトの素材／マーカー／書き出し）
3. どう動かすか（パネルのボタン／メニューのコマンド／ショートカット）
4. 結果はどうなるか（タイムラインが変わる／ファイルができる／情報を見るだけ）
5. 重い処理があるか（音声の解析・文字起こし・AI）
6. 誰が使うか（自分だけ／ほかの人にも配る）

聞き取った言葉で知識の棚を検索し（§6.3）、使える知識・部品・過去の機能の記録を選ぶ。

### 5.2 実現性の判定

「できること・できないこと」の表（`knowledge/core/capabilities.md`）と版の対応表に当てる。できない操作（例: クリップの分割・再生速度の変更・字幕本文の書き換え）なら、正直にそう伝え、代わりの手（FCP XML の作り直し、CEP 補助、MOGRT、利用者の手作業）を説明して選んでもらう。

### 5.3 計画の承認

作業フォルダに計画（`plan.md`）を書き、平易な言葉で見せて承認をもらう。計画には、作るもの・使う雛形と部品・最低版・必要な権限・確かめ方・できないことを書く。

### 5.4 組み立てと実装

1. `new_plugin.py` で雛形から作業フォルダを作る。既定の場所は Mac が `~/PremierePlugins/<名前>/`、Windows が `%USERPROFILE%\PremierePlugins\<名前>\`。macOS の保護フォルダ（書類・デスクトップ・ダウンロード）と、Windows の OneDrive の同期対象を避けるため。既にあれば上書きしない。
2. `add_part.py` で部品を足す。manifest の権限と最低版、`index.html` の読み込みも合わせて更新する。
3. 知識の「API の使い方の型」に沿って実装する。
4. `check.py`（機械の検査）で誤りが 0 件になるまで直す。

### 5.5 Premiere で確かめる

1. 読み込み: UDT の手順を OS 別に案内する。開発者モードは UDT 側と Premiere 側の両方。manifest を変えたら Unload してから Load。
2. 観察: 雛形のプラグインは、自分のログをプラグインのデータフォルダ（`plugin-data:/`）にも書く。Windows では Premiere 製品版の UXP ログの場所が公式に見つからないため（調査 W）、OS に関係なく読める置き場を自前で持つ。`logs.py` がこのログと、Mac の UXP ログ（`~/Library/Logs/Adobe/Adobe Premiere Pro 2026/UXPLogs_*.log`）を探して読み、何が起きたかを AI が確かめる。雛形には「診断」ボタンを入れておき、使う API が利用者の Premiere に本当にあるかを、実装の前に確かめる。公式の文書に載っていても実装されているとは限らないため。診断ボタンはログの保存場所も表示する。
3. 画で確かめる: 必要なら、書き出したコマや画面写真で見る。
4. 利用者にお願いする操作は 1 回に 1 つ。結果を聞いてから次へ進む。
5. 「完成」と言ってよいのは、目的の操作を利用者の Premiere で確かめた後だけ。

### 5.6 直す

5.5 に戻って繰り返す。作業中に新しく分かったことは、利用者の手元の知識ノートに残す（§6.5）。

### 5.7 配る準備（ほかの人にも配るとき）

1. `make_ccx.py` で、配る物だけを集めて .ccx にする。
2. `install_ccx.py` で入れ直して確かめる（Mac・Windows とも UPIA）。
3. 受け取る人向けの「はじめにお読みください」を雛形から作る。
4. 版数の決まりを伝える（同じ版数では更新が届かない。上げるか、先に削除してから入れる）。
5. Adobe の Marketplace に出す場合は、審査の条件（外部アプリの起動不可・プライバシーポリシー等）を案内する。

---

## 6. 知識の棚

### 6.1 種類と置き場所

```
knowledge/
├─ core/        どの要望でも最初に読む基本（版と API、取引の作法、できないこと、画面の制約、確かめ方の作法）
├─ recipes/     要望の型ごとの作り方（例: 選んだクリップに一括で効果、キーで動き、マーカーとチャプター、
│               テロップの一括差し替え、無音カット、字幕、書き出しの自動化、素材の取り込みとビン整理、
│               ショートカット化、ローカルサーバーで重い処理、AI との連携）
├─ features/    これまで作った機能の記録（どう作ったか・使った API・つまずき・結果・状態）
├─ usecases/    失敗事例（症状 → 原因 → 直し方 → 再発防止。版つき）
├─ platform/    mac.md / windows.md（パス・導入・文字コード・権限の違い）
├─ reference/   形式の仕様（.prtextstyle の中身、.prfpset、FCP7 XML、MOGRT の中身、TickTime）
└─ index.json   検索用の索引（kb.py build が作る）
```

### 6.2 1 件の書き方

各ファイルの先頭に次の項目を書く。

```
---
id: ui-flex-rows-collapse
title: 一覧の行が中身より低く潰れる
kind: usecase            # core / recipe / feature / usecase / platform / reference
tags: [画面, CSS, flex, 一覧]
os: [mac, windows]
premiere: ">=25.6"
status: verified         # verified（実機で確認）/ partial（一部だけ確認）/ unverified（未確認）/ superseded（古い。使わない）
parts: [ui-kit]
related: [ui-sp-button-inactive]
---
```

本文は種類ごとに型を決める。usecase は「症状・原因・直し方・再発防止」、feature は「何をする機能か・作り方・使った API・つまずき・結果・今の状態」、recipe は「前提・手順・確認・戻し方」。

### 6.3 探し方

- `kb.py search "顔 追従 スタンプ"` が、id・題・種類・状態・パスを関係の強い順に返す。
- `kb.py show <id>` で 1 件を表示、`kb.py list --kind usecase --os windows` で絞り込む。
- 同じ意味の言葉の表を持つ（例: 「カット」「切る」「分割」「レーザー」「razor」）。
- 索引 `index.json` は `kb.py build` で作り、実ファイルと一致していることをテストで確かめる。

### 6.4 使い分けの決まり（SKILL.md に書く）

1. 聞き取った要望の言葉で検索し、上位を読む。
2. status が verified の知識を優先する。unverified の知識を使うときは「未確認です」と利用者に伝え、診断ボタンで確かめてから採用する。
3. superseded の知識は使わない（古い主張が訂正されたものを残してある）。
4. 部品がある機能は部品を使い、部品が無い機能（Cut&SRT 固有の重い機能など）は features の記録を元に、部品を組み合わせて作る。

### 6.5 使う人の手元での積み上げ

作業中に新しく分かったこと（新しい失敗と直し方など）は、`kb.py note` で利用者の手元（Mac `~/.premiere-plugin-maker/notes/`、Windows `%USERPROFILE%\.premiere-plugin-maker\notes\`）に同じ書き方で残す。次回からの検索にも出る。公開キットへの還元は任意で、GitHub の Issue のひな形を用意する。

### 6.6 積む知識の出どころ

すべて、個人名・個人のパス・鍵・取引先の情報を外して書き直す。原文の丸写しはしない。

| 出どころ | 積むもの |
|---|---|
| Cut & SRT（v0.14.0） | 全タブの機能の記録（カット、テロップと SRT、整列、デザイン、素材、Web、送る、話者、演出のスタンプ・ズーム・画角、クリップ棚、FX、分割・修正、辞書、MCP、再生ヘルパー、設定・診断・サポートパック、導入・更新・配布）と、failures.md・HANDOFF.md の失敗事例 |
| Effect & Design（v0.4.0） | CEP と UXP 補助の併用、MOGRT の生成、アニメと補間の焼き込み、テキストスタイルの取り込み、カタログ、パッケージ |
| 小型 UXP 4 本 | caption-align・clip-clipboard・effect-shortcut・silence-cut の作りと、記録どうしの食い違い |
| KAZARU | .prtextstyle と .prfpset の生成、言葉から数値への対応表 |
| premiere-skills | /cut（無音カット）と /srt（字幕）の作りと終了コードの約束 |
| premiere-agent-kit | MCP の使い方、UXP に無い操作の逃げ道、トラブルの切り分け表、画面操作の作法 |
| 作者の記憶のうちプラグイン作りに効くもの | テロップの置き方と校正、編集点は声の谷、文字起こしと無音カット、日本語の扱い（NFC/NFD）、ローカルブリッジ、検証の鉄則、Web の画面の落とし穴、Jev の使い方 |
| Adobe 公式の最新事実（2026-10-13 調査） | 版ごとの API、26.3 の取引の規則変更、CEP の終了予定、UDT と .ccx と UPIA、UXP の制限、公式サンプルと型定義、フォーラムの頻出の落とし穴 |

---

## 7. 部品

### 7.1 部品の形

`parts/<名前>/part.json` に、名前・説明・置くファイル・manifest に足す権限・必要な最低版・依存（Python のパッケージ・ffmpeg など）・対応 OS・状態・関係する知識を書く。ファイル一式と部品のテストを同じフォルダに置く。

### 7.2 一覧

「状態」は移植元での確認の度合い。キットに移すときに書き直すので、移した後の物は改めて確かめる。

| 部品 | 中身 | 移植元 | 移植元での状態 |
|---|---|---|---|
| ppro-kit（JS） | 取引の 3 段階、TickTime、選択の取得、クリップの取り直し、キー・効果・トランジション・マーカー・コマの書き出し・fps の取得、原因つきのエラー | Cut&SRT の index.js、Effect & Design の core.js、effect-shortcut | 型は実機で確認済み |
| ui-kit（CSS・JS） | 色と文字の決まり、潰れない一覧、ボタンが押せない問題の対策、select のホイール対策、空欄の値の扱い | Cut&SRT の panel.css・index.js | 対策は実機で確認済み |
| probe（JS） | 診断ボタン（API の有無・Premiere と UXP の版をログへ） | Effect & Design の診断の型 | 新規。要確認 |
| local-server（Python・JS） | 127.0.0.1 だけで待つ小さなサーバー、起動ごとの合言葉、握手ファイル、ジョブ、パネル側の呼び出しと待ち、Mac の常駐（launchd）と Windows の常駐（タスク スケジューラ）、導入・診断・削除の骨格 | Cut&SRT の bridge_server と導入まわり | Mac は確認済み。Windows は導入とサーバーの動作まで確認、自動起動は未確認 |
| fcpxml（Python） | FCP7 XML の読み書き（定義は文書に 1 回、ぶら下がりの検査、timebase と ntsc、ネスト、マルチカム）、UXP からの書き出し（26.2 以降）と読み込み | silence_cut.py と XML まわり | 実機で確認済み |
| silence-cut（Python） | 音量の包絡で無音を探して XML を作り直す。終了コードの約束つき | premiere-skills の silence_cut.py | 実機で確認済み |
| transcribe-srt（Python） | 文字起こし（Mac は mlx-whisper、Windows は faster-whisper）と SRT、カット後のタイムラインへの合わせ込み | premiere-skills、Cut&SRT | Mac は確認済み。Windows は利用者の報告あり |
| mogrt-text（Python） | 同梱の Basic Title.mogrt を元に文字スタイルを差し替えた MOGRT、.prtextstyle | Effect & Design の engine、KAZARU | 実機で確認済み |
| motion-bake（JS） | Premiere の補間の式、1 コマごとの直線キーへの焼き込み、.prfpset | Effect & Design の motion.js、KAZARU | 実機で確認済み |
| commands（JS・manifest） | メニューのコマンド（ショートカット化）とスロットの保存 | clip-clipboard、effect-shortcut | Cut&SRT に入れた形で実機確認済み |
| cep-helper（CEP） | UXP に無い再生・停止・分割（QE DOM）、命令の名乗り、未署名の拡張を許す設定 | Cut&SRT の cep/ | 再生は確認済み。分割は未確認。Windows は未対応 |
| mcp-bridge（Python・JS） | AI からプラグインを操作する口（MCP → サーバー → パネルの待ち行列） | Cut&SRT の mcp_premiere.py | 実機で確認済み |
| packaging（Python） | .ccx の作成、UPIA での入れ直し、配布の束、「はじめにお読みください」の雛形 | Effect & Design の build_helper、Cut&SRT の make_release_artifacts | Mac は確認済み |
| keychain（Python） | 鍵を OS の保管庫に置く（Mac はキーチェーン、Windows は DPAPI） | Cut&SRT の keychain_store | 確認済み |
| media-tools（Python） | ffmpeg の場所探し、音声の取り出し、音量の計算 | Cut&SRT | 確認済み |

Cut&SRT 固有の重い機能（話者の振り分け、顔の追従、画角の変更、送るタブ、辞書の学習など）は部品にせず、`knowledge/features/` に作り方と使った道具を記録する。要望が来たら、その記録を元に部品を組み合わせて作る。

### 7.3 部品の足し方

`add_part.py <部品> --project <作業フォルダ>` が、ファイルを写し、manifest の権限と最低版を足し、`index.html` の読み込みを足し、部品のテストを置く。同じ部品を 2 回足しても何も起きない。

---

## 8. 雛形と完成サンプル

### 8.1 雛形

| 雛形 | 中身 | 権限の既定 |
|---|---|---|
| panel | パネルだけ。ppro-kit・ui-kit・probe 入り | ファイルはプラグインのフォルダだけ。ネット無し |
| panel-commands | パネル＋メニューのコマンド | 同上 |
| panel-server | パネル＋ローカルサーバー（local-server 入り） | ネットは「すべて」（127.0.0.1 への接続に必要。合言葉で守る） |
| cep-helper | 単体の CEP 補助（上級。UXP で足りないときだけ。期限つき） | — |

どの雛形も、起動の処理はファイルの末尾で 1 回だけ、`require` は try/catch、ログにはプラグインの印を付ける（`logs.py` で拾うため）、版数は 1 か所（`build_info.json`）から読む。

### 8.2 完成サンプル（見本とテストを兼ねる）

| サンプル | 使う雛形・部品 |
|---|---|
| zoom-button（選んだクリップにゆっくりズームを付ける） | panel、ppro-kit、motion-bake |
| silence-cut（無音カット） | panel-server、fcpxml、silence-cut |
| telop-restyle（テロップのデザインを一括で差し替える） | panel-server、mogrt-text |

---

## 9. 道具

すべて Python 3.9 以上の標準ライブラリだけで書き、Mac と Windows の両方で同じ使い方にする。Mac は `python3 scripts/<道具>.py`、Windows は `py -3 scripts\<道具>.py`。OS の違いは 1 か所（`scripts/lib/osinfo.py`）に集める。

| 道具 | すること |
|---|---|
| doctor.py | 環境の診断（`--json` あり。`--online` のときだけ最新版の有無を GitHub で確かめる） |
| new_plugin.py | 雛形から新しい作業フォルダを作る（上書きしない） |
| add_part.py | 部品を足す |
| check.py | 機械の検査（付録 B） |
| logs.py | UXP のログを探し、プラグインの印の行だけを出す（Mac・Windows） |
| kb.py | 知識の検索・表示・索引づくり・手元のノート |
| make_ccx.py | .ccx を作って検査する |
| install_ccx.py | UPIA で入れる・外す・一覧を見る（既定は試し実行。`--apply` で実行） |

---

## 10. Windows で再現度を上げる仕組み

1. 最初の質問で OS を決め、手順・コマンド・パスを OS 別の表から出す（SKILL.md と `knowledge/platform/windows.md`）。
2. 道具は全部 Python で書き、シェルの違い（bash と PowerShell）に依存しない。
3. Windows の既知の違いを知識に積む（調査 W で確度つきで確認済み）:
   - 公式で確認: UPIA は `C:\Program Files\Common Files\Adobe\Adobe Desktop Common\RemoteComponents\UPI\UnifiedPluginInstallerAgent\UnifiedPluginInstallerAgent.exe` に `/install` `/remove` `/list`。UDT の開発者モードは `%CommonProgramFiles%\Adobe\UXP\Developer\settings.json`（中身は Mac と同じ）。CEP の未署名拡張の許可は `HKCU\Software\Adobe\CSXS.12` に文字列 `PlayerDebugMode`=`"1"`。CEP の拡張フォルダは `%APPDATA%\Adobe\CEP\extensions` ほか。非 ASCII を含む .ps1 は UTF-8 の BOM つきが必須。`-ExecutionPolicy Bypass` はその場限り。Python は Python install manager か `py` ランチャー。ffmpeg は `winget install --id Gyan.FFmpeg -e`（開いたままの画面には PATH が反映されない）。
   - 利用者の Windows 実機の記録（Cut&SRT v0.12.0）: Premiere のフォルダは `C:\Program Files\Adobe\Adobe Premiere Pro 2026\`、Basic Title.mogrt はその下の `Essential Graphics\`、127.0.0.1 の http へ接続できた、cp932 での文字化け・停止が繰り返し起きた。
   - 見つからなかった: Premiere 製品版の UXP ログの場所、UXP の登録簿の場所、26.x の CSXS の番号。登録簿の場所は固定で書かず、.ccx は「External フォルダへ写す」ではなく、ダブルクリックか UPIA で入れるよう案内する。
   - そのほか: .bat は ASCII だけ、PATH の反映、SmartScreen、OneDrive の同期対象、パスの空白、UXP での `file:///C:/` の書き方、Adobe Fonts の場所、CUDA が無いときの CPU への切り替え、タスク スケジューラ（サインイン時の自動起動は未確認）。
4. 機械の検査で、Windows で壊れる書き方を止める（Mac 専用のパス、文字コードを指定しない subprocess、BOM の無い PowerShell、ASCII 以外の .bat、実行ビットへの依存）。Cut&SRT v0.12.0 の Windows 報告（Mac 専用の場所だけを探してデザイン機能が失敗した件）の再発防止にあたる。
5. テストで Windows 形式のパスと文字コードも試す。公開後は GitHub Actions の windows-latest で道具のテストを回す。
6. Windows の実機での確認は利用者にお願いする手順を用意する（診断の結果とログを貼ってもらう）。確かめていない所は「未確認」と書く。

---

## 11. 自動ダウンロードの仕組み

1. **普通の導入**: 2 行の導入で一式が入る。発動時はネットを使わず、スキルのフォルダから部品を写す。
2. **一式が無いとき**: スキルの文書だけを持っている人（コピーした人、ほかの AI）のために、SKILL.md の冒頭に「scripts/ が無ければ取ってくる」手順を書く。Mac は `git clone --depth 1`（無ければ curl で tar.gz）、Windows は git（無ければ PowerShell の Invoke-WebRequest で zip）。置き場所は Mac `~/.premiere-plugin-maker/kit/`、Windows `%USERPROFILE%\.premiere-plugin-maker\kit\`。取ってくる前に、公開リポジトリから取ることを一言知らせる。
3. **更新の確認**: `doctor.py --online` が公開リポジトリの最新版の番号を読み、古ければ更新のしかたを案内する。自動では更新しない。
4. **重い依存**: Whisper のモデル・ffmpeg・Python のパッケージは、その部品を使うときだけ、何を・どこに・どれくらいの大きさで入れるかを見せて許可を取ってから入れる。

---

## 12. 安全の決まり（スキルが必ず守る）

1. 利用者のプロジェクトと素材を上書きしない。作業フォルダは新しく作り、既存は上書きしない。
2. Premiere を変える処理は「取引 1 回 ＝ 取り消し 1 回」を基本にする。一括の変更の前は保存を勧める。
3. 作るプラグインの権限は最小にする。ネットに出る機能は、相手先を示して利用者の同意を取る。鍵は OS の保管庫に置き、ファイルに平文で書かない。
4. インストール・ダウンロード・課金・外部への送信・公開は、事前に許可を取る。
5. 確かめていないことを「動きます」と言わない。
6. 利用者にお願いする画面の操作は 1 回に 1 つ。
7. 他人のテンプレートや有料素材を写さない。サービスの規約に反する自動化はしない。

---

## 13. キット自体の確かめ方

### 13.1 機械の確認

- 道具の単体テスト（一時フォルダを使う。標準ライブラリだけ）
- 雛形と完成サンプルが機械の検査で誤り 0 件
- 知識: 全件の先頭項目の検査、索引と実ファイルの一致、リンク切れ、検索の評価表（S4）
- 衛生: 個人のパス・鍵・利用者名の走査、目録と plugin.json の整合（name と version の一致）、SKILL.md が 200 行以内、`claude plugin validate --strict`

### 13.2 リハーサルの要望（S1 と S4 で使う。利用者が足し引きしてよい）

1. 選んだクリップにゆっくりズームインを付けたい
2. 無音の所を自動でカットしたい
3. 文字起こしして字幕（SRT）を作りたい
4. 選んだテロップ全部に同じデザインを当てたい
5. テロップの長さをカットの境目にそろえたい
6. よく使う効果をボタン 1 つで当てたい／ショートカットにしたい
7. クリップの効果や動きをコピーして、別のクリップに貼りたい
8. マーカーからチャプター一覧を作って、YouTube の概要欄に貼りたい
9. 決まった設定でボタン 1 つで書き出したい
10. 素材のフォルダを読み込んで、ビンに整理したい
11. 話している人ごとにテロップのトラックを分けたい（Cut&SRT 固有の機能。知識から作る）
12. 顔に合わせてスタンプを動かしたい（同上）
13. クリップを分割したい（UXP にできない操作。代わりの手を出せるか）
14. 再生速度を変えたい（同上）

### 13.3 実機での確認（そのときに改めて許可をもらう）

完成サンプル 3 本を、この Mac の Premiere 26.5.2 に UDT で読み込んで動かし、.ccx にして UPIA で入れ直しても動くことを確かめる。

---

## 14. 公開と更新

- 公開先: `github.com/fuuuuuuma/premiere-plugin-maker`（public・MIT）。push の前に必ず確認をもらう。
- README: 何ができるか、導入（Claude Code と Codex の 2 行ずつ）、頼み方の例、必要なもの（Mac と Windows）、できないこと、確かめた範囲、ライセンス。
- 版数: plugin.json の version を上げないと、入れた人に更新が届かない。変更のたびに上げ、CHANGELOG に書く。
- 知識の更新: Premiere の新しい版（27.0 の正式版など）が出たら、版の表を更新する手順を docs に書く。

---

## 15. 範囲外

- C++ を使うプラグイン（Hybrid）
- Adobe Marketplace への申請の代行
- Premiere・UDT・Creative Cloud の自動インストール（案内だけ）
- Cut&SRT 製品そのものの配布
- AI のモデルの重み・有料素材・他人のテンプレートの同梱
- Windows 実機での確認（手順と検査は入れる。結果は利用者の報告で確かめる）

---

## 16. 未確定のこととリスク

| # | 内容 | 対処 |
|---|---|---|
| R1 | Windows の Premiere 製品版の UXP ログの場所が見つからない（調査 W） | 雛形が自分のログをプラグインのデータフォルダに書く（§5.5）。`logs.py` は候補の場所も探す |
| R2 | Codex がスキルのフォルダをどう渡すか未観測 | docu-video-maker の方式で動いた記録がある。リハーサルで確かめる |
| R3 | 名称変更（Premiere Pro → Premiere）の影響。この Mac の 26.5.2 は表示名だけ「Adobe Premiere」で、フォルダ・ログ・実行ファイルの名前は「Premiere Pro」のまま。27.x の製品版は不明 | doctor と logs は `Adobe Premiere*` で探し、どちらの名前でも見つける |
| R4 | CEP は 2028-12 に既定で無効、2029-12 に同梱終了の予定 | cep-helper に期限を明記する。27.0 ベータにある UXP の分割の API が正式になったら切り替える |
| R5 | 大量のクリップを一度に編集すると Premiere が落ちる既知の問題（公式で未解決） | 部品で件数を分けて処理する |
| R6 | 作業フォルダがワークツリーの中にあり、公開前にワークツリーを片付けると消える | 公開まで片付けない。節目ごとに git bundle の控えを取る |
| R7 | 移植元の記録どうしに食い違いがある（TickTime の ticks、TrackItemSelection、insertMogrtFromPath の上書きなど） | 片方だけを書かず、両方と「実装はどちらに合わせたか」を知識に残す。部品は安全な側に合わせる |
| R8 | 失敗事例集の材料（調査 B）が仕上げ中 | 実装の途中で取り込む |

---

## 付録 A. 材料にした調査資料（このセッションの作業用フォルダ。公開しない）

| 記号 | 中身 |
|---|---|
| A | Cut & SRT の構成と UXP API の使い方（manifest、API 一覧、取引の作法、UXP の制約 32 件、CEP ヘルパー、MCP、再利用できるコード 10 個） |
| B | 失敗と壁のユースケース集（仕上げ中） |
| C | 開発中の読み込み・.ccx・導入・テスト体系（事故 30 件と守るテストの対応表） |
| D | Effect & Design（CEP・ExtendScript・QE・MOGRT・補間・パッケージ） |
| E | 小型 UXP 4 本の雛形と再利用部品 |
| F | Claude Code と Codex の両方で配る構造、自動セットアップの前例、premiere-agent-kit の知識 |
| G | Adobe 公式の最新事実（2026-10-13） |
| W | Windows 側の事実（2026-10-13。公式・コミュニティ・案件の実機記録を区別） |

## 付録 B. 機械の検査の項目（初版）

- manifest: 必須項目、version の形、host が配列でない、app が premierepro、minVersion の形、id、入口の id の重複、アイコンの実在、権限が最小か（fs を使わないのに fullAccess など）、127.0.0.1 へ接続するなら network が「すべて」、alert や confirm を使うなら enableAlerts、eval を使うなら allowCodeGenerationFromStrings
- JS: 取引のコールバック内の await、取引の外での create*Action、引数の無い getTrackItems、`new ppro.TrackItemSelection`、存在しないプロパティ（videoFrameRate など）の読み取り、相対パスの require、確かめずに使う MutationObserver、executeTransaction の戻り値を見ていない、ticks の直読み、起動処理が末尾に無い・一度だけでない、使った API の最低版が manifest の minVersion より新しい
- CSS: grid、入力欄の近くの position: fixed の重ね表示、縮む一覧の行
- HTML: 読み込むファイルの実在、未対応の要素
- 配布: index.html が読むファイルが配布物に入っているか、秘密情報らしい名前、個人のパス、manifest と build_info の版の一致
- Windows: ASCII 以外を含む PowerShell の BOM、.bat が ASCII か、文字コードを指定しない subprocess、Mac 専用のパス
- Python の部品: 構文の確認
