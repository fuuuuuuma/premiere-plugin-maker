# ズームボタン

Premiere 用のプラグイン（Zoom Button・id `com.example.zoombutton`）。premiere-plugin-maker で作りました。

## Premiere に読み込む（作っている間）

1. UXP Developer Tools を開き、［Add Plugin］でこのフォルダの `manifest.json` を選ぶ
2. ［Load］を押す。直したら［Reload］。`manifest.json` を変えたら［Unload］してから［Load］
3. Premiere の［ウィンドウ］→［UXP プラグイン］→「ズームボタン」を開く
4. うまく動かないときは「診断」を押し、表示を AI に伝える

UXP Developer Tools に Premiere が出ないときは、Premiere の［設定］→［プラグイン］で開発者モードをオンにして、Premiere を再起動してください。

## ログ

パネルの「診断」に、ログの保存場所が出ます。AI は `logs.py --project <このフォルダ>` で読みます。
