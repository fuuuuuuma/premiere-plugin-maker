---
name: premiere-plugin-maker
description: Premiere（Premiere Pro）用のプラグインを、要望を聞いて作るスキル。UXP のパネル・メニューのコマンド・手元のサーバーで重い処理・CEP 補助（再生・分割）・AI から操作する口まで作れる。「Premiere のプラグインを作りたい」「Premiere でボタン一つで〜したい」「Premiere の拡張機能」「UXP のパネル」「.ccx」「プラグインが読み込まれない・動かない」などでは、明示されていなくても必ず使う。Mac と Windows の両方に対応し、過去の機能・失敗事例・版の知識と部品・雛形・機械の検査を使い、Premiere で動くことを確かめてから完成とする。
---

# Premiere のプラグインを作る

このスキルのフォルダを `<SKILL>` と書く（Claude Code は冒頭の「Base directory for this skill」、Codex はスキル一覧に出るパス）。道具はいつも `<SKILL>/scripts/` から呼び、作業フォルダには写さない。

- Mac: `python3 <SKILL>/scripts/<道具>.py …`
- Windows: PowerShell で `py -3 <SKILL>\scripts\<道具>.py …`（py が無ければ `python`）。文中の `%USERPROFILE%` は場所の書き方で、PowerShell で打つときは `$env:USERPROFILE`

## 0. 毎回、最初に

1. **OS を聞く**: 「お使いのパソコンは Windows と Mac のどちらですか？」（依頼に書いてあれば聞かない）。以降のコマンドとパスは、その OS の形で出す。
2. **一式があるか見る**: `<SKILL>/scripts/doctor.py` が無ければ、「公開リポジトリから一式を取ってきます」と伝えてから取ってくる。
   - Mac: `git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker ~/.premiere-plugin-maker/kit`（git が無ければ `mkdir -p ~/.premiere-plugin-maker && curl -L https://github.com/fuuuuuuma/premiere-plugin-maker/archive/refs/heads/main.tar.gz | tar xz -C ~/.premiere-plugin-maker && mv ~/.premiere-plugin-maker/premiere-plugin-maker-main ~/.premiere-plugin-maker/kit`）
   - Windows（PowerShell）: `git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker "$env:USERPROFILE\.premiere-plugin-maker\kit"`（git が無ければ `Invoke-WebRequest https://github.com/fuuuuuuma/premiere-plugin-maker/archive/refs/heads/main.zip -OutFile "$env:TEMP\ppm.zip"; Expand-Archive "$env:TEMP\ppm.zip" "$env:USERPROFILE\.premiere-plugin-maker"; Rename-Item "$env:USERPROFILE\.premiere-plugin-maker\premiere-plugin-maker-main" kit`）
   - 以降の `<SKILL>` は、取ってきた `kit` の中の `plugins/premiere-plugin-maker/skills/premiere-plugin-maker`。
3. **診断**: `doctor.py --online`（利用者の PC で動かす）。`[NG!]` は直し方を 1 つずつ案内し、入れてよいか聞いてから進む。Premiere・Creative Cloud・UXP Developer Tools は利用者に入れてもらう。

## 1. 聞き取り（1 回に 1 問・選択肢つき）

1. 何をしたいか（1 文で）
2. 何に対してか（選んだクリップ／シーケンス全体／プロジェクトの素材／マーカー／書き出し）
3. どう動かすか（パネルのボタン／メニューのコマンド／キーの割り当て）
4. 結果（タイムラインが変わる／ファイルができる／見るだけ）
5. 重い処理があるか（音声の解析・文字起こし・AI・ファイルの生成）
6. 誰が使うか（自分だけ／ほかの人にも配る）
7. 具体的な中身（どの効果を・どの値で・何秒で、など。「おまかせ」なら見本の値を決めて計画に書く）

## 2. 知識を引く

- `kb.py search <要望の言葉> --os <mac か windows>` を実行し、上位を `kb.py show <id>` で読む。
- 結果が薄ければ `kb.py list --brief` を読み、意味で選ぶ。
- status が verified の知識を優先する。unverified の知識を使うときは「未確認です」と伝え、診断ボタンで確かめてから採用する。superseded は使わない。
- 部品がある機能は部品を使う。部品が無い機能（話者の振り分け・顔の追従など）は、features の記録を元に部品を組み合わせて作る。

## 3. できるかを判定

- `kb.py show core-capabilities` の表に当てる。できない操作（分割・速度の変更・字幕の本文の書き換え・プログラムモニターの再生など）は、そう伝えて代わりの手から選んでもらう。確かめていない抜け道を「動く」と言わない。
- 使う API の最低版は `core-versions` で確かめる（check.py の J014 も止める）。

## 4. 計画を見せて承認をもらう

作るもの・雛形・部品・最低版・権限・確かめ方・できないことを平易な言葉で会話に見せ、承認をもらってから作る（承認の前は作業フォルダを作らない）。承認された計画は、作った作業フォルダに `plan.md` として残す。

## 5. 作る

