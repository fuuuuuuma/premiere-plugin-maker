---
id: core-dev-loop
title: 開発中の読み込み（UDT）と、つながらないときの見方
kind: core
tags: [UDT, UXP Developer Tool, 開発者モード, Load, Reload, Watch, Unload, 読み込み, つながらない, plugins_workspace]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: 開発者モードは UDT 側と Premiere 側の 2 か所で入れて Premiere を再起動する。manifest を変えたら Unload してから Load。直したのに変わらないときは、読み込み元を疑う
related: [core-verification, core-versioning-release, core-manifest-permissions, platform-windows, platform-mac]
---
## 要点

- 開発中のプラグインは、UXP Developer Tool（UDT。Adobe の開発用の道具）から読み込む。入手は Creative Cloud デスクトップの「UXP Developer Tools」。
- 開発者モードは **2 か所**。UDT 側（設定ファイル `settings.json`）と、Premiere 側（設定 → Plugins → 開発者モード）。入れたあと Premiere を再起動する。
- 操作は Add Plugin（manifest.json を選ぶ）→ Load（または Load & Watch）→ 編集 → Reload。**manifest.json を変えたら Unload してから Load し直す**。
- 読み込めたら、Premiere のメニュー「ウィンドウ → UXP プラグイン」から開く。パネルを閉じたらここから開き直す。
- 「直したのに変わらない」ときは、まず Premiere が実際に読んでいる場所を確かめる。

## 詳しく

### 準備（1 回だけ）

1. **UDT を入れる**: Creative Cloud デスクトップ → すべてのアプリ → 「UXP Developer Tools」→ インストール。UDT は管理者権限が要る。初回の起動で、開発者モードを有効にするかを聞かれる。
2. **UDT 側の開発者モード**: 画面の案内が出ないときは、UDT を終了して次の場所に `settings.json` を作り、`{ "developer": true }` を書く（管理者権限）。UDT を起動し直す。

| OS | 場所 |
|---|---|
| Mac | `/Library/Application Support/Adobe/UXP/Developer/settings.json` |
| Windows | `%CommonProgramFiles%\Adobe\UXP\Developer\settings.json` |

3. **Premiere 側の開発者モード**: Premiere の設定 → Plugins → 「開発者モードを有効にする」にチェックして、Premiere を再起動する。Windows で設定がどのメニューにあるかは、公式資料で見つからなかった。画面で確かめる。
4. 前提の版は、Premiere 25.6 以降、UDT 2.2 以降。25.6 以降は、製品版（ベータ版でなく）の Premiere にも、開発者モードをオンにすれば接続できる。

### 日々の流れ

1. UDT の Add Plugin で `manifest.json` を選ぶ。
2. Load、または Load & Watch（ファイルを変えると自動で読み込み直す）。
3. コードを編集して Reload（Watch 中は自動）。
4. **`manifest.json` を変えたら、Unload → Load**。Watch は manifest の変更を拾わない。
5. 困ったら UDT の Logs パネル（UDT のログと、Premiere 側のログ）と、Debug（Chrome の開発者ツールに近い画面）を使う。

UDT の行の状態と出る操作（UDT 2.3 のアプリ内の文字列を読んだ範囲。実際に押して確かめた記録は少ない）: 読み込み前は Load / Load & Watch、読み込み後は Debug / Reload / Watch / Unload。

### UDT が Premiere を見つけない・読み込めないとき

| 症状 | まず確かめること |
|---|---|
| UDT に Premiere が出ない・「No applications are connected」 | 開発者モードが **両方**（UDT 側と Premiere 側）で有効か。Premiere を再起動したか。Premiere の版が 25.6 以上か |
| UDT は製品版を認識せず、ベータ版だけを表示する（Windows での報告） | 開発者モードの入れ直しと再起動。解決の記録は無い |
| Load が通らない・メニューに出ない | `host.minVersion` が Premiere の版より新しくないか（版が足りないと「出てこない」だけの症状になる）。`host.app` が `premierepro` か（`PPRO` は誤り） |
| 起動の順序 | UDT は 127.0.0.1 のポートで待ち、開発者モードの Premiere が起動時に接続しに行く。接続のやり直しは無いようなので、**UDT を先に起動してから Premiere を起動する**のが安全（この順序は自作の代替サーバーでの実測から推定したもの） |
| Add が重複のエラーになる。または、同じ `id` の別の場所のものを Add できてしまい、古い登録のほうが動く | 重複の判定が `id` か場所かは未確認。同じ `id` の古い登録を先に Remove してから Add する |

### 設定ファイルに触るとき

UDT は、登録したプラグインの一覧を `plugins_workspace.json`（Mac は `~/Library/Application Support/Adobe/Adobe UXP Developer Tool/` の中）に持つ。**UDT を開いたまま書き換えない**。UDT は終了時にこのファイルを上書きし、編集が消える。直接書き換えるときは、UDT を終了してから行う。Windows の置き場は見つからなかった。

### 直したのに変わらないとき（読み込み元の確認）

1. UDT に登録されている `manifestPath` が、今編集しているフォルダか。別のコピー（配布用に展開したもの、別の作業フォルダ）を読んでいないか。
2. 手元のサーバーを使うなら、動いているサーバーの実体が編集中の場所か（Mac は `ps` で実行パスを見る）。
3. サーバーを再起動すると合言葉（トークン）が作り直されるので、パネルも Reload する。
4. 配布した .ccx を入れたものと、UDT で読み込んだものは別物。両方入っていると、どちらが動いているか分からなくなる。UDT で読み込んだものは、Creative Cloud のサインイン変更で消える登録簿を使わない。
5. 同じ版数で入れ直しても更新されない（`core-versioning-release`）。

### バンドラーを使うとき

TypeScript などでビルドする場合、UDT に読み込ませる manifest は、ソース側か出力（dist）側かが、公式資料で割れている（公式サンプルは dist 側を読み込ませる）。迷ったら、出力側の manifest を読み込ませ、manifest を変えたら出力し直して Unload → Load する。UDT は依存パッケージを自動では入れない。

## やってはいけないこと

- 開発者モードを片側だけ入れて、「つながらない」と結論する。
- manifest を変えたのに Reload だけで済ませる。
- UDT を開いたまま `plugins_workspace.json` を編集する。
- 読み込み元を確かめずに、同じ修正を何度も試す。
- フォルダ（`External`）へ手でコピーして導入しようとする（`core-versioning-release`）。

## 出どころ

- Adobe 公式の UDT のページ・はじめてのプラグイン・FAQ（取得 2026-10-13）
- Adobe 公式フォーラムの「接続できない」の報告と解決例（2026-01、2026-02。Windows の未解決報告を含む）
- Cut & SRT の開発メモ（UDT の登録ファイル、起動順、稼働実体の確認。Mac）
- Windows の実機での UDT の確認記録は無い（手順は公式の記述による）
