---
id: platform-windows
title: Windows での場所と注意
kind: platform
tags: [Windows, パス, ログ, UPIA, CEP, レジストリ, PowerShell, Python, winget, ffmpeg, cp932, タスク スケジューラ, 確度]
os: [windows]
premiere: ">=25.6"
status: partial
summary: Windows の Premiere・ログ・UDT・UPIA・CEP・Python・ffmpeg・常駐の場所と注意。実機で確かめたものは少なく、各行に確度を付けた
related: [platform-mac, platform-cross]
---
## 違いの表

先に大事なことを書きます。**この表の Windows の値のほとんどは、Windows の実機で確かめていません。** 公式の文書・フォーラム・Windows の利用者から届いた報告から集めたものです。確度の言葉は次の意味です。

- 公式：Adobe・Microsoft・Python の公式ページで確認した
- 案件実機：Cut & SRT を Windows の利用者の PC で動かして確認した
- コミュニティ：フォーラムや第三者の記事、利用者の報告（1 件だけのものを含む）
- 見つからなかった：公式の資料と検索で書いたものが見つからなかった。無いという意味ではない
- 推測：Mac からの類推。表では「推測:」を付けた

| 項目 | Windows | 確度 |
|---|---|---|
| UXP のログ（製品版） | 見つからなかった。Beta 向けの 1 件だけ `C:\Users\<名前>\AppData\Roaming\Adobe\Premiere Pro (Beta)\Logs`。推測: 製品版も `%APPDATA%\Adobe\Premiere Pro` の下の Logs の近く。Mac のフォルダ名から機械的にパスを作らない | 見つからなかった／コミュニティ（Beta） |
| UDT の Logs | UDT の画面の Logs パネルで見る（UDT Logs は接続とロード、App Logs はホストの報告）。ファイルの場所は見つからなかった | 公式（パネル）／見つからなかった（ファイル） |
| UDT の入手 | Creative Cloud デスクトップ → All apps →「UXP Developer Tools」→ Install。管理者権限が要る | 公式 |
| UDT の開発者モード | `%CommonProgramFiles%\Adobe\UXP\Developer\settings.json` に `{ "developer" : true }`（UDT を終了して作り、再起動。管理者権限）。Premiere 側の「開発者モード」（設定 → プラグイン）も別に要り、Premiere の再起動が要る。設定メニューの位置は画面で確かめる | 公式（メニューの位置は見つからなかった） |
| UPIA | `C:\Program Files\Common Files\Adobe\Adobe Desktop Common\RemoteComponents\UPI\UnifiedPluginInstallerAgent\UnifiedPluginInstallerAgent.exe`。`/install <.ccx>`・`/remove <名前>`・`/list all`。先に Premiere を 1 回起動しておく。管理者権限が要る場合がある。**この案件では Windows で UPIA を実行していない** | 公式（実機は未確認） |
| .ccx の導入 | .ccx のダブルクリック → Creative Cloud の案内、という経路は利用者の PC で動いた。ダブルクリックで何も起きない報告もある（.ccx の関連付けが壊れていた例）。そのときは UPIA の `/install`（パスに空白があるので引用符で囲む） | 案件実機／コミュニティ |
| UXP の登録簿 | 見つからなかった。推測: `%APPDATA%\Adobe\UXP\PluginsInfo\v1\premierepro.json`。パスは固定で書かず、Premiere の UXP ログの冒頭にある `PluginsInfo` と `fallback` の行から読む | 見つからなかった |
| 導入済みプラグインの実体 | ユーザー単位 `C:\Users\<名前>\AppData\Roaming\Adobe\UXP\Plugins\External`、全ユーザー `C:\Program Files\Common Files\Adobe\UXP\Plugins\External`。**手でコピーしても読み込まれない**。ダブルクリックか UPIA で入れる | コミュニティ＋公式ブログ |
| CEP の未署名許可 | レジストリ `HKEY_CURRENT_USER\Software\Adobe\CSXS.12`（10〜13 をまとめて）に、文字列値 `PlayerDebugMode` ＝ `"1"`。HKCU なので通常は管理者権限は不要。変更後に Premiere を再起動。コマンドなら `reg add HKCU\Software\Adobe\CSXS.12 /v PlayerDebugMode /t REG_SZ /d 1 /f`（公式には無く未検証） | 公式（実機は未検証） |
| CEP の拡張フォルダ | ユーザー `C:\Users\<名前>\AppData\Roaming\Adobe\CEP\extensions`、全体 `C:\Program Files\Common Files\Adobe\CEP\extensions` と `C:\Program Files (x86)\Common Files\Adobe\CEP\extensions` | 公式 |
| CEP の `.debug` | 拡張フォルダの直下の隠しファイル。作るのは `copy con .debug`。ポートは 1024 以上 65535 未満 | 公式 |
| CEP のログ | `C:\Users\<名前>\AppData\Local\Temp` の `CEP<版>-<ホストID>.log` など。ログレベルは同じレジストリキーの `LogLevel` | 公式 |
| Premiere 本体 | `C:\Program Files\Adobe\Adobe Premiere Pro 2026\`（26.x。名前変更後もフォルダ名はこのまま）。27.x の製品版のフォルダ名は見つからなかった。`Adobe Premiere*` で探す | コミュニティ（Adobe 側の返信）／見つからなかった |
| 版数の読み方 | レジストリや exe に頼らず、パネルの中で `host` の版（`premierepro 26.5.2` の形）を読む。Windows のファイルバージョンの読み方は見つからなかった | 見つからなかった |
| Beta の場所 | 見つからなかった。推測: `C:\Program Files\Adobe\Adobe Premiere Pro (Beta)\` | 見つからなかった |
| Basic Title.mogrt | `%ProgramFiles%\Adobe\Adobe Premiere Pro <版>\Essential Graphics\Basic Title.mogrt`。`%ProgramW6432%` と `%ProgramFiles%` の両方を `Adobe Premiere Pro *` で探す | 案件実機（Windows の利用者の報告） |
| Adobe Fonts | `%APPDATA%\Adobe\CoreSync\plugins\livetype\r`（隠しフォルダ、ファイル名は数字で拡張子なし）。ライセンス上、持ち出して他の用途に使えない | コミュニティ |
| 127.0.0.1 への接続 | UXP の `fetch` で `127.0.0.1` の http に接続できた（manifest の network は `all`、サーバーは 127.0.0.1 に bind）。Windows 特有の公式の注意は見つからなかった。ファイアウォールのダイアログは、127.0.0.1 に bind すれば出なかった、という報告が 1 件ある | 案件実機（接続）／コミュニティ（ダイアログ） |

## 気を付けること

**Python**

- Windows には標準の Python がありません。公式の推奨は Python install manager（python.org、または Microsoft Store）。`py install 3.13`・`py list`・`py -V:3.13` で版を選びます。
- `python` と打って Microsoft Store が開くときは、設定の「アプリ実行エイリアスの管理」で「Python (default)」が有効か確かめます（公式の文言）。
- winget での導入例は `winget install --id Python.Python.3.13 --exact --source winget --scope user --silent`（案件で使った形。ID が存在することは公式の一覧で確認）。
- `pythonw.exe` はコンソールを作らないので、`sys.stdout` と `sys.stderr` が `None` になり得ます。自分でログファイルに付け替えます（常駐のサーバーで必要）。

**文字コード（日本語の Windows で最も多い事故）**

- Python 3.14 以前は、`open()` やパイプの既定が cp932（日本語 Windows の旧い文字コード）です。日本語や絵文字で文字化けするか、落ちます。Cut & SRT の Windows 版で 5 回以上繰り返した事故です。
- 直し方は 3 つ。`encoding="utf-8"` を必ず明示する／子プロセスに `PYTHONUTF8=1` を渡す／常駐サーバーを `-X utf8` で起動する。Python 3.15 からは UTF-8 モードが既定になりましたが、3.13 を固定して使う環境では今も明示が必要です。3.15 の挙動は文書だけで、実機では確かめていません。
- PowerShell 5.1：BOM の無い .ps1 は ANSI として読まれ、日本語が壊れます。**日本語を含む .ps1 は UTF-8（BOM 付き）で保存します。** `Out-File` と `>` は UTF-16、`Set-Content` は ANSI で書くので、ファイルに書く文字コードは明示します。
- .bat：cmd は CP932 で読むので、**.bat は英数字だけ**にして、1 行で .ps1 を呼ぶだけにします（公式の明文は見つからず、案件の実機の記録）。呼び方は `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0x.ps1"`。これは実行ポリシーをそのセッションだけ緩める正規の方法ですが、会社の PC のようにグループポリシーで固定された環境では効きません。

