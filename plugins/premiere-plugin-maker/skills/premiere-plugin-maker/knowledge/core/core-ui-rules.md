---
id: core-ui-rules
title: UXP のパネル画面の制約と直し方
kind: core
tags: [UI, CSS, flex, grid, 画面, sp-button, select, textarea, SVG, MutationObserver, require, 下見, 崩れ]
os: [mac, windows]
premiere: ">=25.6"
status: partial
summary: UXP の画面は Chrome と同じではない。grid が使えず、flex の子は潰れ、一部の部品は押せず、MutationObserver や confirm が無い。下見の Chromium では出ない崩れがあるので最後は実機で見る
parts: [ui-kit]
related: [core-verification, core-api-patterns]
---
## 要点

- UXP のパネルは、ふつうの Web ブラウザとは描画も使える機能も違う。「ブラウザで綺麗に出たから大丈夫」は成り立たない。
- 必ず守る 5 つ: grid を使わず flex で組む、一覧の行には `flex: 0 0 auto`、起動の処理はファイルの末尾に 1 回だけ、`require` に相対パスを使わない、`MutationObserver` や `confirm` を無条件に使わない。
- 画面の崩れは、中身を入れた状態（長い一覧・長い文字）で確かめる。空の一覧では出ない。
- ブラウザでの下見（ヘッドレス Chromium）は補助。最終確認は実機で、機械の検査が 0 件でも目で全画面を見る。

## 詳しく

### 症状と直し方の表

| 症状・制約 | 直し方 |
|---|---|
| CSS の `grid` が使えない | すべて flex。並べて折り返すときは `flex-wrap` |
| `display` の初期値が flex に近い振る舞い | 並べ方は毎回 `display` を書く。`hidden` 属性で出し入れするなら `[hidden]{display:none!important}` を先に置く |
| **flex の子が中身より小さくならない保護を持たない**。行数が `max-height` を超えると行が潰れて、文字とボタンが次の行に重なる（3 回以上再発した） | 縮めたくない子（一覧の行など）に `flex: 0 0 auto`。伸び縮みする入力だけ `min-width: 0`。あふれた分は親のスクロールに任せる |
| ドックの下端のボタンに手が届かない | `html, body` とメインの箱を高さ 100% にし、スクロールする領域に `min-height: 0; overflow-y: auto` |
| `sp-button` が押せない（起動時から表示されているページのボタンが不活性） | 初期ページを一度 `hidden` にして、次のフレームで戻す。保険として `pointerdown` から 400ms 以内に `click` が来なければ実行する（二重実行は時刻で防ぐ） |
| `select` の上でマウスのホイールを回すと値が勝手に変わる | ホイールを止める。直近のホイール後の変更を巻き戻す。1 秒ごとに値を突き合わせる。の 3 段で守る |
| `textarea` の初期値が `null` で、文字を足すと `"null"` が混ざる | 先に `if (!el.value) el.value = ""` |
| 空の数値欄が `NaN` になり、JSON で `null` になって設定や引数を壊す | 送る前に有限でない数を落とす。受け取る側（サーバー）でも型と有限性を検査する（二重の防御） |
| `confirm()` が無い | ボタンを 2 回押す方式（1 回目でラベルを変え、5 秒だけ待つ）。`enableAlerts` を有効にすれば `alert`・`confirm` も使えるが、manifest が要る |
| `position: fixed` の重ね表示（ダイアログ風）が、ネイティブの入力欄の上で透ける。`<dialog>` の実績も無い | 設定を開いている間は元の中身を隠す方式にする |
| `MutationObserver` が無い。使うと起動の途中で `ReferenceError` になり、以降の処理が全部止まった | `typeof MutationObserver === "function"` で分け、無ければ 1 秒ごとに状態を見る方式にする（`check.py` の J007） |
| 複雑な SVG（多段のグラデーション・filter・文字単位の計測）が崩れる | 前もって透明な PNG に焼いて `<img>` で出す。単純な図形のインライン SVG は可 |
| `<details>` が不安定 | クラスで開閉する自前のトグル |
| `require("./foo.js")` のような相対パスの読み込みが効かない | 1 つのファイルにまとめるか、`index.html` の `<script src>` を静的に並べて読み込む。全スクリプトが同じグローバルの空間を共有する（`check.py` の J006） |
| 起動処理が宣言より先に走り `ReferenceError`（TDZ）。または 2 回走って API を二重に呼ぶ | 起動のブロックは必ずファイルの末尾に置き、`initialized` の印で 1 回だけにする（`check.py` の J012）。起動の組み立て全体を try/catch で包み、例外 1 つで全部の操作が死なないようにする |
| 書類にある `<title>` が画面に出てしまう | `title { display: none; }`（`check.py` の H005） |
| `<ul>` `<li>` `<ol>` などが、ただの `div` として扱われる | 見た目が崩れたら `div` で組む |
| `input type="file"` / `type="color"` は使えない（汎用の記述） | ファイルは `localFileSystem` のダイアログを使う |
| `<label for>`、`aria-*`、`contenteditable`、`accesskey` などの属性が効かない | 前提にしない。`tabindex` は仕様と違い、負の値はフォーカスされない |
| イベントを HTML の `on*` 属性に書くと不安定 | `addEventListener` を使う（`check.py` の H003） |
| `requestAnimationFrame` が不安定な環境がある | `setTimeout(0)` を代わりにする |
| 画面は幅 280〜480px のドックが基本 | 横に並べず縦に積む。全幅の主ボタンを入力欄と同じ行に置かない。はみ出し・文字の切れ・縦つぶれ・重なりが幅 280・340・480 で 0 件になるように検査する |

