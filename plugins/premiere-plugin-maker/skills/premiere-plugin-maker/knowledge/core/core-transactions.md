---
id: core-transactions
title: 取引（トランザクション）の作法 ― 取り消し 1 回で戻す
kind: core
tags: [取引, トランザクション, lockedAccess, executeTransaction, Action, 取り消し, キーフレーム, 効果, ESLint]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: タイムラインを変える処理は lockedAccess の中で Action を作り、同期の executeTransaction で足す。非同期の取得は先に済ませ、足した効果の値は別の取引で書く
parts: [ppro-kit]
related: [core-api-patterns, core-versions, core-safety, ref-keyframe-interpolation]
---
## 要点

- タイムラインやクリップを変えるには、Action（変更の指示）を作って、取引（`project.executeTransaction`）に足す。取引 1 回が取り消し（Cmd/Ctrl+Z）1 回になる。
- 取引と lockedAccess のコールバックは完全に同期。中で `await` しない。Action を作るのも取引の中。26.3 からは必須。
- 非同期の取得（部品の生成、クリップの取り直し、matchName の読み取り）は取引の前に全部済ませる。
- 効果を新しく足したときは、その効果の値やキーは別の取引で書く（足す前は設定項目が無いため）。
- `executeTransaction` の戻り値（boolean）を必ず見る。`false` なら確定していない。

## 詳しく

### 3 段階の型

1. **取引の外（非同期でよい）**: クリップのハンドルを取る、`getMatchName()` を読む、`VideoFilterFactory.createComponent` や `TransitionFactory.createVideoTransition` で部品を作る、値やキーを読む。
2. **取引の中（同期だけ）**: `project.lockedAccess(() => project.executeTransaction((ca) => { ... }, "取り消しの名前"))` の中で、`create*Action()` で Action を作り、`ca.addAction()` で足す。
3. **足したものを取り直して設定する処理は別の取引**にする。

```js
project.lockedAccess(() => {
  const ok = project.executeTransaction((ca) => {
    ca.addAction(item.createSetEndAction(newEnd));   // 作るのも足すのも中で、同期で
  }, "終了位置を直す");
  if (ok === false) { /* 確定しなかった。成功と言わない */ }
});
```

外で `await` を挟んで Action を作り、中では足すだけにすると、Action が別の文脈のものになって `The script object is no longer valid` で失敗する。読み取りは外でも通るのに Action だけ落ちるのが目印。

### 規則（T1〜T12）

| # | 規則 | 実機の確認 |
|---|---|---|
| T1 | `executeTransaction` は確定に失敗すると `false` を返す。戻り値を見ないと「何も起きない」になる | 実機（26.5） |
| T2 | 取引 1 回 ＝ 取り消し 1 回（複数クリップでも）。第 2 引数は取り消しの名前。同じ名前を付けても 2 回の取引はまとまらない | 実機（26.5） |
| T3 | Action は 1 つずつ `addAction` し、個別に try/catch する。まとめると 1 つ拒否されただけで全部が `Invalid parameter.` で落ちる | 実機 |
| T4 | 足した効果（`createComponent` の部品）は取引が確定するまで設定項目を持たない。効果を足す取引と、値・キーを書く取引を分ける（取り消しは 2 回になる） | 実機（26.5） |
| T5 | キーを打つには `createSetTimeVaryingAction(true)` が要る。再生ヘッドが 0 のときは時刻 0 に余分なキーが 1 つ増えるので、入点より前を範囲で消す | 実機（26.5） |
| T6 | 単独のキー削除 `createRemoveKeyframeAction` は、作る時点でキーの存在を確かめる。同じ取引で足したキーは消せない。範囲削除 `createRemoveKeyframeRangeAction` は通る | 実機（26.5） |
| T7 | 補間（イーズなど）は同じ取引の中では変えられない（無言で効かない）。別の取引なら効く。1 取引で済ませたいときは 1 コマごとの直線キーに焼き込む（`ref-keyframe-interpolation`） | 実機 |
| T8 | 効果はテキストの部品（`AE.ADBE Text`）の手前に差す（`createInsertComponentAction(filter, 位置)`）。末尾に足すとテキストの下になる | 実機 |
| T9 | トランジションは内部名で作り、長さは ticks で渡す（秒の 0.5 は 14 コマに切り捨てられた）。同じ端に付け直すと置き換わる | 実機（26.5） |
| T10 | `insertMogrtFromPath` は Action を返さず、取引に入れられない。取り消しは取引とは別のエントリになる | 実機 |
| T11 | 取引の外で単独に呼ぶもの: `importFiles`、`openSequence`、`setActiveSequence`、`setSelection`、`insertMogrtFromPath`、`exportSequenceFrame`、`project.save` | 各記録による |
| T12 | 大量の配置は 2 つの取引に束ねる（配置 ／ 尺合わせ）。件数が多くても取り消しは 2 回 | 記録なし（実機での確認の記述が見つからなかった） |

### ほかに覚えておくこと

- 取り消し 1 回で戻したいなら、独立した Action は 1 つの取引にまとめる。依存する連鎖（ビンを作る → 移す → 取り込む）は取引を分けるしかなく、取り消しは複数回になる（Action に戻り値が無いため）。
- 大量のクリップ（500 件以上など）の一括変更で、Premiere が固まる・落ちる既知の問題がある（原因・時期は Adobe から未公表）。件数を分けて実行し、前に保存を勧める（`core-safety`）。
- 公式の ESLint プラグイン `@adobe/eslint-plugin-premierepro` が、取引の外での Action 作成や、コールバック内の `await` を検出する。キットの `check.py` の J001（取引の中の await）、J002（取引の外の Action 作成）、J009（戻り値を見ていない）も同じ趣旨。
- 取引に入れた結果の確認は、書くつもりの件数と書けた件数を比べ、1 つも書けなかったら成功と言わない。
- 取り消しの回数を自動で確かめたいときは、ExtendScript の非公式 `qe.project.undo()` が 26.5 で動いた記録がある（開発用）。

## やってはいけないこと

- 取引のコールバックを `async` にする、中で `await` する。
- Action を取引の外で作って、中で `addAction` だけする（26.3 以降は必須違反）。
- `executeTransaction` の戻り値を無視して「適用しました」と言う。
- 足したばかりの効果の値を、同じ取引の中で書こうとする。
- 1 つの取引に大量の Action を無制限に詰める。

## 出どころ

- Adobe 公式の 26.3 変更履歴（`create*Action` を lockedAccess の内側で作る必須化）と、公式 ESLint プラグインの規則
- Adobe 公式フォーラムの Premiere 統合チームの投稿（26.3 API 更新、2026-07）と、取引の分け方に関する投稿
- Cut & SRT の失敗記録と実機ログ（Premiere 26.3、2026-07〜09）
- Effect & Design の補助プラグインの実機検証（Premiere 26.5、2026-09-19。取り消し回数・キー・補間・トランジションの実測）
- T12 のみ実機の確認記録なし
