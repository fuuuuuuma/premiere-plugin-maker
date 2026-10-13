---
id: platform-mac
title: Mac での場所と注意
kind: platform
tags: [Mac, macOS, パス, ログ, UPIA, CEP, launchd, ffmpeg, Python, Gatekeeper, Apple シリコン, Intel]
os: [mac]
premiere: ">=25.6"
status: verified
summary: Mac の Premiere・ログ・UDT・UPIA・登録簿・CEP・フォント・Python・ffmpeg・launchd の置き場所と、保護フォルダや Gatekeeper で止まる所
related: [platform-windows, platform-cross]
---
## 違いの表

この表は Mac の値です（Windows との並べ方は platform-windows を見てください）。「実測」は、作者の Mac（Premiere 26.5.2、Beta 27.1.0）で読み取って確かめた、という意味です。

| 項目 | Mac の場所・値 | 確度 |
|---|---|---|
| Premiere 本体 | `/Applications/Adobe Premiere Pro 2026/Adobe Premiere Pro 2026.app`。Beta は `/Applications/Adobe Premiere Pro (Beta)/Adobe Premiere Pro (Beta).app` | 実測 |
| 名前の変更 | 26.0 から表示名は「Adobe Premiere」になったが、フォルダ名・実行ファイル名・ログのフォルダ名は「Premiere Pro」のまま。探すときは `Adobe Premiere*` で探し、名前から版を決め打ちしない | 実測 |
| UXP のログ | `~/Library/Logs/Adobe/Adobe Premiere Pro 2026/UXPLogs_<日時>_<連番>.log`。Beta は `.../Adobe Premiere Pro (Beta)/`。`console.log` の出力もここに入る | 実測 |
| UDT（開発ツール）の入手先 | `/Applications/Adobe UXP Developer Tools/`（2.3.0 で確認）。UDT 自身のログは `~/Library/Application Support/Adobe/Adobe UXP Developer Tool/Logs/appLogs-<日付>.log` | 実測 |
| UDT の開発者モード | `/Library/Application Support/Adobe/UXP/Developer/settings.json` に `{"developer": true}`。これは UDT 側。Premiere 側の設定（設定 → プラグイン → 開発者モード）も別に要る | 実測（中身が公式の説明と一致） |
| UDT が覚えている読み込み元 | `~/Library/Application Support/Adobe/Adobe UXP Developer Tool/plugins_workspace.json` の `manifestPath` | 実測 |
| UPIA（導入係） | `/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent`。`--install <.ccx>`・`--remove "<名前>"`・`--list all` | 実測 |
| UXP プラグインの登録簿 | `~/Library/Application Support/Adobe/UXP/PluginsInfo/v1/premierepro.json`（最上位は `plugins` の配列） | 実測 |
| 導入済みプラグインの実体 | `~/Library/Application Support/Adobe/UXP/Plugins/External/<pluginId>_<版>/`。保存領域は `.../UXP/PluginsStorage/PPRO/26/` | 実測 |
| CEP の拡張フォルダ | ユーザー `~/Library/Application Support/Adobe/CEP/extensions/`、全体 `/Library/Application Support/Adobe/CEP/extensions/` | 実測 |
| CEP の未署名許可 | `defaults write com.adobe.CSXS.<番号> PlayerDebugMode 1`。保存された型は文字列の "1"。番号は 10〜13 をまとめて立てるのが安全。確認は `defaults read-type com.adobe.CSXS.12 PlayerDebugMode` | 実測 |
| CEP のログ | `~/Library/Logs/CSXS/CEPHtmlEngine12-PPRO-<Premiere の版>-<拡張ID>.log`。拡張が読み込まれたかは、このファイルの有無と更新時刻で分かる | 実測 |
| 同梱の Basic Title.mogrt | `<アプリ>/Contents/Essential Graphics/Basic Title.mogrt`（製品版も Beta も同じ構成） | 実測 |
| Adobe Fonts の実体 | `~/Library/Application Support/Adobe/CoreSync/plugins/livetype/` の下の隠しフォルダ。`fc-list` には出ない | 実測 |
| 標準の Python | `/usr/bin/python3`（3.9 系）。コマンドライン・デベロッパ・ツール（CLT）が入っていないと「抜け殻」で、起動はできても中身が無い | 実測 |
| ffmpeg | Homebrew なら `/opt/homebrew/bin/ffmpeg`（Intel の Homebrew は `/usr/local/bin`） | 実測 |
| 常駐 | launchd。設定ファイルは `~/Library/LaunchAgents/<ラベル>.plist` | 実測 |