CSS の media query は width・height・prefers-color-scheme が公式に載っている。`transition`・`animation`・`text-transform` は古い汎用の資料では非対応とされる（Premiere で当てはまるかは未確認）ので、頼らない。CSS の変数（`var()`）は使えた記録と未確認の記述が混在する。色の値は書き写して使うのが安全。

### Spectrum の部品

- 組み込みの `sp-*`（Spectrum UXP Widgets）は import 不要で手軽だが、数が限られ、既定の見た目が強い。見た目は `!important` で上書きする。将来非推奨になる可能性がある。
- Spectrum Web Components は本番向けに推奨される。Premiere では 0.37.0 に固定され、manifest の `featureFlags.enableSWCSupport: true` と、npm でのバンドルが要る。

### 下見（ブラウザ）で見えない崩れ

- ヘッドレス Chromium の下見は、UXP の描画そのものではない。flex の押しつぶしは Chromium では起きず、UXP でだけ起きる。
- 下見では「UXP と同じ弱い条件」にする工夫が効く: 全要素に `min-width: 0; min-height: 0` を入れる、`MutationObserver` を消す、偽のサーバーの応答で中身の入った状態を描く。
- 機械の検査（はみ出し・縦つぶれ・重なり・色と文字サイズ）が 0 件でも、全画面を目で採点する。ヘッダーの重なりや本文の消失は、機械では見つからなかった。

## やってはいけないこと

- ブラウザで綺麗に出ただけで「画面は大丈夫」と言う。
- 空の一覧だけで崩れを確かめる。
- `MutationObserver`・`confirm`・`prompt` を存在確認なしに使う。
- 入力欄に被さる固定位置の重ね表示を作る。
- 複雑な SVG をそのまま埋め込む。

## 出どころ

- Cut & SRT の失敗記録（行が潰れて重なる 3 回の再発、sp-button の不活性、select のホイール、MutationObserver、起動順序の事故）。多くは Premiere 26.3〜26.5 の Mac の実機ログで確認
- Adobe 公式の UXP の既知の制限（HTML・CSS・JS の対応）と、Spectrum のページ
- 小型 UXP プラグイン 4 本の引き継ぎ記録（相対 require、details、flex）
- 公式の汎用の既知の問題（Photoshop・XD 時代のページ）は Premiere で未確認のため、断定していない
