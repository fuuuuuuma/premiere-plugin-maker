---
id: core-manifest-permissions
title: manifest（plugin の設計書）と権限の決め方
kind: core
tags: [manifest, 権限, requiredPermissions, host, minVersion, localFileSystem, network, webview, clipboard, launchProcess, icons, id]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: manifest は host を配列にせず、権限は「何をするとき足すか」で最小にする。手元のサーバーへ繋ぐなら network は all、id を変えるとショートカットの割り当てが消える
related: [core-versions, core-safety, core-ui-rules]
---
## 要点

- manifest は plugin の設計書にあたるファイル（`manifest.json`）。Premiere は `manifestVersion: 5`、`host.app` は小文字の `premierepro`。
- `host` は 1 つのオブジェクトにする。配列は開発中の確かめ専用で、配布や Marketplace の検証で落ちる。
- 権限は最小にする。使わない権限（`fullAccess` など）を付けておかない。何をするとき足すかは下の表。
- 手元のサーバー（127.0.0.1）へ `fetch` するなら `network.domains` は `"all"`。個別のアドレスを書くと通信自体が起きなかった記録がある。
- プラグインの `id` を変えると、Premiere 側のメニュー・ショートカットの割り当てが失効する。決めたら変えない。

## 詳しく

### 必須の項目と形

| 項目 | 決まり |
|---|---|
| `manifestVersion` | 5（6 は C++ を使う Hybrid プラグイン用） |
| `id` | プラグインの識別子。逆さドメインの形（例: `com.example.myplugin`）。Marketplace に出すときはポータルが払い出す ID に合わせる |
| `name` | 英数字だけ・3〜45 文字・Adobe の商標を含まない（Marketplace の条件。`check.py` の M009） |
| `version` | `1.2.3` のように数字 3 つ |
| `host` | `{ "app": "premierepro", "minVersion": "25.6.0" }`。`"PPRO"` は誤り。`minVersion` の決め方は `core-versions` |
| `entrypoints` | `type` は `panel` か `command`。`id` はプラグイン内で一意。`label` が要る。パネルは最小・最大・推奨のサイズを持てる（最小＝最大にすると固定） |
| `main` | 入口の HTML（省略時は `main.js`）。実在すること（`check.py` の M013） |
| `icons` | PNG・JPG・SVG。`theme`・`scale`・`species`（動いた記録は文字列の `"generic"`） |

### host.data（公式の文書に無いが実機で動いた形）

```json
"host": { "app": "premierepro", "minVersion": "25.6.0",
          "data": { "apiVersion": 2, "loadEvent": "startup" } }
```

`apiVersion: 2` と `loadEvent: "startup"` は、Premiere の公式 manifest の文書には載っていない。ただし実機（26.3〜26.5）で動いており、パネルを開かなくても command を動かしたいとき（起動時に読み込む）に使う。効き方の根拠は「作者の実測」で、公式には確認できていない。`enableMenuRecording` については、記録が割れている（「ショートカットを割り当てられる」という説明と、「UXP のコマンドは割り当てられず、効いているのは macOS のアプリのショートカットだ」という説明）。何を可能にしているかは確認できていない。

### 権限ごとの「何をするとき足すか」

| 権限 | 足すとき | 注意 |
|---|---|---|
| `localFileSystem: "plugin"`（既定） | 同梱ファイルとデータ置き場だけを読み書きする | まずこれ |
| `localFileSystem: "request"` | ファイル選択のダイアログ経由で読み書きする | 利用者が選んだ物だけ |
| `localFileSystem: "fullAccess"` | `require("fs")` で任意の絶対パスを読み書きする（手元のサーバーの接続情報を読む等） | 使うコードが無いなら付けない（`check.py` の M010） |
| `network.domains` | `fetch`・`WebSocket` を使う | 外部は許可するドメインを書く。ワイルドカードは UXP 7.4 以降トップレベルでは不可。**127.0.0.1 の手元のサーバーには `"all"` が要った**（Mac・26.3 で実機確認。公式の文書には localhost の記述が無い）。通信するのに無いと `check.py` の M011 が止める |
| `clipboard` | クリップボードを使う | `"read"` か `"readAndWrite"`。書き込みしか使わないなら最小に |
| `launchProcess` | 既定のアプリやブラウザを開く | `schemes`（例 `https`）と `extensions` を書く。毎回システムの同意が出る。任意の実行ファイルを引数つきで起動する公式の方法は無い。Marketplace は外部アプリの起動を禁止（ブラウザのリンクだけ可） |
| `webview` | `<webview>` で外部のページを出す | `allow: "yes"` と `domains` が要る。実機では **`"all"` は検証を通るが全遷移を黙って拒否し、トップレベルドメインのワイルドカードの配列（`https://*.com` など）だけが効いた**。`https://*.example.com` は裸のドメインに一致しない |
| `allowCodeGenerationFromStrings` | `eval`・`new Function` を使う | 使わないなら付けない（`check.py` の J011・M012） |
| `featureFlags.enableAlerts` | `alert`・`prompt`・`confirm` を使う | `check.py` の J008 |
| `featureFlags.enableSWCSupport` | Spectrum Web Components を使う | 0.37.0 固定 |
| `enableAddon` / `addon` | C++ の Hybrid プラグイン | manifest 6 以上・26.2 以上。別の扱い |

### 最小の形

画面だけで完結するプラグインは、`localFileSystem: "plugin"` だけで足りる。重い処理を手元のサーバーに任せるなら `network` と、サーバーの接続情報を読むための `fullAccess` を足す。

### id とショートカット

Premiere のメニュー・ショートカットの割り当ては、プラグインの `id` とコマンドの `id` に紐づく。`id` を変えると割り当てが消える。コマンドのメニュー名は 1 文字違うと黙って効かない（macOS のアプリのショートカットはメニュー名の完全一致で照合される）。

## やってはいけないこと

- `host` を配列にしたまま配る。
- 「念のため」で `fullAccess`・`allowCodeGenerationFromStrings` を付ける。
- 手元のサーバーへのアクセスを、個別のアドレスだけで済ませようとする。
- `webview.domains` に `"all"` を書いて「全部許可した」と思い込む。
- 公開後に `id` を変える。
- manifest のコメントや公式の文書に無い項目の効果を、動くと言い切る。

## 出どころ

- Adobe 公式の manifest・権限・ファイル・ネットワーク・外部プロセスのページ（取得 2026-10-13）
- Cut & SRT の manifest と失敗記録（network が all になった経緯、webview の実測、id とショートカット。Premiere 26.3 / Mac）
- 小型 UXP プラグイン 4 本の manifest 比較（権限が実際には使われていなかった例を含む）
- 公式の文書に無い項目（host.data）と、記録が割れている項目（enableMenuRecording）は、本文にそのまま書いた
- Windows の実機で確認した記録は、手元のサーバーへの接続（127.0.0.1）のみ
