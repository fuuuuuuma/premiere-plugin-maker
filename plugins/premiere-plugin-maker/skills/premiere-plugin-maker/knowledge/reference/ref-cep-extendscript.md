---
id: ref-cep-extendscript
title: CEP と ExtendScript と QE DOM
kind: reference
tags: [CEP, ExtendScript, QE DOM, manifest.xml, .debug, PlayerDebugMode, CSInterface, Node, ES3, matchName, 期限]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: UXP に無い操作（分割・再生・テキストの周辺）のための古い方式。manifest.xml・デバッグの口・未署名の許可・Node の罠・ES3 の制約・QE DOM の使い方と、2028-12 に既定で無効になる予定
parts: [cep-helper]
related: [ref-ticktime, ref-mogrt]
---
## 仕様

**CEP と ExtendScript とは**

- CEP は、Premiere の中に Web ページ（Chromium）のパネルを出す古い拡張の方式です。
- ExtendScript は、Premiere を操作する古い言語（JavaScript の古い版、ES3）です。CEP のパネルからだけ呼べます。
- QE DOM は、ExtendScript から使える**非公式**の操作の入口です。UXP に無い「クリップの分割」「再生・停止」「効果の追加」などがここにだけ残っています。非公式なので、Premiere の更新で変わったり、消えたりします。
- 新規の開発は UXP が基本です。CEP は、**UXP でできないことを補う小さな部品に限って**使います（部品 cep-helper）。

**期限（Adobe 公式ブログ、2026-09。確認日 2026-10-13）**

| 区切り | Premiere の場合 |
|---|---|
| 新しい CEP プラグインの Marketplace への受付停止 | 2027-12 |
| CEP が既定で無効になる | 2028-12（利用者は設定でオンに戻せる） |
| Premiere に CEP が同梱されなくなる | 2029-12 |

既存の Marketplace の CEP プラグインは、CEP が外れるまで動作し、更新もできます。Marketplace の外で配る CEP は、2027-12 の区切りの影響を受けません。**ExtendScript はこの移行の対象外**で、削除の予定はないとされています（ExtendScript の資料は Adobe の著作権表記つきですが、コミュニティが運営するページです）。新機能は UXP にだけ追加されます。

昔の資料には「CEP は 2026-09 に終了」「UXP の正式版から 1 年並行」という記述があります。どちらも確定した日付ではなく、公式ブログの新しいスケジュール（上の表）で置き換わっています。

**CEP 拡張の最小構成**

```
<拡張フォルダ>/
  CSXS/manifest.xml     ← 拡張の宣言
  client/index.html     ← パネルの画面
  host/xxx.jsx          ← ExtendScript
  .debug                ← 開発中だけの観測用の口（配らない）
```

`manifest.xml` の要点：

- `Host Name="PPRO" Version="[24.0,99.9]"`：対象は Premiere。右端を広く取ると新しい版でも読み込まれる。
- `RequiredRuntime Name="CSXS" Version="11.0"`：CEP のランタイムの版。実機の Premiere 26.x は CEP エンジン 12 で動いていて、11 を要求しても読み込まれた。
- `MainPath`（画面）・`ScriptPath`（ExtendScript）。ただし `ScriptPath` だけだと、jsx を直してもパネルを開き直すまで反映されません。毎回 jsx の本文を呼び出しに付けて `evalScript` に渡す作りにすると、直しがすぐ反映されます（60KB ほどの本文を毎回送るので重い。印を付けて合っていれば省く工夫もある）。
- `CEFCommandLine`：`--enable-nodejs`（パネル内で Node が使える）、`--allow-file-access-from-files`（`file://` の画像などを読める）。
- `UI`：`Type` は `Panel`（ドックできる）／`Custom`（画面なし）。メニューの名前は「ウィンドウ → エクステンション」に出る。

**デバッグの口と観察**

- 拡張フォルダの直下に隠しファイル `.debug` を置くと（`<Extension Id="..."><HostList><Host Name="PPRO" Port="8951"/>`）、パネルを開いている間 `http://localhost:8951/json` にページの一覧が出て、そこから Chrome DevTools Protocol（CDP）で繋がります。ポートは 1024 以上 65535 未満で、他の拡張とぶつからない値にします。
- CDP でパネルを観察すれば、画面を触らずに、パネルの中のログや画面の様子を読めます。Premiere に送る ExtendScript も、パネル経由の `evalScript` で外から流せます。
- `.debug` は**配布物に入れません**（観測の口を配らないため）。
- CEP のエンジンのログは、Mac の `~/Library/Logs/CSXS/`、Windows の `%TEMP%`（`CEP<版>-<ホストID>.log`）にあります。

**未署名の拡張を読み込ませる（PlayerDebugMode）**

- Mac：`defaults write com.adobe.CSXS.<番号> PlayerDebugMode 1`。型は文字列の "1"。
- Windows：レジストリ `HKEY_CURRENT_USER\Software\Adobe\CSXS.<番号>` に、文字列値 `PlayerDebugMode` ＝ `"1"`。HKCU なので管理者権限は通常不要です。
- どちらも、設定後に Premiere を再起動します。
- 番号は、Premiere のどの版がどの番号を見るかの公式の対応表が、25.0（CEP 12）までしかありません。**10〜13 をまとめて立てる**のが安全です。更新後に動かなくなったら、Mac は `~/Library/Logs/CSXS/` のログ名にあるエンジン番号を見て、その番号の設定を足します。
- 取り外すときも設定は戻しません（ほかの拡張が使うため）。署名つき（ZXP）で配る経路は、使っていません。