**ffmpeg と PATH**

- 導入は `winget install --id Gyan.FFmpeg -e`（公式の manifest で確認）。winget は別名のリンクを `%LOCALAPPDATA%\Microsoft\WinGet\Links` に作ります（コミュニティ）。**開いたままのターミナルには PATH が反映されない**ので、新しくターミナルを開いて `ffmpeg -version` が通ることを完了の条件にします。サーバー側は、PATH に加えて上のリンクの場所も探すようにします。
- Cut & SRT の Windows 用インストーラは ffmpeg を自動では入れません。利用者に先に入れてもらう案内にしています。

**常駐**

- タスク スケジューラに登録します（`Register-ScheduledTask`、トリガーは `-AtLogOn`、実行は `pythonw.exe`）。利用者の PC で「サーバーを起動して接続できる」ところまでは確認しました。**サインイン時の自動起動そのものは未確認**です。管理者権限が要るかどうかも、資料が割れていて断定できません。

**そのほか**

- OneDrive の「フォルダーのバックアップ」の対象（デスクトップ・ドキュメント）に展開した状態で導入すると、同期が割り込みます。対象外のフォルダで展開してもらいます。
- SmartScreen（「Windows によって PC が保護されました」）は実行ポリシーとは別の仕組みです。「詳細情報 → 実行」で進んでもらう案内にします。Windows Defender が難読化した JavaScript を誤検知した報告もあります（Photoshop 側の 1 件）。
- UXP でパスからフォルダやファイルを開くときは、Windows では `file:///C:/...` の形に整えないと失敗します（Cut & SRT の実装の記録。Mac の絶対パスも同じ `file:///` の形で渡す）。
- CUDA が使えない PC では、文字起こしは CPU で動かします。遅いことを先に伝えます（Windows 用の部品は `faster-whisper`）。
- Mac 専用の場所（`/Applications`・`~/Library`）だけを探す部品は Windows では必ず失敗します。Windows 向けに配る前に、そういう書き方と `text=True` だけの `subprocess` を探します（check.py の W 規則が見つけます。platform-cross を見てください）。

## 出どころ

- Windows 側の事実確認の調査資料（2026-10-13。Web で取得した Adobe・Microsoft・Python の公式ページと、Adobe のフォーラム・Community の投稿）
- Cut & SRT の導入ガイドと、Windows の利用者の実機の報告（v0.12.0 以降。.ccx の導入・サーバーの導入と接続・install.bat の経路・cp932 の事故と修正）
- 実機未確認：UPIA の実行、CEP のサイドロード、サインイン時の自動起動、Python 3.15 の UTF-8 既定の挙動
