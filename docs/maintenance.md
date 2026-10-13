# 保守の手引き（知識と版の表を新しく保つ）

## Premiere の新しい版が出たとき

1. Adobe の変更履歴（https://developer.adobe.com/premiere-pro/uxp/changelog ）と、フォーラムの「Premiere xx.x API Updates」を読む
2. 新しく増えた API・変わった API を `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/knowledge/reference/api-since.json` に足す（ベータだけの物は `"beta": true`）
3. `knowledge/core/core-versions.md` の版の歴史に足し、先頭の確認日を更新する
4. 27.0 の正式版が出たら、分割の API（createRazorTrackAction）を実機で確かめ、recipe-razor-workarounds と cep-helper の扱いを見直す
5. CEP の終了の予定（2028-12 に既定で無効・2029-12 に同梱終了）が変わっていないか確かめる

## 知識を足すとき

1. 書き方は既存の知識と同じ（先頭項目・種類ごとの節）。個人名・個人のパス・鍵を書かない
2. `python3 plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts/kb.py build`
3. `python3 plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts/kb.py check` が 0 件
4. 検索の評価表（`knowledge/eval/search_eval.json`）に、その知識を引く言い回しを 1 つ足す

## 版を上げるとき

1. `plugins/premiere-plugin-maker/.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`skills/premiere-plugin-maker/VERSION` を同じ版にする（上げないと、入れた人に届かない）
2. CHANGELOG.md に書く
3. `python3 -m unittest discover -s tests -t tests -v` と `node --test tests/js/*.test.js` と `claude plugin validate . --strict`