## 気を付けること

- 実行ファイルを探すときは、Premiere・CEP・launchd から起動された処理は PATH が最小（`/usr/bin:/bin:/usr/sbin:/sbin`）だと思ってください。ターミナルでは動くのに、パネルからは `ffmpeg` や Homebrew の `python3` が見つからない、という症状の原因はほぼこれです。既知の場所（`/opt/homebrew/bin`・`/usr/local/bin`・`~/.local/bin`）を順に試し、実際に起動して確かめてから使います。
- 抜け殻の `python3`：CLT が無い Mac では `/usr/bin/python3` を呼ぶと「xcode-select」に関する文が出て終わります。出力にそれが含まれていたら次の候補に進み、全部だめなら「`xcode-select --install` を実行してください」と案内します（その案内の画面を開く経路は未確認）。
- Apple シリコンと Intel：文字起こしの `mlx-whisper` などは Apple シリコン専用です。Intel の Mac では別の部品（`faster-whisper` のみ）に縮めるので、機能が減ることを先に伝えます。また、Intel 用にビルドされた ffmpeg が先に見つかると、Apple シリコンでは動きません。
- launchd のログは、動いている間に `truncate` してはいけません（launchd が開いたままの出力先に空洞ができます）。ファイルを別名に `mv` してからジョブを再起動します（`launchctl kickstart -k gui/$(id -u)/<ラベル>`）。
- launchd はシェルの環境変数を引き継ぎません。PATH と HOME は plist に明示します。
- 保護フォルダ：書類・デスクトップ・ダウンロードなど macOS が守る場所にAIの道具がファイルを書くと、`com.apple.macl` という属性が付き、`xattr -c` でも消えないことがあります。配布物の出力先や作業用の置き場所は、保護されていないフォルダにします。
- Gatekeeper：ダウンロードした `.command` はダブルクリックすると「開発元を確認できない」と止まることがあります。受け取る人には `bash` を打ってファイルをターミナルにドラッグしてもらう案内にします。自分の道具が展開したファイルの隔離属性は `xattr -dr com.apple.quarantine <フォルダ>` で外せます。
- UPIA と `defaults write` は、環境変数 HOME を仮のホームに変えても本物のホームに書き込む、という記録があります（作者のメモ。再確認はしていません）。仮のホームで配布版を試すと、パネル本体は仮の側、補助プラグインは本物の側に入ることがあります。
- Creative Cloud をサインアウトすると、Adobe Fonts の実体が空になった記録があります（1 回の実測）。フォントが全部「無い」と出たら、まずサインイン状態を見ます。UPIA で入れたプラグインの登録簿も、サインインの変更で空に書き直されることがあります（core-versioning-release を見てください）。
- 日本語を含むパスでは、Finder や一部の道具が NFD、別の経路が NFC で返します。見た目が同じでも別の文字列として比べられるので、鍵にする前に正規化します（platform-cross）。

## 出どころ

- Windows 側の調査資料に付けた Mac の実測（2026-10-13、作者の Mac で読み取りだけを行った）
- Effect & Design の導入・実機受け入れの記録（2026-09）、Cut & SRT の導入と常駐の記録（2026-07〜10）
- Adobe 公式：UXP Developer Tool と Unified Plugin Installer Agent のドキュメント、CEP の Cookbook