1. 雛形を選ぶ（`kb.py show core-intake`）: panel／panel-commands／panel-server／cep-helper（上級・期限つき・Mac だけ）。一覧は `new_plugin.py --list`。近い完成サンプル（`<SKILL>/examples/` の zoom-button・silence-cut・telop-restyle）があれば、その `index.html` と `index.js` を見本にする。
2. `new_plugin.py --template <雛形> --name "<英字の名前>" --label "<表示名>"`。既定の場所は Mac `~/PremierePlugins/<名前>`、Windows `%USERPROFILE%\PremierePlugins\<名前>`。`--dest` を付けると、そのフォルダ自体が作業フォルダになる。既にあれば上書きしない。
3. 部品を足す: `add_part.py <部品> --project <作業フォルダ>`（一覧は `add_part.py --list`）。
4. `index.js` の `onRun` に処理を書く。型は `core-api-patterns` と `core-transactions`（取引の中で await しない・Action は取引の中で作る・戻り値を見る・1 回の取引で取り消し 1 回）。
5. `check.py <作業フォルダ>` の誤りが 0 件になるまで直す。注意は理由を読んで判断する。
6. サーバーの部品を使うなら、依存（Python の部品・モデル）を入れる前に、何をどれくらい入れるかを見せて許可を取る。

## 6. Premiere で確かめる（ここを通るまで完成と言わない）

1. 読み込み: UXP Developer Tools の［Add Plugin］で `manifest.json` を選び［Load］。直したら［Reload］、manifest を変えたら［Unload］→［Load］。開発者モードは UDT 側と Premiere 側（［設定］→［プラグイン］→ Premiere の再起動）の両方が要る（`core-dev-loop`。Windows は `platform-windows`）。
2. サーバーがあれば入れる: Mac は `server/install_mac.command`、Windows は `server\install_windows.bat`（`ref-local-server`）。
3. パネルの「診断」を押してもらい、`logs.py --project <作業フォルダ>` で結果を読む。使う API が missing なら、実装する前に手を変える。
4. 試してほしい操作は 1 回に 1 つ。結果を聞き、ログを読んでから次へ進む。
5. 見た目はコマの書き出し（`PPM.exportFrame`）か画面写真で確かめる。取り消し（Cmd+Z / Ctrl+Z）で戻ることも確かめる。

## 7. 直す・手元に残す

新しく分かったこと（新しい失敗と直し方など）は `kb.py note --title "…" --tags "…" --body "…"` で手元に残す。次回からの検索に出る。

## 8. 配る（ほかの人にも使ってもらうとき。6 の確認が済んでから）

1. 版数を上げる。manifest と build_info を同じ版にする（`core-versioning-release`）。
2. `make_ccx.py <作業フォルダ> --bundle` で `dist/<名前>_v<版>/` を作る（.ccx・はじめにお読みください・サーバーの zip）。
3. 入れ直して確かめる: `install_ccx.py --reinstall <ccx のパス>`（既定は試し実行。実行は `--apply` を付ける）。
4. Adobe の Marketplace に出すなら、審査の条件を案内する（`core-versioning-release`）。

## 守ること

- 利用者のプロジェクトと素材を上書きしない。一括の変更の前は保存を勧め、件数を伝えて確認する（`core-safety`）。
- Premiere を変える処理は、取り消し 1 回で戻る作りを基本にする（`PPM.transact`）。
- 権限は最小にする。ネットに出る機能は相手先を示して同意を取る。鍵は OS の保管庫に置く（部品 keychain）。
- インストール・ダウンロード・課金・外部への送信・公開、CEP の PlayerDebugMode の設定、MCP の登録は、実行の前に許可を取る。
- 確かめていないことを「動きます」と言わない。未確認は未確認と書く（`core-verification`）。
- 他人のテンプレートや有料素材を写さない。Adobe の配布物（CSInterface.js・Basic Title.mogrt）を作業フォルダや配布物に入れない。

## いつ何を読むか

| こんなとき | 読む知識 |
|---|---|
| 何ができて何ができないか | core-capabilities |
| 版と最低版 | core-versions |
| 取引・取り消し | core-transactions |
| API の書き方 | core-api-patterns |
| 画面が崩れる | core-ui-rules |
| 権限 | core-manifest-permissions |
| 読み込めない・つながらない | core-dev-loop |
| 確かめ方 | core-verification |
| Windows で作る・配る | platform-windows・platform-cross |
| Mac で作る・配る | platform-mac |
| 時間・XML | ref-ticktime・ref-fcp7-xml |
| テロップ・MOGRT | ref-mogrt・ref-prtextstyle・recipe-telop-restyle |
| キー・補間 | ref-keyframe-interpolation・recipe-keyframe-motion |
| 重い処理・サーバー | ref-local-server・recipe-local-server-heavy |
| 再生・分割（CEP） | ref-cep-extendscript・recipe-razor-workarounds |
| AI から操作 | ref-mcp・recipe-agent-mcp |
| 配る | core-versioning-release |

## 終わりの報告の型

1. 何を作ったか（1 文）と作業フォルダの場所
2. Premiere で確かめたこと／まだ確かめていないこと
3. 使い方（ボタン・取り消しの回数）
4. 次にしてほしいこと（あれば 1 つ）
