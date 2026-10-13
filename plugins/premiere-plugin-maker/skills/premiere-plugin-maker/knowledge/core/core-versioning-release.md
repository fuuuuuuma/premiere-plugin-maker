---
id: core-versioning-release
title: 版数と配布（.ccx・入れ方・更新が届かない理由）
kind: core
tags: [版数, build_info, 配布, .ccx, UPIA, 入れ直し, 更新, Creative Cloud, Marketplace, 審査, パッケージ]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 版は manifest と build_info を同じにし、同じ版で入れ直しても更新されない。.ccx は配る物だけを集めて作り、受け取る人はダブルクリックか UPIA で入れる。Windows の UPIA は未確認
parts: [packaging]
related: [core-dev-loop, core-intake, core-safety, platform-windows, platform-mac]
---
## 要点

- 版数は `manifest.json` の `version` と `build_info.json` の `version` を必ず同じにする（`check.py` の P004）。画面に出す版数は `build_info.json` から読み、HTML に直書きしない。
- **同じ版数のまま入れ直しても、更新されないことがある**。版を上げるか、先に削除してから入れる。
- 版を上げるのは、Mac と Windows の両方に関わる変更のとき。片方だけの修正は、同じ版のまま配布物を作り直し、変更履歴を同じ版の行に足す。
- `.ccx` は配るものだけを集めて作る。UDT の Package は、古い登録や余分なファイルを拾うことがあるので、集め方を自分で決めた作り方（`make_ccx.py`）を使う。
- 受け取る人は、`.ccx` のダブルクリック（Creative Cloud デスクトップ経由）か、UPIA（導入の道具）で入れる。`External` フォルダへのコピーを案内しない。

## 詳しく

### 版数

- `build_info.json` は `{ "version": "1.2.3", ... }` を持ち、画面の版表示とサーバー（あれば）が同じファイルを読む。`manifest.json` の `version` と一致しないと配布物を作らない。
- 版の形は数字 3 つ（`1.2.3`）。UDT の Package もこの形を要求する。
- 手元のサーバーを持つなら、パネルとサーバーが同じ版の通信の約束を持っているかを、接続時に照合する。合わなければ接続せず「同じ版へ更新してください」と案内する。
- 画面の版表示は、起動の JavaScript が動かないときにだけ出る古い値が嘘の版数になる事故があった。HTML に版数を直書きしない。

### 同じ版で入れ直しても更新されない

- 手元のサーバーの導入先は、版ごとのフォルダを作り、同じ版が既にあれば上書きしない作りにするのが安全。その場合、同じ版のまま入れ直しても古い物が使われ続ける。サーバーが応答していれば再起動もされない。半日気づかなかった事故がある。
- UPIA で上書きしても、Premiere が古い版を読み続けることがある。入れ直しは**先に外してから入れる**（`install_ccx.py --reinstall`）。外すとき、未導入で失敗しても無視してよい。
- 受け取る人向けの手順にも明記する: 「同じ版数の入れ直しは、先に削除してから」。設定や学習した内容は消えない作りにしておく。
- 開発中の確かめでは、入れた後に導入先の全ファイルを作業中のものと比べる。

### 版を上げる基準

- Mac と Windows の両方に関わる変更だけ上げる。
- 片機種だけの修正は同じ版で作り直し、変更履歴は同じ版の行に追記する。
- 受け手が多い修正は、最後の桁だけ上げる案を改めて検討する。

### .ccx の作り方

- .ccx は中身が ZIP で、署名は要らない。手組みの ZIP でも、Creative Cloud 経由で導入できた実績がある（Mac）。
- 作るときの決まり: 先頭のエントリが `manifest.json`、ディレクトリのエントリを入れない、決まった日時と権限（同じ入力から同じバイト列になる）、入れるのはパネルのファイルだけ。
- UDT の Package の注意: `package.json` や `node_modules` は名前では除外されない。同じ `id` の古い登録を掴んで、古い版の .ccx ができることがある（先に古い登録を Remove してから Add）。`manifest.json` は読み直して整形し直されるので、バイト列が変わる。UDT は終了時に登録の一覧を上書きする。
- 配るものの検査: `index.html` が読む全てのファイルが配布物に入っているか（入れ忘れると、テストが全部通ってもタブが空になる）。名前に `secret`・`token`・`credentials` を含むファイルは、配布の組み立てから黙って落ちることがある（鍵の置き場の部品がこの名前で落ち、配った先のサーバーが起動時に止まる直前だった）。部品名にこれらの語を入れない。作った配布物を展開し、何もない環境で全部読み込めるかを確かめてから配る。
- 個人のパス（`/Users/<名前>/` など）が書き込まれていないか検査する（`check.py` の P003）。