**拡張フォルダ**

- Mac：ユーザー `~/Library/Application Support/Adobe/CEP/extensions/`、全体 `/Library/Application Support/Adobe/CEP/extensions/`
- Windows：ユーザー `%APPDATA%\Adobe\CEP\extensions`、全体 `C:\Program Files\Common Files\Adobe\CEP\extensions`

**CSInterface.js**：パネルから ExtendScript を呼ぶ `evalScript` などの小さな橋です。**Adobe が配っている物で、キットには同梱しません。** 使うときは Adobe の配布元から取り、ライセンスの条件に従います。

## 例

パネルから ExtendScript を呼ぶ約束事：

- 関数の引数は JSON、戻りは JSON の文字列にする。ExtendScript に `JSON` オブジェクトは無いので、自前で直列化する。
- 例外は握って、`{ok:false, error:"利用者向けの一文", detail:"..."}` の形で返す。
- 往復には**タイムアウト**を付ける（45 秒程度）。Premiere がダイアログで止まると、`evalScript` の返事は永遠に来ない。時間切れの後に届いた返事は捨てる。
- 失敗は `"EvalScript error."` で始まる文字列で返る。

QE DOM で効果を足すときは、**付いたかを戻り値と部品数の増加で確かめ**、付かなければ次の名前を試します。

```js
// 日本語 UI では日本語の表示名でしか付かないことがあるので、両方を順に試す
function addEffect(qclip, names) {
  var order = [names.ja, names.en];
  for (var i = 0; i < order.length; i++) {
    var fx = qe.project.getVideoEffectByName(order[i]);   // 取れなければ次へ
    if (!fx) continue;
    var before = qclip.numComponents;
    var rc = qclip.addVideoEffect(fx);
    if (rc === true || qclip.numComponents > before) return order[i];
  }
  return "";
}
```

## 注意

- **Node の罠（実機でだけ止まる）**：
  1. UMD の `if (typeof module === "object") module.exports = ...; else window.X = ...;` は、CEP がページに `module`・`require` を生やすため `window` に載りません。画面が「読み込み中」のまま固まります。**両方に載せます**：`module.exports = api; if (root) root.X = api;`
  2. `child_process` の `exec`・`execFile` の**非同期のコールバックが永遠に来ません**（`fs.readFile` の非同期は来る）。外部のコマンドは `execFileSync` で呼び、直前の描画を済ませるため `setTimeout(..., 0)` で一拍置きます。同期なので、`timeout` と `killSignal` を必ず付けます（付けないと、固まったときに画面ごと止まる）。
  どちらも、Node で動かすユニットテストは全部通ったまま、実機でだけ止まります。
- **PATH は最小**（Mac は `/usr/bin:/bin:/usr/sbin:/sbin`）。`python3` は `/usr/bin/python3`（Xcode のコマンドライン・デベロッパ・ツールに入っている 3.9 系）で、ツールが無いと抜け殻です。
- **ES3 の制約**：`JSON`・`let`・`const`・アロー関数・テンプレート文字列・`Array.isArray`・末尾のカンマは使えません。配列の判定は `Object.prototype.toString.call(v) === "[object Array]"`。ファイルは `File`／`Folder` で読み書きし、ログの失敗で本処理を止めません。
- **Chromium は 99 相当**：`:has()`・コンテナクエリ・CSS のネストは使えません。外部 CSS は読み込めません。`vw`・`vh` は当てになりません。
- **`location.reload()` では新しい JS が載りません**（強くキャッシュされる）。CDP の `Network.setCacheDisabled` と `Page.reload({ignoreCache:true})` で入れ替えます（作者のメモ）。
- **QE DOM**：使う前に `app.enableQE()`。クリップは開始 ticks で探す。コンポーネントは **matchName**（言語に依存しない。例 `AE.ADBE Geometry`）で探し、パラメータは表示名で探す（日本語名と英語名を並べる。UI の言語に縛られるので、他言語の Premiere では未検証）。追加した直後は同じハンドルに現れないことがあるので、取り直す。足した効果はテキスト部品の**手前**に入る。トランジションは `components` が読めず、設定項目は変えられない（長さと位置だけ）。`qe.project.undo()` は 26.5 で動いた（開発の自動検証用）。
- **ソーステキストの `getValue()` は本文でなく内部の生の列**です。本文は FCP XML から読みます（ref-fcp7-xml）。
- 「CEP が今の Premiere で動くか」は、版ごとに確かめます。26.x では読み込まれ、ログも更新されていますが、「Premiere 2026 で CEP が出ない」という報告（原因は公式に確認されていない）もあります。Windows の CEP は、サイドロードを含めて**実機で確かめていません**。
- キットの cep-helper の razor（切る）操作は、Cut & SRT 側で実機の確認が済んでいません。

## 出どころ

- Effect & Design の実機の記録（2026-09：CEP の Node の罠、ExtendScript と QE の操作、`.debug` と CDP での観察）
- Cut & SRT の CEP ヘルパー（再生・停止の実機確認 2026-08-16、razor は未確認）
- Adobe 公式ブログ「Creative Cloud 拡張性の将来：UXP」（2026-09、CEP のスケジュール）と Adobe-CEP の CEP 12 Cookbook（PlayerDebugMode、拡張フォルダ、`.debug`）
- Mac の `~/Library/Logs/CSXS/` と `defaults read-type` の観測（2026-10-13）
