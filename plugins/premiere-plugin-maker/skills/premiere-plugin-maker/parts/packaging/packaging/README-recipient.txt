{{PANEL_LABEL}}（{{PLUGIN_NAME}} v{{VERSION}}）の入れ方

■ Mac / Windows 共通（いちばん簡単）
1. Creative Cloud デスクトップにサインインした状態で、{{PLUGIN_ID}}_{{VERSION}}.ccx をダブルクリックする
2. 確認の画面が出たら［インストール］を押す
3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{{PANEL_LABEL}}」を開く

■ ダブルクリックで入らないとき
- Mac: ターミナルで次を実行（.ccx のところはファイルをドラッグして入れる）
  "/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent" --install <ccx のパス>
- Windows: コマンドプロンプトで次を実行
  "C:\Program Files\Common Files\Adobe\Adobe Desktop Common\RemoteComponents\UPI\UnifiedPluginInstallerAgent\UnifiedPluginInstallerAgent.exe" /install <ccx のパス>

■ 出てこないとき
- Premiere を一度終了して、もう一度開く
- Creative Cloud にサインインし直した後は、入れ直しが要ることがあります
- 同じ版のまま入れ直しても更新されません。Creative Cloud デスクトップの［プラグイン］から一度削除してから入れてください

■ 困ったとき
困っていること・OS・Premiere の版・このプラグインの版・表示されたエラーの全文を、配った人に伝えてください。