### 受け取る人の入れ方

| 方法 | 手順 |
|---|---|
| ダブルクリック（第一の方法） | `.ccx` をダブルクリック → Creative Cloud デスクトップの案内に従う → Premiere を（起動済みなら一度終了して）起動 → ウィンドウ → UXP プラグイン |
| UPIA（代わり） | Mac: `.../UnifiedPluginInstallerAgent --install <絶対パス>.ccx`、Windows: `UnifiedPluginInstallerAgent.exe /install "<絶対パス>.ccx"`。外すときは `--remove "<プラグイン名>"`（Windows は `/remove`）、一覧は `--list all`（`/list all`） |

UPIA の場所は Creative Cloud デスクトップに同梱されている（Mac は `/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/` の下、Windows は `C:\Program Files\Common Files\Adobe\Adobe Desktop Common\RemoteComponents\UPI\UnifiedPluginInstallerAgent\` の下）。`install_ccx.py` が試し実行（コマンドを見せるだけ）から始める。

- Windows の UPIA は、公式の書式は確認できたが、実際に動かした記録は無い。Windows での実機の確認は、`.ccx` のダブルクリック → Creative Cloud 経由の導入までにとどまる。
- 先に Premiere を 1 回起動してある必要がある。ダブルクリックで反応しないときは UPIA を手で実行する。
- 導入後に Premiere の再起動が要るかは、記録が割れている。画面のない補助プラグインは再起動なしで読まれた記録があり、パネルは再起動を案内している例がある。案内は「Premiere を一度終了して起動」にしておくのが安全。

### Creative Cloud のサインインで登録が消える

UPIA や Creative Cloud 経由で入れたプラグインの登録簿（Mac は `~/Library/Application Support/Adobe/UXP/PluginsInfo/v1/premierepro.json`）が、Creative Cloud のサインアウト・サインインで空に書き換わり、Premiere がプラグインを読まなくなることがある（Mac の実測）。UPIA の一覧には残るので気づきにくい。直し方は、もう一度 `--install`。UDT で読み込んだものは、この登録簿を使わないので影響を受けない。製品側の対処として、.ccx をパッケージの中に同梱し、読み込まれていなければ「入れ直す」ボタンで UPIA を呼ぶ作りがある。Windows の登録簿の場所は見つからなかったので、固定のパスで書かず、Premiere の起動ログの冒頭の行から読み取る。

### Marketplace（Adobe の配布の場）

- Adobe Developer Distribution のポータルから申請する。審査の目標は 10 営業日。無料・買い切り・サブスクがある。
- 主な条件: 名前は ASCII で一意、Adobe の商標を含まない、各パネルに固有のアイコン、空の画面・無反応のボタン・進捗の無い長い処理は却下の理由、外部アプリの起動は不可（ブラウザのリンクだけ可）、本番に開発者ツールを残さない、プライバシーポリシーと利用規約の URL とサポート連絡先が要る、破壊的な操作は明示の同意なしに行わない、生成 AI の機能には内容フィルタが要る。有料の機能は審査用のテスト情報を添える。
- `manifest` の `host` は単一のオブジェクト。Marketplace が払い出す `id` に合わせる。
- 独自配布（`.ccx` を自分のサイトなどで配る）は審査なし。受け手に「信頼できる提供元か」の警告が出る。

## やってはいけないこと

- 同じ版数のまま配り直して、「更新しました」と言う。
- UDT の Package の出力を、中身を確かめずにそのまま配る。
- 配布物の中に、個人のパス・鍵・設定ファイルを入れる。
- `External` フォルダなど、Premiere の管理する場所に直接コピーさせる。
- 実機で確かめていない Windows の導入手順を、確認済みのように案内する。

## 出どころ

- Cut & SRT の配布の記録（v0.10〜v0.14。.ccx と手元のサーバーの 2 点セット、版数の扱い、同版入れ直しの事故、名前による除外の事故、個人パスの検査）
- Effect & Design の導入の記録（UPIA での入れ直し、登録簿が空になる実測、2026-09）
- Adobe 公式の配布・パッケージ・導入のページ、Marketplace の審査の指針（取得 2026-10-13）
- Windows の UPIA は公式の書式のみ（案件の実機は未実行）
