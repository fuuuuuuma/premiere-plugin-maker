# premiere-plugin-maker 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 視聴者・編集者が Claude Code / Codex に使わせるだけで、要望に合った Premiere プラグインを Mac でも Windows でも同じ手順・同じ品質で作れるスキル「premiere-plugin-maker」を、部品・雛形・知識の棚・機械の検査つきで作り、公開できる状態にする。

**Architecture:** 公開リポジトリは docu-video-maker と同じ「入れ子の形」で、利用者の PC に入るのは `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/` の中だけ。その中に SKILL.md（手順）・knowledge/（知識の棚）・parts/（部品）・templates/（雛形）・examples/（完成サンプル）・scripts/（Python 標準ライブラリだけの道具）を置く。AI は SKILL.md の手順で、OS を聞き、診断し、知識を検索し、雛形と部品を組み合わせて作り、機械の検査と Premiere での確認を通してから完成とする。

**Tech Stack:** Python 3.9 以上（標準ライブラリだけ・unittest）、JavaScript（UXP。ビルド無しの素の JS）、Node.js 20 以上（キット自体の JS テストだけ。利用者には不要）、ExtendScript（CEP 補助だけ）、GitHub Actions（公開後）。

**Spec:** `docs/superpowers/specs/2026-10-13-premiere-plugin-maker-design.md`（このワークツリーのルートから見たパス）

**材料（調査資料）:** `<作業場所>/docs/superpowers/research/2026-10-13-premiere-plugin-maker/` の A〜G・W と `notes/`（以下「調査 A」などと書く。セッション専用の一時フォルダから写した控えで、親リポジトリでは追跡しない。個人名を含むので、公開物には写さない）

## Global Constraints

- 名前はリポジトリ・目録・プラグイン・スキルとも `premiere-plugin-maker`。公開後は変えない。
- 作業場所: `<作業場所>/projects/常時運用/premiere-plugin-maker/`（独立した git。親リポジトリは追跡しない）。以下、計画の中のパスはこのフォルダ（以下「リポジトリ」）から見た相対パス。
- スキルのフォルダ: `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/`（以下 `SKILL/` と書く。Run のコマンドの中の `SKILL/` も略記なので、打つ前にこのパスへ置き換える。そのまま打つと「ファイルが無い」で止まる）。
- 対象の Premiere: UXP の正式版が入った 25.6 以降（推奨 26.x）。manifest は `manifestVersion: 5`、`host.app: "premierepro"`、`host` は配列にしない。
- 道具は Python 3.9 以上の標準ライブラリだけ。Mac は `python3 SKILL/scripts/<道具>.py`、Windows は `py -3 SKILL\scripts\<道具>.py`。
- 道具の場所は「このスキルのフォルダから見た相対パス」で示す。`${CLAUDE_PLUGIN_ROOT:-…}` の形は使わない（Claude Code でも置き換わらないことが分かっている）。
- Claude 用と Codex 用の plugin.json と `SKILL/VERSION` の版数は必ず同じ（テストで縛る）。
- SKILL.md は 200 行以内。frontmatter は `name` と `description` だけ。
- 利用者の作業フォルダの既定: Mac `~/PremierePlugins/<名前>/`、Windows `%USERPROFILE%\PremierePlugins\<名前>\`。既にあれば上書きしない。
- 利用者の手元のデータ: Mac `~/.premiere-plugin-maker/`、Windows `%USERPROFILE%\.premiere-plugin-maker\`（`kit/` と `notes/`）。
- 作るプラグインの権限は最小。ローカルサーバーは 127.0.0.1 だけで待ち、起動ごとに合言葉（token）を作る。
- 公開物に入れてはいけないもの: 個人のパス（`/Users/<実名>/` など）、鍵・トークン、利用者・取引先の名前、有料素材、他人のテンプレート、Adobe の配布物（`CSInterface.js`、`Basic Title.mogrt` など）、AI のモデルの重み。
- 知識の状態は `verified`（実機で確認）/ `partial`（一部だけ確認）/ `unverified`（未確認）/ `superseded`（古い。使わない）の 4 つだけ。
- スキル・知識・README は日本語の平易な文。発明した略語や記号で圧縮しない。
- 読み書きするテキストは必ず UTF-8（`encoding="utf-8"` を明示）。改行は `\n`。
- サブエージェントを起動するときは必ず `model: sonnet` を指定する（このワークスペースの決まり）。
- コミットはリポジトリ（独立した git）に対して行う。コード（docs・tests 以外）をコミットする直前に `/verify` を実行する（このワークスペースの決まり。対象外と返ったらその旨を作業メモに残す）。コミットの末尾に `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` を付ける。
- GitHub への push・リポジトリの作成・公開は、Task 37 で利用者の確認を取ってからだけ行う。
- Premiere の実機を使う確認（Task 36）は、そのときに利用者の許可を取ってから行う。

## Review Focus

1. **空白と日本語を含むパス**（例: Mac `~/PremierePlugins/テロップ 一括/`、Windows のユーザー名が日本語で空白を含む `C:\Users\<日本語の名前>\`、たとえば「山田 太郎」）。new_plugin・add_part・check・make_ccx・logs・doctor が、どれも壊れずに動くべき。→ Task 2・10・11・14 のテストで空白と日本語のパスを使う。
2. **Windows の cp932 の画面への出力**。どの道具も日本語を出力して落ちてはいけない。→ Task 2 で `setup_stdio()` を作り、Task 4・5・6・10・13 のテストで `PYTHONIOENCODING=cp932` の子プロセスとして起動しても落ちずに終わることを確かめる。
3. **同じ操作のやり直し**（作業フォルダが既にある、同じ部品を 2 回足す、.ccx を作り直す）。上書きで利用者の作業を壊さず、2 回目は何も変えないべき。→ Task 10・11・14 のテスト。
4. **Premiere が複数ある・1 つも無い**（安定版とベータ版、古い 2024・2025 のログフォルダが残っている）。doctor は全部を列挙して最新を選び、logs は最新のログを選ぶべき。→ Task 2・4・13 のテスト。
5. **手で直されて壊れた manifest.json**（コメント・末尾のカンマ・配列になった host）。トレースバックではなく、何行目が悪いかと直し方を日本語で出すべき。add_part は壊れた manifest を書き換えずに止まるべき。→ Task 3・6・11 のテスト。

---

## ファイルの地図

```
premiere-plugin-maker/                         リポジトリ（独立した git）
├─ .claude-plugin/marketplace.json             Claude Code 用の目録（Task 1）
├─ .agents/plugins/marketplace.json            Codex 用の目録（Task 1）
├─ .github/workflows/ci.yml                    macOS / Windows でテスト（Task 33）
├─ .github/ISSUE_TEMPLATE/knowledge.md         知識の還元のひな形（Task 33）
├─ .gitignore  LICENSE  README.md  CHANGELOG.md（Task 1・33）
├─ docs/prompts-ja.md                          デスクトップアプリに貼る文（Task 33）
├─ docs/maintenance.md                         知識と版の表の更新手順（Task 33）
├─ docs/superpowers/{specs,plans}/             設計書と計画の写し（Task 1）
├─ tests/                                      キット自体のテスト（利用者の PC には入らない）
│   ├─ helpers.py                              パスの定数・一時フォルダ（Task 1）
│   ├─ test_*.py                               Python のテスト（各 Task）
│   └─ js/*.test.js, js/fake_ppro.js           JS のテスト（Task 9 以降）
└─ plugins/premiere-plugin-maker/
    ├─ .claude-plugin/plugin.json  .codex-plugin/plugin.json（Task 1）
    └─ skills/premiere-plugin-maker/            = SKILL/
        ├─ SKILL.md  VERSION  agents/openai.yaml（Task 1・32）
        ├─ scripts/
        │   ├─ lib/cli.py osinfo.py fsutil.py（Task 2）
        │   ├─ lib/frontmatter.py manifest.py（Task 3）
        │   ├─ lib/jsscan.py lib/checks/*.py（Task 6〜8）
        │   ├─ lib/png.py lib/project.py（Task 10）
        │   ├─ doctor.py（Task 4） kb.py（Task 5） check.py（Task 6〜8）
        │   ├─ new_plugin.py（Task 10） add_part.py（Task 11） logs.py（Task 13）
        │   └─ make_ccx.py install_ccx.py（Task 14）
        ├─ knowledge/
        │   ├─ core/ recipes/ features/ usecases/ platform/ reference/（Task 24〜27）
        │   ├─ reference/api-since.json（Task 6）
        │   ├─ synonyms.json（Task 5）  index.json（kb.py build が作る）
        │   └─ eval/search_eval.json（Task 28）
        ├─ parts/<部品>/part.json と中身（Task 9・12・14〜23）
        ├─ templates/_base/ と templates/<雛形>/template.json（Task 10・12・15・22）
        └─ examples/zoom-button/ silence-cut/ telop-restyle/（Task 29〜31）
```

## 進め方（フェーズと順番）

| フェーズ | Task | 中身 | 並べて進められるもの |
|---|---|---|---|
| 1 土台 | 1〜4 | リポジトリ・共通ライブラリ・doctor | — |
| 2 知識と検査の仕組み | 5〜8 | kb.py・check.py | Task 24〜27 の知識の中身（Task 5 の後ならいつでも） |
| 3 雛形と組み立て | 9〜14 | JS の部品・雛形・new_plugin・add_part・logs・.ccx | — |
| 4 重い部品 | 15〜23 | サーバー・XML・無音カット・文字起こし・MOGRT・補間・CEP・MCP | 部品どうしは Task 15 の後なら並べてよい |
| 5 知識の中身 | 24〜28 | core・features・usecases・recipes・評価表 | サブエージェントで並行（2 本ずつ） |
| 6 完成サンプル | 29〜31 | zoom-button・silence-cut・telop-restyle | — |
| 7 スキル本体と公開物 | 32〜34 | SKILL.md・README・CI・衛生検査 | — |
| 8 確かめる | 35〜38 | リハーサル・実機・公開・記憶 | — |

テストの実行のしかた（リポジトリのルートで）:

- Python 全部: `python3 -m unittest discover -s tests -t tests -v`
- Python 1 ファイル: `python3 -m unittest discover -s tests -t tests -p 'test_osinfo.py' -v`
- JS 全部: `node --test tests/js/*.test.js`

---

## Phase 1: 土台

### Task 1: リポジトリの骨組みと目録

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `plugins/premiere-plugin-maker/.claude-plugin/plugin.json`
- Create: `plugins/premiere-plugin-maker/.codex-plugin/plugin.json`
- Create: `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/VERSION`
- Create: `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/SKILL.md`（仮。Task 32 で書き直す）
- Create: `.gitignore`、`LICENSE`、`README.md`（仮）、`CHANGELOG.md`
- Create: `docs/superpowers/specs/2026-10-13-premiere-plugin-maker-design.md`（設計書の写し）
- Create: `docs/superpowers/plans/2026-10-13-premiere-plugin-maker.md`（この計画の写し）
- Create: `tests/helpers.py`、`tests/test_package.py`
- Modify: 親リポジトリの `<作業場所>/.gitignore`（このフォルダを追跡しない 1 行）

**Interfaces:**
- Produces: `tests/helpers.py` の定数 `REPO`, `PLUGIN`, `SKILL`, `SCRIPTS`, `KNOWLEDGE`, `PARTS`, `TEMPLATES`, `EXAMPLES` と関数 `temp_dir(prefix) -> pathlib.Path`、`run_script(name, *args, env=None, cwd=None) -> subprocess.CompletedProcess`

- [ ] **Step 1: フォルダを作って git を始める**

```bash
mkdir -p "<作業場所>/projects/常時運用/premiere-plugin-maker"
cd "<作業場所>/projects/常時運用/premiere-plugin-maker"
git init -b main
git -C . config core.quotepath false
mkdir -p .claude-plugin .agents/plugins docs/superpowers/specs docs/superpowers/plans tests/js \
  plugins/premiere-plugin-maker/.claude-plugin plugins/premiere-plugin-maker/.codex-plugin \
  plugins/premiere-plugin-maker/skills/premiere-plugin-maker/{scripts/lib,knowledge,parts,templates,examples,agents}
```

親リポジトリがこのフォルダを追跡しないよう、親の `.gitignore` に 1 行足す（既に無視されているなら足さない）:

```bash
cd ~/ClaudeCode/.claude/worktrees/premiere-plugin-skill-d8b265
git check-ignore -q "projects/常時運用/premiere-plugin-maker/README.md" || printf '\n# 独立した git（premiere-plugin-maker）\nprojects/常時運用/premiere-plugin-maker/\n' >> .gitignore
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/helpers.py`:

```python
"""テストの共通部品。パスの定数と、一時フォルダ・道具の起動。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "premiere-plugin-maker"
SKILL = PLUGIN / "skills" / "premiere-plugin-maker"
SCRIPTS = SKILL / "scripts"
KNOWLEDGE = SKILL / "knowledge"
PARTS = SKILL / "parts"
TEMPLATES = SKILL / "templates"
EXAMPLES = SKILL / "examples"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def temp_dir(prefix: str = "ppm-test-") -> Path:
    """空白と日本語を含む一時フォルダを作る（Review Focus 1）。"""
    base = Path(tempfile.mkdtemp(prefix=prefix))
    path = base / "作業 フォルダ"
    path.mkdir()
    return path


def run_script(name: str, *args: str, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """SKILL/scripts/<name> を別プロセスで起動する。出力は UTF-8 で受け取る。"""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=full_env,
        cwd=str(cwd) if cwd else None,
        timeout=120,
    )
```

`tests/test_package.py`:

```python
import json
import unittest

from helpers import PLUGIN, REPO, SKILL


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PackageTests(unittest.TestCase):
    def test_names_are_the_same_everywhere(self):
        claude_mp = load(REPO / ".claude-plugin" / "marketplace.json")
        codex_mp = load(REPO / ".agents" / "plugins" / "marketplace.json")
        claude_pj = load(PLUGIN / ".claude-plugin" / "plugin.json")
        codex_pj = load(PLUGIN / ".codex-plugin" / "plugin.json")
        for name in (claude_mp["name"], codex_mp["name"], claude_pj["name"], codex_pj["name"],
                     claude_mp["plugins"][0]["name"], codex_mp["plugins"][0]["name"]):
            self.assertEqual(name, "premiere-plugin-maker")

    def test_versions_match(self):
        v1 = load(PLUGIN / ".claude-plugin" / "plugin.json")["version"]
        v2 = load(PLUGIN / ".codex-plugin" / "plugin.json")["version"]
        v3 = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(v1, r"^\d+\.\d+\.\d+$")
        self.assertEqual(v1, v2)
        self.assertEqual(v1, v3)

    def test_sources_point_to_the_plugin_folder(self):
        claude_mp = load(REPO / ".claude-plugin" / "marketplace.json")
        codex_mp = load(REPO / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual((REPO / claude_mp["plugins"][0]["source"]).resolve(), PLUGIN.resolve())
        self.assertEqual((REPO / codex_mp["plugins"][0]["source"]["path"]).resolve(), PLUGIN.resolve())
        self.assertEqual(codex_mp["plugins"][0]["policy"]["installation"], "AVAILABLE")

    def test_license_is_mit(self):
        self.assertIn("MIT License", (REPO / "LICENSE").read_text(encoding="utf-8"))

    def test_skill_md_frontmatter_has_only_name_and_description(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        head = text.split("---", 2)[1]
        keys = [line.split(":", 1)[0].strip() for line in head.strip().splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_package.py' -v`
Expected: FAIL（`marketplace.json` が無いので FileNotFoundError）

- [ ] **Step 4: 目録・plugin.json・VERSION・仮の SKILL.md・LICENSE などを書く**

`.claude-plugin/marketplace.json`:

```json
{
  "name": "premiere-plugin-maker",
  "description": "要望を聞いて Premiere 用のプラグインを作るスキル。部品・雛形・知識・機械の検査つき（Mac / Windows）",
  "owner": {
    "name": "fuuuuuuma"
  },
  "plugins": [
    {
      "name": "premiere-plugin-maker",
      "source": "./plugins/premiere-plugin-maker"
    }
  ]
}
```

`.agents/plugins/marketplace.json`:

```json
{
  "name": "premiere-plugin-maker",
  "interface": {
    "displayName": "Premiere Plugin Maker"
  },
  "plugins": [
    {
      "name": "premiere-plugin-maker",
      "source": {
        "source": "local",
        "path": "./plugins/premiere-plugin-maker"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

`plugins/premiere-plugin-maker/.claude-plugin/plugin.json`:

```json
{
  "name": "premiere-plugin-maker",
  "version": "0.1.0",
  "description": "要望を聞いて Premiere 用のプラグイン（UXP のパネル・コマンド・ローカルサーバー・CEP 補助）を作る。過去の機能・失敗事例・版の知識と、部品・雛形・機械の検査を使い、Premiere で動くことを確かめてから完成とする。Mac / Windows 対応。",
  "author": {
    "name": "fuuuuuuma"
  },
  "license": "MIT",
  "skills": "./skills/"
}
```

`plugins/premiere-plugin-maker/.codex-plugin/plugin.json`:

```json
{
  "name": "premiere-plugin-maker",
  "version": "0.1.0",
  "description": "要望を聞いて Premiere 用のプラグイン（UXP のパネル・コマンド・ローカルサーバー・CEP 補助）を作る。過去の機能・失敗事例・版の知識と、部品・雛形・機械の検査を使い、Premiere で動くことを確かめてから完成とする。Mac / Windows 対応。",
  "author": {
    "name": "fuuuuuuma",
    "url": "https://github.com/fuuuuuuma"
  },
  "repository": "https://github.com/fuuuuuuma/premiere-plugin-maker",
  "license": "MIT",
  "keywords": ["premiere", "premiere-pro", "uxp", "plugin", "cep", "extendscript", "video-editing"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Premiere Plugin Maker",
    "shortDescription": "要望を聞いて Premiere のプラグインを作る",
    "longDescription": "Windows か Mac かを聞き、環境を診断し、要望を 1 問ずつ聞き取ってから、知識の棚と部品・雛形を組み合わせて Premiere 用のプラグインを作ります。機械の検査と Premiere での確認を通してから完成とし、配る準備（.ccx）まで手伝います。",
    "developerName": "fuuuuuuma",
    "category": "Productivity",
    "capabilities": ["Write"],
    "defaultPrompt": [
      "Premiere で、選んだクリップにボタン一つでズームを付けるプラグインを作りたい",
      "Premiere のプラグインが読み込まれないので直してほしい"
    ],
    "brandColor": "#2B5BD7"
  }
}
```

`plugins/premiere-plugin-maker/skills/premiere-plugin-maker/VERSION`:

```
0.1.0
```

`plugins/premiere-plugin-maker/skills/premiere-plugin-maker/SKILL.md`（仮。Task 32 で全文を書く）:

```markdown
---
name: premiere-plugin-maker
description: Premiere 用のプラグインを要望を聞いて作るスキル（作成中）。
---

# Premiere プラグインを作る（作成中）
```

`.gitignore`:

```
__pycache__/
*.pyc
.DS_Store
dist/
node_modules/
*.ccx
.ppm-test-*
```

`LICENSE`（MIT。著作権表示は既存の公開物と同じ書き方にそろえる）:

```
MIT License

Copyright (c) 2026 fuuuuuuma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

`README.md`（仮。Task 33 で書き直す）:

```markdown
# premiere-plugin-maker

要望を聞いて Premiere 用のプラグインを作るスキル（作成中）。
```

`CHANGELOG.md`:

```markdown
# 変更履歴

## 0.1.0（作成中）

- 最初の版。
```

設計書と計画を写す:

```bash
cp <作業場所>/docs/superpowers/specs/2026-10-13-premiere-plugin-maker-design.md docs/superpowers/specs/
cp <作業場所>/docs/superpowers/plans/2026-10-13-premiere-plugin-maker.md docs/superpowers/plans/
```

写した 2 つの文書のうち、個人の絶対パスと調査資料のパスを含む行は、公開前の Task 34 の衛生検査で落ちる。今は写すだけにし、Task 34 で該当行を「（作業メモ。公開物では省略）」に置き換える。

- [ ] **Step 5: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_package.py' -v`
Expected: PASS（5 件）

Run: `claude plugin validate . --strict`
Expected: `Validation passed`。警告で落ちたら、指摘されたキー（例: Claude 用 plugin.json の `license`）を外して再実行し、外したことを CHANGELOG ではなく作業メモ（`docs/superpowers/plans/` の写しの末尾の「実施メモ」節）に書く。

- [ ] **Step 6: コミット**

```bash
git add -A
git commit -m "chore: リポジトリの骨組みと Claude Code / Codex の目録

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 共通ライブラリ（cli・osinfo・fsutil）

**Files:**
- Create: `SKILL/scripts/lib/__init__.py`（空）
- Create: `SKILL/scripts/lib/cli.py`
- Create: `SKILL/scripts/lib/osinfo.py`
- Create: `SKILL/scripts/lib/fsutil.py`
- Test: `tests/test_osinfo.py`、`tests/test_fsutil.py`

**Interfaces:**
- Produces（`lib.cli`）: `setup_stdio() -> None`、`print_json(obj) -> None`
- Produces（`lib.osinfo`）:
  - `detect_os(sys_platform: str | None = None) -> str`（`"mac"` / `"windows"` / `"linux"`）
  - `home(env: Mapping[str, str], os_name: str) -> Path`
  - `kit_home(env, os_name) -> Path`（`<home>/.premiere-plugin-maker`）
  - `notes_dir(env, os_name) -> Path`（`<kit_home>/notes`）
  - `default_projects_dir(env, os_name) -> Path`（`<home>/PremierePlugins`）
  - `python_command(os_name) -> str`（`"python3"` / `"py -3"`）
  - `@dataclass PremiereInstall(name: str, path: str, version: str, beta: bool)`
  - `premiere_installs(env, os_name, read_version=None) -> list[PremiereInstall]`（新しい版が先）
  - `udt_app(env, os_name) -> Path | None`
  - `udt_settings_file(env, os_name) -> Path`
  - `upia_path(env, os_name) -> Path`
  - `uxp_log_dirs(env, os_name) -> list[Path]`（存在するものだけ。新しい順）
  - `plugin_storage_roots(env, os_name) -> list[Path]`（存在しなくても候補を返す）
  - `cep_extensions_dir(env, os_name) -> Path`
  - `adobe_fonts_dir(env, os_name) -> Path`
- Produces（`lib.fsutil`）: `write_text(path, text) -> None`、`atomic_write_text(path, text) -> None`、`copy_new(src: Path, dst: Path) -> list[Path]`（既存のファイルがあれば FileExistsError で、1 つも写さない）、`nfc(text) -> str`、`is_within(child: Path, parent: Path) -> bool`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_osinfo.py`:

```python
import plistlib
import unittest
from pathlib import Path

from helpers import temp_dir
from lib import osinfo


def make_mac_app(root: Path, folder: str, app: str, version: str) -> None:
    contents = root / folder / app / "Contents"
    contents.mkdir(parents=True)
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump({"CFBundleShortVersionString": version}, f)


class DetectOsTests(unittest.TestCase):
    def test_platform_names(self):
        self.assertEqual(osinfo.detect_os("darwin"), "mac")
        self.assertEqual(osinfo.detect_os("win32"), "windows")
        self.assertEqual(osinfo.detect_os("cygwin"), "windows")
        self.assertEqual(osinfo.detect_os("linux"), "linux")


class MacPathTests(unittest.TestCase):
    def setUp(self):
        self.root = temp_dir()
        self.env = {"HOME": str(self.root / "home 山田"), "PPM_APPLICATIONS": str(self.root / "Applications"),
                    "PPM_SYSTEM_LIBRARY": str(self.root / "Library")}

    def test_home_and_kit_dirs_keep_spaces_and_japanese(self):
        self.assertEqual(osinfo.kit_home(self.env, "mac"), Path(self.env["HOME"]) / ".premiere-plugin-maker")
        self.assertEqual(osinfo.default_projects_dir(self.env, "mac"), Path(self.env["HOME"]) / "PremierePlugins")
        self.assertEqual(osinfo.notes_dir(self.env, "mac"), Path(self.env["HOME"]) / ".premiere-plugin-maker" / "notes")

    def test_premiere_installs_lists_release_and_beta_newest_first(self):
        apps = Path(self.env["PPM_APPLICATIONS"])
        make_mac_app(apps, "Adobe Premiere Pro 2025", "Adobe Premiere Pro 2025.app", "25.6.4")
        make_mac_app(apps, "Adobe Premiere Pro 2026", "Adobe Premiere Pro 2026.app", "26.5.2")
        make_mac_app(apps, "Adobe Premiere Pro (Beta)", "Adobe Premiere Pro (Beta).app", "27.1.0")
        found = osinfo.premiere_installs(self.env, "mac")
        self.assertEqual([f.version for f in found], ["27.1.0", "26.5.2", "25.6.4"])
        self.assertEqual([f.beta for f in found], [True, False, False])

    def test_no_premiere_returns_empty_list(self):
        self.assertEqual(osinfo.premiere_installs(self.env, "mac"), [])

    def test_upia_and_udt_settings(self):
        self.assertEqual(
            osinfo.upia_path(self.env, "mac"),
            Path(self.env["PPM_SYSTEM_LIBRARY"]) / "Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent",
        )
        self.assertEqual(osinfo.udt_settings_file(self.env, "mac"),
                         Path(self.env["PPM_SYSTEM_LIBRARY"]) / "Application Support/Adobe/UXP/Developer/settings.json")

    def test_uxp_log_dirs_newest_first_and_only_existing(self):
        logs = Path(self.env["HOME"]) / "Library/Logs/Adobe"
        (logs / "Adobe Premiere Pro 2024").mkdir(parents=True)
        (logs / "Adobe Premiere Pro 2026").mkdir(parents=True)
        (logs / "Adobe Premiere Pro (Beta)").mkdir(parents=True)
        names = [p.name for p in osinfo.uxp_log_dirs(self.env, "mac")]
        self.assertEqual(names, ["Adobe Premiere Pro (Beta)", "Adobe Premiere Pro 2026", "Adobe Premiere Pro 2024"])


class WindowsPathTests(unittest.TestCase):
    """Windows の場所は環境変数から組み立てる。Mac の上でも POSIX のパスを入れて試せる。"""

    def setUp(self):
        self.root = temp_dir()
        self.env = {
            "USERPROFILE": str(self.root / "Users" / "山田 太郎"),
            "APPDATA": str(self.root / "Users" / "山田 太郎" / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(self.root / "Users" / "山田 太郎" / "AppData" / "Local"),
            "ProgramFiles": str(self.root / "Program Files"),
            "CommonProgramFiles": str(self.root / "Program Files" / "Common Files"),
        }

    def test_kit_home_uses_userprofile(self):
        self.assertEqual(osinfo.kit_home(self.env, "windows"), Path(self.env["USERPROFILE"]) / ".premiere-plugin-maker")

    def test_upia_path(self):
        self.assertEqual(
            osinfo.upia_path(self.env, "windows"),
            Path(self.env["CommonProgramFiles"]) / "Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.exe",
        )

    def test_udt_settings_file(self):
        self.assertEqual(osinfo.udt_settings_file(self.env, "windows"),
                         Path(self.env["CommonProgramFiles"]) / "Adobe/UXP/Developer/settings.json")

    def test_premiere_installs_on_windows_uses_injected_version_reader(self):
        (Path(self.env["ProgramFiles"]) / "Adobe" / "Adobe Premiere Pro 2026").mkdir(parents=True)
        found = osinfo.premiere_installs(self.env, "windows", read_version=lambda os_name, path: "26.5.2")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "Adobe Premiere Pro 2026")
        self.assertEqual(found[0].version, "26.5.2")

    def test_windows_version_falls_back_to_year_in_folder_name(self):
        (Path(self.env["ProgramFiles"]) / "Adobe" / "Adobe Premiere Pro 2026").mkdir(parents=True)
        found = osinfo.premiere_installs(self.env, "windows", read_version=lambda os_name, path: "")
        self.assertEqual(found[0].version, "26.x")

    def test_plugin_storage_and_cep_dirs(self):
        roots = osinfo.plugin_storage_roots(self.env, "windows")
        self.assertIn(Path(self.env["APPDATA"]) / "Adobe/UXP/PluginsStorage", roots)
        self.assertEqual(osinfo.cep_extensions_dir(self.env, "windows"), Path(self.env["APPDATA"]) / "Adobe/CEP/extensions")
        self.assertEqual(osinfo.adobe_fonts_dir(self.env, "windows"), Path(self.env["APPDATA"]) / "Adobe/CoreSync/plugins/livetype")

    def test_python_command(self):
        self.assertEqual(osinfo.python_command("windows"), "py -3")
        self.assertEqual(osinfo.python_command("mac"), "python3")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_fsutil.py`:

```python
import unittest

from helpers import temp_dir
from lib import fsutil


class FsutilTests(unittest.TestCase):
    def test_copy_new_refuses_when_any_target_exists_and_copies_nothing(self):
        src = temp_dir() / "src"
        (src / "lib").mkdir(parents=True)
        (src / "a.txt").write_text("a", encoding="utf-8")
        (src / "lib" / "b.js").write_text("b", encoding="utf-8")
        dst = temp_dir() / "dst"
        (dst / "lib").mkdir(parents=True)
        (dst / "lib" / "b.js").write_text("利用者の変更", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            fsutil.copy_new(src, dst)
        self.assertFalse((dst / "a.txt").exists())
        self.assertEqual((dst / "lib" / "b.js").read_text(encoding="utf-8"), "利用者の変更")

    def test_copy_new_copies_tree(self):
        src = temp_dir() / "src"
        (src / "lib").mkdir(parents=True)
        (src / "lib" / "b.js").write_text("b", encoding="utf-8")
        dst = temp_dir() / "dst"
        copied = fsutil.copy_new(src, dst)
        self.assertEqual([p.relative_to(dst).as_posix() for p in copied], ["lib/b.js"])

    def test_atomic_write_and_nfc(self):
        path = temp_dir() / "テスト.json"
        fsutil.atomic_write_text(path, "{}\n")
        self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")
        self.assertEqual(fsutil.nfc("か\u3099"), "が")

    def test_is_within(self):
        base = temp_dir()
        self.assertTrue(fsutil.is_within(base / "a" / "b", base))
        self.assertFalse(fsutil.is_within(base.parent, base))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_osinfo.py' -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'lib'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/lib/__init__.py`: 空のファイル。

`SKILL/scripts/lib/cli.py`:

```python
"""道具の共通の作法（標準出力の文字コード・JSON の出力）。"""
from __future__ import annotations

import json
import sys


def setup_stdio() -> None:
    """Windows の cp932 の画面やパイプでも、日本語で落ちないようにする。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))
```

`SKILL/scripts/lib/osinfo.py`:

```python
"""OS ごとの場所を 1 か所に集める。

テストでは env・os_name・read_version を差し替え、Mac の上でも Windows の組み立てを試せる。
Windows の場所は必ず環境変数（USERPROFILE / APPDATA / LOCALAPPDATA / ProgramFiles / CommonProgramFiles）から作る。
Mac のシステム側（/Applications と /Library）は、テスト用に PPM_APPLICATIONS と PPM_SYSTEM_LIBRARY で差し替えられる。
"""
from __future__ import annotations

import os
import plistlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Mapping, Optional

KIT_DIR_NAME = ".premiere-plugin-maker"


def detect_os(sys_platform: Optional[str] = None) -> str:
    p = sys.platform if sys_platform is None else sys_platform
    if p == "darwin":
        return "mac"
    if p.startswith("win") or p == "cygwin":
        return "windows"
    return "linux"


def _env(env: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    return os.environ if env is None else env


def home(env: Optional[Mapping[str, str]], os_name: str) -> Path:
    e = _env(env)
    if os_name == "windows":
        return Path(e.get("USERPROFILE") or e.get("HOME") or str(Path.home()))
    return Path(e.get("HOME") or str(Path.home()))


def kit_home(env, os_name: str) -> Path:
    return home(env, os_name) / KIT_DIR_NAME


def notes_dir(env, os_name: str) -> Path:
    return kit_home(env, os_name) / "notes"


def default_projects_dir(env, os_name: str) -> Path:
    return home(env, os_name) / "PremierePlugins"


def python_command(os_name: str) -> str:
    return "py -3" if os_name == "windows" else "python3"


def _appdata(env, os_name: str) -> Path:
    e = _env(env)
    return Path(e.get("APPDATA") or (home(env, os_name) / "AppData" / "Roaming"))


def _localappdata(env, os_name: str) -> Path:
    e = _env(env)
    return Path(e.get("LOCALAPPDATA") or (home(env, os_name) / "AppData" / "Local"))


def _program_files(env) -> Path:
    return Path(_env(env).get("ProgramFiles") or r"C:\Program Files")


def _common_program_files(env) -> Path:
    e = _env(env)
    return Path(e.get("CommonProgramFiles") or (_program_files(env) / "Common Files"))


def _mac_applications(env) -> Path:
    return Path(_env(env).get("PPM_APPLICATIONS") or "/Applications")


def _mac_system_library(env) -> Path:
    return Path(_env(env).get("PPM_SYSTEM_LIBRARY") or "/Library")


@dataclass
class PremiereInstall:
    name: str
    path: str
    version: str
    beta: bool


def _version_key(version: str):
    nums = [int(x) for x in re.findall(r"\d+", version)]
    return tuple(nums + [0] * (3 - len(nums))) if nums else (0, 0, 0)


def _read_version(os_name: str, path: Path) -> str:
    if os_name == "mac":
        plist = path / "Contents" / "Info.plist"
        try:
            with open(plist, "rb") as f:
                return str(plistlib.load(f).get("CFBundleShortVersionString", ""))
        except (OSError, plistlib.InvalidFileException):
            return ""
    if os_name == "windows":
        return _read_windows_exe_version(path)
    return ""


def _read_windows_exe_version(folder: Path) -> str:
    """Windows の exe の版を読む（Windows の上だけ）。読めなければ空文字。"""
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return ""
    exes = sorted(folder.glob("Adobe Premiere*.exe"))
    if not exes:
        return ""
    exe = str(exes[0])
    size = ctypes.windll.version.GetFileVersionInfoSizeW(exe, None)
    if not size:
        return ""
    buf = ctypes.create_string_buffer(size)
    if not ctypes.windll.version.GetFileVersionInfoW(exe, 0, size, buf):
        return ""
    ptr = ctypes.c_void_p()
    length = wintypes.UINT()
    if not ctypes.windll.version.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(length)):
        return ""

    class VSFixedFileInfo(ctypes.Structure):
        _fields_ = [("sig", wintypes.DWORD), ("struc", wintypes.DWORD), ("ms", wintypes.DWORD), ("ls", wintypes.DWORD)]

    info = ctypes.cast(ptr, ctypes.POINTER(VSFixedFileInfo)).contents
    return f"{info.ms >> 16}.{info.ms & 0xFFFF}.{info.ls >> 16}"


def premiere_installs(env, os_name: str, read_version: Optional[Callable[[str, Path], str]] = None) -> List[PremiereInstall]:
    """入っている Premiere を新しい版から順に返す。フォルダ名の揺れ（Premiere Pro / Premiere）に強いよう glob で探す。"""
    reader = read_version or _read_version
    found: List[PremiereInstall] = []
    if os_name == "mac":
        root = _mac_applications(env)
        for folder in sorted(root.glob("Adobe Premiere*")):
            if not folder.is_dir():
                continue
            apps = sorted(p for p in folder.glob("Adobe Premiere*.app") if p.is_dir())
            if not apps:
                continue
            found.append(PremiereInstall(folder.name, str(apps[0]), reader("mac", apps[0]), "Beta" in folder.name))
    elif os_name == "windows":
        root = _program_files(env) / "Adobe"
        for folder in sorted(root.glob("Adobe Premiere*")):
            if not folder.is_dir():
                continue
            version = reader("windows", folder)
            if not version:
                year = re.search(r"20(\d\d)", folder.name)
                version = f"{year.group(1)}.x" if year else ""
            found.append(PremiereInstall(folder.name, str(folder), version, "Beta" in folder.name))
    found.sort(key=lambda f: _version_key(f.version), reverse=True)
    return found


def udt_app(env, os_name: str) -> Optional[Path]:
    if os_name == "mac":
        candidate = _mac_applications(env) / "Adobe UXP Developer Tools"
    elif os_name == "windows":
        candidate = _program_files(env) / "Adobe" / "Adobe UXP Developer Tools"
    else:
        return None
    return candidate if candidate.exists() else None


def udt_settings_file(env, os_name: str) -> Path:
    if os_name == "windows":
        return _common_program_files(env) / "Adobe" / "UXP" / "Developer" / "settings.json"
    return _mac_system_library(env) / "Application Support" / "Adobe" / "UXP" / "Developer" / "settings.json"


def upia_path(env, os_name: str) -> Path:
    tail = Path("Adobe") / "Adobe Desktop Common" / "RemoteComponents" / "UPI" / "UnifiedPluginInstallerAgent"
    if os_name == "windows":
        return _common_program_files(env) / tail / "UnifiedPluginInstallerAgent.exe"
    return (_mac_system_library(env) / "Application Support" / tail
            / "UnifiedPluginInstallerAgent.app" / "Contents" / "MacOS" / "UnifiedPluginInstallerAgent")


def _sort_newest_first(dirs: List[Path]) -> List[Path]:
    def key(p: Path):
        if "Beta" in p.name:
            return (9999,)
        year = re.search(r"20(\d\d)", p.name)
        return (int(year.group(1)) if year else 0,)
    return sorted(dirs, key=key, reverse=True)


def uxp_log_dirs(env, os_name: str) -> List[Path]:
    """Premiere の UXP ログのフォルダ（存在するものだけ）。Windows の製品版の場所は公式に見つかっていないので候補を広めに見る。"""
    if os_name == "mac":
        base = home(env, os_name) / "Library" / "Logs" / "Adobe"
        dirs = [p for p in base.glob("Adobe Premiere*") if p.is_dir()]
        return _sort_newest_first(dirs)
    if os_name == "windows":
        roaming = _appdata(env, os_name) / "Adobe"
        dirs = [p / "Logs" for p in roaming.glob("*Premiere*") if (p / "Logs").is_dir()]
        temp = _localappdata(env, os_name) / "Temp" / "UXPLogs"
        if temp.is_dir():
            dirs.append(temp)
        return _sort_newest_first(dirs)
    return []


def plugin_storage_roots(env, os_name: str) -> List[Path]:
    """UXP のプラグインのデータフォルダが入る場所の候補（雛形のログ ppm-log.txt を探すため）。"""
    if os_name == "mac":
        return [home(env, os_name) / "Library" / "Application Support" / "Adobe" / "UXP" / "PluginsStorage"]
    if os_name == "windows":
        return [_appdata(env, os_name) / "Adobe" / "UXP" / "PluginsStorage",
                _localappdata(env, os_name) / "Adobe" / "UXP" / "PluginsStorage"]
    return []


def cep_extensions_dir(env, os_name: str) -> Path:
    if os_name == "windows":
        return _appdata(env, os_name) / "Adobe" / "CEP" / "extensions"
    return home(env, os_name) / "Library" / "Application Support" / "Adobe" / "CEP" / "extensions"


def adobe_fonts_dir(env, os_name: str) -> Path:
    if os_name == "windows":
        return _appdata(env, os_name) / "Adobe" / "CoreSync" / "plugins" / "livetype"
    return home(env, os_name) / "Library" / "Application Support" / "Adobe" / "CoreSync" / "plugins" / "livetype"
```

`SKILL/scripts/lib/fsutil.py`:

```python
"""ファイル操作の共通部品。利用者のファイルを上書きしないことを最優先にする。"""
from __future__ import annotations

import os
import shutil
import unicodedata
from pathlib import Path
from typing import List


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def copy_new(src: Path, dst: Path) -> List[Path]:
    """src の中身を dst へ写す。dst に同じ名前のファイルが 1 つでもあれば、何も写さずに FileExistsError。"""
    src, dst = Path(src), Path(dst)
    files = sorted(p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    clashes = [dst / p.relative_to(src) for p in files if (dst / p.relative_to(src)).exists()]
    if clashes:
        raise FileExistsError("既にあるファイルは上書きしません: " + ", ".join(str(c) for c in clashes[:5]))
    copied: List[Path] = []
    for p in files:
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        copied.append(target)
    return copied


def nfc(text: str) -> str:
    """Finder や zip で NFD になった日本語を NFC にそろえる。"""
    return unicodedata.normalize("NFC", text)


def is_within(child: Path, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_osinfo.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_fsutil.py' -v`
Expected: PASS（osinfo 13 件・fsutil 4 件）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: OS ごとの場所とファイル操作の共通ライブラリ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: frontmatter と manifest のライブラリ

**Files:**
- Create: `SKILL/scripts/lib/frontmatter.py`
- Create: `SKILL/scripts/lib/manifest.py`
- Test: `tests/test_frontmatter.py`、`tests/test_manifest_lib.py`

**Interfaces:**
- Produces（`lib.frontmatter`）: `class FrontmatterError(ValueError)`、`parse(text: str) -> tuple[dict, str]`、`dump(data: dict) -> str`
- Produces（`lib.manifest`）: `class ManifestError(ValueError)`、`load(path) -> dict`、`save(path, data) -> None`、`version_tuple(v: str) -> tuple[int, int, int]`、`min_version(data) -> str`、`raise_min_version(data, needed: str) -> bool`、`merge_permissions(data, perms: dict) -> list[str]`、`merge_feature_flags(data, flags: dict) -> list[str]`、`add_entrypoints(data, entries: list) -> list[str]`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_frontmatter.py`:

```python
import unittest

from lib import frontmatter as fm


class FrontmatterTests(unittest.TestCase):
    def test_parse_scalars_lists_and_quotes(self):
        text = (
            "---\n"
            "id: ui-flex-rows-collapse\n"
            "title: 一覧の行が中身より低く潰れる\n"
            "tags: [画面, CSS, flex]\n"
            "premiere: \">=25.6\"\n"
            "status: verified   # 実機で確認\n"
            "---\n"
            "\n本文\n"
        )
        data, body = fm.parse(text)
        self.assertEqual(data["id"], "ui-flex-rows-collapse")
        self.assertEqual(data["tags"], ["画面", "CSS", "flex"])
        self.assertEqual(data["premiere"], ">=25.6")
        self.assertEqual(data["status"], "verified")
        self.assertEqual(body, "本文\n")

    def test_bom_and_empty_list(self):
        data, _ = fm.parse("\ufeff---\nrelated: []\n---\n")
        self.assertEqual(data["related"], [])

    def test_errors_say_which_line(self):
        with self.assertRaises(fm.FrontmatterError) as ctx:
            fm.parse("---\nid ui\n---\n")
        self.assertIn("2 行目", str(ctx.exception))
        with self.assertRaises(fm.FrontmatterError):
            fm.parse("本文だけ\n")
        with self.assertRaises(fm.FrontmatterError):
            fm.parse("---\nid: x\n")

    def test_dump_roundtrip(self):
        data = {"id": "x", "title": "a: b", "tags": ["c", "d"]}
        again, _ = fm.parse(fm.dump(data) + "本文\n")
        self.assertEqual(again, data)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_manifest_lib.py`:

```python
import unittest

from helpers import temp_dir
from lib import manifest as mf


class ManifestLoadTests(unittest.TestCase):
    def test_broken_json_reports_line_and_column(self):
        path = temp_dir() / "manifest.json"
        path.write_text('{\n  "id": "a",\n  // コメント\n}\n', encoding="utf-8")
        with self.assertRaises(mf.ManifestError) as ctx:
            mf.load(path)
        self.assertIn("3 行目", str(ctx.exception))
        self.assertIn("コメントや末尾のカンマは書けません", str(ctx.exception))

    def test_missing_file(self):
        with self.assertRaises(mf.ManifestError):
            mf.load(temp_dir() / "manifest.json")

    def test_top_level_must_be_object(self):
        path = temp_dir() / "manifest.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(mf.ManifestError):
            mf.load(path)

    def test_save_keeps_japanese_and_trailing_newline(self):
        path = temp_dir() / "manifest.json"
        mf.save(path, {"name": "テロップ"})
        self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "name": "テロップ"\n}\n')


class ManifestMergeTests(unittest.TestCase):
    def base(self):
        return {"host": {"app": "premierepro", "minVersion": "25.6"}, "requiredPermissions": {"localFileSystem": "plugin"}}

    def test_version_tuple(self):
        self.assertEqual(mf.version_tuple("26.2"), (26, 2, 0))
        self.assertEqual(mf.version_tuple("25.6.1"), (25, 6, 1))
        with self.assertRaises(ValueError):
            mf.version_tuple("abc")

    def test_raise_min_version_only_goes_up(self):
        data = self.base()
        self.assertTrue(mf.raise_min_version(data, "26.2"))
        self.assertEqual(data["host"]["minVersion"], "26.2")
        self.assertFalse(mf.raise_min_version(data, "25.6"))
        self.assertEqual(data["host"]["minVersion"], "26.2")

    def test_file_access_is_raised_but_never_lowered(self):
        data = self.base()
        self.assertEqual(mf.merge_permissions(data, {"localFileSystem": "fullAccess"}), ["localFileSystem"])
        self.assertEqual(mf.merge_permissions(data, {"localFileSystem": "request"}), [])
        self.assertEqual(data["requiredPermissions"]["localFileSystem"], "fullAccess")

    def test_network_all_wins_and_lists_merge(self):
        data = self.base()
        mf.merge_permissions(data, {"network": {"domains": ["https://b.example.com"]}})
        mf.merge_permissions(data, {"network": {"domains": ["https://a.example.com"]}})
        self.assertEqual(data["requiredPermissions"]["network"]["domains"], ["https://a.example.com", "https://b.example.com"])
        mf.merge_permissions(data, {"network": {"domains": "all"}})
        self.assertEqual(data["requiredPermissions"]["network"]["domains"], "all")
        self.assertEqual(mf.merge_permissions(data, {"network": {"domains": ["https://c.example.com"]}}), [])

    def test_feature_flags_and_entrypoints(self):
        data = self.base()
        data["entrypoints"] = [{"type": "panel", "id": "main", "label": {"default": "A"}}]
        self.assertEqual(mf.merge_feature_flags(data, {"enableAlerts": True}), ["enableAlerts"])
        added = mf.add_entrypoints(data, [{"type": "command", "id": "cmd1", "label": {"default": "B"}},
                                          {"type": "panel", "id": "main", "label": {"default": "重複"}}])
        self.assertEqual(added, ["cmd1"])
        self.assertEqual(len(data["entrypoints"]), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_frontmatter.py' -v`
Expected: FAIL（`cannot import name 'frontmatter'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/lib/frontmatter.py`:

```python
"""知識ファイルの先頭項目（--- で囲んだ部分）を読み書きする。

標準ライブラリだけで読めるよう、YAML のごく一部だけを扱う:
  key: 値        key: "引用"        key: [a, b, c]        # 以降は注釈
入れ子・複数行の値・リストの中のカンマは書かない。
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Union

Value = Union[str, List[str]]


class FrontmatterError(ValueError):
    pass


def _strip_comment(raw: str) -> str:
    out = []
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or raw[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _value(raw: str, lineno: int) -> Value:
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise FrontmatterError(f"{lineno} 行目: [ の閉じ ] がありません")
        inner = raw[1:-1].strip()
        return [_unquote(x) for x in inner.split(",")] if inner else []
    return _unquote(raw)


def parse(text: str) -> Tuple[Dict[str, Value], str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("1 行目が --- ではありません（先頭項目がありません）")
    data: Dict[str, Value] = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:]).lstrip("\n")
            if body and not body.endswith("\n"):
                body += "\n"
            return data, body
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise FrontmatterError(f"{i + 1} 行目: 「キー: 値」の形ではありません")
        key, raw = line.split(":", 1)
        data[key.strip()] = _value(_strip_comment(raw).strip(), i + 1)
    raise FrontmatterError("先頭項目の閉じの --- がありません")


def dump(data: Dict[str, Value]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
            continue
        s = str(value)
        if any(c in s for c in ":#[]\"") or s != s.strip():
            s = '"' + s.replace('"', "'") + '"'
        lines.append(f"{key}: {s}")
    lines.append("---")
    return "\n".join(lines) + "\n"
```

`SKILL/scripts/lib/manifest.py`:

```python
"""UXP の manifest.json を読む・書く・部品の要る権限を足す。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

LFS_ORDER = ["plugin", "request", "fullAccess"]
CLIPBOARD_ORDER = ["read", "readAndWrite"]


class ManifestError(ValueError):
    pass


def load(path) -> Dict[str, Any]:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ManifestError(f"manifest.json が見つかりません: {path}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestError(
            f"manifest.json の {e.lineno} 行目 {e.colno} 文字目が JSON として読めません（{e.msg}）。"
            "コメントや末尾のカンマは書けません"
        ) from None
    if not isinstance(data, dict):
        raise ManifestError("manifest.json の一番外側が { } ではありません")
    return data


def save(path, data: Dict[str, Any]) -> None:
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def version_tuple(v: str) -> Tuple[int, int, int]:
    m = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(v).strip())
    if not m:
        raise ValueError(f"版数の形が違います: {v}")
    a, b, c = (int(x) if x else 0 for x in m.groups())
    return (a, b, c)


def min_version(data: Dict[str, Any]) -> str:
    host = data.get("host")
    return str(host.get("minVersion", "")) if isinstance(host, dict) else ""


def raise_min_version(data: Dict[str, Any], needed: str) -> bool:
    host = data.setdefault("host", {})
    current = host.get("minVersion")
    if not current or version_tuple(current) < version_tuple(needed):
        host["minVersion"] = needed
        return True
    return False


def merge_permissions(data: Dict[str, Any], perms: Dict[str, Any]) -> List[str]:
    """部品が要る権限を足す。弱い権限は強くするが、強い権限を弱めない。変えた項目名を返す。"""
    rp = data.setdefault("requiredPermissions", {})
    changed: List[str] = []
    for key, val in perms.items():
        if key == "localFileSystem":
            current = rp.get(key, "plugin")
            if LFS_ORDER.index(val) > LFS_ORDER.index(current) or key not in rp:
                rp[key] = max(val, current, key=LFS_ORDER.index)
                changed.append(key)
        elif key == "network":
            current = (rp.get("network") or {}).get("domains")
            want = val.get("domains")
            if current == "all":
                continue
            if want == "all":
                rp["network"] = {"domains": "all"}
                changed.append(key)
                continue
            merged = sorted(set(current or []) | set(want or []))
            if merged != (current or []):
                rp["network"] = {"domains": merged}
                changed.append(key)
        elif key == "clipboard":
            current = rp.get(key)
            if current is None or CLIPBOARD_ORDER.index(val) > CLIPBOARD_ORDER.index(current):
                rp[key] = val
                changed.append(key)
        elif key == "launchProcess":
            current = rp.get(key) or {"schemes": [], "extensions": []}
            new = {
                "schemes": sorted(set(current.get("schemes", [])) | set(val.get("schemes", []))),
                "extensions": sorted(set(current.get("extensions", [])) | set(val.get("extensions", []))),
            }
            if new != current:
                rp[key] = new
                changed.append(key)
        elif isinstance(val, bool):
            if val and not rp.get(key):
                rp[key] = True
                changed.append(key)
        elif rp.get(key) != val:
            rp[key] = val
            changed.append(key)
    return changed


def merge_feature_flags(data: Dict[str, Any], flags: Dict[str, bool]) -> List[str]:
    ff = data.setdefault("featureFlags", {})
    changed = []
    for key, val in flags.items():
        if val and not ff.get(key):
            ff[key] = True
            changed.append(key)
    return changed


def add_entrypoints(data: Dict[str, Any], entries: List[Dict[str, Any]]) -> List[str]:
    eps = data.setdefault("entrypoints", [])
    existing = {e.get("id") for e in eps}
    added = []
    for e in entries:
        if e.get("id") in existing:
            continue
        eps.append(e)
        existing.add(e.get("id"))
        added.append(e["id"])
    return added
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_frontmatter.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_manifest_lib.py' -v`
Expected: PASS（frontmatter 4 件・manifest 9 件）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 知識の先頭項目と manifest.json を扱うライブラリ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: doctor.py（環境の診断）

**Files:**
- Create: `SKILL/scripts/doctor.py`
- Test: `tests/test_doctor.py`

**Interfaces:**
- Consumes: `lib.osinfo` の全関数、`lib.cli.setup_stdio / print_json`
- Produces:
  - `@dataclass Row(item: str, ok: bool, level: str, detail: str, fix: str)`（level は `"必須"` / `"推奨"` / `"任意"` / `"情報"`）
  - `collect(env, os_name, which=shutil.which, online=False, fetch=None, kit_version=None) -> list[Row]`
  - `main(argv=None) -> int`（必須が 1 つでも NG なら 1、それ以外は 0）
  - 出力の行の形: `[OK ] 項目: 詳細` / `[NG!] 項目: 詳細` / `[注意] 項目: 詳細` と、その下に `      直し方: …`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_doctor.py`:

```python
import json
import plistlib
import unittest
from pathlib import Path

from helpers import run_script, temp_dir

import doctor


def fake_which(names):
    return lambda name: f"/usr/bin/{name}" if name in names else None


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.root = temp_dir()
        self.env = {"HOME": str(self.root / "home"), "PPM_APPLICATIONS": str(self.root / "Applications"),
                    "PPM_SYSTEM_LIBRARY": str(self.root / "Library")}

    def add_premiere(self, version="26.5.2", folder="Adobe Premiere Pro 2026"):
        contents = Path(self.env["PPM_APPLICATIONS"]) / folder / f"{folder}.app" / "Contents"
        contents.mkdir(parents=True)
        with open(contents / "Info.plist", "wb") as f:
            plistlib.dump({"CFBundleShortVersionString": version}, f)

    def rows(self, **kw):
        return {r.item: r for r in doctor.collect(self.env, "mac", which=fake_which({"git", "ffmpeg"}), **kw)}

    def test_missing_premiere_is_fatal(self):
        rows = self.rows()
        self.assertFalse(rows["Premiere"].ok)
        self.assertEqual(rows["Premiere"].level, "必須")
        self.assertIn("Creative Cloud", rows["Premiere"].fix)

    def test_old_premiere_is_fatal_and_new_one_passes(self):
        self.add_premiere("25.2.0", "Adobe Premiere Pro 2025")
        self.assertFalse(self.rows()["Premiere"].ok)
        self.add_premiere("26.5.2")
        row = self.rows()["Premiere"]
        self.assertTrue(row.ok)
        self.assertIn("26.5.2", row.detail)

    def test_udt_and_developer_mode(self):
        rows = self.rows()
        self.assertFalse(rows["UXP Developer Tools"].ok)
        (Path(self.env["PPM_APPLICATIONS"]) / "Adobe UXP Developer Tools").mkdir(parents=True)
        settings = Path(self.env["PPM_SYSTEM_LIBRARY"]) / "Application Support/Adobe/UXP/Developer/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"developer" : true}', encoding="utf-8")
        rows = self.rows()
        self.assertTrue(rows["UXP Developer Tools"].ok)
        self.assertTrue(rows["開発者モード（UDT 側）"].ok)

    def test_online_check_reports_newer_version(self):
        rows = self.rows(online=True, fetch=lambda url: "0.2.0\n", kit_version="0.1.0")
        self.assertFalse(rows["キットの版"].ok)
        self.assertIn("0.2.0", rows["キットの版"].detail)

    def test_online_check_survives_offline(self):
        def boom(url):
            raise OSError("offline")
        rows = self.rows(online=True, fetch=boom, kit_version="0.1.0")
        self.assertEqual(rows["キットの版"].level, "情報")
        self.assertIn("確かめられませんでした", rows["キットの版"].detail)

    def test_windows_store_python_alias_is_flagged(self):
        env = {"USERPROFILE": str(self.root / "u"), "ProgramFiles": str(self.root / "pf"), "CommonProgramFiles": str(self.root / "pf" / "Common Files")}
        which = lambda name: r"C:\Users\you\AppData\Local\Microsoft\WindowsApps\python.exe" if name == "python" else None
        rows = {r.item: r for r in doctor.collect(env, "windows", which=which)}
        self.assertIn("Python（Windows）", rows)
        self.assertFalse(rows["Python（Windows）"].ok)
        self.assertIn("py", rows["Python（Windows）"].fix)

    def test_cli_json_and_cp932_console(self):
        proc = run_script("doctor.py", "--json", env={**self.env, "PYTHONIOENCODING": "cp932"})
        self.assertIn(proc.returncode, (0, 1))
        self.assertNotIn("Traceback", proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("rows", data)
        self.assertIn(data["os"], ("mac", "windows", "linux"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_doctor.py' -v`
Expected: FAIL（`No module named 'doctor'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/doctor.py`:

```python
#!/usr/bin/env python3
"""環境の診断。足りない物と直し方を表示する（何もインストールしない）。

使い方:
  Mac:     python3 <このスキル>/scripts/doctor.py [--json] [--online]
  Windows: py -3 <このスキル>\\scripts\\doctor.py [--json] [--online]
--online のときだけ、公開リポジトリの最新版の番号を 1 回読む。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402

SKILL_DIR = HERE.parent
VERSION_URL = "https://raw.githubusercontent.com/fuuuuuuma/premiere-plugin-maker/main/plugins/premiere-plugin-maker/skills/premiere-plugin-maker/VERSION"
MIN_PREMIERE = (25, 6, 0)


@dataclass
class Row:
    item: str
    ok: bool
    level: str
    detail: str
    fix: str = ""


def _vt(v: str):
    import re
    nums = [int(x) for x in re.findall(r"\d+", v)]
    return tuple(nums + [0] * (3 - len(nums)))[:3] if nums else (0, 0, 0)


def _read_kit_version() -> str:
    try:
        return (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as res:
        return res.read().decode("utf-8")


def collect(env, os_name: str, which: Callable[[str], Optional[str]] = shutil.which, online: bool = False,
            fetch: Optional[Callable[[str], str]] = None, kit_version: Optional[str] = None) -> List[Row]:
    rows: List[Row] = []
    rows.append(Row("OS", os_name in ("mac", "windows"), "情報", {"mac": "Mac", "windows": "Windows"}.get(os_name, os_name),
                    "" if os_name in ("mac", "windows") else "このスキルは Mac と Windows を対象にしています"))

    py_ok = sys.version_info >= (3, 9)
    rows.append(Row("Python", py_ok, "必須", sys.version.split()[0],
                    "" if py_ok else "Python 3.9 以上を入れてください（Mac: python.org か Homebrew、Windows: Python install manager）"))
    if os_name == "windows":
        alias = which("python") or ""
        has_py = bool(which("py"))
        store_stub = "WindowsApps" in alias
        rows.append(Row("Python（Windows）", has_py and not store_stub, "推奨",
                        ("py ランチャーがあります" if has_py else "py ランチャーが見つかりません")
                        + ("。python は Microsoft Store の仮の入口です" if store_stub else ""),
                        "" if has_py and not store_stub else
                        "python.org の Python install manager を入れ、以降は `py -3` で呼んでください。"
                        "python で Store が開くときは［設定］→［アプリ実行エイリアス］で python をオフにします"))

    installs = osinfo.premiere_installs(env, os_name)
    usable = [i for i in installs if i.version.endswith(".x") or _vt(i.version) >= MIN_PREMIERE]
    detail = "、".join(f"{i.name}（{i.version or '版不明'}）" for i in installs) or "見つかりません"
    rows.append(Row("Premiere", bool(usable), "必須", detail,
                    "" if usable else "Creative Cloud デスクトップから Premiere 25.6 以降（推奨 26.x）を入れてください"))

    udt = osinfo.udt_app(env, os_name)
    rows.append(Row("UXP Developer Tools", bool(udt), "必須", str(udt) if udt else "見つかりません",
                    "" if udt else "Creative Cloud デスクトップ →［すべてのアプリ］→「UXP Developer Tools」を入れてください（初回は管理者の許可が要ります）"))

    settings = osinfo.udt_settings_file(env, os_name)
    dev_ok = False
    try:
        dev_ok = bool(json.loads(settings.read_text(encoding="utf-8")).get("developer"))
    except (OSError, ValueError, AttributeError):
        dev_ok = False
    rows.append(Row("開発者モード（UDT 側）", dev_ok, "推奨", str(settings) if dev_ok else "まだ有効になっていません",
                    "" if dev_ok else "UXP Developer Tools を起動すると出る案内で Enable を押してください。"
                    "Premiere 側も［設定］→［プラグイン］で開発者モードをオンにして再起動します"))

    upia = osinfo.upia_path(env, os_name)
    rows.append(Row("プラグインの導入ツール（UPIA）", upia.exists(), "任意", str(upia) if upia.exists() else "見つかりません",
                    "" if upia.exists() else "Creative Cloud デスクトップに同梱されています。.ccx を配るときだけ要ります"))

    ffmpeg = which("ffmpeg")
    rows.append(Row("ffmpeg", bool(ffmpeg), "任意", ffmpeg or "見つかりません",
                    "" if ffmpeg else ("音声を扱う部品で要ります。Mac: brew install ffmpeg" if os_name == "mac"
                                       else "音声を扱う部品で要ります。Windows: winget install --id Gyan.FFmpeg -e（入れた後は新しい画面で確かめる）")))

    git = which("git")
    rows.append(Row("git", bool(git), "任意", git or "見つかりません", "" if git else "キットを取ってくる・更新するときに使います"))

    local = kit_version if kit_version is not None else _read_kit_version()
    if online:
        try:
            latest = (fetch or _fetch)(VERSION_URL).strip()
            newer = _vt(latest) > _vt(local)
            rows.append(Row("キットの版", not newer, "推奨", f"手元 {local} / 最新 {latest}",
                            "新しい版があります。Claude Code: claude plugin marketplace update premiere-plugin-maker → "
                            "claude plugin update premiere-plugin-maker@premiere-plugin-maker／Codex: codex plugin marketplace upgrade premiere-plugin-maker"
                            if newer else ""))
        except Exception:  # noqa: BLE001  ネットが無いときも診断は止めない
            rows.append(Row("キットの版", True, "情報", f"手元 {local}（最新の版は確かめられませんでした）", ""))
    else:
        rows.append(Row("キットの版", True, "情報", f"手元 {local}", ""))
    return rows


def _mark(row: Row) -> str:
    if row.ok:
        return "[OK ]"
    return "[NG!]" if row.level == "必須" else "[注意]"


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="Premiere プラグイン作りの環境を診断する")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--online", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    rows = collect(os.environ, os_name, online=args.online)
    fatal = [r for r in rows if r.level == "必須" and not r.ok]
    if args.json:
        cli.print_json({"os": os_name, "ok": not fatal, "rows": [asdict(r) for r in rows]})
    else:
        for r in rows:
            print(f"{_mark(r)} {r.item}: {r.detail}")
            if r.fix and not r.ok:
                print(f"      直し方: {r.fix}")
        print()
        print("必須はそろっています。" if not fatal else "必須が足りません: " + "、".join(r.item for r in fatal))
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_doctor.py' -v`
Expected: PASS（7 件）

Run（手で 1 回）: `python3 plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts/doctor.py`
Expected: この Mac では `Premiere: Adobe Premiere Pro (Beta)（27.1.0）、Adobe Premiere Pro 2026（26.5.2）` と UDT・開発者モードが `[OK ]`。出力を作業メモに貼る。

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: doctor.py（Premiere・UDT・開発者モード・Python・ffmpeg・キットの版の診断）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 2: 知識と検査の仕組み

### Task 5: kb.py（知識の棚を引く道具）と同義語の表

**Files:**
- Create: `SKILL/scripts/kb.py`
- Create: `SKILL/knowledge/synonyms.json`
- Create: `SKILL/knowledge/{core,recipes,features,usecases,platform,reference}/.gitkeep`
- Test: `tests/test_kb.py`

**Interfaces:**
- Consumes: `lib.frontmatter.parse / dump`、`lib.osinfo.notes_dir / detect_os`、`lib.fsutil.write_text`、`lib.cli`
- Produces（`kb`）:
  - 定数 `FOLDER_KIND = {"core": "core", "recipes": "recipe", "features": "feature", "usecases": "usecase", "platform": "platform", "reference": "reference"}`、`STATUSES`、`OSES = ("mac", "windows")`、`REQUIRED = ("id", "title", "kind", "tags", "os", "premiere", "status", "summary")`
  - `load(knowledge_dir, notes_dir=None) -> list[tuple[dict, str]]`（dict の鍵は REQUIRED ＋ `parts` `related` `path` `source`）
  - `build_index(knowledge_dir) -> list[dict]`、`index_text(entries) -> str`
  - `load_synonyms(knowledge_dir) -> list[list[str]]`
  - `search(items, query, synonyms, os_name=None, kind=None, include_superseded=False, limit=5) -> list[tuple[float, dict]]`
  - `check_all(knowledge_dir, parts_dir) -> list[str]`（問題の文の一覧。空なら合格）
  - `write_note(notes_dir, title, tags, kind, oses, body, now=None) -> Path`
- 知識の 1 件の書き方（全 Task 共通）:

```
---
id: ui-flex-rows-collapse            # 英小文字・数字・ハイフン。ファイル名と同じ
title: 一覧の行が中身より低く潰れる
kind: usecase                        # core / recipe / feature / usecase / platform / reference（置き場所と一致）
tags: [画面, CSS, flex, 一覧]
os: [mac, windows]
premiere: ">=25.6"
status: verified                     # verified / partial / unverified / superseded
summary: UXP の flex の子は中身より小さく潰れる。一覧の行に flex: 0 0 auto を付ける
parts: [ui-kit]                      # 任意。関係する部品
related: [ui-sp-button-inactive]     # 任意。関係する知識の id
---
本文（種類ごとの型は Task 24〜27）
```

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_kb.py`:

```python
import json
import unittest
from pathlib import Path

from helpers import run_script, temp_dir

import kb
from lib import frontmatter as fm


def entry(kind_folder, **kw):
    data = {"id": kw["id"], "title": kw["title"], "kind": kb.FOLDER_KIND[kind_folder], "tags": kw.get("tags", []),
            "os": kw.get("os", ["mac", "windows"]), "premiere": ">=25.6", "status": kw.get("status", "verified"),
            "summary": kw.get("summary", kw["title"])}
    if "related" in kw:
        data["related"] = kw["related"]
    if "parts" in kw:
        data["parts"] = kw["parts"]
    return fm.dump(data) + "\n" + kw.get("body", "本文の説明。" * 10) + "\n"


class KbTests(unittest.TestCase):
    def setUp(self):
        self.k = temp_dir() / "knowledge"
        self.parts = self.k.parent / "parts"
        (self.parts / "ui-kit").mkdir(parents=True)
        (self.parts / "ui-kit" / "part.json").write_text("{}", encoding="utf-8")
        for folder in kb.FOLDER_KIND:
            (self.k / folder).mkdir(parents=True)
        self.write("usecases", id="ui-flex-rows-collapse", title="一覧の行が中身より低く潰れる", tags=["画面", "CSS", "flex"],
                   parts=["ui-kit"], related=["core-transactions"])
        self.write("core", id="core-transactions", title="取引の作法", tags=["取引", "undo", "Action"])
        self.write("features", id="feat-cutsrt-cut", title="無音カットの作り", tags=["カット", "無音", "XML"], os=["mac", "windows"])
        self.write("usecases", id="win-cp932", title="Windows で文字化けして止まる", tags=["Windows", "文字コード"], os=["windows"])
        self.write("usecases", id="old-claim", title="古い主張（クリップの分割はできない）", tags=["カット"], status="superseded")
        (self.k / "synonyms.json").write_text(json.dumps({"groups": [["カット", "切る", "分割", "razor"], ["取り消し", "undo"]]}, ensure_ascii=False), encoding="utf-8")
        (self.k / "index.json").write_text(kb.index_text(kb.build_index(self.k)), encoding="utf-8")

    def write(self, folder, **kw):
        (self.k / folder / f"{kw['id']}.md").write_text(entry(folder, **kw), encoding="utf-8")

    def search(self, q, **kw):
        return [e["id"] for _, e in kb.search(kb.load(self.k), q, kb.load_synonyms(self.k), **kw)]

    def test_title_and_tags_rank_first(self):
        self.assertEqual(self.search("一覧 潰れる")[0], "ui-flex-rows-collapse")

    def test_synonyms_expand(self):
        self.assertEqual(self.search("分割したい")[0], "feat-cutsrt-cut")
        self.assertIn("core-transactions", self.search("取り消し"))

    def test_os_filter_and_superseded(self):
        self.assertNotIn("win-cp932", self.search("文字化け", os_name="mac"))
        self.assertIn("win-cp932", self.search("文字化け", os_name="windows"))
        self.assertNotIn("old-claim", self.search("カット"))
        self.assertIn("old-claim", self.search("カット", include_superseded=True))

    def test_check_passes_then_catches_problems(self):
        self.assertEqual(kb.check_all(self.k, self.parts), [])
        self.write("usecases", id="dup", title="重複", tags=["a"], status="maybe", related=["nothing"])
        (self.k / "usecases" / "dup2.md").write_text(entry("usecases", id="dup", title="同じ id", tags=["b"]), encoding="utf-8")
        problems = "\n".join(kb.check_all(self.k, self.parts))
        self.assertIn("status は", problems)
        self.assertIn("related の nothing がありません", problems)
        self.assertIn("重複", problems)
        self.assertIn("ファイル名と id が違います", problems)
        self.assertIn("index.json が古いです", problems)

    def test_kind_must_match_folder(self):
        text = entry("core", id="misplaced", title="置き場所が違う", tags=["x"]).replace("kind: core", "kind: recipe")
        (self.k / "core" / "misplaced.md").write_text(text, encoding="utf-8")
        self.assertTrue(any("kind が置き場所と違います" in p for p in kb.check_all(self.k, self.parts)))

    def test_notes_are_searchable(self):
        notes = self.k.parent / "notes"
        path = kb.write_note(notes, "ズームのキーが 1 コマずれる", ["キーフレーム", "ズーム"], "usecase", ["mac"], "入点を足し忘れていた。")
        self.assertTrue(path.exists())
        ids = [e["id"] for _, e in kb.search(kb.load(self.k, notes), "ズーム", kb.load_synonyms(self.k))]
        self.assertTrue(ids[0].startswith("note-"))

    def test_cli_search_json_and_cp932(self):
        proc = run_script("kb.py", "--knowledge", str(self.k), "--notes", str(self.k.parent / "none"),
                          "search", "一覧", "--json", env={"PYTHONIOENCODING": "cp932"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)[0]["id"], "ui-flex-rows-collapse")

    def test_cli_show_and_list(self):
        proc = run_script("kb.py", "--knowledge", str(self.k), "show", "core-transactions")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("取引の作法", proc.stdout)
        proc = run_script("kb.py", "--knowledge", str(self.k), "list", "--brief")
        self.assertIn("feat-cutsrt-cut", proc.stdout)
        proc = run_script("kb.py", "--knowledge", str(self.k), "show", "nope")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_kb.py' -v`
Expected: FAIL（`No module named 'kb'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/kb.py`:

```python
#!/usr/bin/env python3
"""知識の棚を引く道具。

  kb.py search <言葉...> [--limit 5] [--os mac|windows] [--kind K] [--include-superseded] [--json]
  kb.py show <id>
  kb.py list [--kind K] [--os X] [--status S] [--brief] [--json]
  kb.py build                 index.json を作り直す
  kb.py check                 先頭項目・id の重複・関係の切れ・索引の古さを調べる（問題があれば終了コード 1）
  kb.py note --title T --tags a,b [--kind usecase] [--os mac,windows] (--body TEXT | --body-file F)

検索は機械的な一致（題・タグ・要約・本文）。結果が薄いときは list --brief を読み、意味で選ぶこと。
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, frontmatter, fsutil, osinfo  # noqa: E402

SKILL_DIR = HERE.parent
KNOWLEDGE = SKILL_DIR / "knowledge"
PARTS = SKILL_DIR / "parts"
FOLDER_KIND = {"core": "core", "recipes": "recipe", "features": "feature", "usecases": "usecase",
               "platform": "platform", "reference": "reference"}
STATUSES = ("verified", "partial", "unverified", "superseded")
OSES = ("mac", "windows")
REQUIRED = ("id", "title", "kind", "tags", "os", "premiere", "status", "summary")
STATUS_WEIGHT = {"verified": 1.0, "partial": 0.9, "unverified": 0.8, "superseded": 0.5}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SPLIT_RE = re.compile(r"[\s、。・,，/／「」『』（）()]+")


def norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def _as_list(v) -> List[str]:
    if isinstance(v, list):
        return v
    return [v] if v else []


def read_entry(path: Path, base: Path, source: str) -> Tuple[Dict, str]:
    data, body = frontmatter.parse(path.read_text(encoding="utf-8"))
    entry = {k: data.get(k, "") for k in REQUIRED}
    entry["tags"] = _as_list(entry["tags"])
    entry["os"] = _as_list(entry["os"])
    entry["parts"] = _as_list(data.get("parts", []))
    entry["related"] = _as_list(data.get("related", []))
    entry["path"] = path.relative_to(base).as_posix() if source == "kit" else str(path)
    entry["source"] = source
    return entry, body


def load(knowledge_dir: Path = KNOWLEDGE, notes_dir: Optional[Path] = None) -> List[Tuple[Dict, str]]:
    items: List[Tuple[Dict, str]] = []
    for folder in FOLDER_KIND:
        d = Path(knowledge_dir) / folder
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                items.append(read_entry(p, Path(knowledge_dir), "kit"))
    if notes_dir and Path(notes_dir).is_dir():
        for p in sorted(Path(notes_dir).glob("*.md")):
            try:
                items.append(read_entry(p, Path(notes_dir), "note"))
            except frontmatter.FrontmatterError:
                continue
    return items


def build_index(knowledge_dir: Path = KNOWLEDGE) -> List[Dict]:
    return sorted((e for e, _ in load(knowledge_dir)), key=lambda e: (e["kind"], e["id"]))


def index_text(entries: List[Dict]) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=1) + "\n"


def load_synonyms(knowledge_dir: Path = KNOWLEDGE) -> List[List[str]]:
    p = Path(knowledge_dir) / "synonyms.json"
    if not p.exists():
        return []
    groups = json.loads(p.read_text(encoding="utf-8")).get("groups", [])
    return [[norm(w) for w in g] for g in groups]


def query_terms(query: str, synonyms: List[List[str]]) -> List[List[str]]:
    """言葉ごとに、同じ意味の言葉をまとめた組を返す（「無音カット」のような複合語は両方の組に広げる）。"""
    groups = []
    for raw in SPLIT_RE.split(norm(query)):
        if not raw:
            continue
        alts = {raw}
        for g in synonyms:
            if any(raw == w or (len(w) >= 2 and w in raw) for w in g):
                alts.update(g)
        groups.append(sorted(alts))
    return groups


def _has_cjk(s: str) -> bool:
    return any("\u3040" <= ch <= "\u9fff" for ch in s)


def _score(entry: Dict, body_n: str, alts: List[str]) -> float:
    title = norm(entry["title"])
    summary = norm(entry["summary"])
    tags = [norm(t) for t in entry["tags"]]
    best = 0.0
    for t in alts:
        s = 0.0
        if t in title:
            s += 6
        if any(t == tag for tag in tags):
            s += 6
        elif any(len(tag) >= 2 and (t in tag or tag in t) for tag in tags):
            s += 3
        if t in summary:
            s += 3
        if t in entry["id"]:
            s += 2
        s += min(body_n.count(t), 5) * 0.5
        if s == 0 and _has_cjk(t) and len(t) >= 3:
            grams = {t[i:i + 2] for i in range(len(t) - 1)}
            s += sum(0.5 for g in grams if g in title or g in summary)
        best = max(best, s)
    return best


def search(items, query: str, synonyms, os_name: Optional[str] = None, kind: Optional[str] = None,
           include_superseded: bool = False, limit: int = 5) -> List[Tuple[float, Dict]]:
    groups = query_terms(query, synonyms)
    results = []
    for entry, body in items:
        if entry["status"] == "superseded" and not include_superseded:
            continue
        if os_name and entry["os"] and os_name not in entry["os"]:
            continue
        if kind and entry["kind"] != kind:
            continue
        body_n = norm(body)
        total = sum(_score(entry, body_n, alts) for alts in groups)
        if total <= 0:
            continue
        results.append((round(total * STATUS_WEIGHT.get(entry["status"], 0.8), 2), entry))
    results.sort(key=lambda r: (-r[0], r[1]["id"]))
    return results[:limit]


def check_all(knowledge_dir: Path = KNOWLEDGE, parts_dir: Path = PARTS) -> List[str]:
    knowledge_dir, parts_dir = Path(knowledge_dir), Path(parts_dir)
    problems: List[str] = []
    seen: Dict[str, str] = {}
    items = []
    for folder, kind in FOLDER_KIND.items():
        d = knowledge_dir / folder
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            rel = p.relative_to(knowledge_dir).as_posix()
            try:
                entry, body = read_entry(p, knowledge_dir, "kit")
            except frontmatter.FrontmatterError as e:
                problems.append(f"{rel}: {e}")
                continue
            items.append(entry)
            for k in REQUIRED:
                if not entry[k]:
                    problems.append(f"{rel}: 先頭項目「{k}」がありません")
            if entry["id"] and not ID_RE.match(entry["id"]):
                problems.append(f"{rel}: id は英小文字・数字・ハイフンだけにします")
            if entry["id"] and p.stem != entry["id"]:
                problems.append(f"{rel}: ファイル名と id が違います（{entry['id']}）")
            if entry["kind"] and entry["kind"] != kind:
                problems.append(f"{rel}: kind が置き場所と違います（{folder}/ は {kind}）")
            if entry["status"] and entry["status"] not in STATUSES:
                problems.append(f"{rel}: status は {' / '.join(STATUSES)} のどれかです（{entry['status']}）")
            for o in entry["os"]:
                if o not in OSES:
                    problems.append(f"{rel}: os は mac / windows だけです（{o}）")
            if entry["id"] in seen:
                problems.append(f"{rel}: id が {seen[entry['id']]} と重複しています")
            seen.setdefault(entry["id"], rel)
            if len(body.strip()) < 40:
                problems.append(f"{rel}: 本文が短すぎます（40 文字未満）")
    for entry in items:
        for r in entry["related"]:
            if r not in seen:
                problems.append(f"{entry['path']}: related の {r} がありません")
        for part in entry["parts"]:
            if not (parts_dir / part / "part.json").exists():
                problems.append(f"{entry['path']}: parts の {part} がありません")
    index_path = knowledge_dir / "index.json"
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index_text(build_index(knowledge_dir)):
        problems.append("index.json が古いです。kb.py build を実行してください")
    return problems


def write_note(notes_dir: Path, title: str, tags: List[str], kind: str, oses: List[str], body: str,
               now: Optional[datetime.datetime] = None) -> Path:
    now = now or datetime.datetime.now()
    nid = "note-" + now.strftime("%Y%m%d-%H%M%S")
    first = body.strip().splitlines()[0][:80] if body.strip() else title
    data = {"id": nid, "title": title, "kind": kind, "tags": tags, "os": oses, "premiere": ">=25.6",
            "status": "unverified", "summary": first}
    path = Path(notes_dir) / f"{nid}.md"
    if path.exists():
        raise FileExistsError(f"同じ名前のノートがあります: {path}")
    fsutil.write_text(path, frontmatter.dump(data) + "\n" + body.strip() + "\n")
    return path


def _print_results(results) -> None:
    if not results:
        print("見つかりませんでした。言葉を変えるか、kb.py list --brief を読んで意味で選んでください。")
        return
    for n, (score, e) in enumerate(results, 1):
        print(f"{n}. [{e['kind']}/{e['status']}] {e['id']} — {e['title']}（{score}）")
        print(f"    {('knowledge/' + e['path']) if e['source'] == 'kit' else e['path']}")
        print(f"    要約: {e['summary']}")


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="知識の棚を引く")
    ap.add_argument("--knowledge", default=str(KNOWLEDGE))
    ap.add_argument("--notes", default=None)
    ap.add_argument("--parts", default=str(PARTS))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("words", nargs="+")
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--os", choices=OSES)
    s.add_argument("--kind", choices=sorted(FOLDER_KIND.values()))
    s.add_argument("--include-superseded", action="store_true")
    s.add_argument("--json", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("id")
    ls = sub.add_parser("list")
    ls.add_argument("--kind", choices=sorted(FOLDER_KIND.values()))
    ls.add_argument("--os", choices=OSES)
    ls.add_argument("--status", choices=STATUSES)
    ls.add_argument("--brief", action="store_true")
    ls.add_argument("--json", action="store_true")
    sub.add_parser("build")
    sub.add_parser("check")
    nt = sub.add_parser("note")
    nt.add_argument("--title", required=True)
    nt.add_argument("--tags", required=True)
    nt.add_argument("--kind", default="usecase", choices=sorted(FOLDER_KIND.values()))
    nt.add_argument("--os", default="mac,windows")
    group = nt.add_mutually_exclusive_group(required=True)
    group.add_argument("--body")
    group.add_argument("--body-file")
    args = ap.parse_args(argv)

    knowledge = Path(args.knowledge)
    notes = Path(args.notes) if args.notes else osinfo.notes_dir(os.environ, osinfo.detect_os())

    if args.cmd == "build":
        fsutil.write_text(knowledge / "index.json", index_text(build_index(knowledge)))
        print(f"index.json を作りました（{len(build_index(knowledge))} 件）")
        return 0
    if args.cmd == "check":
        problems = check_all(knowledge, Path(args.parts))
        for p in problems:
            print("・" + p)
        print("問題はありません。" if not problems else f"{len(problems)} 件の問題があります。")
        return 1 if problems else 0
    if args.cmd == "note":
        body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
        path = write_note(notes, args.title, [t.strip() for t in args.tags.split(",") if t.strip()], args.kind,
                          [o.strip() for o in args.os.split(",") if o.strip()], body)
        print(f"手元のノートに残しました: {path}")
        return 0

    items = load(knowledge, notes)
    if args.cmd == "search":
        results = search(items, " ".join(args.words), load_synonyms(knowledge), os_name=args.os, kind=args.kind,
                         include_superseded=args.include_superseded, limit=args.limit)
        if args.json:
            cli.print_json([{"score": score, **e} for score, e in results])
        else:
            _print_results(results)
        return 0
    if args.cmd == "show":
        for e, body in items:
            if e["id"] == args.id:
                path = knowledge / e["path"] if e["source"] == "kit" else Path(e["path"])
                print(f"# {path}")
                print(path.read_text(encoding="utf-8"))
                return 0
        print(f"id が {args.id} の知識はありません。kb.py search で探してください。")
        return 1
    if args.cmd == "list":
        rows = [e for e, _ in items
                if (not args.kind or e["kind"] == args.kind)
                and (not args.os or not e["os"] or args.os in e["os"])
                and (not args.status or e["status"] == args.status)]
        if args.json:
            cli.print_json(rows)
        else:
            for e in rows:
                if args.brief:
                    print(f"{e['id']} | {e['kind']} | {e['status']} | {e['title']} — {e['summary']}")
                else:
                    print(f"{e['id']}\t{e['kind']}\t{e['status']}\t{e['title']}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/knowledge/synonyms.json`:

```json
{
  "groups": [
    ["カット", "切る", "分割", "レーザー", "razor", "編集点"],
    ["テロップ", "字幕", "キャプション", "caption", "srt", "文字"],
    ["無音", "silence", "間", "ジェットカット"],
    ["キーフレーム", "キー", "keyframe", "アニメ", "動き", "モーション"],
    ["ズーム", "拡大", "スケール", "scale", "zoom"],
    ["書き出し", "エクスポート", "export", "レンダリング"],
    ["読み込み", "インポート", "import", "取り込み"],
    ["マーカー", "marker", "チャプター"],
    ["エフェクト", "効果", "effect"],
    ["トランジション", "transition", "つなぎ"],
    ["ショートカット", "コマンド", "command", "キーボード"],
    ["サーバー", "server", "常駐", "バックグラウンド"],
    ["文字起こし", "whisper", "音声認識", "transcribe"],
    ["話者", "スピーカー", "speaker", "話している人"],
    ["顔", "face", "追従", "トラッキング"],
    ["windows", "ウィンドウズ", "win"],
    ["mac", "マック", "macos"],
    ["配布", "配る", "ccx", "パッケージ", "インストール", "導入"],
    ["エラー", "失敗", "動かない", "表示されない", "読み込めない", "出ない"],
    ["パネル", "画面", "ui", "ボタン"],
    ["mogrt", "モーショングラフィックス", "グラフィック", "テキストスタイル", "prtextstyle"],
    ["xml", "fcp", "final cut"],
    ["fps", "フレームレート", "timebase", "ntsc"],
    ["取り消し", "undo", "cmd+z", "元に戻す"],
    ["ai", "llm", "claude", "codex", "gemini", "jev"],
    ["cep", "extendscript", "qe", "jsx"],
    ["再生", "プレビュー", "play"],
    ["ビン", "bin", "フォルダ"],
    ["選択", "選んだ", "selection"],
    ["版", "バージョン", "version", "minversion"],
    ["鍵", "api キー", "トークン", "キーチェーン"],
    ["mcp", "エージェント", "agent"]
  ]
}
```

空のフォルダを git に残すため、各フォルダに `.gitkeep` を置く（Task 24〜27 で中身が入ったら消してよい）。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_kb.py' -v`
Expected: PASS（9 件）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: kb.py（知識の検索・表示・索引・検査・手元のノート）と同義語の表

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: check.py の土台・manifest の検査・API の最低版の表

**Files:**
- Create: `SKILL/scripts/check.py`
- Create: `SKILL/scripts/lib/checks/__init__.py`
- Create: `SKILL/scripts/lib/checks/manifest_rules.py`
- Create: `SKILL/knowledge/reference/api-since.json`
- Test: `tests/check_helpers.py`、`tests/test_check_manifest.py`

**Interfaces:**
- Consumes: `lib.manifest.load / version_tuple`、`lib.cli`
- Produces（`lib.checks`）:
  - `@dataclass Finding(rule: str, severity: str, file: str, line: int, message: str, why: str, fix: str)`（severity は `"error"` か `"warn"`。file はプロジェクトから見た posix の相対パス。line は 1 始まり、0 はファイル全体）
  - `class Project(root: Path, kit_dir: Path)`: 属性 `root` `kit_dir` `manifest`（dict か None）`manifest_error`（str か None）、メソッド `files(*suffixes) -> list[Path]`、`panel_files(*suffixes) -> list[Path]`（`server/` `cep/` `tests/` `packaging/` を除く）、`text(path) -> str`、`rel(path) -> str`、`min_version() -> str`、`permissions() -> dict`、`feature_flags() -> dict`、`line_of(path, needle) -> int`
  - `rule(fn)`（デコレーター。検査の関数 `fn(project) -> list[Finding]` を登録する）
  - `run_all(root, kit_dir) -> list[Finding]`（誤りが先。`ppm-ignore: 規則名` の注釈がある行は外す）
- Produces（`check.py`）: `main(argv=None) -> int`（誤りがあれば 1、manifest.json が無ければ 2、それ以外 0）。`--json` は `{"ok", "errors", "warnings", "findings": [...]}`、`--strict` は注意も誤りとして数える
- 規則の名前: `M`＝manifest、`J`＝JS、`C`＝CSS、`H`＝HTML、`P`＝配布、`W`＝Windows、`Y`＝Python
- Produces（`tests/check_helpers.py`）: `GOOD_MANIFEST`（dict）、`make_project(files: dict[str, str|bytes|dict], manifest: dict | None = None) -> Path`、`findings(root) -> list`、`rules(root) -> set[str]`

- [ ] **Step 1: 失敗するテストを書く**

`tests/check_helpers.py`:

```python
"""check.py のテスト用に、小さなプラグインのフォルダを作る。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from helpers import SKILL, temp_dir
from lib import checks

GOOD_MANIFEST = {
    "manifestVersion": 5,
    "id": "com.example.test",
    "name": "Test Plugin",
    "version": "0.1.0",
    "main": "index.html",
    "host": {"app": "premierepro", "minVersion": "25.6", "data": {"apiVersion": 2, "loadEvent": "startup"}},
    "entrypoints": [{"type": "panel", "id": "mainPanel", "label": {"default": "テスト"}}],
    "icons": [{"width": 24, "height": 24, "path": "icons/icon.png", "scale": [1, 2], "theme": ["all"], "species": "generic"}],
    "requiredPermissions": {"localFileSystem": "plugin"},
}

GOOD_HTML = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><title>T</title>
<link rel="stylesheet" href="panel.css" /></head>
<body><button id="run" type="button">実行</button><script src="index.js"></script></body></html>
"""

GOOD_JS = """let ppro = null;
try { ppro = require("premierepro"); } catch (e) {}
function boot() {}
if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", boot); } else { boot(); }
"""


def make_project(files=None, manifest=None) -> Path:
    root = temp_dir()
    data = copy.deepcopy(GOOD_MANIFEST) if manifest is None else manifest
    base = {"index.html": GOOD_HTML, "index.js": GOOD_JS, "panel.css": "title { display: none; }\n",
            "icons/icon.png": b"\x89PNG\r\n\x1a\n", "build_info.json": {"name": "Test Plugin", "version": "0.1.0"},
            ".ppm/project.json": {"name": "Test Plugin", "pluginId": "com.example.test"}}
    base.update(files or {})
    if data is not None:
        base.setdefault("manifest.json", data)
    for rel, content in base.items():
        if content is None:
            continue
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        elif isinstance(content, (dict, list)):
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")
    return root


def findings(root: Path):
    return checks.run_all(root, SKILL)


def rules(root: Path):
    return {f.rule for f in findings(root)}
```

`tests/test_check_manifest.py`:

```python
import copy
import json
import unittest

from check_helpers import GOOD_MANIFEST, findings, make_project, rules
from helpers import run_script


def m(**changes):
    data = copy.deepcopy(GOOD_MANIFEST)
    for k, v in changes.items():
        data[k] = v
    return data


class ManifestRuleTests(unittest.TestCase):
    def test_good_project_has_no_errors(self):
        errors = [f for f in findings(make_project()) if f.severity == "error"]
        self.assertEqual(errors, [], errors)

    def test_broken_json_is_one_clear_error(self):
        # 末尾のカンマ。JSON の読み手は、閉じかっこのある 3 行目で気づく
        root = make_project({"manifest.json": '{\n "id": "a",\n}\n'})
        fs = findings(root)
        self.assertEqual([f.rule for f in fs if f.severity == "error"], ["M001"])
        self.assertIn("3 行目", fs[0].message + fs[0].why)

    def test_required_keys(self):
        data = m()
        del data["entrypoints"]
        self.assertIn("M002", rules(make_project(manifest=data)))

    def test_manifest_version(self):
        self.assertIn("M003", rules(make_project(manifest=m(manifestVersion=4))))
        warn = [f for f in findings(make_project(manifest=m(manifestVersion=6))) if f.rule == "M003"]
        self.assertEqual(warn[0].severity, "warn")

    def test_version_shape(self):
        self.assertIn("M004", rules(make_project(manifest=m(version="1.0"))))

    def test_host_must_be_object_for_premierepro(self):
        self.assertIn("M005", rules(make_project(manifest=m(host=[{"app": "premierepro", "minVersion": "25.6"}]))))
        self.assertIn("M005", rules(make_project(manifest=m(host={"app": "PPRO", "minVersion": "25.6"}))))

    def test_old_min_version_warns(self):
        f = [x for x in findings(make_project(manifest=m(host={"app": "premierepro", "minVersion": "25.2"}))) if x.rule == "M006"]
        self.assertEqual(f[0].severity, "warn")

    def test_entrypoints_are_unique_and_labeled(self):
        eps = [{"type": "panel", "id": "a", "label": {"default": "A"}}, {"type": "command", "id": "a"}]
        self.assertIn("M007", rules(make_project(manifest=m(entrypoints=eps))))

    def test_icon_file_must_exist(self):
        root = make_project({"icons/icon.png": None})
        (root / "icons" / "icon.png").unlink(missing_ok=True)
        self.assertIn("M008", rules(root))

    def test_non_ascii_name_warns(self):
        self.assertIn("M009", rules(make_project(manifest=m(name="テロップ"))))

    def test_main_file_must_exist(self):
        self.assertIn("M013", rules(make_project(manifest=m(main="missing.html"))))

    def test_cli_exit_codes_and_json(self):
        good = make_project()
        proc = run_script("check.py", str(good), "--json", env={"PYTHONIOENCODING": "cp932"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["ok"])
        bad = make_project(manifest=m(version="x"))
        self.assertEqual(run_script("check.py", str(bad)).returncode, 1)
        empty = make_project(manifest=None)
        (empty / "manifest.json").unlink(missing_ok=True)
        self.assertEqual(run_script("check.py", str(empty)).returncode, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_check_manifest.py' -v`
Expected: FAIL（`cannot import name 'checks'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/lib/checks/__init__.py`:

```python
"""機械の検査の土台。規則は各モジュールの @rule で登録する。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .. import manifest as manifest_lib

SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".ppm"}
NON_PANEL_DIRS = {"server", "cep", "tests", "packaging"}


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    why: str
    fix: str


class Project:
    def __init__(self, root: Path, kit_dir: Path):
        self.root = Path(root)
        self.kit_dir = Path(kit_dir)
        self.manifest: Optional[dict] = None
        self.manifest_error: Optional[str] = None
        self._texts: Dict[Path, str] = {}
        try:
            self.manifest = manifest_lib.load(self.root / "manifest.json")
        except manifest_lib.ManifestError as e:
            self.manifest_error = str(e)

    def files(self, *suffixes: str) -> List[Path]:
        out = []
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            parts = p.relative_to(self.root).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            if suffixes and p.suffix.lower() not in suffixes:
                continue
            out.append(p)
        return out

    def panel_files(self, *suffixes: str) -> List[Path]:
        return [p for p in self.files(*suffixes) if p.relative_to(self.root).parts[0] not in NON_PANEL_DIRS]

    def text(self, path: Path) -> str:
        path = Path(path)
        if path not in self._texts:
            try:
                self._texts[path] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._texts[path] = ""
        return self._texts[path]

    def rel(self, path: Path) -> str:
        return Path(path).relative_to(self.root).as_posix()

    def min_version(self) -> str:
        return manifest_lib.min_version(self.manifest or {})

    def permissions(self) -> dict:
        return (self.manifest or {}).get("requiredPermissions") or {}

    def feature_flags(self) -> dict:
        return (self.manifest or {}).get("featureFlags") or {}

    def line_of(self, path: Path, needle: str) -> int:
        for i, line in enumerate(self.text(path).splitlines(), 1):
            if needle in line:
                return i
        return 0


RULES: List[Callable[[Project], List[Finding]]] = []


def rule(fn):
    RULES.append(fn)
    return fn


_IGNORE_RE = re.compile(r"ppm-ignore:\s*([A-Z][0-9]{3}(?:\s*,\s*[A-Z][0-9]{3})*)")


def _suppressed(lines: List[str], line_no: int, rule_name: str) -> bool:
    for ln in (line_no, line_no - 1):
        if 1 <= ln <= len(lines):
            m = _IGNORE_RE.search(lines[ln - 1])
            if m and rule_name in [x.strip() for x in m.group(1).split(",")]:
                return True
    return False


def run_all(root: Path, kit_dir: Path) -> List[Finding]:
    from . import manifest_rules  # noqa: F401  （登録のための import。Task 7・8 で残りを足す）
    project = Project(root, kit_dir)
    found: List[Finding] = []
    for fn in RULES:
        found.extend(fn(project))
    out = []
    for f in found:
        if f.line and f.file:
            lines = project.text(project.root / f.file).splitlines()
            if _suppressed(lines, f.line, f.rule):
                continue
        out.append(f)
    return sorted(out, key=lambda f: (f.severity != "error", f.file, f.line, f.rule))
```

`SKILL/scripts/lib/checks/manifest_rules.py`:

```python
"""manifest.json の検査（M001〜M009、M013）。M010〜M012 は使い方を見るので js_rules.py にある。"""
from __future__ import annotations

import re
from typing import List

from .. import manifest as manifest_lib
from . import Finding, Project, rule

REQUIRED_KEYS = ("manifestVersion", "id", "name", "version", "host", "entrypoints")


def _f(rule_name, severity, message, why, fix, line=0):
    return Finding(rule_name, severity, "manifest.json", line, message, why, fix)


@rule
def manifest_rules(p: Project) -> List[Finding]:
    if p.manifest_error:
        return [_f("M001", "error", "manifest.json が読めません", p.manifest_error,
                   "書かれている行を直してください。JSON にはコメント（// や /* */）と末尾のカンマは書けません")]
    if p.manifest is None:
        return []
    m = p.manifest
    out: List[Finding] = []
    for key in REQUIRED_KEYS:
        if key not in m:
            out.append(_f("M002", "error", f"manifest.json に「{key}」がありません",
                          "Premiere がプラグインとして読み込めません", f"雛形の manifest.json と同じ形で「{key}」を書いてください"))
    mv = m.get("manifestVersion")
    if mv is not None and mv != 5:
        if mv == 6:
            out.append(_f("M003", "warn", "manifestVersion が 6 です", "6 は C++ を使う Hybrid プラグイン用です",
                          "普通のパネルなら 5 にしてください"))
        else:
            out.append(_f("M003", "error", f"manifestVersion が {mv} です", "Premiere の UXP は 5 を読みます", "5 にしてください"))
    version = m.get("version")
    if version is not None and not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        out.append(_f("M004", "error", f"version が「{version}」です", "版数は 1.2.3 のように数字 3 つで書く決まりです",
                      "例: 0.1.0"))
    host = m.get("host")
    if host is not None:
        if isinstance(host, list):
            out.append(_f("M005", "error", "host が配列になっています", "配列は開発の確かめ専用で、配布や Marketplace の検証で落ちます",
                          '{"app": "premierepro", "minVersion": "25.6"} の形にしてください'))
        elif isinstance(host, dict):
            if host.get("app") != "premierepro":
                out.append(_f("M005", "error", f"host.app が「{host.get('app')}」です", "Premiere は小文字の premierepro です",
                              '"app": "premierepro" にしてください'))
            mvv = host.get("minVersion")
            try:
                if manifest_lib.version_tuple(str(mvv)) < (25, 6, 0):
                    out.append(_f("M006", "warn", f"minVersion が {mvv} です", "UXP の正式版は Premiere 25.6 からです（それより前はベータ版だけ）",
                                  "特に理由が無ければ 25.6 以上にしてください"))
            except ValueError:
                out.append(_f("M005", "error", f"minVersion「{mvv}」が版数の形ではありません", "読み込める版を決められません",
                              "例: 25.6 や 26.2"))
    eps = m.get("entrypoints")
    if isinstance(eps, list):
        seen = set()
        for e in eps:
            eid = e.get("id")
            if e.get("type") not in ("panel", "command"):
                out.append(_f("M007", "error", f"入口「{eid}」の type が「{e.get('type')}」です", "panel か command だけが使えます", "どちらかにしてください"))
            if eid in seen:
                out.append(_f("M007", "error", f"入口の id「{eid}」が重複しています", "どちらかが無視されます", "id を別の名前にしてください"))
            seen.add(eid)
            label = e.get("label")
            if not (isinstance(label, dict) and label.get("default")) and not isinstance(label, str):
                out.append(_f("M007", "error", f"入口「{eid}」に label がありません", "メニューに名前が出ません",
                              '"label": {"default": "表示名"} を書いてください'))
    for icon in m.get("icons") or []:
        path = icon.get("path")
        if path and not (p.root / path).exists():
            out.append(_f("M008", "error", f"アイコン「{path}」がありません", "読み込みで失敗したり、配布の検査で落ちたりします",
                          "そのパスに PNG を置くか、icons の行を直してください"))
    name = m.get("name")
    if isinstance(name, str) and any(ord(c) > 127 for c in name):
        out.append(_f("M009", "warn", "name に英数字以外が入っています", "Marketplace の条件は英数字だけで、文字化けの原因にもなります",
                      "name は英数字にし、日本語はパネルの label に書いてください"))
    main = m.get("main") or "main.js"
    if not (p.root / main).exists():
        out.append(_f("M013", "error", f"入口のファイル「{main}」がありません", "パネルが空のまま開きます",
                      "manifest の main を index.html などの実在するファイルにしてください"))
    return out
```

`SKILL/scripts/check.py`:

```python
#!/usr/bin/env python3
"""作ったプラグインを機械で検査する。過去に実機で起きた失敗を、実機に入れる前に止めるための門。

使い方:
  Mac:     python3 <このスキル>/scripts/check.py <プラグインのフォルダ> [--json] [--strict]
  Windows: py -3 <このスキル>\\scripts\\check.py <プラグインのフォルダ> [--json] [--strict]
誤りが 1 件でもあれば終了コード 1。誤りは必ず直す。注意は理由を読んで判断する。
1 行だけ規則を外すときは、その行か直前の行に「ppm-ignore: J010」のような注釈を書く。
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import checks, cli  # noqa: E402

SKILL_DIR = HERE.parent


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="プラグインを機械で検査する")
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.project).expanduser()
    if not (root / "manifest.json").exists():
        print(f"manifest.json が見つかりません: {root}\nプラグインのフォルダ（manifest.json がある所）を指定してください。")
        return 2
    found = checks.run_all(root, SKILL_DIR)
    errors = [f for f in found if f.severity == "error" or (args.strict and f.severity == "warn")]
    if args.json:
        cli.print_json({"ok": not errors, "errors": len(errors), "warnings": len(found) - len(errors),
                        "findings": [asdict(f) for f in found]})
    else:
        for file, group in groupby(sorted(found, key=lambda f: (f.file, f.line)), key=lambda f: f.file):
            print(f"■ {file}")
            for f in group:
                kind = "誤り" if f.severity == "error" or args.strict else "注意"
                where = f"{f.line} 行目" if f.line else "全体"
                print(f"  [{kind}] {where}（{f.rule}）: {f.message}")
                print(f"        なぜ: {f.why}")
                print(f"        直し方: {f.fix}")
        print(f"\n誤り {len(errors)} 件・注意 {len(found) - len(errors)} 件")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/knowledge/reference/api-since.json`（Task 7 の J014 が使う。値は調査 G §3.4・§3.5 と調査 A §2.3・§3.6 から）:

```json
{
  "note": "Premiere の UXP API の最低版（公式リファレンスの Since と変更履歴、2026-10-13 調査）。check.py の J014 が使う。名前が一般的すぎて誤検知するもの（setPosition・guid など）は載せない。",
  "apis": {
    "ProjectConverter": {"since": "26.2", "what": "FCP XML・OTIO・AAF の書き出し"},
    "exportAsFinalCutProXML": {"since": "26.2", "what": "ProjectConverter.exportAsFinalCutProXML"},
    "exportAsOpenTimelineIO": {"since": "26.2", "what": "ProjectConverter.exportAsOpenTimelineIO"},
    "getVideoFrameRate": {"since": "26.2", "what": "SequenceSettings.getVideoFrameRate()"},
    "isProject": {"since": "26.2", "what": "Project.isProject"},
    "closeSequence": {"since": "26.2", "what": "Project.closeSequence"},
    "createSubClipAction": {"since": "26.3", "what": "ClipProjectItem.createSubClipAction"},
    "createSequenceWithPresetPath": {"since": "26.3", "what": "Project.createSequenceWithPresetPath"},
    "launchEncoder": {"since": "26.3", "what": "EncoderManager.launchEncoder"},
    "startBatchEncode": {"since": "26.3", "what": "EncoderManager.startBatchEncode"},
    "setEmbeddedXMPEnabled": {"since": "26.3", "what": "EncoderManager"},
    "setSidecarXMPEnabled": {"since": "26.3", "what": "EncoderManager"},
    "ObjectMaskUtils": {"since": "26.3", "what": "マスク"},
    "exportAAF": {"since": "26.3", "what": "ProjectConverter.exportAAF"},
    "querySupportedLanguages": {"since": "26.3", "what": "Transcript"},
    "hasTranscript": {"since": "26.3", "what": "Transcript"},
    "C2PAService": {"since": "26.5", "what": "コンテンツ認証"},
    "MediaManager": {"since": "26.5", "what": "メディアキャッシュ"},
    "WorkAreaUtils": {"since": "26.5", "what": "作業エリアの in/out"},
    "transcribeClipProjectItem": {"since": "26.5", "what": "Transcript"},
    "isLanguagePackAvailable": {"since": "26.5", "what": "Transcript"},
    "getBackgroundColor": {"since": "26.5", "what": "uxp.host.getBackgroundColor()"},
    "applicationPath": {"since": "26.5", "what": "uxp.host.applicationPath"},
    "createRazorTrackAction": {"since": "27.0", "beta": true, "what": "クリップの分割（27.0 ベータの公式サンプルにだけある）"},
    "createRazorAllTracksAction": {"since": "27.0", "beta": true, "what": "全トラックの分割（27.0 ベータ）"},
    "MogrtText": {"since": "27.0", "beta": true, "what": "MOGRT の文字（27.0 ベータの型定義）"},
    "MogrtComment": {"since": "27.0", "beta": true, "what": "MOGRT のコメント（27.0 ベータの型定義）"},
    "buildNumber": {"since": "27.0", "beta": true, "what": "uxp.host.buildNumber"}
  }
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_check_manifest.py' -v`
Expected: PASS（12 件）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: check.py の土台と manifest の検査、API の最低版の表

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: check.py の JS・CSS・HTML の検査

**Files:**
- Create: `SKILL/scripts/lib/jsscan.py`
- Create: `SKILL/scripts/lib/checks/js_rules.py`
- Create: `SKILL/scripts/lib/checks/css_html_rules.py`
- Modify: `SKILL/scripts/lib/checks/__init__.py`（`run_all` の import に `js_rules, css_html_rules` を足す）
- Test: `tests/test_jsscan.py`、`tests/test_check_js.py`、`tests/test_check_css_html.py`

**Interfaces:**
- Produces（`lib.jsscan`）:
  - `blank(text: str) -> str`（コメントと文字列リテラルの中身を空白に。長さと改行の位置は保つ）
  - `line_of(text: str, pos: int) -> int`
  - `match_close(clean: str, open_pos: int) -> int`（対応する閉じ括弧の位置。無ければ -1）
  - `callback_spans(clean: str, names=("lockedAccess", "executeTransaction", "transact")) -> list[tuple[int, int, str]]`（`.名前(` に渡した最初の関数の本体の範囲）
  - `builder_spans(original: str, clean: str) -> list[tuple[int, int]]`（`ppm: action-builder` の注釈の直後の関数の本体）
- 規則（severity）:

| 規則 | 重さ | 見つけるもの |
|---|---|---|
| J001 | error | 取引（lockedAccess・executeTransaction・PPM.transact）のコールバックの中の await |
| J002 | warn | 取引の外で作る create…Action（`ppm: action-builder` の関数の中は除く） |
| J003 | error | 引数の無い `getTrackItems()`（受け手の名前に sel を含むものは除く） |
| J004 | error | `new (ppro.)TrackItemSelection(` |
| J005 | error / warn | settings から `videoFrameRate` `frameRate` をプロパティで読む（error）、`videoFrameRect` `frameRect`（warn） |
| J006 | error | 相対パスの require（`require("./…")`） |
| J007 | warn | `typeof MutationObserver` の確かめが無い MutationObserver |
| J008 | error / warn | `alert(` `confirm(` `prompt(`（enableAlerts が無ければ error、あれば warn） |
| J009 | warn | executeTransaction の戻り値を見ていない |
| J010 | warn | `.ticks` の直読み（`createWithTicks` は除く） |
| J011 | error | eval・new Function（allowCodeGenerationFromStrings が無いとき） |
| J012 | warn | 起動の処理（document.readyState の判定）がファイルの後ろ 2 割より前にある |
| J013 | error | 127.0.0.1 / localhost へ接続するのに network.domains が "all" でない |
| J014 | error / warn | 使っている API の最低版が minVersion より新しい（ベータ限定は warn） |
| J015 | warn | `getMediaType()` を数値と比べている（Guid が返る） |
| M010 | warn | localFileSystem が fullAccess なのに、絶対パスのファイル操作が見当たらない |
| M011 | error / warn | 通信するのに network の権限が無い（error）／権限があるのに通信していない（warn） |
| M012 | warn | allowCodeGenerationFromStrings が true なのに eval などを使っていない |
| C001 | error | CSS の grid |
| C002 | warn | `position: fixed`（入力欄の上に重ねると透ける） |
| C004 | warn | transition・animation（効かないことがある） |
| H001 | error | index.html が読むファイル（script・link・img）が無い |
| H002 | warn | ul・ol・li（div として扱われる） |
| H003 | error | 属性に書いたイベント（onclick= など。allowCodeGenerationFromStrings が無いとき） |
| H004 | warn | `<input type="file">` `type="color"`（使えない） |
| H005 | warn | `<title>` があるのに CSS で隠していない（パネルに文字として出る） |

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jsscan.py`:

```python
import unittest

from lib import jsscan


class JsscanTests(unittest.TestCase):
    def test_blank_keeps_length_and_newlines(self):
        src = 'a = "x // y"; // comment\nb = /re{1}/g; /* c\n d */ c = `t ${1}`;\n'
        out = jsscan.blank(src)
        self.assertEqual(len(out), len(src))
        self.assertEqual(out.count("\n"), src.count("\n"))
        self.assertNotIn("comment", out)
        self.assertNotIn("x // y", out)
        self.assertIn("b =", out)

    def test_callback_spans_arrow_function_and_expression(self):
        src = "project.lockedAccess(() => {\n project.executeTransaction((ca) => { ca.addAction(x); }, 'u');\n});\nPPM.transact(p, 'l', (add) => add('a', () => t.createSetEndAction(z)));\n"
        clean = jsscan.blank(src)
        names = [name for _, _, name in jsscan.callback_spans(clean)]
        self.assertEqual(names, ["lockedAccess", "executeTransaction", "transact"])
        start, end, _ = jsscan.callback_spans(clean)[2]
        self.assertIn("createSetEndAction", clean[start:end])

    def test_builder_spans(self):
        src = "// ppm: action-builder\nfunction keyActions(add, p) {\n  add('k', () => p.createAddKeyframeAction(kf));\n}\nfunction other() {}\n"
        spans = jsscan.builder_spans(src, jsscan.blank(src))
        self.assertEqual(len(spans), 1)
        self.assertIn("createAddKeyframeAction", src[spans[0][0]:spans[0][1]])
        self.assertNotIn("other", src[spans[0][0]:spans[0][1]])


if __name__ == "__main__":
    unittest.main()
```

`tests/test_check_js.py`:

```python
import copy
import unittest

from check_helpers import GOOD_MANIFEST, findings, make_project, rules


def js(code, manifest=None):
    return make_project({"index.js": code + "\nif (document.readyState === 'loading') {} else { boot(); }\n"}, manifest=manifest)


def with_perm(**perms):
    data = copy.deepcopy(GOOD_MANIFEST)
    data["requiredPermissions"].update(perms)
    return data


class JsRuleTests(unittest.TestCase):
    def test_j001_await_inside_transaction(self):
        bad = "project.lockedAccess(() => { project.executeTransaction(async (ca) => { await x(); }, 'u'); });"
        self.assertIn("J001", rules(js(bad)))
        ok = "const v = await x();\nproject.lockedAccess(() => { project.executeTransaction((ca) => { ca.addAction(v); }, 'u'); });"
        self.assertNotIn("J001", rules(js(ok)))

    def test_j002_action_outside_transaction(self):
        bad = "const a = clip.createSetEndAction(t);\nproject.lockedAccess(() => { const ok = project.executeTransaction((ca) => { ca.addAction(a); }, 'u'); });"
        self.assertIn("J002", rules(js(bad)))
        builder = "// ppm: action-builder\nfunction acts(add, c, t) { add('e', () => c.createSetEndAction(t)); }"
        self.assertNotIn("J002", rules(js(builder)))

    def test_j003_get_track_items_without_args(self):
        self.assertIn("J003", rules(js("const items = await track.getTrackItems();")))
        self.assertNotIn("J003", rules(js("const items = await sel.getTrackItems();")))
        self.assertNotIn("J003", rules(js("const items = await track.getTrackItems(1, false);")))

    def test_j004_new_track_item_selection(self):
        self.assertIn("J004", rules(js("const s = new ppro.TrackItemSelection();")))

    def test_j005_frame_rate_property(self):
        self.assertIn("J005", rules(js("const fps = settings.videoFrameRate;")))
        self.assertNotIn("J005", rules(js("const fr = await settings.getVideoFrameRate(); // ppm-ignore: J014")))

    def test_j006_relative_require(self):
        self.assertIn("J006", rules(js("const u = require('./util.js');")))

    def test_j007_mutation_observer_guard(self):
        self.assertIn("J007", rules(js("new MutationObserver(() => {});")))
        self.assertNotIn("J007", rules(js("if (typeof MutationObserver === 'function') { new MutationObserver(() => {}); }")))

    def test_j008_alerts(self):
        self.assertIn("J008", rules(js("confirm('消しますか');")))
        self.assertNotIn("J008", rules(js("PPM.ui.confirm('x');")))

    def test_j009_unchecked_transaction(self):
        self.assertIn("J009", rules(js("project.lockedAccess(() => {\n  project.executeTransaction((ca) => { ca.addAction(a); }, 'u');\n});")))
        self.assertNotIn("J009", rules(js("project.lockedAccess(() => {\n  ok = project.executeTransaction((ca) => { ca.addAction(a); }, 'u');\n});")))

    def test_j010_ticks_direct_read(self):
        self.assertIn("J010", rules(js("const t = start.ticks;")))
        self.assertNotIn("J010", rules(js("const t = ppro.TickTime.createWithTicks('1'); const n = start.ticksNumber;")))

    def test_j011_eval_needs_permission(self):
        self.assertIn("J011", rules(js("eval('1');")))
        self.assertNotIn("J011", rules(js("eval('1');", manifest=with_perm(allowCodeGenerationFromStrings=True))))

    def test_j012_boot_not_at_end(self):
        code = "if (document.readyState === 'loading') {} else { boot(); }\n" + "\n".join(f"const v{i} = {i};" for i in range(30))
        root = make_project({"index.js": code})
        self.assertIn("J012", rules(root))

    def test_j013_loopback_needs_network_all(self):
        code = "const r = await fetch('http://127.0.0.1:3850/ping');"
        self.assertIn("J013", rules(js(code)))
        self.assertNotIn("J013", rules(js(code, manifest=with_perm(network={"domains": "all"}))))

    def test_j014_api_newer_than_min_version(self):
        code = "const ok = await ppro.ProjectConverter.exportAsFinalCutProXML(seq, p, true);"
        self.assertIn("J014", rules(js(code)))
        data = copy.deepcopy(GOOD_MANIFEST)
        data["host"]["minVersion"] = "26.2"
        self.assertNotIn("J014", rules(js(code, manifest=data)))
        beta = [f for f in findings(js("editor.createRazorTrackAction(a);")) if f.rule == "J014"]
        self.assertEqual(beta[0].severity, "warn")

    def test_j015_media_type_compare(self):
        self.assertIn("J015", rules(js("if ((await item.getMediaType()) === 1) {}")))

    def test_m010_m011_m012_permission_use(self):
        self.assertIn("M010", rules(js("const a = 1;", manifest=with_perm(localFileSystem="fullAccess"))))
        self.assertNotIn("M010", rules(js("const fs = require('fs');", manifest=with_perm(localFileSystem="fullAccess"))))
        self.assertIn("M011", rules(js("const r = await fetch('https://example.com');")))
        self.assertIn("M011", rules(js("const a = 1;", manifest=with_perm(network={"domains": "all"}))))
        self.assertIn("M012", rules(js("const a = 1;", manifest=with_perm(allowCodeGenerationFromStrings=True))))

    def test_ignore_comment(self):
        self.assertNotIn("J010", rules(js("const t = start.ticks; // ppm-ignore: J010")))

    def test_cep_and_server_js_are_not_checked_as_panel(self):
        root = make_project({"cep/client/main.js": "var t = start.ticks; confirm('x');"})
        self.assertFalse({"J010", "J008"} & rules(root))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_check_css_html.py`:

```python
import unittest

from check_helpers import GOOD_HTML, make_project, rules


class CssHtmlRuleTests(unittest.TestCase):
    def test_c001_grid(self):
        self.assertIn("C001", rules(make_project({"panel.css": ".a { display: grid; }\ntitle{display:none}"})))

    def test_c002_fixed_and_c004_animation(self):
        r = rules(make_project({"panel.css": "title{display:none}\n.o { position: fixed; transition: opacity 1s; }"}))
        self.assertIn("C002", r)
        self.assertIn("C004", r)

    def test_h001_missing_script(self):
        html = GOOD_HTML.replace('<script src="index.js"></script>', '<script src="lib/missing.js"></script><script src="index.js"></script>')
        self.assertIn("H001", rules(make_project({"index.html": html})))

    def test_h002_lists_and_h004_inputs(self):
        html = GOOD_HTML.replace("<body>", '<body><ul><li>a</li></ul><input type="file" />')
        r = rules(make_project({"index.html": html}))
        self.assertIn("H002", r)
        self.assertIn("H004", r)

    def test_h003_inline_handler(self):
        html = GOOD_HTML.replace('<button id="run"', '<button onclick="go()" id="run"')
        self.assertIn("H003", rules(make_project({"index.html": html})))

    def test_h005_title_not_hidden(self):
        self.assertIn("H005", rules(make_project({"panel.css": ".a { color: #fff; }"})))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_jsscan.py' -v`
Expected: FAIL（`cannot import name 'jsscan'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/lib/jsscan.py`:

```python
"""JS を「だいたい」読むための道具（構文木は作らない）。

blank() でコメントと文字列の中身を空白に置き換えてから正規表現で探すと、
文字列やコメントの中の言葉を誤って拾わない。長さと改行の位置は元と同じなので、行番号はそのまま使える。
"""
from __future__ import annotations

import re
from typing import List, Tuple

_REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^")
_PAIRS = {"(": ")", "{": "}", "[": "]"}


def blank(text: str) -> str:
    out = list(text)
    n = len(text)
    i = 0
    prev = ""

    def fill(a: int, b: int) -> None:
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            fill(i, j)
            i = j
            continue
        if c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            fill(i, j)
            i = j
            continue
        if c in "\"'`":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == c or (c != "`" and text[j] == "\n"):
                    break
                j += 1
            fill(i + 1, j)
            i = j + 1
            prev = c
            continue
        if c == "/" and (prev == "" or prev in _REGEX_PREV):
            j = i + 1
            in_class = False
            while j < n and text[j] != "\n":
                ch = text[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    break
                j += 1
            fill(i + 1, j)
            i = j + 1
            prev = "/"
            continue
        if not c.isspace():
            prev = c
        i += 1
    return "".join(out)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, max(pos, 0)) + 1


def match_close(clean: str, open_pos: int) -> int:
    opener = clean[open_pos]
    closer = _PAIRS.get(opener)
    if not closer:
        return -1
    depth = 0
    for k in range(open_pos, len(clean)):
        ch = clean[k]
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return k
    return -1


def callback_spans(clean: str, names=("lockedAccess", "executeTransaction", "transact")) -> List[Tuple[int, int, str]]:
    """`.名前(` と、受け手の無い `名前(` の両方を見る（ppro-kit の中の transact(…) の呼び出しも取引として扱う）。
    `function transact(` のような定義は除く。"""
    spans: List[Tuple[int, int, str]] = []
    pattern = re.compile(r"(?<![\w$])(?:[\w$]+\s*\.\s*)?(" + "|".join(names) + r")\s*\(")
    for m in pattern.finditer(clean):
        if re.search(r"function\s+$", clean[max(0, m.start() - 20):m.start()]):
            continue
        open_paren = m.end() - 1
        close_paren = match_close(clean, open_paren)
        if close_paren < 0:
            continue
        args = clean[open_paren + 1:close_paren]
        fm = re.search(r"=>|\bfunction\b", args)
        if not fm:
            continue
        start = open_paren + 1 + fm.end()
        if fm.group(0) == "function":
            brace = clean.find("{", start, close_paren)
            if brace < 0:
                continue
            spans.append((brace, match_close(clean, brace), m.group(1)))
            continue
        k = start
        while k < close_paren and clean[k].isspace():
            k += 1
        if k < close_paren and clean[k] == "{":
            spans.append((k, match_close(clean, k), m.group(1)))
        else:
            spans.append((k, close_paren, m.group(1)))
    return spans


def builder_spans(original: str, clean: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    for m in re.finditer(r"ppm:\s*action-builder", original):
        brace = clean.find("{", m.end())
        if brace < 0:
            continue
        end = match_close(clean, brace)
        if end > brace:
            spans.append((brace, end))
    return spans


def inside(pos: int, spans) -> bool:
    return any(a <= pos <= b for a, b, *_ in spans)
```

`SKILL/scripts/lib/checks/js_rules.py`:

```python
"""パネルの JS の検査（J001〜J015、M010〜M012）。実機で踏んだ失敗の型を、読み込む前に止める。"""
from __future__ import annotations

import json
import re
from typing import List

from .. import jsscan
from .. import manifest as manifest_lib
from . import Finding, Project, rule


def _api_since(p: Project) -> dict:
    path = p.kit_dir / "knowledge" / "reference" / "api-since.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("apis", {})
    except (OSError, ValueError):
        return {}


def _finding(p, path, text, pos, rule_name, severity, message, why, fix):
    return Finding(rule_name, severity, p.rel(path), jsscan.line_of(text, pos), message, why, fix)


@rule
def js_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    perms = p.permissions()
    flags = p.feature_flags()
    apis = _api_since(p)
    try:
        minv = manifest_lib.version_tuple(p.min_version() or "0")
    except ValueError:
        minv = (0, 0, 0)
    for path in p.panel_files(".js"):
        text = p.text(path)
        clean = jsscan.blank(text)
        spans = jsscan.callback_spans(clean)
        builders = jsscan.builder_spans(text, clean)

        for a, b, name in spans:
            for m in re.finditer(r"\bawait\b", clean[a:b]):
                out.append(_finding(p, path, text, a + m.start(), "J001", "error",
                                    f"取引（{name}）の中で await しています",
                                    "取引のコールバックは完全に同期でなければならず、await を挟むと Action が無効になり「The script object is no longer valid」で失敗します",
                                    "非同期の取得（getComponentChain・createComponent など）を取引の前に済ませ、中では Action を作って足すだけにしてください"))
        for m in re.finditer(r"\.\s*(create[A-Z]\w*Action)\s*\(", clean):
            if jsscan.inside(m.start(), spans) or jsscan.inside(m.start(), builders):
                continue
            out.append(_finding(p, path, text, m.start(), "J002", "warn", f"{m.group(1)} を取引の外で作っています",
                                "Premiere 26.3 から、Action は lockedAccess の中で作るのが必須です",
                                "PPM.transact の中で作るか、Action を作る関数の前に「// ppm: action-builder」と書いて取引の中から呼んでください"))
        for m in re.finditer(r"(\w+)\s*\.\s*getTrackItems\s*\(\s*\)", clean):
            if re.search("sel", m.group(1), re.I):
                continue
            out.append(_finding(p, path, text, m.start(), "J003", "error", "getTrackItems() を引数なしで呼んでいます",
                                "トラックの getTrackItems は (種類, 空も含めるか) の 2 つが必須で、無いと空の配列か例外になります",
                                "track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false) のように呼んでください"))
        for m in re.finditer(r"new\s+(?:ppro\s*\.\s*)?TrackItemSelection\s*\(", clean):
            out.append(_finding(p, path, text, m.start(), "J004", "error", "new TrackItemSelection() を使っています",
                                "Premiere 26.3 では、後の setSelection が「Connection to object lost」で失敗します",
                                "await sequence.getSelection() で取った選択に addItem / removeItem してください"))
        for m in re.finditer(r"\b\w*[Ss]ettings\w*\s*\.\s*(videoFrameRate|frameRate|videoFrameRect|frameRect)\b(?!\s*\()", clean):
            rect = "Rect" in m.group(1)
            out.append(_finding(p, path, text, m.start(), "J005", "warn" if rect else "error",
                                f"シーケンス設定の {m.group(1)} をプロパティとして読んでいます",
                                "そのプロパティは存在せず、黙って undefined になります（30fps 決め打ちで壊した事故あり）",
                                "await settings.getVideoFrameRate() の .value を使い、読めなかったら既定値を詰めずに止めてください"))
        for m in re.finditer(r"require\s*\(\s*[\"']\.{1,2}/", text):
            out.append(_finding(p, path, text, m.start(), "J006", "error", "require を相対パスで使っています",
                                "UXP では require の相対パスが解決されず、分けたファイルが読み込めません",
                                "index.html の <script src> で順に読み込み、関数は PPM などのグローバルに載せてください"))
        if re.search(r"\bMutationObserver\b", clean) and not re.search(r"typeof\s+MutationObserver", clean):
            out.append(_finding(p, path, text, clean.find("MutationObserver"), "J007", "warn", "MutationObserver を確かめずに使っています",
                                "UXP には MutationObserver が無いことがあり、その場で止まります",
                                "typeof MutationObserver === \"function\" で分け、無ければ setInterval で見張ってください"))
        for m in re.finditer(r"(?<![\w.$])(alert|confirm|prompt)\s*\(", clean):
            enabled = bool(flags.get("enableAlerts"))
            out.append(_finding(p, path, text, m.start(), "J008", "warn" if enabled else "error", f"{m.group(1)}() を使っています",
                                "Premiere の UXP では featureFlags.enableAlerts が無いと使えず、あっても出ないことがあります",
                                "パネルの中に確認の表示を作る（2 回押しで確定など）か、PPM.ui の表示を使ってください"))
        for m in re.finditer(r"(^|[;{}\n])\s*(?:[\w$]+\s*\.\s*)*executeTransaction\s*\(", clean):
            out.append(_finding(p, path, text, m.end(), "J009", "warn", "executeTransaction の戻り値を見ていません",
                                "受け付けられなかったときは false が返り、見ないと「何も起きない」まま成功のように見えます",
                                "ok = project.executeTransaction(...) とし、false なら原因つきのエラーを出してください（PPM.transact はこれをします）"))
        for m in re.finditer(r"\.\s*ticks\b(?!Number)", clean):
            out.append(_finding(p, path, text, m.start(), "J010", "warn", "TickTime の .ticks を直接読んでいます",
                                "版によって .ticks が 0 や文字列になる記録があります",
                                "PPM.ticksOf(time) を使ってください（ticksNumber → ticks → seconds の順に読みます）"))
        if not perms.get("allowCodeGenerationFromStrings"):
            for m in re.finditer(r"(?<![\w.$])eval\s*\(|\bnew\s+Function\s*\(", clean):
                out.append(_finding(p, path, text, m.start(), "J011", "error", "eval / new Function を使っています",
                                    "manifest の allowCodeGenerationFromStrings が無いと使えません",
                                    "文字列からコードを作らない書き方にしてください（どうしても要るなら権限を足す）"))
        boot = re.search(r"document\s*\.\s*readyState", clean)
        if boot and jsscan.line_of(text, boot.start()) < 0.8 * max(1, text.count("\n") + 1):
            out.append(_finding(p, path, text, boot.start(), "J012", "warn", "起動の処理がファイルの末尾にありません",
                                "UXP は読み込みの途中で起動してしまうことがあり、後ろで宣言した const を踏んで止まります",
                                "起動の判定（document.readyState）と boot() の呼び出しをファイルの最後に置いてください"))
        if re.search(r"127\.0\.0\.1|localhost", text) and re.search(r"\bfetch\s*\(|XMLHttpRequest|WebSocket", clean):
            if (perms.get("network") or {}).get("domains") != "all":
                pos = text.find("127.0.0.1") if "127.0.0.1" in text else text.find("localhost")
                out.append(_finding(p, path, text, pos, "J013", "error", "手元のサーバーへ接続するのに network.domains が \"all\" ではありません",
                                    "個別の許可（http://127.0.0.1:3850 など）では、通信そのものが起きなかった記録があります（Premiere 26.3・Mac）",
                                    "manifest の requiredPermissions.network を {\"domains\": \"all\"} にし、サーバー側を 127.0.0.1 と合言葉で守ってください"))
        for name, info in apis.items():
            for m in re.finditer(r"\b" + re.escape(name) + r"\b", clean):
                try:
                    since = manifest_lib.version_tuple(info["since"])
                except (KeyError, ValueError):
                    continue
                if since <= minv:
                    continue
                beta = bool(info.get("beta"))
                out.append(_finding(p, path, text, m.start(), "J014", "warn" if beta else "error",
                                    f"{name} は Premiere {info['since']}{'（ベータ）' if beta else ''} からの API です",
                                    f"manifest の minVersion（{p.min_version()}）では読み込めても、この API が無くて止まります（{info.get('what', '')}）",
                                    f"minVersion を {info['since']} 以上にするか、typeof で確かめて無ければ別の手にしてください"
                                    if not beta else "ベータ版にしか無い API です。正式版で使えるまで、代わりの手を用意してください"))
                break
        for m in re.finditer(r"getMediaType\s*\(\s*\)\s*\)?\s*[!=]==?\s*\d", clean):
            out.append(_finding(p, path, text, m.start(), "J015", "warn", "getMediaType() を数値と比べています",
                                "getMediaType は Guid を返すので、数値との比較は常に偽になります",
                                "item.constructor.name が VideoClipTrackItem / AudioClipTrackItem かで分けてください（PPM.getSelectedClips の kind）"))
    out.extend(_permission_use(p))
    return out


def _permission_use(p: Project) -> List[Finding]:
    if p.manifest is None:
        return []
    perms = p.permissions()
    js_raw = "\n".join(p.text(x) for x in p.panel_files(".js"))
    js_clean = "\n".join(jsscan.blank(p.text(x)) for x in p.panel_files(".js"))
    html_text = "\n".join(p.text(x) for x in p.panel_files(".html"))
    out: List[Finding] = []
    # require("fs") の "fs" は文字列なので、元の文で探す（blank では消える）
    if perms.get("localFileSystem") == "fullAccess" and not re.search(r"require\s*\(\s*[\"']fs[\"']\s*\)|getEntryWithUrl|file:/", js_raw):
        out.append(Finding("M010", "warn", "manifest.json", 0, "localFileSystem が fullAccess ですが、絶対パスのファイル操作が見当たりません",
                           "権限が強いほど、受け取った人が入れるのをためらいます", "要らなければ \"plugin\" に下げてください"))
    # 通信の有無はコメントを除いた文で見る（コメントの中の fetch を数えない）
    uses_net = bool(re.search(r"\bfetch\s*\(|XMLHttpRequest|new\s+WebSocket", js_clean))
    if uses_net and not perms.get("network"):
        out.append(Finding("M011", "error", "manifest.json", 0, "通信しているのに network の権限がありません",
                           "許可していない相手への通信は失敗します", "requiredPermissions.network.domains に相手を書いてください（手元のサーバーなら \"all\"）"))
    if perms.get("network") and not uses_net:
        out.append(Finding("M011", "warn", "manifest.json", 0, "network の権限がありますが、通信が見当たりません",
                           "使わない権限は外す決まりです", "requiredPermissions.network を消してください"))
    if perms.get("allowCodeGenerationFromStrings") and not (re.search(r"(?<![\w.$])eval\s*\(|new\s+Function\s*\(", js_clean)
                                                           or re.search(r"\son[a-z]+\s*=", html_text)):
        out.append(Finding("M012", "warn", "manifest.json", 0, "allowCodeGenerationFromStrings が true ですが、使っていません",
                           "使わない権限は外す決まりです", "false にするか、行ごと消してください"))
    return out
```

`SKILL/scripts/lib/checks/css_html_rules.py`:

```python
"""CSS と HTML の検査（C001・C002・C004、H001〜H005）。"""
from __future__ import annotations

import re
from typing import List

from . import Finding, Project, rule

_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


@rule
def css_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.panel_files(".css"):
        raw = p.text(path)
        text = _CSS_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw)
        for m in re.finditer(r"display\s*:\s*(?:inline-)?grid|grid-template", text):
            out.append(Finding("C001", "error", p.rel(path), _line(text, m.start()), "CSS の grid を使っています",
                               "UXP は grid に対応していません", "flex（一覧は flex-wrap）で並べてください"))
        for m in re.finditer(r"position\s*:\s*fixed", text):
            out.append(Finding("C002", "warn", p.rel(path), _line(text, m.start()), "position: fixed を使っています",
                               "重ね表示の下にある入力欄が透けて前に出た記録があります", "重ねずに、元の中身を隠して出す形にしてください"))
        for m in re.finditer(r"(?<![\w-])(transition|animation)\s*:", text):
            out.append(Finding("C004", "warn", p.rel(path), _line(text, m.start()), f"{m.group(1)} を使っています",
                               "UXP では効かないことがあります", "動きに頼らない見た目にしてください"))
    return out


@rule
def html_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    css_all = "\n".join(p.text(x) for x in p.panel_files(".css"))
    perms = p.permissions()
    for path in p.panel_files(".html"):
        text = p.text(path)
        for m in re.finditer(r"<(?:script|img)\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']|<link\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']", text, re.I):
            ref = m.group(1) or m.group(2)
            if re.match(r"^(https?:|data:|plugin:|#)", ref):
                continue
            if not (path.parent / ref.split("?")[0]).exists():
                out.append(Finding("H001", "error", p.rel(path), _line(text, m.start()), f"読み込むファイル「{ref}」がありません",
                                   "その部分が動かず、パネルが空になることがあります", "ファイルを置くか、行を消してください"))
        for m in re.finditer(r"<(ul|ol|li)\b", text, re.I):
            out.append(Finding("H002", "warn", p.rel(path), _line(text, m.start()), f"<{m.group(1)}> を使っています",
                               "UXP では div として扱われ、点や番号が出ません", "div と CSS で並べてください"))
        if not perms.get("allowCodeGenerationFromStrings"):
            for m in re.finditer(r"<[^>]+\son[a-z]+\s*=", text, re.I):
                out.append(Finding("H003", "error", p.rel(path), _line(text, m.start()), "属性にイベント（onclick= など）を書いています",
                                   "allowCodeGenerationFromStrings が無いと動きません", "index.js で addEventListener を使ってください"))
        for m in re.finditer(r"<input\b[^>]*type\s*=\s*[\"']?(file|color)", text, re.I):
            out.append(Finding("H004", "warn", p.rel(path), _line(text, m.start()), f"<input type=\"{m.group(1)}\"> を使っています",
                               "UXP では使えません", "ファイルは require(\"uxp\").storage.localFileSystem.getFileForOpening() で選ばせてください"))
        if re.search(r"<title\b", text, re.I) and not re.search(r"title\s*\{[^}]*display\s*:\s*none", css_all):
            out.append(Finding("H005", "warn", p.rel(path), _line(text, text.lower().find("<title")), "<title> を隠していません",
                               "UXP では <title> の文字がパネルに出てしまいます", "CSS に title { display: none; } を書いてください"))
    return out
```

`SKILL/scripts/lib/checks/__init__.py` の `run_all` の import を次に変える:

```python
    from . import css_html_rules, js_rules, manifest_rules  # noqa: F401  （登録のための import。Task 8 で残りを足す）
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_jsscan.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_check_js.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_check_css_html.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_check_manifest.py' -v`
Expected: PASS（jsscan 3・JS 19・CSS/HTML 6・manifest 12）。manifest のテストの「良いプロジェクト」に新しい誤りが出たら、`check_helpers.GOOD_*` ではなく規則の誤検知を直す。

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: check.py の JS・CSS・HTML の検査（実機で踏んだ失敗の型を読み込む前に止める）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: check.py の配布・Windows・Python の検査

**Files:**
- Create: `SKILL/scripts/lib/checks/package_rules.py`
- Create: `SKILL/scripts/lib/checks/platform_rules.py`
- Create: `SKILL/scripts/lib/privacy.py`
- Modify: `SKILL/scripts/lib/checks/__init__.py`（`run_all` の import に `package_rules, platform_rules` を足す）
- Test: `tests/test_check_package_platform.py`、`tests/test_privacy.py`

**Interfaces:**
- Produces（`lib.privacy`）:
  - `PLACEHOLDER_USERS = {"<name>", "name", "you", "user", "username", "USER", "USERNAME", "%USERNAME%", "example", "runner", "runneradmin", "Shared", "Public", "<user>", "<username>"}`
  - `personal_paths(text: str) -> list[tuple[int, str]]`（(行番号, 見つけたパス) の一覧。/Users/<実名>/ と C:\Users\<実名>\ と /home/<実名>/）
  - `secret_like_name(name: str) -> bool`
  - `token_like(text: str) -> list[tuple[int, str]]`（`ghp_` `github_pat_` `sk-` などの形）
- 規則:

| 規則 | 重さ | 見つけるもの |
|---|---|---|
| P002 | error | 秘密らしい名前のファイル（secret・token・credential・password・.env・ready） |
| P003 | error | 個人のパス・鍵の形の文字列 |
| P004 | error | manifest.json と build_info.json の版の食い違い |
| P005 | error | 置き換え忘れの `{{…}}` |
| P006 | warn | `.ppm/project.json` が無い（この道具で作ったフォルダではない） |
| W001 | error | ASCII 以外を含むのに BOM の無い .ps1 |
| W002 | error | ASCII 以外を含む .bat / .cmd |
| W003 | error / warn | text=True なのに encoding の無い subprocess（error）、encoding の無いテキストの open（warn） |
| W004 | warn | Mac 専用のパス（/Applications・~/Library・/opt/homebrew）を OS の分岐なしで書いている .py / .js |
| W005 | error | .command / .sh の `$変数` の直後に日本語（bash 3.2 と set -u で止まる） |
| Y001 | error | Python の構文の誤り |

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_privacy.py`:

```python
import unittest

from lib import privacy


class PrivacyTests(unittest.TestCase):
    def test_personal_paths(self):
        # 実名に見える見本は実行時に組み立てる（このファイル自体が Task 34 の衛生検査に引っかからないように）
        who = "yama" + "da"
        text = f"a /Users/{who}/Desktop/x\nb /Users/Shared/ok\nc C:\\Users\\{who}\\AppData\nd /Users/<name>/ok\ne /home/{who}/x"
        found = [line for line, _ in privacy.personal_paths(text)]
        self.assertEqual(found, [1, 3, 5])

    def test_secret_names_and_tokens(self):
        self.assertTrue(privacy.secret_like_name("my_secret_store.py"))
        self.assertTrue(privacy.secret_like_name(".env"))
        self.assertTrue(privacy.secret_like_name("ready"))
        self.assertFalse(privacy.secret_like_name("keychain_store.py"))
        self.assertEqual(len(privacy.token_like("x = 'ghp_" + "a" * 36 + "'")), 1)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_check_package_platform.py`:

```python
import unittest

from check_helpers import make_project, rules


class PackageRuleTests(unittest.TestCase):
    def test_p002_secret_named_file(self):
        self.assertIn("P002", rules(make_project({"server/secret_store.py": "x = 1\n"})))

    def test_p003_personal_path(self):
        self.assertIn("P003", rules(make_project({"lib/a.js": "const p = '/Users/" + "yamada/x';\n"})))

    def test_p004_version_mismatch(self):
        self.assertIn("P004", rules(make_project({"build_info.json": {"name": "T", "version": "9.9.9"}})))

    def test_p005_placeholder_left(self):
        self.assertIn("P005", rules(make_project({"README.md": "名前: {{PLUGIN_NAME}}\n"})))

    def test_p006_not_made_by_kit(self):
        root = make_project()
        (root / ".ppm" / "project.json").unlink()
        self.assertIn("P006", rules(root))


class PlatformRuleTests(unittest.TestCase):
    def test_w001_ps1_without_bom(self):
        self.assertIn("W001", rules(make_project({"server/install.ps1": "Write-Host 'こんにちは'\n"})))
        self.assertNotIn("W001", rules(make_project({"server/install.ps1": "\ufeffWrite-Host 'こんにちは'\n".encode("utf-8")})))

    def test_w002_bat_non_ascii(self):
        self.assertIn("W002", rules(make_project({"server/install.bat": "echo 日本語\r\n"})))

    def test_w003_subprocess_text_without_encoding(self):
        bad = "import subprocess\nsubprocess.run(['x'], capture_output=True, text=True)\n"
        self.assertIn("W003", rules(make_project({"server/a.py": bad})))
        ok = "import subprocess\nsubprocess.run(['x'], capture_output=True, text=True, encoding='utf-8')\n"
        self.assertNotIn("W003", rules(make_project({"server/a.py": ok})))

    def test_w004_mac_only_path(self):
        self.assertIn("W004", rules(make_project({"server/a.py": "P = '/Applications/Adobe Premiere Pro 2026'\n"})))
        ok = "import sys\nP = '/Applications/x' if sys.platform == 'darwin' else 'C:/x'\n"
        self.assertNotIn("W004", rules(make_project({"server/a.py": ok})))

    def test_w005_bash_variable_followed_by_japanese(self):
        self.assertIn("W005", rules(make_project({"server/install.command": "#!/bin/bash\nset -u\necho \"$APPを入れます\"\n"})))
        self.assertNotIn("W005", rules(make_project({"server/install.command": "#!/bin/bash\nset -u\necho \"${APP}を入れます\"\n"})))

    def test_y001_python_syntax(self):
        self.assertIn("Y001", rules(make_project({"server/a.py": "def f(:\n"})))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_privacy.py' -v`
Expected: FAIL（`cannot import name 'privacy'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/lib/privacy.py`:

```python
"""公開物・配布物に個人情報や鍵が混ざっていないかを見る（check.py とキット自体の衛生検査で共有）。"""
from __future__ import annotations

import re
from typing import List, Tuple

PLACEHOLDER_USERS = {"<name>", "name", "you", "user", "username", "USER", "USERNAME", "%USERNAME%", "example",
                     "runner", "runneradmin", "Shared", "Public", "<user>", "<username>", "<ユーザー名>"}
# 名前の部分に ( ) [ ] を含めないのは、この正規表現の文字列そのもの（このファイル）を個人のパスと見誤らないため
_MAC = re.compile(r"/Users/([^/\s\"'`<>()\[\]]+)/")
_HOME = re.compile(r"/home/([^/\s\"'`<>()\[\]]+)/")
_WIN = re.compile(r"[A-Za-z]:\\{1,2}Users\\{1,2}([^\\/\s\"'`<>()\[\]]+)")
_TOKENS = re.compile(r"(?:ghp_|github_pat_|gho_|sk-proj-|sk-ant-|xox[bp]-|AKIA)[A-Za-z0-9_\-]{16,}")
_SECRET_NAME = re.compile(r"(secret|token|credential|password|passwd)", re.I)


def personal_paths(text: str) -> List[Tuple[int, str]]:
    found: List[Tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for rx in (_MAC, _HOME, _WIN):
            for m in rx.finditer(line):
                if m.group(1) not in PLACEHOLDER_USERS and not m.group(1).startswith(("{", "$", "%")):
                    found.append((i, m.group(0)))
                    break
            else:
                continue
            break
    return found


def secret_like_name(name: str) -> bool:
    if name in (".env", "ready") or name.startswith(".env."):
        return True
    return bool(_SECRET_NAME.search(name))


def token_like(text: str) -> List[Tuple[int, str]]:
    return [(i, m.group(0)[:12] + "…") for i, line in enumerate(text.splitlines(), 1) for m in _TOKENS.finditer(line)]
```

`SKILL/scripts/lib/checks/package_rules.py`:

```python
"""配る物の検査（P002〜P006）。"""
from __future__ import annotations

import json
import re
from typing import List

from .. import privacy
from . import Finding, Project, rule

TEXT_SUFFIXES = (".js", ".json", ".html", ".css", ".md", ".py", ".txt", ".jsx", ".xml", ".ps1", ".bat", ".cmd",
                 ".command", ".sh", ".plist", ".template")


@rule
def package_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.files():
        if privacy.secret_like_name(path.name):
            out.append(Finding("P002", "error", p.rel(path), 0, f"秘密らしい名前のファイル「{path.name}」があります",
                               "鍵や合言葉のファイルが配布物に混ざると漏れます。名前だけで配布から外す仕組みに部品が消される事故もありました",
                               "鍵はファイルに書かず OS の保管庫へ。部品なら secret・token を含まない名前にしてください"))
    for path in p.files(*TEXT_SUFFIXES):
        text = p.text(path)
        for line, found in privacy.personal_paths(text):
            out.append(Finding("P003", "error", p.rel(path), line, f"個人のパス「{found}」が書かれています",
                               "受け取った人の PC には無いパスで、名前も漏れます", "~ や環境変数、プラグインのフォルダからの相対で書いてください"))
        for line, found in privacy.token_like(text):
            out.append(Finding("P003", "error", p.rel(path), line, f"鍵の形の文字列「{found}」があります",
                               "鍵がそのまま配られます", "鍵は消し、OS の保管庫か利用者の設定から読むようにしてください"))
        for m in re.finditer(r"\{\{[A-Z_]+\}\}", text):
            out.append(Finding("P005", "error", p.rel(path), text.count("\n", 0, m.start()) + 1, f"置き換え忘れの「{m.group(0)}」があります",
                               "雛形の印がそのまま残っています", "new_plugin.py か add_part.py で作り直すか、正しい値に書き換えてください"))
    info = p.root / "build_info.json"
    if p.manifest and info.exists():
        try:
            bv = json.loads(p.text(info)).get("version")
        except ValueError:
            bv = None
        if bv != p.manifest.get("version"):
            out.append(Finding("P004", "error", "build_info.json", 0, f"版が manifest.json（{p.manifest.get('version')}）と違います（{bv}）",
                               "画面に出る版と、Premiere が見る版がずれます", "両方を同じ版にしてください"))
    if not (p.root / ".ppm" / "project.json").exists():
        out.append(Finding("P006", "warn", ".ppm/project.json", 0, "この道具で作ったフォルダではありません",
                           "部品の追加（add_part.py）が使えません", "new_plugin.py で作ったフォルダに中身を移すと、部品と検査がそろいます"))
    return out
```

`SKILL/scripts/lib/checks/platform_rules.py`:

```python
"""Windows で壊れる書き方と Python の構文の検査（W001〜W005、Y001）。"""
from __future__ import annotations

import re
from typing import List

from . import Finding, Project, rule

_MAC_ONLY = re.compile(r"/Applications/|~/Library|/Library/|/opt/homebrew")
_OS_BRANCH = re.compile(r"sys\.platform|platform\.system|os\.platform\(|process\.platform|darwin|osinfo\.|os_name")


def _call_text(text: str, start: int) -> str:
    depth = 0
    for k in range(start, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return text[start:k + 1]
    return text[start:]


@rule
def platform_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.files(".ps1"):
        raw = path.read_bytes()
        if any(b > 127 for b in raw) and not raw.startswith(b"\xef\xbb\xbf"):
            out.append(Finding("W001", "error", p.rel(path), 0, "日本語を含む .ps1 に BOM がありません",
                               "Windows PowerShell 5.1 は BOM の無いファイルを ANSI として読み、文字化けして止まります",
                               "UTF-8（BOM 付き）で保存してください"))
    for path in p.files(".bat", ".cmd"):
        if any(b > 127 for b in path.read_bytes()):
            out.append(Finding("W002", "error", p.rel(path), 0, ".bat / .cmd に英数字以外が入っています",
                               "cmd は CP932 で読むので、日本語やパスが化けます", "英数字だけにし、日本語の処理は .ps1 か Python に任せてください"))
    for path in p.files(".py"):
        text = p.text(path)
        try:
            compile(text, str(path), "exec")
        except SyntaxError as e:
            out.append(Finding("Y001", "error", p.rel(path), e.lineno or 0, f"Python の構文の誤り: {e.msg}",
                               "このファイルは動きません", "示された行を直してください"))
            continue
        for m in re.finditer(r"subprocess\.(?:run|Popen|check_output|check_call)\s*\(", text):
            call = _call_text(text, m.end() - 1)
            if re.search(r"text\s*=\s*True|universal_newlines\s*=\s*True", call) and "encoding" not in call:
                out.append(Finding("W003", "error", p.rel(path), text.count("\n", 0, m.start()) + 1,
                                   "text=True なのに encoding がありません", "Windows では cp932 で読み書きされ、日本語や絵文字で止まります",
                                   "encoding=\"utf-8\", errors=\"replace\" を足してください"))
        for m in re.finditer(r"(?<![\w.])open\s*\(", text):
            call = _call_text(text, m.end() - 1)
            if "encoding" not in call and not re.search(r"[\"'][rwax+]*b[rwax+]*[\"']", call):
                out.append(Finding("W003", "warn", p.rel(path), text.count("\n", 0, m.start()) + 1,
                                   "テキストの open に encoding がありません", "Windows では cp932 になります", "encoding=\"utf-8\" を足してください"))
    for path in p.files(".py", ".js"):
        text = p.text(path)
        m = _MAC_ONLY.search(text)
        if m and not _OS_BRANCH.search(text):
            out.append(Finding("W004", "warn", p.rel(path), text.count("\n", 0, m.start()) + 1, f"Mac 専用の場所「{m.group(0)}」を書いています",
                               "Windows ではその場所が無く、黙って失敗します（Mac 専用の場所だけを探して Windows で失敗した事故あり）",
                               "OS で分けるか、Windows の場所（環境変数 APPDATA・ProgramFiles）も探してください"))
    for path in p.files(".command", ".sh"):
        text = p.text(path)
        for m in re.finditer(r"\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])", text):
            out.append(Finding("W005", "error", p.rel(path), text.count("\n", 0, m.start()) + 1, f"「{m.group(0)}」の直後に日本語が続いています",
                               "Mac の bash 3.2 は日本語の一部を変数名と読み、set -u で止まります（新しく入れた人のほぼ全員が踏んだ）",
                               "${変数} のように波かっこで囲んでください"))
    return out
```

`SKILL/scripts/lib/checks/__init__.py` の `run_all` の import を次に変える:

```python
    from . import css_html_rules, js_rules, manifest_rules, package_rules, platform_rules  # noqa: F401
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -v`
Expected: PASS（ここまでの全件）。`test_check_manifest.test_good_project_has_no_errors` が P/W/Y の規則で落ちたら、規則の誤検知を直す。

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: check.py の配布・Windows・Python の検査と、個人情報の走査

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 3: 雛形と組み立ての道具

### Task 9: JS の部品（logger・ppro-kit・ui-kit・probe）と JS テストの土台

**Files:**
- Create: `SKILL/parts/logger/part.json`、`SKILL/parts/logger/lib/ppm-logger.js`
- Create: `SKILL/parts/ppro-kit/part.json`、`SKILL/parts/ppro-kit/lib/ppm-ppro-kit.js`
- Create: `SKILL/parts/ui-kit/part.json`、`SKILL/parts/ui-kit/lib/ppm-ui-kit.js`、`SKILL/parts/ui-kit/lib/ppm-ui-kit.css`
- Create: `SKILL/parts/probe/part.json`、`SKILL/parts/probe/lib/ppm-probe.js`
- Create: `tests/js/fake_ppro.js`、`tests/js/load_parts.js`
- Test: `tests/js/ppro_kit.test.js`、`tests/js/logger_probe.test.js`、`tests/js/ui_kit.test.js`

**Interfaces:**
- 全部の JS の部品は同じ包み方にする（CEP で UMD の判定が window に載らなかった失敗を避けるため、else を使わず両方に載せる）:

```js
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  /* 中身 */
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

- Produces（`PPM.log`、logger）: `init({uxp, tag, fileName="ppm-log.txt", maxLines=500})`、`info(msg, data)` `warn(msg, data)` `error(msg, data)`（どれも書いた 1 行を返す。形は `ISO時刻 [tag] LEVEL msg {json}`）、`flush() -> Promise<boolean>`、`filePath() -> Promise<string>`、`lines() -> string[]`
- Produces（`PPM`、ppro-kit）: `TICKS_PER_SECOND`、`init({ppro, uxp, tag})`（logger の init も呼ぶ）、`modules() -> {ppro, uxp}`、`err(symptom, why, next) -> Error`（`.ppm = {symptom, why, next}`）、`resolve(v)`、`ticksOf(t) -> number`、`secondsOf(t) -> number`、`time(seconds) -> TickTime`、`timeFromTicks(ticks) -> TickTime`、`getProjectAndSequence() -> Promise<{project, sequence}>`、`describeClip(item)`、`getSelectedClips(sequence) -> Promise<Clip[]>`（`Clip = {item, name, trackIndex, kind: "video"|"audio"|"unknown", startTicks, endTicks, startSeconds, endSeconds}`）、`listTrackClips(sequence, kind, trackIndex)`、`findClip(sequence, kind, trackIndex, startTicks)`、`transact(project, label, build: (add) => void) -> {ok, added, warnings}`（`add(what, makeAction) -> boolean`）、`toValue(v)`、`findParam(item, componentMatchNames[], paramNames[]) -> Promise<{component, param, index, chain}|null>`、`keyframeActions(add, param, inPointSeconds, keys[{t, value}]) -> number`、`setValueAction(add, param, value) -> boolean`、`addEffect(project, item, matchName)`、`addTransition(project, item, matchName, seconds, atStart)`、`addMarkers(project, sequence, [{seconds, name, comment, duration}])`、`exportFrame(sequence, seconds, fileName, {width, height, timeoutMs}) -> Promise<string>`（データフォルダへ書き、実際のパスを返す）、`getFrameRate(sequence) -> Promise<{fps, timebase, ntsc, detected}>`（読めなければ `detected: false`。30 を詰めない）、`hostInfo() -> {app, version, uxp, os}`、`joinPath(folder, name)`
- Produces（`PPM.ui`、ui-kit）: `showOk(el, text)`、`showInfo(el, text)`、`showError(el, error)`（`error.ppm` があれば「症状・なぜ・次の一手」の 3 行）、`busy(button, on, label)`、`textValue(el) -> string`、`numberValue(el, fallback) -> number`、`protectSelect(select)`。CSS の部品の名前は `ppm-` で始める（`.ppm-app` `.ppm-header` `.ppm-title` `.ppm-scroll` `.ppm-page` `.ppm-list` `.ppm-row` `.ppm-field` `.ppm-label` `.ppm-input` `.ppm-hint` `.ppm-btn` `.ppm-btn-primary` `.ppm-btn-quiet` `.ppm-result` `.ppm-footer` `.ppm-version`）
- Produces（`PPM.probe`、probe）: `STATIC: string[]`、`LIVE: string[]`、`kindOf(obj, path[]) -> "function"|"object"|...|"missing"|"error: …"`、`run(extraStatic?) -> Promise<Report>`（`Report = {at, host, statics, live, logFile, notes}`）、`runAndShow(el) -> Promise<Report>`
- Produces（テスト）: `tests/js/fake_ppro.js` の `makeFake(opts) -> {ppro, project, sequence, clips, log, chain}`（`opts`: `noProject` `noSequence` `commitResult` `rejectAction` `fps` `withText` `selected`）、`TPS`。`tests/js/load_parts.js` の `loadParts(files: string[], extra?) -> vm.Context`（`ctx.PPM` に部品が載る）、`PARTS`
- 部品の `part.json` の書き方（Task 11 で `add_part.py` が読む。全部品で共通）:

```json
{
  "name": "部品の名前（フォルダ名と同じ）",
  "description": "何をする部品か（1 文）",
  "status": "verified | partial | unverified",
  "os": ["mac", "windows"],
  "requires": ["先に入れる部品"],
  "files": {"部品の中の相対パス": "作業フォルダの中の相対パス（フォルダなら末尾 /）"},
  "scripts": ["index.html に足す <script> の src（この順）"],
  "styles": ["index.html に足す <link> の href"],
  "permissions": {"localFileSystem": "fullAccess"},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": ["サーバー側の Python の依存（requirements.txt へ）"],
  "knowledge": ["関係する知識の id"],
  "notes": "使い方の短い説明"
}
```

- [ ] **Step 1: テストの土台（偽物の premierepro と読み込み役）を書く**

`tests/js/fake_ppro.js`:

```js
// 本物の premierepro の「形」をまねた偽物。
// 取得は Promise、Action は lockedAccess の中でだけ作れる、executeTransaction は boolean を返す、
// getTrackItems は引数が無いと失敗する、getVideoFrameRate は {value} を返すメソッド。
"use strict";

const TPS = 254016000000;

class TickTime {
  constructor(ticks) {
    this.ticksNumber = Number(ticks);
    this.ticks = String(ticks);
    this.seconds = Number(ticks) / TPS;
  }
  static createWithSeconds(s) { return new TickTime(Math.round(Number(s) * TPS)); }
  static createWithTicks(t) {
    if (typeof t !== "string") throw new Error("createWithTicks には文字列を渡す");
    return new TickTime(Number(t));
  }
}

class PointF { constructor(x, y) { this.x = x; this.y = y; } }

function makeFake(opts = {}) {
  const log = { actions: [], transactions: [], locked: 0, exports: [] };
  let inLock = false;
  const guard = (name) => {
    if (!inLock) throw new Error(`The script object is no longer valid (${name} を lockedAccess の外で作った)`);
  };
  const action = (name, args) => { guard(name); return { __action: name, args }; };

  const makeParam = (displayName, value) => ({
    displayName,
    value,
    createKeyframe(v) { return { value: v, position: null }; },
    createAddKeyframeAction(kf) { return action("addKeyframe", [kf]); },
    createSetTimeVaryingAction(on) { return action("setTimeVarying", [on]); },
    createRemoveKeyframeRangeAction(a, b) { return action("removeKeyframeRange", [a, b]); },
    createSetValueAction(kf, safe) { return action("setValue", [kf, safe]); },
  });
  const motion = {
    params: [makeParam("Position", new PointF(0.5, 0.5)), makeParam("Scale", 100), makeParam("Rotation", 0)],
    async getMatchName() { return "AE.ADBE Motion"; },
    getParamCount() { return 3; },
    getParam(i) { return this.params[i]; },
  };
  const text = { async getMatchName() { return "AE.ADBE Text"; }, getParamCount() { return 0; }, getParam() { return null; } };
  const components = opts.withText ? [motion, text] : [motion];
  const chain = {
    getComponentCount() { return components.length; },
    getComponentAtIndex(i) { return components[i]; },
    createAppendComponentAction(c) { return action("appendComponent", [c]); },
    createInsertComponentAction(c, i) { return action("insertComponent", [c, i]); },
  };

  class VideoClipTrackItem {
    constructor(name, start, end, inPoint, track) { Object.assign(this, { _n: name, _s: start, _e: end, _in: inPoint, _t: track }); }
    async getName() { return this._n; }
    async getStartTime() { return TickTime.createWithSeconds(this._s); }
    async getEndTime() { return TickTime.createWithSeconds(this._e); }
    async getInPoint() { return TickTime.createWithSeconds(this._in); }
    async getTrackIndex() { return this._t; }
    async getComponentChain() { return chain; }
    createSetEndAction(t) { return action("setEnd", [t]); }
    createAddVideoTransitionAction(tr, opt) { return action("addTransition", [tr, opt]); }
  }

  const clips = opts.clips || [new VideoClipTrackItem("A", 0, 2, 3600, 0), new VideoClipTrackItem("B", 2, 5, 0, 1)];
  const selection = { async getTrackItems() { return opts.selected || clips; } };
  const track = {
    getTrackItems(type, includeEmpty) {
      if (type === undefined || includeEmpty === undefined) throw new Error("Not Enough Parameters");
      return clips.filter((c) => c._t === 0);
    },
  };
  const settings = { async getVideoFrameRate() { return { value: opts.fps === undefined ? 30000 / 1001 : opts.fps }; } };
  const sequence = {
    async getSelection() { return selection; },
    async getVideoTrack() { return track; },
    async getVideoTrackCount() { return 1; },
    async getAudioTrack() { return track; },
    async getSettings() { return opts.noFrameRateMethod ? {} : settings; },
    async getPlayerPosition() { return TickTime.createWithSeconds(0); },
  };
  const project = {
    lockedAccess(cb) {
      if (cb.constructor.name === "AsyncFunction") throw new Error("lockedAccess のコールバックは同期のみ");
      inLock = true;
      log.locked += 1;
      try { cb(); } finally { inLock = false; }
    },
    executeTransaction(cb, label) {
      guard("executeTransaction");
      if (cb.constructor.name === "AsyncFunction") throw new Error("executeTransaction のコールバックは同期のみ");
      const added = [];
      const ca = {
        addAction(a) {
          if (!a || !a.__action || opts.rejectAction === a.__action) throw new Error("Invalid parameter.");
          added.push(a);
        },
      };
      cb(ca);
      log.transactions.push({ label, actions: added });
      log.actions.push(...added);
      return opts.commitResult === undefined ? true : opts.commitResult;
    },
    async getActiveSequence() { return opts.noSequence ? null : sequence; },
  };
  const markersApi = {
    createAddMarkerAction(name, type, start, duration, comment) { return action("addMarker", [name, type, start, duration, comment]); },
  };
  class AddTransitionOptions {
    setApplyToStart(v) { this.start = v; }
    setDuration(t) { this.duration = t; }
    setForceSingleSided(v) { this.single = v; }
  }
  const ppro = {
    TickTime,
    PointF,
    AddTransitionOptions,
    Constants: { TrackItemType: { CLIP: 1 } },
    Marker: { MARKER_TYPE_COMMENT: "Comment" },
    Project: { async getActiveProject() { return opts.noProject ? null : project; } },
    Markers: { async getMarkers() { return markersApi; } },
    VideoFilterFactory: { async createComponent(mn) { return { matchName: mn }; } },
    TransitionFactory: { async createVideoTransition(mn) { return { matchName: mn }; } },
    SequenceEditor: { async getEditor() { return { insertMogrtFromPath() {}, createOverwriteItemAction() {} }; } },
    Exporter: { async exportSequenceFrame(seq, t, name, folder, w, h) { log.exports.push({ name, folder, w, h }); return true; } },
  };
  return { ppro, project, sequence, clips, log, chain, motion, VideoClipTrackItem };
}

module.exports = { makeFake, TickTime, PointF, TPS };
```

`tests/js/load_parts.js`:

```js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const PARTS = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts");

// 部品を Premiere の UXP に近い条件（module も require も無いページ）で読み込む
function loadParts(files, extra = {}) {
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, ...extra });
  for (const f of files) {
    vm.runInContext(fs.readFileSync(path.join(PARTS, f), "utf8"), ctx, { filename: f });
  }
  return ctx;
}

// vm の中のオブジェクトは deepStrictEqual が通らないので、JSON で写して比べる
function plain(v) { return JSON.parse(JSON.stringify(v)); }

module.exports = { loadParts, plain, PARTS };
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/js/ppro_kit.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake, TPS } = require("./fake_ppro");

function kit(opts) {
  const fake = makeFake(opts);
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null, tag: "t" });
  return { PPM: ctx.PPM, fake };
}

test("プロジェクトが無いと 3 点つきのエラー", async () => {
  const { PPM } = kit({ noProject: true });
  await assert.rejects(PPM.getProjectAndSequence(), (e) => e.ppm && e.ppm.symptom.includes("プロジェクト") && e.ppm.next.length > 0);
});

test("選択したクリップを ticks と秒で返す", async () => {
  const { PPM } = kit();
  const { sequence } = await PPM.getProjectAndSequence();
  const clips = await PPM.getSelectedClips(sequence);
  assert.equal(clips.length, 2);
  assert.equal(clips[0].kind, "video");
  assert.equal(clips[1].startTicks, 2 * TPS);
  assert.equal(clips[1].endSeconds, 5);
});

test("transact はロックの中で Action を作り、件数を返す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  const r = PPM.transact(project, "終わりを動かす", (add) => { add("end", () => fake.clips[0].createSetEndAction(PPM.time(1))); });
  assert.equal(r.ok, true);
  assert.equal(r.added, 1);
  assert.equal(fake.log.transactions[0].label, "終わりを動かす");
});

test("Premiere が受け付けないとエラーにする", async () => {
  const { PPM, fake } = kit({ commitResult: false });
  const { project } = await PPM.getProjectAndSequence();
  assert.throws(() => PPM.transact(project, "u", (add) => add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)))), /受け付けませんでした/);
});

test("1 つ弾かれても残りは足す。全部弾かれたら成功と言わない", async () => {
  const { PPM, fake } = kit({ rejectAction: "setEnd" });
  const { project } = await PPM.getProjectAndSequence();
  assert.throws(() => PPM.transact(project, "u", (add) => add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)))), /どの変更も/);
  const r = PPM.transact(project, "u2", (add) => {
    add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)));
    add("tr", () => fake.clips[0].createAddVideoTransitionAction({}, {}));
  });
  assert.equal(r.added, 1);
  assert.equal(r.warnings.length, 1);
});

test("キーは入点を足した素材時間に打ち、余分なキーを範囲で消す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  const scale = fake.motion.params[1];
  PPM.transact(project, "zoom", (add) => { PPM.keyframeActions(add, scale, 3600, [{ t: 0, value: 100 }, { t: 2, value: 110 }]); });
  const names = fake.log.actions.map((a) => a.__action);
  assert.deepEqual(names, ["removeKeyframeRange", "setTimeVarying", "addKeyframe", "addKeyframe", "removeKeyframeRange"]);
  assert.equal(fake.log.actions[3].args[0].position.seconds, 3602);
});

test("findParam は表示名の日本語・英語どちらでも見つける", async () => {
  const { PPM, fake } = kit();
  const found = await PPM.findParam(fake.clips[0], ["AE.ADBE Motion"], ["Scale", "スケール"]);
  assert.equal(found.index, 1);
  assert.equal(await PPM.findParam(fake.clips[0], ["AE.ADBE Opacity"], ["Opacity"]), null);
});

test("効果はテキストの部品の手前に差す", async () => {
  const { PPM, fake } = kit({ withText: true });
  const { project } = await PPM.getProjectAndSequence();
  await PPM.addEffect(project, fake.clips[0], "AE.ADBE Geometry2");
  const a = fake.log.actions[0];
  assert.equal(a.__action, "insertComponent");
  assert.equal(a.args[1], 1);
});

test("トランジションの長さは ticks で渡す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  await PPM.addTransition(project, fake.clips[0], "AE.ADBE Cross Dissolve New", 0.5, true);
  assert.equal(fake.log.actions[0].args[1].duration.ticksNumber, 0.5 * TPS);
});

test("マーカーは 1 件ずつ Action にする", async () => {
  const { PPM, fake } = kit();
  const { project, sequence } = await PPM.getProjectAndSequence();
  await PPM.addMarkers(project, sequence, [{ seconds: 1, name: "a" }, { seconds: 2, name: "b", comment: "c" }]);
  assert.equal(fake.log.actions.length, 2);
  assert.equal(fake.log.actions[1].args[4], "c");
});

test("フレームレート: 29.97 は 30 の NTSC。読めなければ 30 を詰めない", async () => {
  let { PPM } = kit();
  let { sequence } = await PPM.getProjectAndSequence();
  const fr = await PPM.getFrameRate(sequence);
  assert.equal(fr.timebase, 30);
  assert.equal(fr.ntsc, true);
  ({ PPM } = kit({ noFrameRateMethod: true }));
  ({ sequence } = await PPM.getProjectAndSequence());
  const none = await PPM.getFrameRate(sequence);
  assert.equal(none.detected, false);
  assert.ok(Number.isNaN(none.fps));
});

test("findClip は getTrackItems に引数 2 つを渡す", async () => {
  const { PPM } = kit();
  const { sequence } = await PPM.getProjectAndSequence();
  const found = await PPM.findClip(sequence, "video", 0, 0);
  assert.equal(await found.getName(), "A");
});

test("ticksOf は ticksNumber → ticks → seconds の順に読む", () => {
  const { PPM } = kit();
  assert.equal(PPM.ticksOf({ ticksNumber: 5, ticks: "0" }), 5);
  assert.equal(PPM.ticksOf({ ticks: "7" }), 7);
  assert.equal(PPM.ticksOf({ seconds: 1 }), TPS);
  assert.equal(PPM.ticksOf(null), 0);
});
```

`tests/js/logger_probe.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts, plain } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

function memUxp() {
  const files = {};
  const folder = {
    nativePath: "/tmp/作業 フォルダ/PluginData",
    async createFile(name) {
      return {
        nativePath: `${folder.nativePath}/${name}`,
        async write(text) { files[name] = text; },
      };
    },
    async getEntry(name) { if (!(name in files)) throw new Error("無い"); return { name }; },
  };
  return {
    files,
    uxp: {
      host: { name: "premierepro", version: "26.5.2" },
      versions: { uxp: "9.4.0" },
      storage: { localFileSystem: { async getDataFolder() { return folder; } }, formats: { utf8: "utf8" } },
    },
  };
}

test("ログは console と ppm-log.txt に同じ行を書き、最後の maxLines 行だけ残す", async () => {
  const mem = memUxp();
  const ctx = loadParts(["logger/lib/ppm-logger.js"]);
  ctx.PPM.log.init({ uxp: mem.uxp, tag: "zoom", maxLines: 3 });
  for (let i = 0; i < 5; i++) ctx.PPM.log.info(`行${i}`, { i });
  assert.equal(ctx.PPM.log.lines().length, 3);
  assert.equal(await ctx.PPM.log.flush(), true);
  assert.match(mem.files["ppm-log.txt"], /\[zoom\] INFO 行4 \{"i":4\}/);
  assert.equal(await ctx.PPM.log.filePath(), "/tmp/作業 フォルダ/PluginData/ppm-log.txt");
});

test("probe は無い API を missing と書き、ログの場所を返す", async () => {
  const mem = memUxp();
  const fake = makeFake();
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: mem.uxp, tag: "p" });
  const r = plain(await ctx.PPM.probe.run());
  assert.equal(r.statics["Project.getActiveProject"], "function");
  assert.equal(r.statics["ProjectConverter.exportAsFinalCutProXML"], "missing");
  assert.equal(r.live["settings.getVideoFrameRate"], "function");
  assert.equal(r.host.version, "26.5.2");
  assert.ok(r.logFile.endsWith("ppm-log.txt"));
});
```

`tests/js/ui_kit.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

function el(initial = {}) {
  const attrs = {};
  const handlers = {};
  return Object.assign({
    textContent: "", value: null,
    setAttribute(k, v) { attrs[k] = String(v); }, getAttribute(k) { return k in attrs ? attrs[k] : null; },
    removeAttribute(k) { delete attrs[k]; }, addEventListener(t, f) { (handlers[t] = handlers[t] || []).push(f); },
    fire(t) { (handlers[t] || []).forEach((f) => f()); }, attrs,
  }, initial);
}

test("showError は症状・なぜ・次の一手の 3 行にする", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const box = el();
  const e = new Error("x");
  e.ppm = { symptom: "クリップが選ばれていません", why: "選んだクリップに対して行います", next: "選んでから押してください" };
  ctx.PPM.ui.showError(box, e);
  assert.equal(box.attrs["data-state"], "error");
  assert.equal(box.textContent.split("\n").length, 3);
});

test("空欄や null は既定値にする", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: null }), 2), 2);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: "" }), 2), 2);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: "1.5" }), 2), 1.5);
  assert.equal(ctx.PPM.ui.textValue(el({ value: null })), "");
});

test("busy はボタンの文字を戻す", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const b = el({ textContent: "実行" });
  ctx.PPM.ui.busy(b, true, "処理中…");
  assert.equal(b.textContent, "処理中…");
  ctx.PPM.ui.busy(b, false);
  assert.equal(b.textContent, "実行");
  assert.equal(b.getAttribute("disabled"), null);
});

test("ホイール直後の select の変更は戻す", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const s = el({ value: "a" });
  ctx.PPM.ui.protectSelect(s);
  s.fire("wheel");
  s.value = "b";
  s.fire("change");
  assert.equal(s.value, "a");
});
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `node --test tests/js/*.test.js`
Expected: FAIL（`ENOENT` で部品のファイルが無い）

- [ ] **Step 4: 部品を書く**

`SKILL/parts/logger/lib/ppm-logger.js`:

```js
/* ppm-logger — パネルのログを 2 か所に書く。
 *  1) console.log（Mac では Premiere の UXP ログ UXPLogs_*.log に出る）
 *  2) プラグインのデータフォルダの ppm-log.txt（Windows でも場所が決まる。AI は logs.py で読む）
 * ファイルへは最後の maxLines 行を 0.3 秒ごとにまとめて書き直す（追記の作法に頼らない）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const state = { uxp: null, tag: "ppm", fileName: "ppm-log.txt", maxLines: 500, lines: [], timer: null, folder: null, path: "" };

  function safeJson(data) {
    if (data === undefined) return "";
    try { return " " + JSON.stringify(data); } catch (e) { return " [文字にできないデータ]"; }
  }

  function write(level, msg, data) {
    const line = `${new Date().toISOString()} [${state.tag}] ${level} ${msg}${safeJson(data)}`;
    try { console.log(line); } catch (e) { /* 出せなくても続ける */ }
    state.lines.push(line);
    if (state.lines.length > state.maxLines) state.lines.splice(0, state.lines.length - state.maxLines);
    schedule();
    return line;
  }

  function schedule() {
    if (state.timer || !state.uxp) return;
    state.timer = setTimeout(() => { state.timer = null; flush().catch(() => {}); }, 300);
  }

  async function dataFolder() {
    if (state.folder) return state.folder;
    const lfs = state.uxp && state.uxp.storage && state.uxp.storage.localFileSystem;
    if (!lfs || typeof lfs.getDataFolder !== "function") return null;
    state.folder = await lfs.getDataFolder();
    return state.folder;
  }

  async function flush() {
    const folder = await dataFolder();
    if (!folder) return false;
    const file = await folder.createFile(state.fileName, { overwrite: true });
    const formats = state.uxp.storage.formats;
    await file.write(state.lines.join("\n") + "\n", formats ? { format: formats.utf8 } : undefined);
    state.path = file.nativePath || "";
    return true;
  }

  async function filePath() {
    if (state.path) return state.path;
    let folder = null;
    try { folder = await dataFolder(); } catch (e) { folder = null; }
    if (!folder || !folder.nativePath) return "";
    const sep = String(folder.nativePath).indexOf("\\") >= 0 ? "\\" : "/";
    return folder.nativePath + sep + state.fileName;
  }

  PPM.log = {
    init(opts) {
      const o = opts || {};
      state.uxp = o.uxp || null;
      if (o.tag) state.tag = o.tag;
      if (o.fileName) state.fileName = o.fileName;
      if (o.maxLines) state.maxLines = o.maxLines;
    },
    info(msg, data) { return write("INFO", msg, data); },
    warn(msg, data) { return write("WARN", msg, data); },
    error(msg, data) { return write("ERROR", msg, data); },
    flush,
    filePath,
    lines() { return state.lines.slice(); },
  };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/ppro-kit/lib/ppm-ppro-kit.js`:

```js
/* ppm-ppro-kit — Premiere の UXP API を安全に使うための型（Cut & SRT と Effect & Design で実機確認した書き方）。
 * 決まり:
 *  - 取引（lockedAccess → executeTransaction）のコールバックは完全に同期。中で await しない。
 *  - Action は取引の中で作る（Premiere 26.3 から必須）。非同期の取得は取引の前に済ませる。
 *  - Action は 1 つずつ足して、失敗を個別に拾う（まとめると 1 つ弾かれただけで全部落ちる）。
 *  - executeTransaction の戻り値 false を必ず見る。全部失敗したら成功と言わない。
 *  - TrackItem のハンドルは保存しない。使う直前に取り直す。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const TICKS_PER_SECOND = 254016000000;
  const BIG_SECONDS = 100000; // 素材時間の上限（MOGRT の入点は約 3600 秒）
  const state = { ppro: null, uxp: null };

  function init(opts) {
    const o = opts || {};
    state.ppro = o.ppro || null;
    state.uxp = o.uxp || null;
    if (PPM.log && typeof PPM.log.init === "function") PPM.log.init({ uxp: o.uxp, tag: o.tag });
  }
  function modules() { return { ppro: state.ppro, uxp: state.uxp }; }

  function err(symptom, why, next) {
    const e = new Error(symptom);
    e.ppm = { symptom, why: why || "", next: next || "" };
    return e;
  }

  function ppro() {
    if (!state.ppro) {
      throw err("Premiere の機能が使えません", "Premiere の外で開いているか、PPM.init が呼ばれていません",
        "Premiere の［ウィンドウ］→［UXP プラグイン］から開き直してください");
    }
    return state.ppro;
  }

  async function resolve(v) { return v && typeof v.then === "function" ? await v : v; }

  function ticksOf(t) {
    if (!t) return 0;
    if (typeof t.ticksNumber === "number") return t.ticksNumber;
    if (t.ticks !== undefined && t.ticks !== null && t.ticks !== "") return Number(t.ticks); // ppm-ignore: J010
    if (typeof t.seconds === "number") return Math.round(t.seconds * TICKS_PER_SECOND);
    return 0;
  }
  function secondsOf(t) {
    if (!t) return 0;
    if (typeof t.seconds === "number") return t.seconds;
    return ticksOf(t) / TICKS_PER_SECOND;
  }
  function time(seconds) { return ppro().TickTime.createWithSeconds(Number(seconds)); }
  function timeFromTicks(ticks) { return ppro().TickTime.createWithTicks(String(Math.round(Number(ticks)))); }

  async function getProjectAndSequence() {
    const project = await ppro().Project.getActiveProject();
    if (!project) {
      throw err("プロジェクトが開かれていません", "この操作は開いているプロジェクトに対して行います", "Premiere でプロジェクトを開いてから、もう一度押してください");
    }
    const sequence = await project.getActiveSequence();
    if (!sequence) {
      throw err("シーケンスが開かれていません", "この操作はタイムラインに出ているシーケンスに対して行います", "シーケンスをタイムラインに開いてから、もう一度押してください");
    }
    return { project, sequence };
  }

  function clipKind(item) {
    // getMediaType は Guid を返すので数値で比べられない。クラス名で分ける
    const n = item && item.constructor && item.constructor.name;
    if (n === "VideoClipTrackItem") return "video";
    if (n === "AudioClipTrackItem") return "audio";
    return "unknown";
  }

  async function describeClip(item) {
    const start = await item.getStartTime();
    const end = await item.getEndTime();
    return {
      item,
      name: (await resolve(item.getName())) || "",
      trackIndex: await resolve(item.getTrackIndex()),
      kind: clipKind(item),
      startTicks: ticksOf(start),
      endTicks: ticksOf(end),
      startSeconds: secondsOf(start),
      endSeconds: secondsOf(end),
    };
  }

  async function getSelectedClips(sequence) {
    const sel = await sequence.getSelection();
    const items = sel ? (await resolve(sel.getTrackItems())) || [] : [];
    const out = [];
    for (const item of items) {
      try { out.push(await describeClip(item)); }
      catch (e) { if (PPM.log) PPM.log.warn("選択の読み取りに失敗", { message: String((e && e.message) || e) }); }
    }
    return out;
  }

  function clipType() {
    const C = state.ppro && state.ppro.Constants && state.ppro.Constants.TrackItemType;
    return C && C.CLIP !== undefined ? C.CLIP : 1;
  }

  async function listTrackClips(sequence, kind, trackIndex) {
    const track = kind === "audio" ? await sequence.getAudioTrack(trackIndex) : await sequence.getVideoTrack(trackIndex);
    if (!track) return [];
    return (await resolve(track.getTrackItems(clipType(), false))) || [];
  }

  async function findClip(sequence, kind, trackIndex, startTicks) {
    for (const it of await listTrackClips(sequence, kind, trackIndex)) {
      if (ticksOf(await it.getStartTime()) === Number(startTicks)) return it;
    }
    return null;
  }

  function transact(project, label, build) {
    const result = { ok: false, added: 0, warnings: [] };
    project.lockedAccess(() => {
      result.ok = project.executeTransaction((ca) => {
        const add = (what, make) => {
          try { ca.addAction(make()); result.added += 1; return true; }
          catch (e) { result.warnings.push(`${what}: ${String((e && e.message) || e)}`); return false; }
        };
        build(add);
      }, label) !== false;
    });
    if (!result.ok) {
      throw err("Premiere が変更を受け付けませんでした", "トラックがロックされているか、対象のクリップが消えた可能性があります",
        "トラックのロックを外し、対象を選び直してから、もう一度押してください");
    }
    if (result.added === 0 && result.warnings.length) {
      throw err("どの変更も受け付けられませんでした", result.warnings.slice(0, 3).join(" / "), "診断ボタンを押し、表示された内容を AI に伝えてください");
    }
    return result;
  }

  function toValue(v) {
    const P = state.ppro && state.ppro.PointF;
    if (Array.isArray(v) && v.length === 2 && P) return new P(Number(v[0]), Number(v[1]));
    return v;
  }

  async function findParam(item, componentMatchNames, paramNames) {
    const chain = await item.getComponentChain();
    const count = await resolve(chain.getComponentCount());
    for (let i = 0; i < count; i++) {
      const comp = await resolve(chain.getComponentAtIndex(i));
      const mn = await resolve(comp.getMatchName());
      if (componentMatchNames.indexOf(mn) < 0) continue;
      const pc = await resolve(comp.getParamCount());
      for (let k = 0; k < pc; k++) {
        const param = await resolve(comp.getParam(k));
        if (param && paramNames.indexOf(param.displayName) >= 0) return { component: comp, param, index: k, chain };
      }
    }
    return null;
  }

  // ppm: action-builder
  function keyframeActions(add, param, inPointSeconds, keys) {
    add("キーを消す", () => param.createRemoveKeyframeRangeAction(time(0), time(BIG_SECONDS)));
    add("時間変化をオン", () => param.createSetTimeVaryingAction(true));
    let n = 0;
    for (const k of keys) {
      const at = inPointSeconds + Number(k.t); // キーの時刻は素材時間（クリップの入点からの位置）
      if (add("キー", () => { const kf = param.createKeyframe(toValue(k.value)); kf.position = time(at); return param.createAddKeyframeAction(kf); })) n += 1;
    }
    // 時間変化をオンにすると時刻 0 に余分なキーが増える（再生ヘッドが 0 のとき）。入点より前を範囲で消す
    if (inPointSeconds > 0.001) add("余分なキーを消す", () => param.createRemoveKeyframeRangeAction(time(0), time(inPointSeconds - 0.0005)));
    return n;
  }

  // ppm: action-builder
  function setValueAction(add, param, value) {
    return add("値", () => param.createSetValueAction(param.createKeyframe(toValue(value)), false));
  }

  async function textComponentIndex(chain) {
    const count = await resolve(chain.getComponentCount());
    for (let i = 0; i < count; i++) {
      const comp = await resolve(chain.getComponentAtIndex(i));
      if ((await resolve(comp.getMatchName())) === "AE.ADBE Text") return i;
    }
    return -1;
  }

  async function addEffect(project, item, matchName) {
    const filter = await ppro().VideoFilterFactory.createComponent(matchName); // 部品は取引の外で作る
    const chain = await item.getComponentChain();
    const at = await textComponentIndex(chain); // テキストの部品の手前に差す（末尾だと文字の下になる）
    // 足した効果は取引が確定するまで設定項目を持たない。値を変えるときは、別の取引で取り直してから
    return transact(project, `効果を追加: ${matchName}`, (add) => {
      if (at >= 0) add("効果", () => chain.createInsertComponentAction(filter, at));
      else add("効果", () => chain.createAppendComponentAction(filter));
    });
  }

  async function addTransition(project, item, matchName, seconds, atStart) {
    const P = ppro();
    const transition = await resolve(P.TransitionFactory.createVideoTransition(String(matchName)));
    const opt = new P.AddTransitionOptions();
    if (typeof opt.setApplyToStart === "function") opt.setApplyToStart(!!atStart);
    // 長さは ticks で渡す（秒で渡すとコマ単位に切り捨てられた: 0.5 秒 → 14 コマ）
    if (typeof opt.setDuration === "function") opt.setDuration(timeFromTicks(Number(seconds) * TICKS_PER_SECOND));
    if (typeof opt.setForceSingleSided === "function") opt.setForceSingleSided(true);
    return transact(project, `トランジション: ${matchName}`, (add) => {
      add("トランジション", () => item.createAddVideoTransitionAction(transition, opt));
    });
  }

  async function addMarkers(project, sequence, markers) {
    const P = ppro();
    const api = await P.Markers.getMarkers(sequence);
    const type = (P.Marker && P.Marker.MARKER_TYPE_COMMENT) || "Comment";
    return transact(project, "マーカーを追加", (add) => {
      for (const m of markers) {
        add(m.name || "マーカー", () => api.createAddMarkerAction(String(m.name || ""), type, time(m.seconds), time(m.duration || 0), String(m.comment || "")));
      }
    });
  }

  function joinPath(folder, name) {
    const f = String(folder);
    const sep = f.indexOf("\\") >= 0 ? "\\" : "/";
    return f.replace(/[\\/]+$/, "") + sep + name;
  }

  async function exportFrame(sequence, seconds, fileName, opts) {
    const o = opts || {};
    const lfs = state.uxp && state.uxp.storage && state.uxp.storage.localFileSystem;
    if (!lfs) throw err("書き出し先を用意できません", "UXP の保存の機能が見つかりません", "Premiere の中で開いてください");
    const folder = await lfs.getDataFolder();
    const ok = await resolve(ppro().Exporter.exportSequenceFrame(sequence, time(seconds), fileName, folder.nativePath, o.width || 1920, o.height || 1080));
    // 返事が来ても書き終わっていないことがある（Cut&SRT 2026-10-05）。ファイルができるのを待つ
    const deadline = Date.now() + (o.timeoutMs || 15000);
    while (Date.now() < deadline) {
      for (const name of [fileName, fileName + ".png"]) {
        try { if (await folder.getEntry(name)) return joinPath(folder.nativePath, name); } catch (e) { /* まだ無い */ }
      }
      await new Promise((r) => setTimeout(r, 300));
    }
    throw err("コマの書き出しが終わりませんでした", ok === false ? "Premiere が書き出しを受け付けませんでした" : "待ってもファイルができませんでした",
      "プレイヘッドをその時刻に置いてから、もう一度試してください");
  }

  async function getFrameRate(sequence) {
    try {
      const settings = await sequence.getSettings();
      if (settings && typeof settings.getVideoFrameRate === "function") { // ppm-ignore: J014
        const fr = await settings.getVideoFrameRate(); // ppm-ignore: J014
        const fps = fr && typeof fr.value === "number" ? fr.value : NaN;
        if (Number.isFinite(fps) && fps > 0) {
          // 許容 0.01（60 と 59.94 の差 0.06 を同じと見なさない）
          let timebase = Math.round(fps);
          let ntsc = false;
          if (Math.abs(fps - 29.97) < 0.01) { timebase = 30; ntsc = true; }
          else if (Math.abs(fps - 23.976) < 0.01) { timebase = 24; ntsc = true; }
          else if (Math.abs(fps - 59.94) < 0.01) { timebase = 60; ntsc = true; }
          return { fps: ntsc ? (timebase * 1000) / 1001 : timebase, timebase, ntsc, detected: true };
        }
      }
    } catch (e) {
      if (PPM.log) PPM.log.warn("フレームレートを読めません", { message: String((e && e.message) || e) });
    }
    return { fps: NaN, timebase: null, ntsc: null, detected: false }; // 読めないときに 30 を詰めない（30 決め打ちで壊した事故あり）
  }

  function hostInfo() {
    const u = state.uxp;
    const host = (u && u.host) || {};
    let os = "";
    try { os = require("os").platform(); } catch (e) { os = ""; }
    return { app: host.name || "", version: host.version || "", uxp: (u && u.versions && u.versions.uxp) || "", os };
  }

  Object.assign(PPM, {
    TICKS_PER_SECOND, init, modules, err, resolve, ticksOf, secondsOf, time, timeFromTicks, getProjectAndSequence,
    describeClip, getSelectedClips, listTrackClips, findClip, transact, toValue, findParam, keyframeActions,
    setValueAction, addEffect, addTransition, addMarkers, exportFrame, getFrameRate, hostInfo, joinPath,
  });
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/ui-kit/lib/ppm-ui-kit.js`:

```js
/* ppm-ui-kit — 結果の表示・ボタンの処理中・空欄の値・select の誤操作（Cut & SRT で実機で踏んだ対策）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  function setState(el, state, text) {
    if (!el) return;
    el.setAttribute("data-state", state);
    el.textContent = text;
  }
  function showOk(el, text) { setState(el, "ok", text); }
  function showInfo(el, text) { setState(el, "info", text); }
  function showError(el, e) {
    const p = e && e.ppm;
    const text = p ? `${p.symptom}\nなぜ: ${p.why}\n次の一手: ${p.next}` : `うまくいきませんでした: ${String((e && e.message) || e)}`;
    setState(el, "error", text);
  }
  function busy(button, on, label) {
    if (!button) return;
    if (on) {
      if (!button.getAttribute("data-label")) button.setAttribute("data-label", button.textContent);
      button.textContent = label || "処理中…";
      button.setAttribute("disabled", "");
    } else {
      const saved = button.getAttribute("data-label");
      if (saved) button.textContent = saved;
      button.removeAttribute("data-label");
      button.removeAttribute("disabled");
    }
  }
  // UXP の空欄の value は null のことがある（"null" が混ざる・NaN が設定を壊す事故があった）
  function textValue(el) {
    if (!el) return "";
    const v = el.value;
    return v === null || v === undefined ? "" : String(v);
  }
  function numberValue(el, fallback) {
    const n = parseFloat(textValue(el));
    return Number.isFinite(n) ? n : fallback;
  }
  // select の上でホイールを回すと値が勝手に変わる。ホイールから 300ms 以内の変更は戻す
  function protectSelect(select) {
    if (!select) return;
    let lastWheel = 0;
    let committed = select.value;
    select.addEventListener("wheel", () => { lastWheel = Date.now(); });
    select.addEventListener("change", () => {
      if (Date.now() - lastWheel < 300) { select.value = committed; return; }
      committed = select.value;
    });
  }

  PPM.ui = { showOk, showInfo, showError, busy, textValue, numberValue, protectSelect };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/ui-kit/lib/ppm-ui-kit.css`:

```css
/* ppm-ui-kit — UXP で崩れにくい見た目の決まり（Cut & SRT で実機確認した対策入り）。
 * - grid は使わない（UXP は非対応）。並べるのは flex だけ
 * - flex の子は中身より小さく潰れることがある → 一覧の行と page の子は縮めない
 * - <title> は隠す（パネルに文字として出る） */
:root {
  --ppm-bg: #1e1e1e;
  --ppm-panel: #262626;
  --ppm-line: #3a3a3a;
  --ppm-text: #e6e6e6;
  --ppm-sub: #a8a8a8;
  --ppm-accent: #2b5bd7;
  --ppm-accent-text: #ffffff;
  --ppm-ok: #3fb26b;
  --ppm-error: #e5534b;
  --ppm-info: #5a9bd5;
}
html, body { height: 100%; margin: 0; background: var(--ppm-bg); color: var(--ppm-text); font-size: 12px; }
title { display: none; }
.ppm-app { display: flex; flex-direction: column; height: 100%; }
.ppm-header { display: flex; flex-direction: row; align-items: center; padding: 10px 12px 6px; flex-shrink: 0; }
.ppm-title { font-size: 14px; font-weight: 700; margin: 0; }
.ppm-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 4px 12px 12px; }
.ppm-page { display: flex; flex-direction: column; }
.ppm-page > * { flex-shrink: 0; margin-bottom: 8px; }
.ppm-list { display: flex; flex-direction: column; overflow-y: auto; }
.ppm-list > * { flex: 0 0 auto; }
.ppm-row { display: flex; flex-direction: row; align-items: center; }
.ppm-row > * { margin-right: 6px; }
.ppm-field { display: flex; flex-direction: column; }
.ppm-label { color: var(--ppm-sub); margin-bottom: 4px; }
.ppm-input { min-width: 0; background: var(--ppm-panel); color: var(--ppm-text); border: 1px solid var(--ppm-line); border-radius: 4px; padding: 4px 6px; }
.ppm-hint { color: var(--ppm-sub); margin: 0; }
.ppm-btn { border: 1px solid var(--ppm-line); border-radius: 4px; padding: 6px 10px; background: var(--ppm-panel); color: var(--ppm-text); }
.ppm-btn-primary { background: var(--ppm-accent); border-color: var(--ppm-accent); color: var(--ppm-accent-text); font-weight: 700; }
.ppm-btn-quiet { background: transparent; }
.ppm-btn[disabled] { opacity: 0.5; }
.ppm-result { white-space: pre-wrap; padding: 8px; border-radius: 4px; border: 1px solid var(--ppm-line); min-height: 18px; }
.ppm-result[data-state="ok"] { border-color: var(--ppm-ok); }
.ppm-result[data-state="error"] { border-color: var(--ppm-error); }
.ppm-result[data-state="info"] { border-color: var(--ppm-info); }
.ppm-footer { display: flex; flex-direction: row; align-items: center; justify-content: space-between; padding: 6px 12px; border-top: 1px solid var(--ppm-line); flex-shrink: 0; }
.ppm-version { color: var(--ppm-sub); }
```

`SKILL/parts/probe/lib/ppm-probe.js`:

```js
/* ppm-probe — 診断ボタン。使う API が、この Premiere に本当にあるかを確かめてログに残す。
 * 公式の文書に載っていても、実装されているとは限らない。実装する前に、ここで確かめてから使う。
 * API の名前は文字列で持つ（check.py の版の検査が、名前だけの記述を誤って拾わないため）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const STATIC = [
    "Project.getActiveProject", "SequenceEditor.getEditor", "Markers.getMarkers", "Exporter.exportSequenceFrame",
    "ProjectConverter.exportAsFinalCutProXML", "VideoFilterFactory.createComponent", "TransitionFactory.createVideoTransition",
    "TickTime.createWithSeconds", "EncoderManager.getManager", "ProjectUtils.getSelection", "WorkAreaUtils",
  ];
  const LIVE = [
    "sequence.getSettings", "sequence.getSelection", "sequence.getVideoTrack", "sequence.getVideoTrackCount",
    "sequence.getPlayerPosition", "settings.getVideoFrameRate", "editor.insertMogrtFromPath",
    "editor.createOverwriteItemAction", "editor.createRazorTrackAction",
  ];

  function kindOf(obj, path) {
    try {
      let cur = obj;
      for (const key of path) {
        if (cur === null || cur === undefined) return "missing";
        cur = cur[key];
      }
      return cur === undefined ? "missing" : typeof cur;
    } catch (e) {
      return "error: " + String((e && e.message) || e);
    }
  }

  async function run(extraStatic) {
    const { ppro } = PPM.modules();
    const report = { at: new Date().toISOString(), host: PPM.hostInfo(), statics: {}, live: {}, logFile: "", notes: [] };
    for (const name of STATIC.concat(extraStatic || [])) report.statics[name] = ppro ? kindOf(ppro, name.split(".")) : "missing";
    try {
      const { project, sequence } = await PPM.getProjectAndSequence();
      const settings = await sequence.getSettings();
      const editor = await ppro.SequenceEditor.getEditor(sequence);
      const live = { project, sequence, settings, editor };
      for (const name of LIVE) {
        const parts = name.split(".");
        report.live[name] = kindOf(live[parts[0]], parts.slice(1));
      }
    } catch (e) {
      report.notes.push("シーケンスを開いてから押すと、もっと詳しく調べられます（" + String((e && e.message) || e) + "）");
    }
    report.logFile = PPM.log ? await PPM.log.filePath() : "";
    if (PPM.log) PPM.log.info("probe", report);
    return report;
  }

  async function runAndShow(el) {
    const r = await run();
    const missing = Object.keys(r.statics).filter((k) => r.statics[k] === "missing")
      .concat(Object.keys(r.live).filter((k) => r.live[k] === "missing"));
    const lines = [
      `Premiere ${r.host.version || "?"}（UXP ${r.host.uxp || "?"}・${r.host.os || "?"}）`,
      `無い API: ${missing.length ? missing.join("、") : "なし"}`,
      `ログ: ${r.logFile || "（場所を確かめられませんでした）"}`,
    ].concat(r.notes);
    if (PPM.ui) PPM.ui.showInfo(el, lines.join("\n"));
    else if (el) el.textContent = lines.join("\n");
    if (PPM.log) { try { await PPM.log.flush(); } catch (e) { /* 書けなくても表示は出す */ } }
    return r;
  }

  PPM.probe = { STATIC, LIVE, kindOf, run, runAndShow };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

4 つの `part.json`（`files` と `scripts` は上の場所に合わせる。状態は Task 36 の実機確認までは `unverified` か `partial`）:

`SKILL/parts/logger/part.json`:

```json
{
  "name": "logger",
  "description": "パネルのログを console とプラグインのデータフォルダの ppm-log.txt に書く。AI は logs.py で読む",
  "status": "unverified",
  "os": ["mac", "windows"],
  "requires": [],
  "files": {"lib/ppm-logger.js": "lib/ppm-logger.js"},
  "scripts": ["lib/ppm-logger.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["core-verification"],
  "notes": "PPM.log.info / warn / error。保存場所は PPM.log.filePath() と、診断ボタンの表示で分かる"
}
```

`SKILL/parts/ppro-kit/part.json`:

```json
{
  "name": "ppro-kit",
  "description": "Premiere の UXP API を安全に使う型（取引・選択・キー・効果・トランジション・マーカー・コマの書き出し・fps）",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["logger"],
  "files": {"lib/ppm-ppro-kit.js": "lib/ppm-ppro-kit.js"},
  "scripts": ["lib/ppm-ppro-kit.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["core-transactions", "core-api-patterns"],
  "notes": "書き方の元は実機で確認済み。この部品としてまとめた形は Task 36 で確かめる"
}
```

`SKILL/parts/ui-kit/part.json`:

```json
{
  "name": "ui-kit",
  "description": "UXP で崩れにくい見た目と、結果の表示・処理中・空欄の値・select の誤操作の対策",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": [],
  "files": {"lib/ppm-ui-kit.js": "lib/ppm-ui-kit.js", "lib/ppm-ui-kit.css": "lib/ppm-ui-kit.css"},
  "scripts": ["lib/ppm-ui-kit.js"],
  "styles": ["lib/ppm-ui-kit.css"],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["core-ui-rules"],
  "notes": "部品の名前は ppm- で始まる。select の対策は Cut&SRT の 3 段の対策を 1 段に縮めたもの"
}
```

`SKILL/parts/probe/part.json`:

```json
{
  "name": "probe",
  "description": "診断ボタン。使う API がこの Premiere にあるかを調べ、版とログの場所と一緒に表示・記録する",
  "status": "unverified",
  "os": ["mac", "windows"],
  "requires": ["ppro-kit", "ui-kit"],
  "files": {"lib/ppm-probe.js": "lib/ppm-probe.js"},
  "scripts": ["lib/ppm-probe.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["core-verification"],
  "notes": "調べたい API は PPM.probe.run([\"クラス.メソッド\"]) で足せる"
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js`
Expected: PASS（ppro-kit 13・logger/probe 2・ui-kit 4）

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: JS の部品（ログ・Premiere 操作の型・見た目・診断）と偽物の premierepro

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: 雛形（_base・panel）と new_plugin.py

**Files:**
- Create: `SKILL/templates/_base/manifest.json`、`index.html`、`index.js`、`panel.css`、`build_info.json`、`README.md`
- Create: `SKILL/templates/panel/template.json`
- Create: `SKILL/scripts/lib/png.py`、`SKILL/scripts/lib/project.py`
- Create: `SKILL/scripts/new_plugin.py`
- Test: `tests/test_new_plugin.py`、`tests/js/template_boot.test.js`

**Interfaces:**
- Consumes: `add_part.add_part`（Task 11。Task 10 の Step 3 では仮の `add_part.py` を置き、Task 11 で中身を書く）、`lib.manifest.version_tuple`、`lib.fsutil`、`lib.osinfo`
- Produces（`lib.project`）: `PROJECT_FILE = Path(".ppm") / "project.json"`、`class ProjectError(ValueError)`、`slugify(name) -> str`、`camel(slug) -> str`、`new_info(name, label=None, plugin_id=None, author=None, min_version="25.6", template="panel", kit_version="") -> dict`（鍵: `name label slug pluginId panelId appName logTag version minVersion template parts kitVersion`）、`placeholders(info) -> dict`（`{{PLUGIN_ID}} {{PLUGIN_NAME}} {{PANEL_ID}} {{PANEL_LABEL}} {{MIN_VERSION}} {{LOG_TAG}} {{APP_NAME}} {{VERSION}} {{SLUG}}`）、`substitute(text, mapping) -> str`、`load(project_dir) -> dict`、`save(project_dir, info) -> None`
- Produces（`lib.png`）: `color_for(text) -> tuple[int, int, int]`、`rounded_icon(size: int, rgb) -> bytes`（PNG のバイト列）
- Produces（`new_plugin`）: `TEXT_SUFFIXES`、`resolve_template(name, templates_dir) -> {"name", "files": Path, "parts": list[str], "minVersion": str}`、`create_project(template, dest, name, label=None, plugin_id=None, author=None, min_version=None, kit_dir=SKILL_DIR) -> {"dest": str, "info": dict, "parts": list[str]}`、`main(argv=None) -> int`（成功 0・既にある 2・入力の誤り 3）
- 雛形の `template.json`: `{"name", "description", "extends"（任意）, "files"（任意。既定 "_base"）, "parts": [...], "minVersion"}`
- 雛形の index.html には印 `<!-- ppm:styles-end -->` と `<!-- ppm:scripts-end -->` を必ず置く（add_part がこの前に足す）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_new_plugin.py`:

```python
import json
import unittest

from helpers import SKILL, run_script, temp_dir

import new_plugin
from lib import checks
from lib import project as projlib


class NewPluginTests(unittest.TestCase):
    def make(self, **kw):
        dest = temp_dir() / "ズーム ボタン"
        result = new_plugin.create_project(kw.pop("template", "panel"), dest, kw.pop("name", "Zoom Button"),
                                           label=kw.pop("label", "ズームボタン"), **kw)
        return dest, result

    def test_panel_project_has_files_parts_and_passes_check(self):
        dest, result = self.make()
        for rel in ("manifest.json", "index.html", "index.js", "panel.css", "build_info.json", "README.md",
                    "icons/icon.png", "icons/icon@2x.png", "lib/ppm-logger.js", "lib/ppm-ppro-kit.js",
                    "lib/ppm-ui-kit.js", "lib/ppm-ui-kit.css", "lib/ppm-probe.js", ".ppm/project.json"):
            self.assertTrue((dest / rel).exists(), rel)
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "com.ppm.zoombutton")
        self.assertEqual(manifest["entrypoints"][0]["label"]["default"], "ズームボタン")
        self.assertEqual(manifest["host"]["minVersion"], "25.6")
        self.assertEqual(result["info"]["parts"], ["logger", "ppro-kit", "ui-kit", "probe"])
        html = (dest / "index.html").read_text(encoding="utf-8")
        order = [html.index(s) for s in ("lib/ppm-logger.js", "lib/ppm-ppro-kit.js", "lib/ppm-ui-kit.js", "lib/ppm-probe.js", "index.js\"")]
        self.assertEqual(order, sorted(order))
        self.assertTrue((dest / "icons" / "icon.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        errors = [f for f in checks.run_all(dest, SKILL) if f.severity == "error"]
        self.assertEqual(errors, [], errors)

    def test_existing_folder_is_never_overwritten(self):
        dest = temp_dir() / "既存"
        dest.mkdir()
        (dest / "index.js").write_text("利用者のコード", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            new_plugin.create_project("panel", dest, "Zoom Button")
        self.assertEqual((dest / "index.js").read_text(encoding="utf-8"), "利用者のコード")
        self.assertFalse((dest / "manifest.json").exists())

    def test_name_needs_ascii_letters_and_label_rejects_quotes(self):
        with self.assertRaises(projlib.ProjectError):
            new_plugin.create_project("panel", temp_dir() / "a", "ズーム")
        with self.assertRaises(projlib.ProjectError):
            new_plugin.create_project("panel", temp_dir() / "b", "Zoom", label='ズーム"ボタン')

    def test_unknown_template_lists_available(self):
        with self.assertRaises(ValueError) as ctx:
            new_plugin.create_project("nope", temp_dir() / "c", "Zoom")
        self.assertIn("panel", str(ctx.exception))

    def test_cli_json_and_exit_codes(self):
        dest = temp_dir() / "cli"
        proc = run_script("new_plugin.py", "--template", "panel", "--name", "Cli Test", "--label", "テスト",
                          "--dest", str(dest), "--json", env={"PYTHONIOENCODING": "cp932"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["info"]["slug"], "cli-test")
        again = run_script("new_plugin.py", "--template", "panel", "--name", "Cli Test", "--dest", str(dest))
        self.assertEqual(again.returncode, 2)
        self.assertIn("上書きしません", again.stdout)


if __name__ == "__main__":
    unittest.main()
```

`tests/js/template_boot.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { PARTS } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

const BASE = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/templates/_base");

function element(id) {
  const handlers = {};
  const attrs = {};
  return {
    id, textContent: "", value: null, handlers,
    addEventListener(t, f) { (handlers[t] = handlers[t] || []).push(f); },
    setAttribute(k, v) { attrs[k] = String(v); }, getAttribute(k) { return k in attrs ? attrs[k] : null; }, removeAttribute(k) { delete attrs[k]; },
  };
}

function boot(readyState) {
  const fake = makeFake();
  const setupCalls = [];
  const elements = {};
  const document = {
    readyState,
    listeners: {},
    getElementById(id) { return (elements[id] = elements[id] || element(id)); },
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); },
  };
  const uxp = {
    entrypoints: { setup(o) { setupCalls.push(o); } },
    host: { name: "premierepro", version: "26.5.2" },
    versions: { uxp: "9.4.0" },
    storage: {
      formats: { utf8: "utf8" },
      localFileSystem: {
        async getDataFolder() { return { nativePath: "/tmp/d", async createFile() { return { async write() {}, nativePath: "/tmp/d/ppm-log.txt" }; }, async getEntry() { throw new Error("無い"); } }; },
        async getPluginFolder() { return { async getEntry() { return { async read() { return '{"name":"T","version":"0.1.0"}'; } }; } }; },
      },
    },
  };
  const requireFake = (name) => { if (name === "uxp") return uxp; if (name === "premierepro") return fake.ppro; throw new Error("Module not found: " + name); };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document, require: requireFake });
  for (const f of ["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "ui-kit/lib/ppm-ui-kit.js", "probe/lib/ppm-probe.js"]) {
    vm.runInContext(fs.readFileSync(path.join(PARTS, f), "utf8"), ctx);
  }
  const src = fs.readFileSync(path.join(BASE, "index.js"), "utf8").replace(/\{\{PANEL_ID\}\}/g, "mainPanel").replace(/\{\{LOG_TAG\}\}/g, "t").replace(/\{\{PLUGIN_NAME\}\}/g, "T");
  vm.runInContext(src, ctx);
  return { ctx, document, elements, setupCalls };
}

test("読み込み済みなら、その場で 1 回だけ起動し、パネルを登録する", () => {
  const { elements, setupCalls, document } = boot("complete");
  assert.equal(setupCalls.length, 1);
  assert.ok(setupCalls[0].panels.mainPanel);
  assert.equal(elements.run.handlers.click.length, 1);
  (document.listeners.DOMContentLoaded || []).forEach((f) => f());
  assert.equal(elements.run.handlers.click.length, 1);
});

test("読み込み中なら DOMContentLoaded を待つ", () => {
  const { elements, document } = boot("loading");
  assert.equal(elements.run, undefined);
  document.listeners.DOMContentLoaded.forEach((f) => f());
  assert.equal(elements.run.handlers.click.length, 1);
});
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_new_plugin.py' -v`
Expected: FAIL（`No module named 'new_plugin'`）

- [ ] **Step 3: 雛形と道具を書く**

`SKILL/templates/_base/manifest.json`（実機で動いた caption-align と Cut & SRT の形に合わせる。`species` は文字列）:

```json
{
  "manifestVersion": 5,
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "{{VERSION}}",
  "main": "index.html",
  "host": {
    "app": "premierepro",
    "minVersion": "{{MIN_VERSION}}",
    "data": {
      "apiVersion": 2,
      "loadEvent": "startup"
    }
  },
  "entrypoints": [
    {
      "type": "panel",
      "id": "{{PANEL_ID}}",
      "label": { "default": "{{PANEL_LABEL}}" },
      "minimumSize": { "width": 260, "height": 240 },
      "maximumSize": { "width": 2000, "height": 2000 },
      "preferredDockedSize": { "width": 320, "height": 460 },
      "preferredFloatingSize": { "width": 360, "height": 520 }
    }
  ],
  "icons": [
    { "width": 24, "height": 24, "path": "icons/icon.png", "scale": [1, 2], "theme": ["all"], "species": "generic" }
  ],
  "requiredPermissions": {
    "localFileSystem": "plugin"
  }
}
```

`SKILL/templates/_base/index.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>{{PLUGIN_NAME}}</title>
  <!-- ppm:styles-start -->
  <!-- ppm:styles-end -->
  <link rel="stylesheet" href="panel.css" />
</head>
<body>
  <div class="ppm-app">
    <header class="ppm-header">
      <h1 class="ppm-title">{{PANEL_LABEL}}</h1>
    </header>
    <main class="ppm-scroll">
      <section class="ppm-page" id="page-main">
        <p class="ppm-hint">タイムラインでクリップを選んでから押してください。</p>
        <button id="run" class="ppm-btn ppm-btn-primary" type="button">実行</button>
        <div id="result" class="ppm-result" data-state="idle"></div>
      </section>
    </main>
    <footer class="ppm-footer">
      <button id="probe" class="ppm-btn ppm-btn-quiet" type="button">診断</button>
      <span id="version" class="ppm-version"></span>
    </footer>
  </div>
  <!-- ppm:scripts-start -->
  <!-- ppm:scripts-end -->
  <script src="index.js"></script>
</body>
</html>
```

`SKILL/templates/_base/index.js`:

```js
/* {{PLUGIN_NAME}} — パネルの本体。
 * 部品（lib/ の PPM.*）は index.html の <script> で先に読み込まれている。require の相対パスは使わない。
 * 起動の処理はこのファイルの末尾で 1 回だけ行う（UXP は読み込みの途中で起動することがあり、
 * 途中で起動すると、後ろで宣言した const を踏んで止まるため）。 */
"use strict";

let ppro = null;
let uxp = null;
try {
  uxp = require("uxp");
  ppro = require("premierepro");
} catch (e) {
  // Premiere の外（下見など）では、画面だけ動かす
}

const APP = { tag: "{{LOG_TAG}}", booted: false };

function $(id) { return document.getElementById(id); }

async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "処理中…");
  try {
    const { sequence } = await PPM.getProjectAndSequence();
    const clips = await PPM.getSelectedClips(sequence);
    if (clips.length === 0) {
      throw PPM.err("クリップが選ばれていません", "この操作は選んだクリップに対して行います", "タイムラインでクリップを選んでから、もう一度押してください");
    }
    // ここに、このプラグインの処理を書く（knowledge/core/core-api-patterns.md の型に合わせる）
    PPM.ui.showOk(out, `${clips.length} 本のクリップを確認しました`);
    PPM.log.info("run ok", { count: clips.length });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("run failed", { message: String((e && e.message) || e) });
  } finally {
    PPM.ui.busy($("run"), false);
  }
}

async function showVersion() {
  try {
    const folder = await uxp.storage.localFileSystem.getPluginFolder();
    const entry = await folder.getEntry("build_info.json");
    const info = JSON.parse(await entry.read({ format: uxp.storage.formats.utf8 }));
    $("version").textContent = `v${info.version}`;
  } catch (e) {
    $("version").textContent = "";
  }
}

function boot() {
  if (APP.booted) return;
  APP.booted = true;
  PPM.init({ ppro, uxp, tag: APP.tag });
  $("run").addEventListener("click", onRun);
  $("probe").addEventListener("click", () => { PPM.probe.runAndShow($("result")); });
  showVersion();
  PPM.log.info("boot", PPM.hostInfo());
}

if (uxp && uxp.entrypoints && typeof uxp.entrypoints.setup === "function") {
  const commands = PPM.commands ? (PPM.commands.define("runMain", onRun), PPM.commands.table()) : {};
  try {
    uxp.entrypoints.setup({
      panels: { "{{PANEL_ID}}": { create() {}, show() {}, hide() {}, destroy() {} } },
      commands,
    });
  } catch (e) {
    // 2 回目の setup は失敗するので無視する
  }
}

// ここから下は動かさない（起動はファイルの末尾で 1 回だけ）
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
```

`SKILL/templates/_base/panel.css`:

```css
/* このプラグイン固有の見た目。共通の決まりは lib/ppm-ui-kit.css にある（grid は使わない・一覧の行は縮めない）。 */
title { display: none; }
```

`SKILL/templates/_base/build_info.json`:

```json
{
  "name": "{{PLUGIN_NAME}}",
  "version": "{{VERSION}}"
}
```

`SKILL/templates/_base/README.md`:

```markdown
# {{PANEL_LABEL}}

Premiere 用のプラグイン（{{PLUGIN_NAME}}・id `{{PLUGIN_ID}}`）。premiere-plugin-maker で作りました。

## Premiere に読み込む（作っている間）

1. UXP Developer Tools を開き、［Add Plugin］でこのフォルダの `manifest.json` を選ぶ
2. ［Load］を押す。直したら［Reload］。`manifest.json` を変えたら［Unload］してから［Load］
3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{{PANEL_LABEL}}」を開く
4. うまく動かないときは「診断」を押し、表示を AI に伝える

UXP Developer Tools に Premiere が出ないときは、Premiere の［設定］→［プラグイン］で開発者モードをオンにして、Premiere を再起動してください。

## ログ

パネルの「診断」に、ログの保存場所が出ます。AI は `logs.py --project <このフォルダ>` で読みます。
```

`SKILL/templates/panel/template.json`:

```json
{
  "name": "panel",
  "description": "パネルだけ（いちばん小さい形）。ログ・Premiere 操作の型・見た目・診断ボタン入り",
  "files": "_base",
  "parts": ["logger", "ppro-kit", "ui-kit", "probe"],
  "minVersion": "25.6"
}
```

`SKILL/scripts/lib/project.py`:

```python
"""利用者のプラグインのフォルダの情報（.ppm/project.json）と、雛形の印の置き換え。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

from . import fsutil

PROJECT_FILE = Path(".ppm") / "project.json"


class ProjectError(ValueError):
    pass


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


def camel(slug: str) -> str:
    return "".join(w.capitalize() for w in slug.split("-") if w)


def new_info(name: str, label: Optional[str] = None, plugin_id: Optional[str] = None, author: Optional[str] = None,
             min_version: str = "25.6", template: str = "panel", kit_version: str = "") -> Dict:
    slug = slugify(name)
    if not slug:
        raise ProjectError("名前に英字を入れてください（例: Zoom Button）。日本語の表示名は --label で付けられます")
    shown = (label or name).strip()
    if any(c in shown for c in '"\\<>{}'):
        raise ProjectError("表示名に \" \\ < > { } は使えません")
    who = slugify(author or "").replace("-", "") or "ppm"
    pid = plugin_id or f"com.{who}.{slug.replace('-', '')}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", pid):
        raise ProjectError(f"id「{pid}」に使えない文字があります（英数字・ピリオド・ハイフンだけ）")
    return {"name": name.strip(), "label": shown, "slug": slug, "pluginId": pid, "panelId": "mainPanel",
            "appName": camel(slug), "logTag": slug, "version": "0.1.0", "minVersion": min_version,
            "template": template, "parts": [], "kitVersion": kit_version}


def placeholders(info: Dict) -> Dict[str, str]:
    return {"{{PLUGIN_ID}}": info["pluginId"], "{{PLUGIN_NAME}}": info["name"], "{{PANEL_ID}}": info["panelId"],
            "{{PANEL_LABEL}}": info["label"], "{{MIN_VERSION}}": info["minVersion"], "{{LOG_TAG}}": info["logTag"],
            "{{APP_NAME}}": info["appName"], "{{VERSION}}": info["version"], "{{SLUG}}": info["slug"]}


def substitute(text: str, mapping: Dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def load(project_dir) -> Dict:
    path = Path(project_dir) / PROJECT_FILE
    if not path.exists():
        raise ProjectError(f"{path} がありません。new_plugin.py で作ったフォルダを指定してください")
    return json.loads(path.read_text(encoding="utf-8"))


def save(project_dir, info: Dict) -> None:
    fsutil.atomic_write_text(Path(project_dir) / PROJECT_FILE, json.dumps(info, ensure_ascii=False, indent=2) + "\n")
```

`SKILL/scripts/lib/png.py`:

```python
"""アイコンの PNG を標準ライブラリだけで作る（角の丸い単色の四角）。"""
from __future__ import annotations

import hashlib
import struct
import zlib
from typing import Tuple

PALETTE = [(43, 91, 215), (63, 178, 107), (229, 83, 75), (230, 160, 40), (140, 90, 220), (40, 170, 190), (210, 80, 150), (110, 120, 135)]


def color_for(text: str) -> Tuple[int, int, int]:
    return PALETTE[hashlib.sha256(text.encode("utf-8")).digest()[0] % len(PALETTE)]


def _inside(x: int, y: int, size: int, r: int) -> bool:
    cx = min(max(x, r), size - 1 - r)
    cy = min(max(y, r), size - 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def rounded_icon(size: int, rgb: Tuple[int, int, int]) -> bytes:
    r = max(2, size // 5)
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            raw += bytes((rgb[0], rgb[1], rgb[2], 255 if _inside(x, y, size, r) else 0))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
```

`SKILL/scripts/new_plugin.py`:

```python
#!/usr/bin/env python3
"""雛形から新しいプラグインの作業フォルダを作る（既にあれば上書きしない）。

使い方:
  Mac:     python3 <このスキル>/scripts/new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン"
  Windows: py -3 <このスキル>\\scripts\\new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン"
  任意: --dest <フォルダ>（既定 ~/PremierePlugins/<名前>）、--id、--author <英字>、--min-version、--json、--list
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import add_part  # noqa: E402
from lib import cli, fsutil, osinfo, png  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
TEXT_SUFFIXES = {".json", ".html", ".js", ".css", ".md", ".txt", ".py", ".jsx", ".xml", ".plist", ".template",
                 ".command", ".ps1", ".bat", ".sh"}


def resolve_template(name: str, templates_dir: Path) -> dict:
    chain = []
    seen = set()
    current = name
    while current:
        if current in seen:
            raise ValueError(f"雛形の extends が輪になっています: {current}")
        seen.add(current)
        path = templates_dir / current / "template.json"
        if not path.exists():
            available = ", ".join(sorted(p.parent.name for p in templates_dir.glob("*/template.json")))
            raise ValueError(f"雛形「{current}」はありません。使えるのは: {available}")
        data = json.loads(path.read_text(encoding="utf-8"))
        chain.append(data)
        current = data.get("extends")
    chain.reverse()
    parts = []
    for t in chain:
        for p in t.get("parts", []):
            if p not in parts:
                parts.append(p)
    min_version = max((t.get("minVersion", "25.6") for t in chain), key=mf.version_tuple)
    return {"name": name, "files": templates_dir / (chain[0].get("files") or "_base"), "parts": parts, "minVersion": min_version}


def create_project(template: str, dest, name: str, label=None, plugin_id=None, author=None, min_version=None,
                   kit_dir: Path = SKILL_DIR) -> dict:
    kit_dir = Path(kit_dir)
    tpl = resolve_template(template, kit_dir / "templates")
    kit_version = (kit_dir / "VERSION").read_text(encoding="utf-8").strip() if (kit_dir / "VERSION").exists() else ""
    info = projlib.new_info(name, label, plugin_id, author, min_version or tpl["minVersion"], template, kit_version)
    dest = Path(dest) if dest else osinfo.default_projects_dir(os.environ, osinfo.detect_os()) / info["slug"]
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"{dest} は既にあります（上書きしません）。別の名前にするか --dest で空のフォルダを指定してください")
    created = not dest.exists()
    try:
        dest.mkdir(parents=True, exist_ok=True)
        mapping = projlib.placeholders(info)
        for src in sorted(p for p in tpl["files"].rglob("*") if p.is_file()):
            target = dest / src.relative_to(tpl["files"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() in TEXT_SUFFIXES:
                fsutil.write_text(target, projlib.substitute(src.read_text(encoding="utf-8"), mapping))
            else:
                shutil.copy2(src, target)
        color = png.color_for(info["slug"])
        (dest / "icons").mkdir(exist_ok=True)
        (dest / "icons" / "icon.png").write_bytes(png.rounded_icon(24, color))
        (dest / "icons" / "icon@1x.png").write_bytes(png.rounded_icon(24, color))
        (dest / "icons" / "icon@2x.png").write_bytes(png.rounded_icon(48, color))
        projlib.save(dest, info)
        installed = []
        for part in tpl["parts"]:
            installed.extend(add_part.add_part(dest, part, kit_dir)["installed"])
        return {"dest": str(dest), "info": projlib.load(dest), "parts": installed}
    except Exception:
        if created:
            shutil.rmtree(dest, ignore_errors=True)
        raise


def _next_steps(dest: str, label: str, os_name: str) -> str:
    py = osinfo.python_command(os_name)
    sep = "\\" if os_name == "windows" else "/"
    return "\n".join([
        f"作りました: {dest}",
        "次にすること:",
        f"  1. UXP Developer Tools の［Add Plugin］で {dest}{sep}manifest.json を選ぶ",
        "  2. ［Load］を押す（直したら［Reload］。manifest.json を変えたら［Unload］→［Load］）",
        f"  3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{label}」を開く",
        f"  4. 「診断」を押し、{py} <このスキル>{sep}scripts{sep}logs.py --project \"{dest}\" で結果を読む",
    ])


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="雛形から新しいプラグインを作る")
    ap.add_argument("--template", default="panel")
    ap.add_argument("--name")
    ap.add_argument("--label")
    ap.add_argument("--dest")
    ap.add_argument("--id", dest="plugin_id")
    ap.add_argument("--author")
    ap.add_argument("--min-version")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    templates = SKILL_DIR / "templates"
    if args.list:
        for p in sorted(templates.glob("*/template.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            print(f"{data['name']}: {data.get('description', '')}")
        return 0
    if not args.name:
        print("--name に英字の名前を入れてください（例: --name \"Zoom Button\" --label \"ズームボタン\"）")
        return 3
    try:
        result = create_project(args.template, args.dest, args.name, args.label, args.plugin_id, args.author, args.min_version)
    except FileExistsError as e:
        print(str(e))
        return 2
    except (ValueError, projlib.ProjectError, add_part.PartError, mf.ManifestError) as e:
        print(str(e))
        return 3
    if args.json:
        cli.print_json(result)
    else:
        print(_next_steps(result["dest"], result["info"]["label"], osinfo.detect_os()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Task 11 の前に new_plugin.py が import できるよう、`SKILL/scripts/add_part.py` を仮に置く（Task 11 の Step 3 で全文に置き換える）:

```python
"""部品を足す（仮。Task 11 で中身を書く）。"""
class PartError(ValueError):
    pass


def add_part(project_dir, name, kit_dir=None, _stack=None):
    raise PartError("add_part.py はまだありません（Task 11）")
```

- [ ] **Step 4: Task 11 を先に終えてからテストを通す**

new_plugin のテストは部品の追加を通るので、Task 11 の Step 3 まで進めてから実行する。

Run: `python3 -m unittest discover -s tests -t tests -p 'test_new_plugin.py' -v && node --test tests/js/template_boot.test.js`
Expected: PASS（Python 5・JS 2）

- [ ] **Step 5: コミット（Task 11 と一緒に）**

Task 11 の Step 5 でまとめてコミットする。

---

### Task 11: add_part.py（部品を足す）と部品の検査

**Files:**
- Modify: `SKILL/scripts/add_part.py`（仮のものを全文に置き換える）
- Test: `tests/test_add_part.py`、`tests/test_parts.py`

**Interfaces:**
- Consumes: `lib.project.load / save / placeholders / substitute`、`lib.manifest.load / save / merge_permissions / merge_feature_flags / add_entrypoints / raise_min_version`、`lib.fsutil.write_text`
- Produces（`add_part`）:
  - 定数 `PART_KEYS`、`SCRIPTS_END = "<!-- ppm:scripts-end -->"`、`STYLES_END = "<!-- ppm:styles-end -->"`、`STATUSES = ("verified", "partial", "unverified")`
  - `class PartError(ValueError)`
  - `list_parts(parts_dir) -> list[str]`、`load_part(name, parts_dir) -> dict`（足りない鍵は既定値で埋める）
  - `add_part(project_dir, name, kit_dir=SKILL_DIR) -> {"part", "installed": list[str], "already": bool, "files": list[str], "manifest": list[str]}`
  - `main(argv=None) -> int`（成功 0・部品やフォルダの誤り 3）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_add_part.py`:

```python
import json
import shutil
import unittest
from pathlib import Path

from helpers import SKILL, run_script, temp_dir

import add_part
import new_plugin
from lib import manifest as mf


def kit_copy() -> Path:
    """本物の雛形と部品を写した一時のキット。テスト用の部品 demo / demo-base を足す。"""
    kit = temp_dir() / "kit"
    shutil.copytree(SKILL / "templates", kit / "templates")
    shutil.copytree(SKILL / "parts", kit / "parts")
    (kit / "VERSION").write_text("0.0.0\n", encoding="utf-8")
    base = kit / "parts" / "demo-base"
    (base / "lib").mkdir(parents=True)
    (base / "lib" / "demo-base.js").write_text("// {{PLUGIN_ID}}\n", encoding="utf-8")
    (base / "part.json").write_text(json.dumps({"name": "demo-base", "description": "d", "status": "unverified", "os": ["mac", "windows"],
                                                "files": {"lib/demo-base.js": "lib/demo-base.js"}, "scripts": ["lib/demo-base.js"]}), encoding="utf-8")
    demo = kit / "parts" / "demo"
    (demo / "lib").mkdir(parents=True)
    (demo / "server").mkdir()
    (demo / "lib" / "demo.js").write_text("const app = '{{APP_NAME}}';\n", encoding="utf-8")
    (demo / "lib" / "demo.css").write_text(".d { color: #fff; }\n", encoding="utf-8")
    (demo / "server" / "job.py").write_text("NAME = 'demo'\n", encoding="utf-8")
    (demo / "part.json").write_text(json.dumps({
        "name": "demo", "description": "テスト用", "status": "unverified", "os": ["mac", "windows"], "requires": ["demo-base"],
        "files": {"lib/demo.js": "lib/demo.js", "lib/demo.css": "lib/demo.css", "server/": "server/"},
        "scripts": ["lib/demo.js"], "styles": ["lib/demo.css"],
        "permissions": {"localFileSystem": "fullAccess", "network": {"domains": "all"}},
        "entrypoints": [{"type": "command", "id": "demoCmd", "label": {"default": "{{PANEL_LABEL}}: デモ"}}],
        "minVersion": "26.2", "pythonDeps": ["numpy"]}, ensure_ascii=False), encoding="utf-8")
    return kit


class AddPartTests(unittest.TestCase):
    def setUp(self):
        self.kit = kit_copy()
        self.dest = temp_dir() / "テスト プロジェクト"
        new_plugin.create_project("panel", self.dest, "Demo Plugin", label="デモ", kit_dir=self.kit)

    def test_adds_files_tags_permissions_and_requires(self):
        r = add_part.add_part(self.dest, "demo", self.kit)
        self.assertEqual(r["installed"], ["demo-base", "demo"])
        self.assertEqual((self.dest / "lib" / "demo.js").read_text(encoding="utf-8"), "const app = 'DemoPlugin';\n")
        self.assertTrue((self.dest / "server" / "job.py").exists())
        html = (self.dest / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index("lib/demo-base.js"), html.index("lib/demo.js"))
        self.assertLess(html.index("lib/demo.js"), html.index('src="index.js"'))
        self.assertIn('<link rel="stylesheet" href="lib/demo.css">', html)
        m = mf.load(self.dest / "manifest.json")
        self.assertEqual(m["requiredPermissions"]["localFileSystem"], "fullAccess")
        self.assertEqual(m["requiredPermissions"]["network"], {"domains": "all"})
        self.assertEqual(m["host"]["minVersion"], "26.2")
        self.assertEqual(m["entrypoints"][-1]["label"]["default"], "デモ: デモ")
        self.assertIn("numpy", (self.dest / "server" / "requirements.txt").read_text(encoding="utf-8"))
        info = json.loads((self.dest / ".ppm" / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(info["parts"][-2:], ["demo-base", "demo"])
        self.assertEqual(info["minVersion"], "26.2")

    def test_second_time_changes_nothing(self):
        add_part.add_part(self.dest, "demo", self.kit)
        before = {p: p.read_bytes() for p in self.dest.rglob("*") if p.is_file()}
        r = add_part.add_part(self.dest, "demo", self.kit)
        self.assertTrue(r["already"])
        after = {p: p.read_bytes() for p in self.dest.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_user_edited_file_is_not_overwritten(self):
        # 先に入る requires の部品（demo-base）は入ってよい。demo の中身は 1 つも書かない
        (self.dest / "lib").mkdir(exist_ok=True)
        (self.dest / "lib" / "demo.js").write_text("利用者の変更\n", encoding="utf-8")
        manifest_before = (self.dest / "manifest.json").read_text(encoding="utf-8")
        with self.assertRaises(add_part.PartError):
            add_part.add_part(self.dest, "demo", self.kit)
        self.assertEqual((self.dest / "lib" / "demo.js").read_text(encoding="utf-8"), "利用者の変更\n")
        self.assertEqual((self.dest / "manifest.json").read_text(encoding="utf-8"), manifest_before)

    def test_broken_manifest_stops_without_writing(self):
        (self.dest / "manifest.json").write_text('{"id": "x",}', encoding="utf-8")
        with self.assertRaises(mf.ManifestError):
            add_part.add_part(self.dest, "demo", self.kit)
        self.assertFalse((self.dest / "lib" / "demo.js").exists())

    def test_missing_marker_is_explained(self):
        html = (self.dest / "index.html").read_text(encoding="utf-8").replace("<!-- ppm:scripts-end -->", "")
        (self.dest / "index.html").write_text(html, encoding="utf-8")
        with self.assertRaises(add_part.PartError) as ctx:
            add_part.add_part(self.dest, "demo", self.kit)
        self.assertIn("ppm:scripts-end", str(ctx.exception))

    def test_unknown_part_lists_available(self):
        with self.assertRaises(add_part.PartError) as ctx:
            add_part.add_part(self.dest, "nope", self.kit)
        self.assertIn("ppro-kit", str(ctx.exception))

    def test_cli_list(self):
        proc = run_script("add_part.py", "--list")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ppro-kit", proc.stdout)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_parts.py`（全部の部品の part.json を検査する。部品が増えるたびに自動で対象になる）:

```python
import json
import unittest

from helpers import PARTS

import add_part
from lib import manifest as mf


class PartsTests(unittest.TestCase):
    def test_every_part_is_well_formed(self):
        names = add_part.list_parts(PARTS)
        self.assertTrue(names)
        for name in names:
            with self.subTest(part=name):
                raw = json.loads((PARTS / name / "part.json").read_text(encoding="utf-8"))
                self.assertEqual(raw["name"], name)
                self.assertFalse(set(raw) - add_part.PART_KEYS, f"知らない項目: {set(raw) - add_part.PART_KEYS}")
                part = add_part.load_part(name, PARTS)
                self.assertIn(part["status"], add_part.STATUSES)
                self.assertTrue(set(part["os"]) <= {"mac", "windows"})
                mf.version_tuple(part["minVersion"])
                targets = {dst for _, dst in add_part._expand_files(PARTS / name, part["files"])}
                for s in part["scripts"] + part["styles"]:
                    self.assertIn(s, targets, f"{s} が files にありません")
                for req in part["requires"]:
                    self.assertIn(req, names, f"requires の {req} がありません")
                for src in part["files"]:
                    self.assertTrue((PARTS / name / src).exists(), src)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_add_part.py' -v`
Expected: FAIL（仮の add_part が `PartError: add_part.py はまだありません` を出す）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/add_part.py`（全文）:

```python
#!/usr/bin/env python3
"""作業フォルダに部品を足す。ファイルを写し、index.html の読み込みと manifest の権限・最低版をそろえる。

使い方:
  Mac:     python3 <このスキル>/scripts/add_part.py <部品> --project <作業フォルダ>
  Windows: py -3 <このスキル>\\scripts\\add_part.py <部品> --project <作業フォルダ>
  --list で使える部品の一覧。同じ部品を 2 回足しても何も変えない。利用者が書き換えたファイルは上書きしない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, fsutil  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
PART_KEYS = {"name", "description", "status", "os", "requires", "files", "scripts", "styles", "permissions",
             "featureFlags", "entrypoints", "minVersion", "pythonDeps", "knowledge", "notes"}
DEFAULTS = {"requires": [], "files": {}, "scripts": [], "styles": [], "permissions": {}, "featureFlags": {},
            "entrypoints": [], "minVersion": "25.6", "pythonDeps": [], "knowledge": [], "notes": "",
            "os": ["mac", "windows"], "status": "unverified"}
STATUSES = ("verified", "partial", "unverified")
SCRIPTS_END = "<!-- ppm:scripts-end -->"
STYLES_END = "<!-- ppm:styles-end -->"
TEXT_SUFFIXES = {".json", ".html", ".js", ".css", ".md", ".txt", ".py", ".jsx", ".xml", ".plist", ".template",
                 ".command", ".ps1", ".bat", ".sh"}


class PartError(ValueError):
    pass


def list_parts(parts_dir: Path = SKILL_DIR / "parts") -> List[str]:
    return sorted(p.parent.name for p in Path(parts_dir).glob("*/part.json"))


def load_part(name: str, parts_dir: Path = SKILL_DIR / "parts") -> Dict:
    path = Path(parts_dir) / name / "part.json"
    if not path.exists():
        raise PartError(f"部品「{name}」はありません。使えるのは: {', '.join(list_parts(parts_dir))}")
    data = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(data) - PART_KEYS
    if unknown:
        raise PartError(f"{path} に知らない項目があります: {', '.join(sorted(unknown))}")
    for key, value in DEFAULTS.items():
        data.setdefault(key, json.loads(json.dumps(value)))
    return data


def _expand_files(part_dir: Path, mapping: Dict[str, str]) -> List[Tuple[Path, str]]:
    out: List[Tuple[Path, str]] = []
    for src_rel, dst_rel in mapping.items():
        src = part_dir / src_rel
        if src.is_dir():
            for p in sorted(x for x in src.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix != ".pyc"):
                out.append((p, (Path(dst_rel) / p.relative_to(src)).as_posix()))
        elif src.is_file():
            out.append((src, dst_rel))
        else:
            raise PartError(f"部品のファイル {src} がありません")
    return out


def _render(src: Path, mapping: Dict[str, str]) -> bytes:
    if src.suffix.lower() in TEXT_SUFFIXES:
        return projlib.substitute(src.read_text(encoding="utf-8"), mapping).encode("utf-8")
    return src.read_bytes()


def _insert_tags(html: str, scripts: List[str], styles: List[str]) -> str:
    if scripts and SCRIPTS_END not in html:
        raise PartError(f"index.html に {SCRIPTS_END} の印がありません。雛形の index.html と同じ印を、index.js を読む行の上に戻してください")
    if styles and STYLES_END not in html:
        raise PartError(f"index.html に {STYLES_END} の印がありません。雛形と同じ印を <head> の中に戻してください")
    for s in scripts:
        tag = f'<script src="{s}"></script>'
        if tag not in html:
            html = html.replace(SCRIPTS_END, f"{tag}\n  {SCRIPTS_END}", 1)
    for s in styles:
        tag = f'<link rel="stylesheet" href="{s}">'
        if tag not in html:
            html = html.replace(STYLES_END, f"{tag}\n  {STYLES_END}", 1)
    return html


def add_part(project_dir, name: str, kit_dir: Path = SKILL_DIR, _stack=None) -> Dict:
    project_dir = Path(project_dir)
    kit_dir = Path(kit_dir)
    parts_dir = kit_dir / "parts"
    info = projlib.load(project_dir)
    result = {"part": name, "installed": [], "already": False, "files": [], "manifest": []}
    if name in info.get("parts", []):
        result["already"] = True
        return result
    stack = list(_stack or [])
    if name in stack:
        raise PartError("部品の requires が輪になっています: " + " → ".join(stack + [name]))
    part = load_part(name, parts_dir)
    manifest_path = project_dir / "manifest.json"
    mf.load(manifest_path)  # 壊れていたら ManifestError で止める（何も書き換えない）
    for req in part["requires"]:
        result["installed"].extend(add_part(project_dir, req, kit_dir, stack + [name])["installed"])
    info = projlib.load(project_dir)
    data = mf.load(manifest_path)
    mapping = projlib.placeholders(info)

    plan = []
    for src, dst_rel in _expand_files(parts_dir / name, part["files"]):
        content = _render(src, mapping)
        target = project_dir / dst_rel
        if target.exists():
            if target.read_bytes() == content:
                continue
            raise PartError(f"{dst_rel} は既にあり、中身が違います（上書きしません）。書き換えたなら、部品の中身と見比べて手で合わせてください")
        plan.append((target, content, src))
    html_path = project_dir / (data.get("main") or "index.html")
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    new_html = _insert_tags(html, part["scripts"], part["styles"]) if html_path.exists() else html

    changes = mf.merge_permissions(data, part["permissions"])
    changes += mf.merge_feature_flags(data, part["featureFlags"])
    entries = [json.loads(projlib.substitute(json.dumps(e, ensure_ascii=False), mapping)) for e in part["entrypoints"]]
    changes += [f"entrypoint:{x}" for x in mf.add_entrypoints(data, entries)]
    if part["minVersion"] and mf.raise_min_version(data, part["minVersion"]):
        changes.append(f"minVersion:{part['minVersion']}")
        info["minVersion"] = data["host"]["minVersion"]

    # ここから書き込む（確かめ終わってから）
    for target, content, src in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if src.suffix in (".command", ".sh"):
            target.chmod(0o755)
        result["files"].append(target.relative_to(project_dir).as_posix())
    if new_html != html:
        fsutil.write_text(html_path, new_html)
    mf.save(manifest_path, data)
    if part["pythonDeps"]:
        req = project_dir / "server" / "requirements.txt"
        lines = req.read_text(encoding="utf-8").splitlines() if req.exists() else []
        for dep in part["pythonDeps"]:
            if dep not in lines:
                lines.append(dep)
        fsutil.write_text(req, "\n".join(lines) + "\n")
    info["parts"] = info.get("parts", []) + [name]
    projlib.save(project_dir, info)
    result["manifest"] = changes
    result["installed"].append(name)
    return result


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="作業フォルダに部品を足す")
    ap.add_argument("part", nargs="?")
    ap.add_argument("--project")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    parts_dir = SKILL_DIR / "parts"
    if args.list or not args.part:
        for name in list_parts(parts_dir):
            p = load_part(name, parts_dir)
            print(f"{name}（{p['status']}・{'/'.join(p['os'])}）: {p['description']}")
        return 0
    if not args.project:
        print("--project に作業フォルダを指定してください")
        return 3
    try:
        r = add_part(Path(args.project).expanduser(), args.part)
    except (PartError, projlib.ProjectError, mf.ManifestError) as e:
        print(str(e))
        return 3
    if args.json:
        cli.print_json(r)
    elif r["already"]:
        print(f"{args.part} は既に入っています（何も変えていません）")
    else:
        print(f"足しました: {', '.join(r['installed'])}")
        if r["manifest"]:
            print(f"manifest の変更: {', '.join(r['manifest'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_add_part.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_new_plugin.py' -v && node --test tests/js/*.test.js`
Expected: PASS（add_part 7・parts 1・new_plugin 5・JS 全部）

- [ ] **Step 5: コミット（Task 10 と 11 をまとめて）**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 雛形（_base・panel）と new_plugin.py・add_part.py（上書きしない・2 回目は何もしない）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: 部品 commands と雛形 panel-commands

**Files:**
- Create: `SKILL/parts/commands/part.json`、`SKILL/parts/commands/lib/ppm-commands.js`
- Create: `SKILL/templates/panel-commands/template.json`
- Test: `tests/js/commands.test.js`、`tests/test_templates.py`

**Interfaces:**
- Produces（`PPM.commands`）: `define(id, handler)`（失敗はログへ）、`table() -> {id: async function}`。雛形の index.js は `PPM.commands` があれば `define("runMain", onRun)` してから `uxp.entrypoints.setup({commands: PPM.commands.table()})` に渡す（Task 10 で書き済み）
- Produces（`tests/test_templates.py`）: 全部の雛形を作り、機械の検査で誤り 0 件を確かめる（雛形が増えるたびに自動で対象になる）

- [ ] **Step 1: 失敗するテストを書く**

`tests/js/commands.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

test("define した命令が table に出て、失敗はログに残る", async () => {
  const ctx = loadParts(["logger/lib/ppm-logger.js", "commands/lib/ppm-commands.js"]);
  let ran = 0;
  ctx.PPM.commands.define("runMain", async () => { ran += 1; });
  ctx.PPM.commands.define("broken", async () => { throw new Error("壊れた"); });
  const table = ctx.PPM.commands.table();
  await table.runMain();
  await table.broken();
  assert.equal(ran, 1);
  assert.ok(ctx.PPM.log.lines().some((l) => l.includes("command failed") && l.includes("壊れた")));
});
```

`tests/test_templates.py`:

```python
import json
import unittest

from helpers import SKILL, TEMPLATES, temp_dir

import new_plugin
from lib import checks


class TemplateTests(unittest.TestCase):
    def test_every_template_scaffolds_and_passes_check(self):
        names = sorted(p.parent.name for p in TEMPLATES.glob("*/template.json"))
        self.assertIn("panel", names)
        for name in names:
            with self.subTest(template=name):
                dest = temp_dir() / f"雛形 {name}"
                new_plugin.create_project(name, dest, f"Test {name}", label=f"テスト {name}")
                errors = [f for f in checks.run_all(dest, SKILL) if f.severity == "error"]
                self.assertEqual(errors, [], errors)

    def test_panel_commands_adds_a_menu_command(self):
        dest = temp_dir() / "cmd"
        new_plugin.create_project("panel-commands", dest, "Cmd Test", label="コマンド")
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        commands = [e for e in manifest["entrypoints"] if e["type"] == "command"]
        self.assertEqual(commands[0]["id"], "runMain")
        self.assertEqual(commands[0]["label"]["default"], "コマンド: 実行")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `node --test tests/js/commands.test.js`
Expected: FAIL（`ENOENT … ppm-commands.js`）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/commands/lib/ppm-commands.js`:

```js
/* ppm-commands — メニューのコマンド（［ウィンドウ］→［UXP プラグイン］の下に出る）。
 * Premiere の［キーボードショートカット］には UXP のコマンドを割り当てられない。
 * Mac はシステム設定の「キーボードショートカット → アプリのショートカット」で、メニュー名と同じ名前を書けば割り当てられる
 * （名前が 1 文字違うと黙って効かない）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const table = {};
  PPM.commands = {
    define(id, handler) {
      table[id] = async function () {
        try { await handler(); }
        catch (e) { if (PPM.log) PPM.log.error("command failed", { id, message: String((e && e.message) || e) }); }
      };
    },
    table() { return Object.assign({}, table); },
  };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/commands/part.json`:

```json
{
  "name": "commands",
  "description": "メニューのコマンド。パネルを開かずに処理を実行でき、Mac はシステム設定でキーを割り当てられる",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["logger"],
  "files": {"lib/ppm-commands.js": "lib/ppm-commands.js"},
  "scripts": ["lib/ppm-commands.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [{"type": "command", "id": "runMain", "label": {"default": "{{PANEL_LABEL}}: 実行"}}],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["recipe-commands-shortcuts"],
  "notes": "index.js の PPM.commands.define(\"runMain\", onRun) がメニューの「実行」で呼ばれる。コマンドを足すときは part.json と同じ形で manifest に足し、define する"
}
```

`SKILL/templates/panel-commands/template.json`:

```json
{
  "name": "panel-commands",
  "description": "パネル＋メニューのコマンド（パネルを開かずに実行・Mac はキーの割り当てができる）",
  "extends": "panel",
  "parts": ["commands"],
  "minVersion": "25.6"
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_templates.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 commands と雛形 panel-commands

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: logs.py（ログを読む）

**Files:**
- Create: `SKILL/scripts/logs.py`
- Test: `tests/test_logs.py`

**Interfaces:**
- Consumes: `lib.osinfo.plugin_storage_roots / uxp_log_dirs / detect_os`、`lib.project.load`、`lib.cli`
- Produces（`logs`）: `find_plugin_logs(env, os_name, plugin_id, file_name="ppm-log.txt", max_depth=7) -> list[Path]`（新しい順）、`find_uxp_logs(env, os_name, limit=1) -> list[Path]`（新しい順）、`tail(path, lines=80, grep=None, marker=None) -> list[str]`、`main(argv=None) -> int`（見つかれば 0、1 つも無ければ 1）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_logs.py`:

```python
import json
import os
import sys
import time
import unittest
from pathlib import Path

from helpers import run_script, temp_dir

import logs


class LogsTests(unittest.TestCase):
    def setUp(self):
        self.home = temp_dir() / "home 山田"
        self.env = {"HOME": str(self.home)}
        storage = self.home / "Library/Application Support/Adobe/UXP/PluginsStorage"
        old = storage / "PPROBETA/27/Developer/com.ppm.zoom/PluginData/ppm-log.txt"
        new = storage / "PPRO/26/Developer/com.ppm.zoom/PluginData/ppm-log.txt"
        for p, text in ((old, "古い\n"), (new, "a [zoom] INFO 新しい\nb [zoom] ERROR 失敗\n")):
            p.parent.mkdir(parents=True)
            p.write_text(text, encoding="utf-8")
        os.utime(old, (time.time() - 100, time.time() - 100))
        uxp = self.home / "Library/Logs/Adobe"
        (uxp / "Adobe Premiere Pro 2025").mkdir(parents=True)
        (uxp / "Adobe Premiere Pro 2026").mkdir(parents=True)
        (uxp / "Adobe Premiere Pro 2025" / "UXPLogs_2025.log").write_text("x [zoom] 古い年\n", encoding="utf-8")
        latest = uxp / "Adobe Premiere Pro 2026" / "UXPLogs_2026.log"
        latest.write_text("y [other] 他のプラグイン\nz [zoom] INFO boot\n", encoding="utf-8")
        os.utime(uxp / "Adobe Premiere Pro 2025" / "UXPLogs_2025.log", (time.time() - 100, time.time() - 100))

    def test_plugin_logs_newest_first(self):
        found = logs.find_plugin_logs(self.env, "mac", "com.ppm.zoom")
        self.assertEqual(len(found), 2)
        self.assertIn("PPRO/26", found[0].as_posix())

    def test_uxp_log_is_newest_and_filtered_by_marker(self):
        latest = logs.find_uxp_logs(self.env, "mac")
        self.assertEqual(latest[0].name, "UXPLogs_2026.log")
        self.assertEqual(logs.tail(latest[0], marker="[zoom]"), ["z [zoom] INFO boot"])

    def test_windows_storage_root(self):
        env = {"USERPROFILE": str(self.home), "APPDATA": str(self.home / "AppData/Roaming"), "LOCALAPPDATA": str(self.home / "AppData/Local")}
        p = Path(env["APPDATA"]) / "Adobe/UXP/PluginsStorage/PPRO/26/Developer/com.ppm.zoom/PluginData/ppm-log.txt"
        p.parent.mkdir(parents=True)
        p.write_text("w\n", encoding="utf-8")
        self.assertEqual(logs.find_plugin_logs(env, "windows", "com.ppm.zoom"), [p])

    @unittest.skipUnless(sys.platform == "darwin", "Mac の場所の木を偽物で作っているので Mac だけ（Windows は test_windows_storage_root で見る）")
    def test_cli_project_and_json(self):
        project = temp_dir() / "proj"
        (project / ".ppm").mkdir(parents=True)
        (project / ".ppm" / "project.json").write_text(json.dumps({"pluginId": "com.ppm.zoom", "logTag": "zoom"}), encoding="utf-8")
        proc = run_script("logs.py", "--project", str(project), "--json", env={**self.env, "PYTHONIOENCODING": "cp932"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("ERROR 失敗", "\n".join(data["plugin"][0]["lines"]))

    def test_cli_nothing_found(self):
        proc = run_script("logs.py", "--plugin-id", "com.none.x", env={"HOME": str(temp_dir())})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("診断", proc.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_logs.py' -v`
Expected: FAIL（`No module named 'logs'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/logs.py`:

```python
#!/usr/bin/env python3
"""プラグインのログを読む（AI が「Premiere で何が起きたか」を確かめるため）。

  logs.py --project <作業フォルダ> [--lines 80] [--grep 文字] [--json] [--list]
  logs.py --plugin-id com.example.x [--tag x]
  logs.py --file <診断ボタンが表示したログのパス>
探す場所: プラグインのデータフォルダの ppm-log.txt（Mac・Windows）と、Mac の UXP ログ（UXPLogs_*.log）の印の行。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402
from lib import project as projlib  # noqa: E402


def find_plugin_logs(env, os_name: str, plugin_id: str, file_name: str = "ppm-log.txt", max_depth: int = 7) -> List[Path]:
    found: List[Path] = []
    for root in osinfo.plugin_storage_roots(env, os_name):
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            if depth >= max_depth:
                dirnames[:] = []
            if file_name in filenames and plugin_id in Path(dirpath).as_posix():
                found.append(Path(dirpath) / file_name)
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def find_uxp_logs(env, os_name: str, limit: int = 1) -> List[Path]:
    files: List[Path] = []
    for d in osinfo.uxp_log_dirs(env, os_name):
        files.extend(p for p in d.glob("UXPLogs_*.log") if p.is_file())
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def tail(path: Path, lines: int = 80, grep: Optional[str] = None, marker: Optional[str] = None) -> List[str]:
    text = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    if marker:
        text = [line for line in text if marker in line]
    if grep:
        text = [line for line in text if grep in line]
    return text[-lines:]


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="プラグインのログを読む")
    ap.add_argument("--project")
    ap.add_argument("--plugin-id")
    ap.add_argument("--tag")
    ap.add_argument("--file")
    ap.add_argument("--lines", type=int, default=80)
    ap.add_argument("--grep")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    plugin_id, tag = args.plugin_id, args.tag
    if args.project:
        info = projlib.load(Path(args.project).expanduser())
        plugin_id = plugin_id or info.get("pluginId")
        tag = tag or info.get("logTag")
    marker = f"[{tag}]" if tag else None
    plugin_files = [Path(args.file)] if args.file else (find_plugin_logs(os.environ, os_name, plugin_id) if plugin_id else [])
    uxp_files = find_uxp_logs(os.environ, os_name) if marker else []
    result = {
        "plugin": [{"path": str(p), "lines": [] if args.list else tail(p, args.lines, args.grep)} for p in plugin_files[:1]],
        "uxp": [{"path": str(p), "lines": [] if args.list else tail(p, args.lines, args.grep, marker)} for p in uxp_files],
    }
    if args.json:
        cli.print_json(result)
    else:
        for kind, title in (("plugin", "プラグインのログ"), ("uxp", "Premiere の UXP ログ（印の行だけ）")):
            for item in result[kind]:
                print(f"■ {title}: {item['path']}")
                for line in item["lines"]:
                    print("  " + line)
    if not plugin_files and not any(item["lines"] for item in result["uxp"]):
        print("ログが見つかりませんでした。パネルの「診断」を押すと保存場所が表示されるので、その場所を --file で渡してください。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_logs.py' -v`
Expected: PASS（5 件）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: logs.py（データフォルダの ppm-log.txt と Mac の UXP ログを読む）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: make_ccx.py・install_ccx.py と部品 packaging

**Files:**
- Create: `SKILL/scripts/make_ccx.py`
- Create: `SKILL/scripts/install_ccx.py`
- Create: `SKILL/parts/packaging/part.json`、`SKILL/parts/packaging/packaging/README-recipient.txt`
- Test: `tests/test_make_ccx.py`、`tests/test_install_ccx.py`

**Interfaces:**
- Consumes: `lib.manifest.load`、`lib.privacy.personal_paths / token_like / secret_like_name`、`lib.project.load / placeholders / substitute`、`lib.osinfo.upia_path / detect_os`
- Produces（`make_ccx`）: `class CcxError(ValueError)`、`EXCLUDE_TOP = {"server", "cep", "tests", ".ppm", "dist", "node_modules", "packaging", ".git"}`、`collect_files(project_dir) -> list[str]`（manifest.json が先頭）、`validate(project_dir, files) -> None`（問題があれば CcxError）、`build_ccx(project_dir, out_path=None) -> Path`（既定 `dist/<id>_<version>.ccx`。同じ中身なら同じバイト列）、`build_bundle(project_dir) -> Path`（`dist/<名前>_v<版>/` に .ccx・「はじめにお読みください.txt」・あればサーバーの zip）、`main(argv=None) -> int`
- Produces（`install_ccx`）: `upia_command(os_name, upia, action, arg=None) -> list[str]`（action は `install` `remove` `list`。Mac は `--install`、Windows は `/install`）、`plugin_name_in_ccx(path) -> str`、`run(cmds, runner) -> list[dict]`、`main(argv=None, runner=subprocess.run) -> int`（既定は試し実行で、`--apply` のときだけ実行）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_make_ccx.py`:

```python
import json
import unittest
import zipfile

from helpers import temp_dir

import make_ccx
import new_plugin


class MakeCcxTests(unittest.TestCase):
    def setUp(self):
        self.dest = temp_dir() / "配る プラグイン"
        new_plugin.create_project("panel", self.dest, "Ship Test", label="配る")

    def test_collects_only_panel_files_manifest_first(self):
        (self.dest / "server").mkdir()
        (self.dest / "server" / "job.py").write_text("x = 1\n", encoding="utf-8")
        files = make_ccx.collect_files(self.dest)
        self.assertEqual(files[0], "manifest.json")
        for rel in ("index.html", "index.js", "panel.css", "lib/ppm-ppro-kit.js", "lib/ppm-ui-kit.css", "icons/icon.png",
                    "icons/icon@2x.png", "build_info.json"):
            self.assertIn(rel, files)
        self.assertFalse(any(f.startswith(("server/", ".ppm/")) for f in files))

    def test_build_is_deterministic(self):
        a = make_ccx.build_ccx(self.dest, self.dest / "dist" / "a.ccx")
        b = make_ccx.build_ccx(self.dest, self.dest / "dist" / "b.ccx")
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(a) as z:
            infos = z.infolist()
            self.assertEqual(infos[0].filename, "manifest.json")
            self.assertTrue(all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in infos))
            self.assertFalse(any(i.filename.endswith("/") for i in infos))

    def test_default_name_uses_id_and_version(self):
        out = make_ccx.build_ccx(self.dest)
        self.assertEqual(out.name, "com.ppm.shiptest_0.1.0.ccx")

    def test_missing_referenced_file_is_an_error(self):
        (self.dest / "lib" / "ppm-probe.js").unlink()
        with self.assertRaises(make_ccx.CcxError) as ctx:
            make_ccx.collect_files(self.dest)
        self.assertIn("ppm-probe.js", str(ctx.exception))

    def test_personal_path_and_version_mismatch_stop_the_build(self):
        (self.dest / "lib" / "ppm-ui-kit.js").write_text("// /Users/" + "yamada/x\n", encoding="utf-8")
        with self.assertRaises(make_ccx.CcxError):
            make_ccx.build_ccx(self.dest)

    def test_bundle_has_ccx_readme_and_server_zip(self):
        (self.dest / "server").mkdir()
        (self.dest / "server" / "ppm_server.py").write_text("x = 1\n", encoding="utf-8")
        folder = make_ccx.build_bundle(self.dest)
        names = sorted(p.name for p in folder.iterdir())
        self.assertIn("com.ppm.shiptest_0.1.0.ccx", names)
        self.assertIn("はじめにお読みください.txt", names)
        self.assertIn("ShipTest_server_v0.1.0.zip", names)
        readme = (folder / "はじめにお読みください.txt").read_text(encoding="utf-8")
        self.assertIn("配る", readme)
        self.assertNotIn("{{", readme)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_install_ccx.py`:

```python
import subprocess
import unittest
import zipfile

from helpers import temp_dir

import install_ccx


def fake_ccx():
    path = temp_dir() / "a.ccx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", '{"name": "Ship Test", "id": "com.ppm.shiptest", "version": "0.1.0"}')
    return path


class FakeRunner:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        code, out = self.outputs.pop(0)
        return subprocess.CompletedProcess(cmd, code, out, "")


class InstallCcxTests(unittest.TestCase):
    def test_command_shapes(self):
        self.assertEqual(install_ccx.upia_command("mac", "/u", "install", "/x.ccx"), ["/u", "--install", "/x.ccx"])
        self.assertEqual(install_ccx.upia_command("windows", "C:/u.exe", "remove", "Ship Test"), ["C:/u.exe", "/remove", "Ship Test"])
        self.assertEqual(install_ccx.upia_command("mac", "/u", "list"), ["/u", "--list", "all"])

    def test_plugin_name_from_ccx(self):
        self.assertEqual(install_ccx.plugin_name_in_ccx(fake_ccx()), "Ship Test")

    def test_dry_run_runs_nothing(self):
        runner = FakeRunner([])
        code = install_ccx.main(["--install", str(fake_ccx())], runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(runner.calls, [])

    def test_apply_reinstall_removes_then_installs_and_tolerates_remove_failure(self):
        runner = FakeRunner([(1, "status -406"), (0, "Installation Successful")])
        code = install_ccx.main(["--reinstall", str(fake_ccx()), "--apply", "--upia", "/u"], runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual([c[1] for c in runner.calls], ["--remove", "--install"] if install_ccx.osinfo.detect_os() != "windows" else ["/remove", "/install"])

    def test_apply_install_failure_is_reported(self):
        runner = FakeRunner([(1, "Error code -1")])
        code = install_ccx.main(["--install", str(fake_ccx()), "--apply", "--upia", "/u"], runner=runner)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_make_ccx.py' -v`
Expected: FAIL（`No module named 'make_ccx'`）

- [ ] **Step 3: 実装を書く**

`SKILL/scripts/make_ccx.py`:

```python
#!/usr/bin/env python3
"""配る用の .ccx を作る（パネルが読むファイルだけを集め、毎回同じバイト列になるように固める）。

使い方:
  Mac:     python3 <このスキル>/scripts/make_ccx.py <作業フォルダ> [--out <ファイル>] [--bundle] [--json]
  Windows: py -3 <このスキル>\\scripts\\make_ccx.py <作業フォルダ> [--out <ファイル>] [--bundle] [--json]
--bundle は dist/<名前>_v<版>/ に .ccx・はじめにお読みください.txt・（あれば）サーバーの zip をまとめる。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, fsutil, privacy  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
EXCLUDE_TOP = {"server", "cep", "tests", ".ppm", "dist", "node_modules", "packaging", ".git"}
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".js", ".json", ".html", ".css", ".txt", ".md", ".svg"}
DEFAULT_README = """{{PANEL_LABEL}}（{{PLUGIN_NAME}} v{{VERSION}}）の入れ方

■ Mac / Windows 共通
1. Creative Cloud デスクトップにサインインした状態で、{{PLUGIN_ID}}_{{VERSION}}.ccx をダブルクリックする
2. 確認の画面が出たら［インストール］を押す
3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{{PANEL_LABEL}}」を開く

■ 出てこないとき
- Premiere を一度終了して、もう一度開く
- Creative Cloud にサインインし直した後は、入れ直しが要ることがあります
- 同じ版のまま入れ直しても更新されません。Creative Cloud デスクトップの［プラグイン］から一度削除してから入れてください
"""


class CcxError(ValueError):
    pass


def _norm(rel: PurePosixPath) -> str:
    parts: List[str] = []
    for part in rel.parts:
        if part == "..":
            if not parts:
                raise CcxError(f"プラグインのフォルダの外を読もうとしています: {rel}")
            parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def _html_refs(text: str) -> List[str]:
    refs = re.findall(r"<(?:script|img)\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
    refs += re.findall(r"<link\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
    return [r.split("?")[0] for r in refs if not re.match(r"^(https?:|data:|plugin:|#)", r)]


def _css_refs(text: str) -> List[str]:
    return [r for r in re.findall(r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)", text) if not re.match(r"^(https?:|data:)", r)]


def collect_files(project_dir) -> List[str]:
    root = Path(project_dir)
    data = mf.load(root / "manifest.json")
    files = {"manifest.json"}
    queue = [data.get("main") or "main.js"]
    while queue:
        rel = queue.pop()
        if rel in files:
            continue
        if PurePosixPath(rel).parts and PurePosixPath(rel).parts[0] in EXCLUDE_TOP:
            raise CcxError(f"{rel} は配る物に入らない場所（{PurePosixPath(rel).parts[0]}/）にあります")
        path = root / rel
        if not path.is_file():
            raise CcxError(f"{rel} がありません（index.html か CSS が読みに行くファイルです）")
        files.add(rel)
        base = PurePosixPath(rel).parent
        if path.suffix.lower() == ".html":
            queue.extend(_norm(base / r) for r in _html_refs(path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".css":
            queue.extend(_norm(base / r) for r in _css_refs(path.read_text(encoding="utf-8")))
    for icon in data.get("icons") or []:
        p = icon.get("path")
        if not p:
            continue
        if not (root / p).is_file():
            raise CcxError(f"アイコン {p} がありません")
        files.add(p)
        stem = PurePosixPath(p)
        for scale in icon.get("scale") or []:
            candidate = (stem.parent / f"{stem.stem}@{scale}x{stem.suffix}").as_posix()
            if (root / candidate).is_file():
                files.add(candidate)
    if (root / "build_info.json").is_file():
        files.add("build_info.json")
    pkg = root / ".ppm" / "package.json"
    if pkg.is_file():
        for pattern in json.loads(pkg.read_text(encoding="utf-8")).get("include", []):
            for p in sorted(root.glob(pattern)):
                rel = p.relative_to(root).as_posix()
                if p.is_file() and PurePosixPath(rel).parts[0] not in EXCLUDE_TOP:
                    files.add(rel)
    return sorted(files, key=lambda x: (x != "manifest.json", x))


def validate(project_dir, files: List[str]) -> None:
    root = Path(project_dir)
    data = mf.load(root / "manifest.json")
    problems = []
    for rel in files:
        name = PurePosixPath(rel).name
        if privacy.secret_like_name(name):
            problems.append(f"{rel}: 秘密らしい名前のファイルは配りません")
        if Path(rel).suffix.lower() in TEXT_SUFFIXES:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
            for line, found in privacy.personal_paths(text):
                problems.append(f"{rel} の {line} 行目: 個人のパス {found}")
            for line, found in privacy.token_like(text):
                problems.append(f"{rel} の {line} 行目: 鍵の形の文字列 {found}")
            if re.search(r"\{\{[A-Z_]+\}\}", text):
                problems.append(f"{rel}: 置き換え忘れの {{{{…}}}} があります")
    info = root / "build_info.json"
    if info.is_file():
        bv = json.loads(info.read_text(encoding="utf-8")).get("version")
        if bv != data.get("version"):
            problems.append(f"build_info.json の版（{bv}）が manifest.json（{data.get('version')}）と違います")
    if problems:
        raise CcxError("配る前に直すことがあります:\n- " + "\n- ".join(problems))


def _write_zip(out: Path, entries) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, data, mode in entries:
            info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            info.external_attr = (mode & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    os.replace(tmp, out)
    return out


def build_ccx(project_dir, out_path: Optional[Path] = None) -> Path:
    root = Path(project_dir)
    files = collect_files(root)
    validate(root, files)
    data = mf.load(root / "manifest.json")
    out = Path(out_path) if out_path else root / "dist" / f"{data['id']}_{data['version']}.ccx"
    return _write_zip(out, [(rel, (root / rel).read_bytes(), 0o100644) for rel in files])


def build_bundle(project_dir) -> Path:
    root = Path(project_dir)
    info = projlib.load(root)
    data = mf.load(root / "manifest.json")
    folder = root / "dist" / f"{info['appName']}_v{data['version']}"
    folder.mkdir(parents=True, exist_ok=True)
    ccx = build_ccx(root, folder / f"{data['id']}_{data['version']}.ccx")
    template = root / "packaging" / "README-recipient.txt"
    text = template.read_text(encoding="utf-8") if template.is_file() else DEFAULT_README
    fsutil.write_text(folder / "はじめにお読みください.txt", projlib.substitute(text, projlib.placeholders({**info, "version": data["version"]})))
    server = root / "server"
    if server.is_dir():
        entries = []
        for p in sorted(x for x in server.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix != ".pyc"):
            rel = p.relative_to(root).as_posix()
            if privacy.secret_like_name(p.name):
                raise CcxError(f"{rel}: 秘密らしい名前のファイルは配りません")
            mode = 0o100755 if p.suffix in (".command", ".sh") else 0o100644
            entries.append((rel, p.read_bytes(), mode))
        _write_zip(folder / f"{info['appName']}_server_v{data['version']}.zip", entries)
    return folder


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="配る用の .ccx を作る")
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--bundle", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.bundle:
            out = build_bundle(Path(args.project).expanduser())
        else:
            out = build_ccx(Path(args.project).expanduser(), Path(args.out) if args.out else None)
    except (CcxError, mf.ManifestError, projlib.ProjectError) as e:
        print(str(e))
        return 1
    if args.json:
        cli.print_json({"ok": True, "path": str(out)})
    else:
        print(f"作りました: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/scripts/install_ccx.py`:

```python
#!/usr/bin/env python3
"""Adobe の導入ツール（UPIA）で .ccx を入れる・外す・一覧を見る。既定は試し実行（コマンドを見せるだけ）。

使い方:
  Mac:     python3 <このスキル>/scripts/install_ccx.py --reinstall <ファイル.ccx> --apply
  Windows: py -3 <このスキル>\\scripts\\install_ccx.py --reinstall <ファイル.ccx> --apply
  --install <ccx> / --reinstall <ccx>（先に外してから入れる）/ --remove <プラグイン名> / --list
同じ版数のまま入れ直しても更新されないことがあるので、作り直したら --reinstall を使う。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402


def upia_command(os_name: str, upia, action: str, arg=None) -> List[str]:
    prefix = "/" if os_name == "windows" else "--"
    cmd = [str(upia), prefix + action]
    if action == "list":
        cmd.append("all")
    elif arg is not None:
        cmd.append(str(arg))
    return cmd


def plugin_name_in_ccx(path) -> str:
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("manifest.json").decode("utf-8"))["name"]


def run(cmds, runner) -> List[dict]:
    results = []
    for cmd, must_succeed in cmds:
        proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        out = (proc.stdout or "") + (proc.stderr or "")
        ok = proc.returncode == 0 or "successful" in out.lower()
        results.append({"command": cmd, "ok": ok, "required": must_succeed, "output": out.strip()})
    return results


def main(argv=None, runner=subprocess.run) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="UPIA で .ccx を入れる・外す")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--install")
    group.add_argument("--reinstall")
    group.add_argument("--remove")
    group.add_argument("--list", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--upia")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    upia = Path(args.upia) if args.upia else osinfo.upia_path(os.environ, os_name)
    cmds = []
    if args.list:
        cmds.append((upia_command(os_name, upia, "list"), True))
    elif args.remove:
        cmds.append((upia_command(os_name, upia, "remove", args.remove), True))
    else:
        ccx = Path(args.install or args.reinstall).expanduser().resolve()
        if args.reinstall:
            cmds.append((upia_command(os_name, upia, "remove", plugin_name_in_ccx(ccx)), False))
        cmds.append((upia_command(os_name, upia, "install", ccx), True))
    if not args.apply:
        print("試し実行です（まだ何もしていません）。実行するときは --apply を付けます:")
        for cmd, _ in cmds:
            print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
        return 0
    if not upia.exists() and not args.upia:
        print(f"UPIA が見つかりません: {upia}\nCreative Cloud デスクトップを入れてください。.ccx のダブルクリックでも入れられます。")
        return 1
    results = run(cmds, runner)
    failed = [r for r in results if r["required"] and not r["ok"]]
    if args.json:
        cli.print_json({"ok": not failed, "results": results})
    else:
        for r in results:
            print(("[OK ] " if r["ok"] else ("[NG!] " if r["required"] else "[注意] ")) + " ".join(r["command"]))
            if r["output"]:
                print("      " + r["output"].replace("\n", "\n      "))
        if not failed:
            print("入れました。Premiere の［ウィンドウ］→［UXP プラグイン］に出ないときは、Premiere を再起動してください。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/packaging/part.json`:

```json
{
  "name": "packaging",
  "description": "配る準備。受け取る人向けの「はじめにお読みください」の雛形（make_ccx.py --bundle が使う）",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": [],
  "files": {"packaging/README-recipient.txt": "packaging/README-recipient.txt"},
  "scripts": [],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["core-versioning-release"],
  "notes": "packaging/README-recipient.txt を書き換えると、--bundle の「はじめにお読みください.txt」が変わる"
}
```

`SKILL/parts/packaging/packaging/README-recipient.txt`:

```
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
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_make_ccx.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_install_ccx.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（make_ccx 6・install_ccx 5・parts 1）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: make_ccx.py（配る物だけを同じバイト列で固める）・install_ccx.py（UPIA・既定は試し実行）・部品 packaging

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 4: 重い部品

この Phase の部品は、パネル側の JS とサーバー側の Python の両方を持つものが多い。サーバー側は local-server（Task 15）の上に乗るので、Task 15 を先に終える。Task 16 以降は互いに独立しているので、並べて進めてよい。

### Task 15: 部品 local-server と雛形 panel-server

**Files:**
- Create: `SKILL/parts/local-server/part.json`
- Create: `SKILL/parts/local-server/server/ppm_server.py`、`ppm_paths.py`、`ppm_jobs.py`、`config.json`、`install.py`、`launchd.plist.template`、`install_mac.command`、`uninstall_mac.command`、`install_windows.bat`、`uninstall_windows.bat`、`jobs/__init__.py`、`jobs/echo.py`、`ext/__init__.py`
- Create: `SKILL/parts/local-server/lib/ppm-server-client.js`
- Create: `SKILL/templates/panel-server/template.json`
- Modify: `tests/js/load_parts.js`（`loadParts(files, extra = {}, replace = {})` にして、読み込む前に `{{…}}` を置き換えられるようにする）
- Test: `tests/server_helpers.py`、`tests/test_local_server.py`、`tests/js/server_client.test.js`

**Interfaces:**
- サーバーの約束（他の部品のジョブと口が使う）:
  - 握手のファイル: Mac `~/Library/Application Support/<APP_NAME>/server.json`、Windows `%APPDATA%\<APP_NAME>\server.json`。中身 `{"pid", "httpPort", "token", "version", "protocol": 1, "tmpDir", "serverDir"}`。テストでは環境変数 `PPM_APP_SUPPORT_ROOT` と `PPM_LOG_ROOT` で置き場所を変えられる
  - ヘッダー `X-PPM-Token`。違えば 403
  - `GET /ping` → `{"ok", "app", "version", "protocol", "jobs": [...]}`
  - `POST /jobs/<種類>` → 202 `{"jobId"}`／動いているジョブがあれば 409／無い種類は 404
  - `GET /jobs/<id>` → `{"id", "kind", "status": "queued|running|done|error|cancelled", "percent", "message", "result", "error": {"message", "why", "next"}}`（ジョブの失敗も HTTP は 200）
  - `POST /jobs/<id>/cancel`
  - ジョブ: `server/jobs/<名前>.py` に `NAME = "名前"` と `def run(params: dict, ctx) -> dict`。`ctx.progress(percent, message)`、`ctx.cancelled() -> bool`、`ctx.tmp_dir: str`、`ctx.app: str`、`ctx.log(msg)`。理由つきで止めるときは `from ppm_jobs import JobError; raise JobError("症状", "なぜ", "次の一手")`
  - 追加の口: `server/ext/<名前>.py` に `ROUTES = {("GET" or "POST", "/path"): handler}`、`handler(request: {"path", "query", "body"}, ctx: {"token", "app", "tmp_dir", "log"}) -> (status: int, obj: dict)`
- Produces（`PPM.server`、パネル側）: `connect({tries=5, intervalMs=4000}) -> Promise<handshake>`、`call(path, {method, body}) -> Promise<object>`（403 なら握手を読み直して 1 回だけやり直す）、`runJob(kind, params, {onProgress, fastMs=300, slowMs=1500}) -> Promise<result>`、`tmpPath(name) -> string`、`handshakePath() -> string`、`readHandshake() -> Promise<handshake>`
- Produces（`install.py`）: `--dry-run`（何もしない）、`--force`（同じ版の runtime を置き換える）、`--with-deps`（requirements.txt の依存を専用の venv に入れる。入れる前に利用者の許可を取ること）、`--uninstall`、`--status`。常駐の名前は Mac `com.ppm.<appname小文字>.server`、Windows のタスク `<APP_NAME> Server`
- Produces（`tests/server_helpers.py`）: `make_server_dir(jobs=None, ext=None, app="PpmTest") -> Path`、`class LiveServer(server_dir)`（`call(path, body=None, token=True) -> (status, obj)`、`wait_job(job_id) -> dict`、`stop()`、属性 `info` `root` `handshake_path`）

- [ ] **Step 1: 失敗するテストを書く**

`tests/server_helpers.py`:

```python
"""local-server の部品を一時フォルダに写して、本物のサーバーとして起動するテスト用の道具。"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from helpers import PARTS, temp_dir

SERVER_SRC = PARTS / "local-server" / "server"


def make_server_dir(jobs=None, ext=None, app="PpmTest", extra_dirs=()) -> Path:
    d = temp_dir() / "server"
    shutil.copytree(SERVER_SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    for src in extra_dirs:
        shutil.copytree(src, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    (d / "config.json").write_text(json.dumps({"app": app, "version": "0.1.0", "protocol": 1, "port": 0}), encoding="utf-8")
    for name, code in (jobs or {}).items():
        (d / "jobs" / f"{name}.py").write_text(code, encoding="utf-8")
    for name, code in (ext or {}).items():
        (d / "ext" / f"{name}.py").write_text(code, encoding="utf-8")
    return d


class LiveServer:
    def __init__(self, server_dir: Path, app="PpmTest"):
        self.root = temp_dir()
        self.env = {**os.environ, "PPM_APP_SUPPORT_ROOT": str(self.root / "support"),
                    "PPM_LOG_ROOT": str(self.root / "logs"), "PYTHONUTF8": "1"}
        self.proc = subprocess.Popen([sys.executable, str(server_dir / "ppm_server.py")], env=self.env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.handshake_path = self.root / "support" / app / "server.json"
        deadline = time.time() + 20
        while time.time() < deadline and not self.handshake_path.exists():
            if self.proc.poll() is not None:
                raise RuntimeError("サーバーが起動しませんでした: " + self.proc.stderr.read().decode("utf-8", "replace"))
            time.sleep(0.1)
        self.info = json.loads(self.handshake_path.read_text(encoding="utf-8"))

    def call(self, path, body=None, token=True):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-PPM-Token"] = self.info["token"]
        req = urllib.request.Request(f"http://127.0.0.1:{self.info['httpPort']}{path}", data=data,
                                     method="POST" if body is not None else "GET", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")

    def wait_job(self, job_id, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            _, job = self.call(f"/jobs/{job_id}")
            if job["status"] in ("done", "error", "cancelled"):
                return job
            time.sleep(0.1)
        raise AssertionError("ジョブが終わりませんでした")

    def stop(self):
        if self.proc.poll() is None:
            if sys.platform == "win32":
                self.proc.terminate()
            else:
                self.proc.send_signal(signal.SIGTERM)
            self.proc.wait(timeout=10)
        self.proc.stderr.close()
```

`tests/test_local_server.py`:

```python
import importlib.util
import json
import os
import stat
import subprocess
import sys
import unittest

from server_helpers import LiveServer, make_server_dir

SLOW = "import time\nNAME = 'slow'\ndef run(params, ctx):\n    for _ in range(100):\n        if ctx.cancelled():\n            return None\n        time.sleep(0.05)\n    return {'ok': True}\n"
BOOM = "from ppm_jobs import JobError\nNAME = 'boom'\ndef run(params, ctx):\n    raise JobError('止めました', '理由です', '次の一手です')\n"
HELLO = "ROUTES = {('GET', '/hello'): lambda req, ctx: (200, {'hi': ctx['app']})}\n"


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(make_server_dir(jobs={"slow": SLOW, "boom": BOOM}, ext={"hello": HELLO}))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_handshake_is_private_and_complete(self):
        info = self.server.info
        for key in ("pid", "httpPort", "token", "version", "protocol", "tmpDir", "serverDir"):
            self.assertIn(key, info)
        if sys.platform != "win32":
            self.assertEqual(stat.S_IMODE(os.stat(self.server.handshake_path).st_mode), 0o600)

    def test_token_is_required(self):
        self.assertEqual(self.server.call("/ping", token=False)[0], 403)
        code, data = self.server.call("/ping")
        self.assertEqual(code, 200)
        self.assertIn("echo", data["jobs"])

    def test_echo_job(self):
        code, start = self.server.call("/jobs/echo", {"テキスト": "こんにちは"})
        self.assertEqual(code, 202)
        job = self.server.wait_job(start["jobId"])
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["result"]["echo"]["テキスト"], "こんにちは")

    def test_unknown_job_and_route(self):
        self.assertEqual(self.server.call("/jobs/nope", {})[0], 404)
        self.assertEqual(self.server.call("/nope")[0], 404)

    def test_one_job_at_a_time_and_cancel(self):
        _, slow = self.server.call("/jobs/slow", {})
        self.assertEqual(self.server.call("/jobs/echo", {})[0], 409)
        self.server.call(f"/jobs/{slow['jobId']}/cancel", {})
        self.assertEqual(self.server.wait_job(slow["jobId"])["status"], "cancelled")

    def test_job_error_keeps_reason_and_http_200(self):
        _, start = self.server.call("/jobs/boom", {})
        job = self.server.wait_job(start["jobId"])
        self.assertEqual(job["status"], "error")
        self.assertEqual(job["error"], {"message": "止めました", "why": "理由です", "next": "次の一手です"})

    def test_extension_route(self):
        self.assertEqual(self.server.call("/hello"), (200, {"hi": "PpmTest"}))
        self.assertEqual(self.server.call("/hello", token=False)[0], 403)


class ShutdownTests(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "Windows の terminate は後始末を走らせない")
    def test_handshake_is_removed_on_stop(self):
        s = LiveServer(make_server_dir())
        s.stop()
        self.assertFalse(s.handshake_path.exists())


class InstallTests(unittest.TestCase):
    def load_install(self, server_dir):
        spec = importlib.util.spec_from_file_location("ppm_install_under_test", server_dir / "install.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_dry_run_changes_nothing(self):
        d = make_server_dir()
        support = d.parent / "support"
        env = {**os.environ, "PPM_APP_SUPPORT_ROOT": str(support), "PPM_LOG_ROOT": str(d.parent / "logs"), "PYTHONIOENCODING": "cp932"}
        proc = subprocess.run([sys.executable, str(d / "install.py"), "--dry-run"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("runtime", proc.stdout)
        self.assertIn("試し実行", proc.stdout)
        self.assertFalse(support.exists())

    def test_plist_escapes_paths(self):
        mod = self.load_install(make_server_dir())
        text = mod.plist_text("/opt/a&b/python3", mod.Path("/srv/ppm_server.py"))
        self.assertIn("/opt/a&amp;b/python3", text)
        self.assertIn("com.ppm.ppmtest.server", text)


if __name__ == "__main__":
    unittest.main()
```

`tests/js/server_client.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

// 実名に見えるホームは実行時に組み立てる（Task 34 の衛生検査に引っかからないように）
const WIN_HOME = "C:\\" + "Users\\山田 太郎";
const MAC_HOME = "/Users/" + "someone";

function client({ platform = "darwin", responses = [], handshakes = [{ token: "t1", httpPort: 5000, protocol: 1, tmpDir: "/tmp/x" }] } = {}) {
  let reads = 0;
  const seen = { paths: [], calls: [] };
  const fs = {
    async readFile(p) {
      seen.paths.push(p);
      const h = handshakes[Math.min(reads, handshakes.length - 1)];
      reads += 1;
      if (!h) throw new Error("ENOENT");
      return JSON.stringify(h);
    },
  };
  const os = { homedir: () => (platform === "win32" ? WIN_HOME : MAC_HOME), platform: () => platform };
  const fetch = async (url, opts) => {
    seen.calls.push({ url, opts });
    const r = responses.shift();
    if (r instanceof Error) throw r;
    return { status: r.status, async json() { return r.body; } };
  };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "local-server/lib/ppm-server-client.js"],
    { require: (n) => (n === "fs" ? fs : n === "os" ? os : null), fetch }, { "{{APP_NAME}}": "PpmTest" });
  return { PPM: ctx.PPM, seen };
}

test("握手のファイルの場所（Mac と Windows）", () => {
  assert.equal(client().PPM.server.handshakePath(), `${MAC_HOME}/Library/Application Support/PpmTest/server.json`);
  assert.equal(client({ platform: "win32" }).PPM.server.handshakePath(), `${WIN_HOME}\\AppData\\Roaming\\PpmTest\\server.json`);
});

test("合言葉を付けて呼び、403 なら読み直して 1 回だけやり直す", async () => {
  const { PPM, seen } = client({
    handshakes: [{ token: "old", httpPort: 5000, protocol: 1, tmpDir: "/t" }, { token: "new", httpPort: 5001, protocol: 1, tmpDir: "/t" }],
    responses: [{ status: 403, body: {} }, { status: 200, body: { ok: true } }],
  });
  const r = await PPM.server.call("/ping");
  assert.equal(r.ok, true);
  assert.equal(seen.calls[0].opts.headers["X-PPM-Token"], "old");
  assert.equal(seen.calls[1].opts.headers["X-PPM-Token"], "new");
  assert.equal(seen.calls[1].url, "http://127.0.0.1:5001/ping");
});

test("約束の番号が違えばつながない", async () => {
  const { PPM } = client({ handshakes: [{ token: "t", httpPort: 1, protocol: 9, tmpDir: "/t" }] });
  await assert.rejects(PPM.server.readHandshake(), /版が合いません/);
});

test("サーバーが無ければ、入れ方を案内する", async () => {
  const { PPM } = client({ handshakes: [null] });
  await assert.rejects(PPM.server.readHandshake(), (e) => e.ppm && e.ppm.next.includes("install"));
});

test("runJob は終わるまで待ち、進み具合を知らせる", async () => {
  const progress = [];
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, { status: 200, body: { status: "running", percent: 50 } }, { status: 200, body: { status: "done", result: { a: 1 } } }] });
  const r = await PPM.server.runJob("echo", {}, { fastMs: 1, onProgress: (p) => progress.push(p) });
  assert.equal(r.a, 1);
  assert.deepEqual(progress, [50, 0]);
});

test("ジョブの失敗は理由つきのエラーにする", async () => {
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, { status: 200, body: { status: "error", error: { message: "止めました", why: "理由", next: "次" } } }] });
  await assert.rejects(PPM.server.runJob("x", {}, { fastMs: 1 }), (e) => e.ppm.why === "理由");
});

test("通信が 3 回続けて切れたら諦める", async () => {
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, new Error("down"), new Error("down"), new Error("down")] });
  await assert.rejects(PPM.server.runJob("x", {}, { fastMs: 1 }), /down/);
});
```

`tests/js/load_parts.js` の `loadParts` を、置き換えの表を受け取る形にする:

```js
function loadParts(files, extra = {}, replace = {}) {
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, ...extra });
  for (const f of files) {
    let src = fs.readFileSync(path.join(PARTS, f), "utf8");
    for (const [k, v] of Object.entries(replace)) src = src.split(k).join(v);
    vm.runInContext(src, ctx, { filename: f });
  }
  return ctx;
}
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_local_server.py' -v`
Expected: FAIL（部品のフォルダが無いので `copytree` が失敗）

- [ ] **Step 3: サーバー側を書く**

`SKILL/parts/local-server/server/ppm_paths.py`:

```python
"""OS ごとのサーバーの置き場所。配った先でも動くよう、キットの道具に頼らずここだけで完結させる。
テストでは PPM_APP_SUPPORT_ROOT と PPM_LOG_ROOT で置き場所を変えられる。"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _home() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    return Path(os.environ.get("HOME") or Path.home())


def app_support(app: str) -> Path:
    root = os.environ.get("PPM_APP_SUPPORT_ROOT")
    if root:
        return Path(root) / app
    if sys.platform == "darwin":
        return _home() / "Library" / "Application Support" / app
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or (_home() / "AppData" / "Roaming")) / app
    return _home() / ".local" / "share" / app


def log_dir(app: str) -> Path:
    root = os.environ.get("PPM_LOG_ROOT")
    if root:
        return Path(root) / app
    if sys.platform == "darwin":
        return _home() / "Library" / "Logs" / app
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or (_home() / "AppData" / "Local")) / app / "Logs"
    return _home() / ".local" / "state" / app / "logs"
```

`SKILL/parts/local-server/server/ppm_jobs.py`:

```python
"""ジョブを書くときの共通部品。jobs/<名前>.py は NAME と run(params, ctx) を持つ。"""
from __future__ import annotations


class JobError(Exception):
    """利用者に見せる理由つきの失敗。パネルには「症状・なぜ・次の一手」で出る。"""

    def __init__(self, message: str, why: str = "", next_step: str = ""):
        super().__init__(message)
        self.why = why
        self.next_step = next_step


def need(params: dict, key: str, kind=str):
    """必須の引数を取り出す。無い・型が違うときは理由つきで止める。"""
    value = params.get(key)
    if value is None or (kind is not None and not isinstance(value, kind)):
        raise JobError(f"「{key}」が渡されていません", "パネルからサーバーへの呼び出しが足りません", "パネルを開き直してから、もう一度試してください")
    return value
```

`SKILL/parts/local-server/server/ppm_server.py`:

```python
#!/usr/bin/env python3
"""プラグイン用の手元のサーバー（127.0.0.1 だけで待つ）。

- 起動ごとに合言葉（token）を作り、server.json に書く（待ち受けを始めてから・0600・原子的に置き換え）
- パネルはヘッダー X-PPM-Token に合言葉を付けて呼ぶ。違えば 403
- 重い処理は「ジョブ」として 1 本ずつ動かす（POST /jobs/<種類> → GET /jobs/<id>）
- ジョブが失敗しても HTTP は 200 で {"status": "error"} を返す（通信の失敗と区別するため）
- 追加の口は server/ext/*.py の ROUTES に書く（mcp-bridge・cep-helper の部品が使う）
"""
from __future__ import annotations

import importlib
import json
import os
import secrets
import signal
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402
from ppm_jobs import JobError  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
VERSION = CONFIG.get("version", "0.0.0")
PROTOCOL = int(CONFIG.get("protocol", 1))
TOKEN = secrets.token_hex(16)
APP_DIR = ppm_paths.app_support(APP)
TMP_DIR = APP_DIR / "tmp"
LOG_FILE = ppm_paths.log_dir(APP) / "server.log"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1_000_000:
        os.replace(LOG_FILE, LOG_FILE.with_name("server.log.1"))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


class Job:
    def __init__(self, kind: str, params: dict):
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.params = params
        self.status = "queued"
        self.percent = 0
        self.message = ""
        self.result = None
        self.error = None
        self.cancel_event = threading.Event()

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "status": self.status, "percent": self.percent,
                "message": self.message, "result": self.result, "error": self.error}


class JobContext:
    def __init__(self, job: Job):
        self._job = job
        self.tmp_dir = str(TMP_DIR)
        self.app = APP

    def progress(self, percent: float, message: str = "") -> None:
        self._job.percent = max(0, min(100, int(percent)))
        if message:
            self._job.message = message

    def cancelled(self) -> bool:
        return self._job.cancel_event.is_set()

    def log(self, msg: str) -> None:
        log(f"[{self._job.kind}] {msg}")


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = {}
        self.running = None

    def start(self, kind: str, params: dict, fn) -> Job:
        with self.lock:
            if self.running is not None and self.running.status in ("queued", "running"):
                raise RuntimeError("busy")
            job = Job(kind, params)
            self.jobs[job.id] = job
            self.running = job
        threading.Thread(target=self._run, args=(job, fn), daemon=True).start()
        return job

    def _run(self, job: Job, fn) -> None:
        job.status = "running"
        try:
            job.result = fn(job.params, JobContext(job))
            if job.cancel_event.is_set():
                job.status = "cancelled"
            else:
                job.status = "done"
                job.percent = 100
        except JobError as e:
            job.status = "error"
            job.error = {"message": str(e), "why": e.why, "next": e.next_step}
            log(f"[{job.kind}] error: {e}")
        except Exception as e:  # noqa: BLE001  想定外も理由を返す
            job.status = "error"
            job.error = {"message": f"{e}（{type(e).__name__}）", "why": "思わぬ失敗です",
                         "next": f"{LOG_FILE} の内容を AI に伝えてください"}
            log(f"[{job.kind}] crash: {traceback.format_exc()}")


STORE = Store()
JOBS = {}
ROUTES = {}


def load_modules(folder: str) -> list:
    mods = []
    for path in sorted((HERE / folder).glob("*.py")):
        if not path.name.startswith("_"):
            mods.append(importlib.import_module(f"{folder}.{path.stem}"))
    return mods


class Handler(BaseHTTPRequestHandler):
    server_version = "ppm"

    def log_message(self, fmt, *args):  # 呼び出しのたびの記録はしない（ポーリングでログが膨らむ）
        pass

    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-PPM-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}

    def _dispatch(self, method: str) -> None:
        if not secrets.compare_digest(self.headers.get("X-PPM-Token", ""), TOKEN):
            return self._send(403, {"error": "合言葉が違います", "next": "パネルを開き直してください（サーバーを起動し直すと合言葉が変わります）"})
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        try:
            body = self._body() if method == "POST" else {}
        except ValueError:
            return self._send(400, {"error": "送られてきた JSON が読めません"})
        if method == "GET" and parts == ["ping"]:
            return self._send(200, {"ok": True, "app": APP, "version": VERSION, "protocol": PROTOCOL, "jobs": sorted(JOBS)})
        if method == "POST" and len(parts) == 2 and parts[0] == "jobs":
            fn = JOBS.get(parts[1])
            if fn is None:
                return self._send(404, {"error": f"ジョブ「{parts[1]}」はありません", "jobs": sorted(JOBS)})
            try:
                job = STORE.start(parts[1], body, fn)
            except RuntimeError:
                return self._send(409, {"error": "別の処理が動いています。終わるまで待ってください"})
            return self._send(202, {"jobId": job.id})
        if method == "GET" and len(parts) == 2 and parts[0] == "jobs":
            job = STORE.jobs.get(parts[1])
            return self._send(200, job.to_dict()) if job else self._send(404, {"error": "そのジョブはありません"})
        if method == "POST" and len(parts) == 3 and parts[0] == "jobs" and parts[2] == "cancel":
            job = STORE.jobs.get(parts[1])
            if job is None:
                return self._send(404, {"error": "そのジョブはありません"})
            job.cancel_event.set()
            return self._send(200, {"ok": True})
        handler = ROUTES.get((method, url.path))
        if handler is not None:
            code, obj = handler({"path": url.path, "query": parse_qs(url.query), "body": body},
                                {"token": TOKEN, "app": APP, "tmp_dir": str(TMP_DIR), "log": log})
            return self._send(code, obj)
        return self._send(404, {"error": "その口はありません"})

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def write_handshake(port: int) -> Path:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    data = {"pid": os.getpid(), "httpPort": port, "token": TOKEN, "version": VERSION, "protocol": PROTOCOL,
            "tmpDir": str(TMP_DIR), "serverDir": str(HERE)}
    path = APP_DIR / "server.json"
    tmp = APP_DIR / f".server.json.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    return path


def remove_handshake() -> None:
    path = APP_DIR / "server.json"
    try:
        if json.loads(path.read_text(encoding="utf-8")).get("pid") == os.getpid():
            path.unlink()
    except (OSError, ValueError):
        pass


def _stop(*_args):
    raise KeyboardInterrupt


def main() -> int:
    if sys.stdout is None or sys.stderr is None:  # pythonw（Windows の常駐）では標準出力が無い
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(LOG_FILE, "a", encoding="utf-8")
    for mod in load_modules("jobs"):
        if hasattr(mod, "NAME") and hasattr(mod, "run"):
            JOBS[mod.NAME] = mod.run
    for mod in load_modules("ext"):
        ROUTES.update(getattr(mod, "ROUTES", {}))
    port = int(os.environ.get("PPM_PORT") or CONFIG.get("port", 0))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        log(f"待ち受けを始められません（{e}）。同じポートを別のサーバーが使っていないか確かめてください")
        return 1
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)
    write_handshake(httpd.server_address[1])
    log(f"started {APP} {VERSION} on 127.0.0.1:{httpd.server_address[1]} jobs={sorted(JOBS)} routes={sorted(p for _, p in ROUTES)}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        remove_handshake()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/local-server/server/config.json`:

```json
{
  "app": "{{APP_NAME}}",
  "version": "{{VERSION}}",
  "protocol": 1,
  "port": 0
}
```

`SKILL/parts/local-server/server/jobs/__init__.py` と `ext/__init__.py`: 空のファイル。

`SKILL/parts/local-server/server/jobs/echo.py`:

```python
"""動作の確かめ用のジョブ（受け取った値をそのまま返す）。"""
NAME = "echo"


def run(params, ctx):
    ctx.progress(50, "受け取りました")
    return {"echo": params}
```

`SKILL/parts/local-server/server/launchd.plist.template`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>__LABEL__</string>
  <key>ProgramArguments</key>
  <array><string>__PYTHON__</string><string>__SERVER__</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/><key>Crashed</key><true/></dict>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUTF8</key><string>1</string>
  </dict>
  <key>StandardOutPath</key><string>__LOG_DIR__/server.out.log</string>
  <key>StandardErrorPath</key><string>__LOG_DIR__/server.err.log</string>
</dict>
</plist>
```

`SKILL/parts/local-server/server/install.py`:

```python
#!/usr/bin/env python3
"""手元のサーバーを入れる・外す・確かめる（Mac は launchd、Windows はタスク スケジューラ）。

  Mac:     python3 server/install.py [--dry-run] [--force] [--with-deps] | --uninstall | --status
  Windows: py -3 server\\install.py   （同じ）
- 版ごとの置き場所（runtime/<版>/）に写してから常駐させる。同じ版が既にあれば写さない（--force で置き換え）
- --with-deps のときだけ requirements.txt の依存を専用の環境（venv）に入れる。入れる前に利用者の許可を取ること
- 最後に server.json と /ping で、新しい版が動いていることを確かめる
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import venv
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
VERSION = CONFIG.get("version", "0.0.0")
LABEL = f"com.ppm.{APP.lower()}.server"
TASK = f"{APP} Server"


def _out(text: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print(text)


def runtime_dir() -> Path:
    return ppm_paths.app_support(APP) / "runtime" / VERSION


def venv_dir() -> Path:
    return ppm_paths.app_support(APP) / "venv" / VERSION


def requirements() -> list:
    req = HERE / "requirements.txt"
    if not req.exists():
        return []
    return [line.strip() for line in req.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def missing_deps() -> list:
    out = []
    for dep in requirements():
        name = dep.split(";")[0].split("[")[0]
        for sep in ("==", ">=", "<=", "~=", ">", "<"):
            name = name.split(sep)[0]
        module = name.strip().replace("-", "_")
        if importlib.util.find_spec(module) is None:
            out.append(dep)
    return out


def service_python(with_deps: bool) -> str:
    if with_deps:
        return str(venv_dir() / ("Scripts/pythonw.exe" if sys.platform == "win32" else "bin/python3"))
    if sys.platform == "win32":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        return str(pyw if pyw.exists() else sys.executable)
    return sys.executable


def plist_text(python: str, server: Path) -> str:
    tpl = (HERE / "launchd.plist.template").read_text(encoding="utf-8")
    values = {"__LABEL__": LABEL, "__PYTHON__": python, "__SERVER__": str(server), "__LOG_DIR__": str(ppm_paths.log_dir(APP))}
    for key, value in values.items():
        tpl = tpl.replace(key, escape(value))
    return tpl


def _ps(text: str) -> str:
    return text.replace("'", "''")


def _powershell(script: str) -> subprocess.CompletedProcess:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _startup_file() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / f"{APP}-server.pyw"


def register_service(python: str, server: Path, apply: bool, plan: list) -> None:
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        uid = os.getuid()
        plan.append(f"常駐の設定を書いて起動する: {plist}")
        if not apply:
            return
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(plist_text(python, server), encoding="utf-8")
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True)
        r = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{LABEL}"], capture_output=True)
    elif sys.platform == "win32":
        plan.append(f"タスク スケジューラに「{TASK}」を登録して起動する（サインインのたびに起動）")
        if not apply:
            return
        script = (f"$a = New-ScheduledTaskAction -Execute '{_ps(python)}' -Argument '\"{_ps(str(server))}\"';"
                  "$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME;"
                  "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0;"
                  f"Register-ScheduledTask -TaskName '{_ps(TASK)}' -Action $a -Trigger $t -Settings $s -Force | Out-Null;"
                  f"Start-ScheduledTask -TaskName '{_ps(TASK)}'")
        if _powershell(script).returncode != 0:
            # 登録できない環境（会社の PC の制限など）では、スタートアップに起動用のファイルを置き、今すぐ起動する
            startup = _startup_file()
            startup.parent.mkdir(parents=True, exist_ok=True)
            startup.write_text(f"import runpy\nrunpy.run_path({str(server)!r}, run_name='__main__')\n", encoding="utf-8")
            subprocess.Popen([python, str(server)], creationflags=0x00000008 | 0x00000200, close_fds=True)
            plan.append(f"タスクの登録ができなかったので、スタートアップに置きました: {startup}")
    else:
        plan.append("この OS には常駐の仕組みを用意していません。python3 server/ppm_server.py で起動してください")


def unregister_service() -> None:
    if sys.platform == "darwin":
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"], capture_output=True)
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        if plist.exists():
            plist.unlink()
    elif sys.platform == "win32":
        _powershell(f"Unregister-ScheduledTask -TaskName '{_ps(TASK)}' -Confirm:$false")
        if _startup_file().exists():
            _startup_file().unlink()


def ping(timeout: float = 3.0) -> dict:
    info = json.loads((ppm_paths.app_support(APP) / "server.json").read_text(encoding="utf-8"))
    req = urllib.request.Request(f"http://127.0.0.1:{info['httpPort']}/ping", headers={"X-PPM-Token": info["token"]})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def wait_ready(timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = ping()
            if data.get("version") == VERSION:
                return data
        except Exception:  # noqa: BLE001  まだ起動していない
            pass
        time.sleep(0.5)
    raise SystemExit(f"サーバーが応答しません。{ppm_paths.log_dir(APP)} のログを AI に伝えてください")


def write_current(dst: Path) -> None:
    path = ppm_paths.app_support(APP) / "runtime" / "current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".current.json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"version": VERSION, "runtimeDir": str(dst)}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="手元のサーバーを入れる・外す")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--with-deps", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(argv)
    if args.status:
        try:
            _out(f"動いています: {ping()}")
            return 0
        except Exception as e:  # noqa: BLE001
            _out(f"動いていません（{e}）")
            return 1
    if args.uninstall:
        unregister_service()
        _out("常駐を外しました（設定とログは残しています）")
        return 0
    plan = []
    apply = not args.dry_run
    dst = runtime_dir()
    copy_needed = args.force or not dst.exists()
    plan.append(f"写す: {HERE} → {dst}" if copy_needed else f"同じ版 {VERSION} が既にあるので写しません（置き換えるときは --force）: {dst}")
    deps = requirements()
    if args.with_deps and deps:
        plan.append(f"専用の環境を作って依存を入れる: {venv_dir()}（{', '.join(deps)}）")
    elif deps and missing_deps():
        plan.append(f"足りない依存: {', '.join(missing_deps())}（--with-deps で専用の環境に入れられます。入れる前に許可を取ってください）")
    python = service_python(args.with_deps and bool(deps))
    register_service(python, dst / "ppm_server.py", False, plan)
    _out("\n".join("・" + p for p in plan))
    if not apply:
        _out("（試し実行です。何もしていません）")
        return 0
    if args.with_deps and deps:
        venv.create(venv_dir(), with_pip=True)
        py = venv_dir() / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
        r = subprocess.run([str(py), "-m", "pip", "install", "-r", str(HERE / "requirements.txt")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            _out("依存を入れられませんでした:\n" + (r.stdout + r.stderr)[-3000:])
            return 1
    if copy_needed:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
    write_current(dst)
    register_service(python, dst / "ppm_server.py", True, [])
    data = wait_ready()
    _out(f"入れました。{APP} {data['version']} が動いています。パネルを開き直してください")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/local-server/server/install_mac.command`:

```bash
#!/bin/bash
# ターミナルで「bash 」（後ろに空白）と打ち、このファイルをドラッグして Enter で実行する
set -eu
LC_ALL=C
DIR="$(cd "$(dirname "${0}")" && pwd)"
exec /usr/bin/env python3 "${DIR}/install.py" "$@"
```

`SKILL/parts/local-server/server/uninstall_mac.command`:

```bash
#!/bin/bash
set -eu
LC_ALL=C
DIR="$(cd "$(dirname "${0}")" && pwd)"
exec /usr/bin/env python3 "${DIR}/install.py" --uninstall
```

`SKILL/parts/local-server/server/install_windows.bat`（英数字だけ）:

```bat
@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0install.py" %*
) else (
  python "%~dp0install.py" %*
)
pause
```

`SKILL/parts/local-server/server/uninstall_windows.bat`（英数字だけ）:

```bat
@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0install.py" --uninstall
) else (
  python "%~dp0install.py" --uninstall
)
pause
```

- [ ] **Step 4: パネル側・part.json・雛形を書く**

`SKILL/parts/local-server/lib/ppm-server-client.js`:

```js
/* ppm-server-client — パネルから手元のサーバーを呼ぶ。
 * - 合言葉は server.json から読む（サーバーを起動し直すと変わるので、403 なら読み直して 1 回だけやり直す）
 * - ジョブは「始める → 状態を見に行く」。最初の 5 回は 0.3 秒、その後 1.5 秒ごと。通信が 3 回続けて切れたら諦める
 * - 127.0.0.1 へつなぐには manifest の network.domains が "all" であること（個別の許可では通信が起きなかった） */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const APP = "{{APP_NAME}}";
  const PROTOCOL = 1;
  const state = { handshake: null };

  function handshakePath() {
    const os = require("os");
    const home = os.homedir();
    if (os.platform() === "win32") return `${home}\\AppData\\Roaming\\${APP}\\server.json`;
    return `${home}/Library/Application Support/${APP}/server.json`;
  }

  async function readHandshake() {
    const fs = require("fs");
    let raw;
    try {
      raw = await fs.readFile(handshakePath(), { encoding: "utf-8" });
    } catch (e) {
      throw PPM.err("サーバーが動いていません", "server.json が見つかりません（まだ入れていないか、止まっています）",
        "作業フォルダの server の install（Mac は install_mac.command、Windows は install_windows.bat）を実行してから、パネルを開き直してください");
    }
    const h = JSON.parse(raw);
    if (!h.token || !h.httpPort) throw PPM.err("サーバーの情報が壊れています", "server.json に合言葉かポートがありません", "サーバーを入れ直してください");
    if (Number(h.protocol) !== PROTOCOL) {
      throw PPM.err("パネルとサーバーの版が合いません", `サーバーの約束の番号が ${h.protocol}（パネルは ${PROTOCOL}）です`, "パネルとサーバーを同じ版で入れ直してください");
    }
    state.handshake = h;
    return h;
  }

  async function call(path, opts, retried) {
    const o = opts || {};
    if (!state.handshake) await readHandshake();
    const h = state.handshake;
    const res = await fetch(`http://127.0.0.1:${h.httpPort}${path}`, {
      method: o.method || "GET",
      headers: { "Content-Type": "application/json", "X-PPM-Token": h.token },
      body: o.body ? JSON.stringify(o.body) : undefined,
    });
    if (res.status === 403 && !retried) {
      await readHandshake();
      return call(path, o, true);
    }
    let data = {};
    try { data = await res.json(); } catch (e) { data = {}; }
    if (res.status >= 400) {
      throw PPM.err(data.error || `サーバーがエラーを返しました（${res.status}）`, data.why || "", data.next || "パネルを開き直してから、もう一度試してください");
    }
    return data;
  }

  async function connect(opts) {
    const o = opts || {};
    const tries = o.tries || 5;
    let last = null;
    for (let i = 0; i < tries; i++) {
      try {
        await readHandshake();
        await call("/ping");
        return state.handshake;
      } catch (e) {
        last = e;
        if (i < tries - 1) await new Promise((r) => setTimeout(r, o.intervalMs === undefined ? 4000 : o.intervalMs));
      }
    }
    throw last;
  }

  async function runJob(kind, params, opts) {
    const o = opts || {};
    const start = await call(`/jobs/${kind}`, { method: "POST", body: params || {} });
    let polls = 0;
    let failures = 0;
    for (;;) {
      await new Promise((r) => setTimeout(r, polls < 5 ? (o.fastMs || 300) : (o.slowMs || 1500)));
      polls += 1;
      let job;
      try {
        job = await call(`/jobs/${start.jobId}`);
        failures = 0;
      } catch (e) {
        failures += 1;
        if (failures >= 3) throw e;
        continue;
      }
      if (o.onProgress) o.onProgress(job.percent || 0, job.message || "");
      if (job.status === "done") return job.result;
      if (job.status === "cancelled") throw PPM.err("処理を止めました", "途中で止めたので、結果はありません", "必要なら、もう一度実行してください");
      if (job.status === "error") {
        const e = job.error || {};
        throw PPM.err(e.message || "サーバーの処理が失敗しました", e.why || "", e.next || "");
      }
    }
  }

  function tmpPath(name) {
    if (!state.handshake) throw PPM.err("サーバーにつながっていません", "まだ connect していません", "先に PPM.server.connect() を呼んでください");
    return PPM.joinPath(state.handshake.tmpDir, name);
  }

  PPM.server = { connect, call, runJob, tmpPath, handshakePath, readHandshake };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/local-server/part.json`:

```json
{
  "name": "local-server",
  "description": "重い処理を任せる手元のサーバー（127.0.0.1 だけ・起動ごとの合言葉・ジョブ）。Mac は launchd、Windows はタスク スケジューラで常駐",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["ppro-kit"],
  "files": {"server/": "server/", "lib/ppm-server-client.js": "lib/ppm-server-client.js"},
  "scripts": ["lib/ppm-server-client.js"],
  "styles": [],
  "permissions": {"localFileSystem": "fullAccess", "network": {"domains": "all"}},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["ref-local-server", "recipe-local-server-heavy"],
  "notes": "ジョブは server/jobs/<名前>.py に NAME と run(params, ctx)。パネルからは await PPM.server.connect() のあと await PPM.server.runJob(\"名前\", {...})。入れ方は server/install_mac.command か install_windows.bat"
}
```

`SKILL/templates/panel-server/template.json`:

```json
{
  "name": "panel-server",
  "description": "パネル＋手元のサーバー（音声の解析・ファイルの生成・AI など、パネルだけでは重い処理）",
  "extends": "panel",
  "parts": ["local-server"],
  "minVersion": "25.6"
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_local_server.py' -v && node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_templates.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（local-server 10・JS 全部・templates 2・parts 1）。`test_templates` で panel-server の作業フォルダが W003（文字コード）や W004（Mac 専用の場所）で誤りになったら、部品のコードを直す。

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 local-server（合言葉・ジョブ・常駐の導入）と雛形 panel-server

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: 部品 media-tools と keychain

**Files:**
- Create: `SKILL/parts/media-tools/part.json`、`SKILL/parts/media-tools/server/ppm_media.py`
- Create: `SKILL/parts/keychain/part.json`、`SKILL/parts/keychain/server/ppm_keychain.py`（移植元: Cut & SRT の `server/keychain_store.py`）
- Test: `tests/test_media_tools.py`、`tests/test_keychain.py`

**Interfaces:**
- Produces（`ppm_media`）: `find_tool(name, which=shutil.which, run=subprocess.run) -> str | None`（Mac は `/opt/homebrew/bin` を先に見る。Windows は `%LOCALAPPDATA%\Microsoft\WinGet\Links` も見る。候補は実際に `-version` で起動して確かめる）、`extract_pcm16(path, rate=16000, start=None, duration=None) -> bytes`、`rms_db(samples, window: int) -> list[float]`（無音は -120.0）、`probe_duration(path) -> float`、`class MediaError(RuntimeError)`
- Produces（`ppm_keychain`）: `SERVICE`（config.json の app）、`set_secret(name, value)`、`get_secret(name) -> str | None`、`delete_secret(name)`、`has_secret(name) -> bool`。Mac はキーチェーン（値は `security -i` の標準入力で渡し、コマンドラインに出さない）、Windows は DPAPI（ユーザー単位）でアプリのフォルダに暗号化して置く
- 安全の決まり（テストとこの Task の作業に必ず守る）: **本物のキーチェーン・資格情報の保管庫に書かない**。テストは `subprocess` を偽物に差し替える。Windows の DPAPI のテストは Windows の上でだけ走らせる（Cut&SRT で、試験項目が本物のキーチェーンに残った事故があった）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_media_tools.py`:

```python
import array
import math
import shutil
import subprocess
import sys
import unittest

from helpers import PARTS, temp_dir

sys.path.insert(0, str(PARTS / "media-tools" / "server"))
import ppm_media  # noqa: E402


class MediaToolsTests(unittest.TestCase):
    def test_rms_db_silence_and_full_scale(self):
        silence = array.array("h", [0] * 1600)
        self.assertEqual(ppm_media.rms_db(silence, 800), [-120.0, -120.0])
        tone = array.array("h", [int(32767 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(1600)])
        for v in ppm_media.rms_db(tone, 800):
            self.assertAlmostEqual(v, -3.0, delta=0.2)

    def test_find_tool_checks_that_it_runs(self):
        ok = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "ffmpeg version", "")
        broken = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "bad")
        self.assertEqual(ppm_media.find_tool("ffmpeg", which=lambda n: "/x/ffmpeg", run=ok, extra=[]), "/x/ffmpeg")
        self.assertIsNone(ppm_media.find_tool("ffmpeg", which=lambda n: "/x/ffmpeg", run=broken, extra=[]))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg が無い")
    def test_extract_and_probe_with_real_ffmpeg(self):
        wav = temp_dir() / "音 テスト.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(wav)], check=True)
        self.assertAlmostEqual(ppm_media.probe_duration(wav), 1.0, delta=0.05)
        pcm = ppm_media.extract_pcm16(wav, rate=16000)
        self.assertAlmostEqual(len(pcm) / 2, 16000, delta=200)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_keychain.py`:

```python
import json
import subprocess
import sys
import unittest
from unittest import mock

from helpers import PARTS, temp_dir

SERVER = temp_dir() / "server"
SERVER.mkdir()
(SERVER / "config.json").write_text(json.dumps({"app": "PpmTest"}), encoding="utf-8")
src = (PARTS / "keychain" / "server" / "ppm_keychain.py").read_text(encoding="utf-8")
(SERVER / "ppm_keychain.py").write_text(src, encoding="utf-8")
sys.path.insert(0, str(SERVER))
import ppm_keychain  # noqa: E402


class MacKeychainTests(unittest.TestCase):
    """本物のキーチェーンには書かない。security の呼び出しを偽物に差し替えて、渡し方だけを確かめる。"""

    @unittest.skipUnless(sys.platform == "darwin", "Mac だけ")
    def test_value_goes_through_stdin_not_argv(self):
        calls = []

        def fake_run(cmd, **kw):
            calls.append((cmd, kw.get("input")))
            if "find-generic-password" in " ".join(cmd):
                return subprocess.CompletedProcess(cmd, 0, "秘密の値\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(ppm_keychain.subprocess, "run", side_effect=fake_run):
            ppm_keychain.set_secret("api", "秘密の値")
        for cmd, stdin in calls:
            self.assertNotIn("秘密の値", " ".join(cmd))
        self.assertTrue(any(stdin and "秘密の値" in stdin for _, stdin in calls))
        self.assertTrue(all("PpmTest" in " ".join(c) + (s or "") for c, s in calls))

    def test_bad_names_are_rejected(self):
        with self.assertRaises(ValueError):
            ppm_keychain.set_secret("名前に 空白", "x")


@unittest.skipUnless(sys.platform == "win32", "Windows だけ（DPAPI）")
class WindowsDpapiTests(unittest.TestCase):
    def test_roundtrip(self):
        ppm_keychain.set_secret("test-roundtrip", "値")
        try:
            self.assertEqual(ppm_keychain.get_secret("test-roundtrip"), "値")
        finally:
            ppm_keychain.delete_secret("test-roundtrip")
        self.assertFalse(ppm_keychain.has_secret("test-roundtrip"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_media_tools.py' -v`
Expected: FAIL（`No module named 'ppm_media'`）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/media-tools/server/ppm_media.py`:

```python
"""ffmpeg の場所探しと、音声の取り出し・音量の計算（標準ライブラリだけ）。

- Mac は /opt/homebrew/bin を先に見る（~/.local/bin などに Intel 専用の ffmpeg が混ざっている Mac があった）
- Windows は winget の別名リンク（%LOCALAPPDATA%\\Microsoft\\WinGet\\Links）も見る。開いたままの画面には PATH が反映されない
- 見つけた候補は実際に起動して確かめる（which で見つかっても動くとは限らない）
"""
from __future__ import annotations

import array
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional


class MediaError(RuntimeError):
    pass


def _candidates(name: str) -> List[str]:
    if sys.platform == "darwin":
        return [f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"]
    if sys.platform == "win32":
        links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
        return [str(links)]
    return []


def find_tool(name: str, which: Callable[[str], Optional[str]] = shutil.which, run=subprocess.run,
              extra: Optional[List[str]] = None) -> Optional[str]:
    candidates = (_candidates(name) if extra is None else extra) + [which(name) or ""]
    for path in candidates:
        if not path or (extra is None and not Path(path).exists() and path != which(name)):
            continue
        try:
            r = run([path, "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0:
            return path
    return None


def _tool(name: str) -> str:
    path = find_tool(name)
    if not path:
        hint = "brew install ffmpeg" if sys.platform == "darwin" else "winget install --id Gyan.FFmpeg -e（入れた後は新しい画面で）"
        raise MediaError(f"{name} が見つかりません。入れ方: {hint}")
    return path


def extract_pcm16(path, rate: int = 16000, start: Optional[float] = None, duration: Optional[float] = None) -> bytes:
    cmd = [_tool("ffmpeg"), "-nostdin", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"]
    r = subprocess.run(cmd, capture_output=True, timeout=3600)
    if r.returncode != 0:
        raise MediaError("音声を取り出せませんでした: " + r.stderr.decode("utf-8", "replace")[-500:])
    return r.stdout


def rms_db(samples, window: int) -> List[float]:
    """window 個ずつの音量（dBFS）。無音は -120.0。"""
    if not isinstance(samples, array.array):
        samples = array.array("h", samples)
    out = []
    for i in range(0, len(samples) - window + 1, window):
        chunk = samples[i:i + window]
        mean = sum(s * s for s in chunk) / window
        out.append(-120.0 if mean <= 0 else round(20 * math.log10(math.sqrt(mean) / 32768.0), 2))
    return out


def probe_duration(path) -> float:
    r = subprocess.run([_tool("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0:
        raise MediaError("長さを読めませんでした: " + r.stderr[-500:])
    return float(r.stdout.strip())
```

`SKILL/parts/keychain/server/ppm_keychain.py`: Cut & SRT の `premiere-cut-srt-plugin/server/keychain_store.py` を写し、次の 3 点だけ変える。

1. サービス名を固定の `"CutSRT"` から、同じフォルダの `config.json` の `app` に変える:

```python
import json
from pathlib import Path

SERVICE = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))["app"]
```

2. Windows の暗号化したファイルの置き場所を `%APPDATA%\CutSRTPlugin\secrets\` から `%APPDATA%\<SERVICE>\secrets\` に変える（`ppm_paths.app_support(SERVICE) / "secrets"` を使う）。
3. 先頭の説明に「本物のキーチェーンへの書き込みを試すときは、使い捨てのキーチェーン（`keychain=` 引数）だけを使う」を残す。

写したあと `grep -n "CutSRT" ppm_keychain.py` が 0 件であることを確かめる。

`SKILL/parts/media-tools/part.json`:

```json
{
  "name": "media-tools",
  "description": "ffmpeg の場所探し（実際に起動して確かめる）・音声の取り出し・音量の計算",
  "status": "verified",
  "os": ["mac", "windows"],
  "requires": ["local-server"],
  "files": {"server/ppm_media.py": "server/ppm_media.py"},
  "scripts": [],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["recipe-silence-cut", "platform-windows"],
  "notes": "ジョブの中で import ppm_media して使う。ffmpeg が無ければ MediaError に入れ方が入る"
}
```

`SKILL/parts/keychain/part.json`:

```json
{
  "name": "keychain",
  "description": "AI などの API キーを OS の保管庫に置く（Mac はキーチェーン、Windows は DPAPI）。ファイルに平文で書かない",
  "status": "verified",
  "os": ["mac", "windows"],
  "requires": ["local-server"],
  "files": {"server/ppm_keychain.py": "server/ppm_keychain.py"},
  "scripts": [],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["recipe-ai-integration"],
  "notes": "部品の名前に secret・token を入れない（配布の検査で落ちる）。パネルには「保存済みかどうか」だけを返す"
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_media_tools.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_keychain.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（Mac では keychain の Windows のテストは skip）

確認（本物のキーチェーンに何も書いていないこと）:

Run: `security find-generic-password -s PpmTest 2>&1 | head -1`
Expected: `security: SecKeychainSearchCopyNext: The specified item could not be found in the keychain.`

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 media-tools（ffmpeg を起動して確かめる）と keychain（OS の保管庫）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 17: 部品 fcpxml（FCP7 XML の読み書き）

**Files:**
- Create: `SKILL/parts/fcpxml/part.json`、`SKILL/parts/fcpxml/server/ppm_fcpxml.py`、`SKILL/parts/fcpxml/server/jobs/read_texts.py`、`SKILL/parts/fcpxml/lib/ppm-fcpxml.js`
- Test: `tests/xml_fixtures.py`、`tests/test_fcpxml.py`、`tests/js/fcpxml_panel.test.js`

**Interfaces:**
- Produces（`ppm_fcpxml`）: `TICKS_PER_SECOND`、`class XmlError(ValueError)`、`load(path) -> ElementTree`（DOCTYPE を外して読む。ENTITY は拒否。xmeml 以外は拒否）、`save(tree, path)`（`<?xml …?>` と `<!DOCTYPE xmeml>` を付ける）、`is_definition(el) -> bool`（子要素を持つか）、`definitions(root, tag="file") -> dict[id, Element]`、`dangling(root, tag="file") -> list[id]`、`ensure_first_definition(root, tag="file") -> int`、`rate_of(el) -> (timebase, ntsc)`（その要素の直下の rate）、`fps(timebase, ntsc) -> Fraction`、`frames_to_seconds(frames, timebase, ntsc) -> float`、`seconds_to_frames(seconds, timebase, ntsc) -> int`、`ticks_per_frame(timebase, ntsc) -> int`、`main_sequence(root) -> Element`、`tracks(seq, kind="video"|"audio") -> list[Element]`、`clipitems(track) -> list[Element]`、`clip_range(ci) -> (start, end)`、`clip_text(ci) -> str | None`（GraphicAndType の本文）、`find_clip(seq, kind, track_index, start_frame) -> Element | None`、`media_path(file_el) -> str | None`
- Produces（ジョブ `read_texts`）: params `{"xmlPath": str, "clips": [{"trackIndex": int, "startTicks": number}]}` → `{"texts": [{"trackIndex", "startTicks", "text": str | null}], "timebase", "ntsc"}`
- Produces（`PPM.fcpxml`、パネル側）: `exportActiveSequence(fileName) -> Promise<string>`（`ProjectConverter.exportAsFinalCutProXML` で server の tmpDir に書き、パスを返す。Premiere 26.2 以上）、`importAndOpen(path) -> Promise<sequence | null>`（読み込みの前後でシーケンスの数を比べて、新しいものを開く）
- Produces（`tests/xml_fixtures.py`）: `write_wav(path, parts=[(秒, 振幅)], rate=48000)`、`write_xmeml(path, media_path, seconds=5, tb=30, ntsc=False, graphic_texts=None)`（graphic_texts を渡すと V2 にテロップのクリップを並べる）、`file_url(path) -> str`（Windows のドライブ文字にも対応）

- [ ] **Step 1: 失敗するテストを書く**

`tests/xml_fixtures.py`（Cut & SRT の `server/tests/test_cut_e2e.py` の `_write_test_wav` と `_write_test_xml` を元に、テロップと Windows のパスを足したもの）:

```python
"""合成の音声と FCP7 XML を作る（実在の素材を使わずに、カットや本文の読み取りを試すため）。"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from urllib.parse import quote

TICKS_PER_SECOND = 254016000000


def write_wav(path, parts=((2.0, 16000), (1.0, 55), (2.0, 16000)), rate=48000) -> Path:
    """(秒, 振幅) を順につないだ 440Hz の音。振幅 55 はおよそ -55dBFS（既定の閾値 -48dB では無音扱い）。"""
    samples = []
    for seconds, amp in parts:
        samples.extend(int(amp * math.sin(2 * math.pi * 440 * i / rate)) for i in range(int(rate * seconds)))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return Path(path)


def file_url(path) -> str:
    p = str(Path(path).resolve()).replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return "file://localhost" + quote(p)


def _rate(tb, ntsc):
    return f"<rate><timebase>{tb}</timebase><ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc></rate>"


def write_xmeml(path, media_path, seconds=5, tb=30, ntsc=False, graphic_texts=None) -> Path:
    total = int(round(seconds * (tb * 1000 / 1001 if ntsc else tb)))
    r = _rate(tb, ntsc)
    graphics = ""
    if graphic_texts:
        items = []
        step = total // len(graphic_texts)
        for i, text in enumerate(graphic_texts):
            s, e = i * step, (i + 1) * step
            items.append(f"""<clipitem id="g-{i}"><name>{text}</name><enabled>TRUE</enabled><duration>{e - s}</duration>{r}
              <start>{s}</start><end>{e}</end><in>0</in><out>{e - s}</out>
              <file id="gfile-{i}"><name>グラフィック</name><mediaSource>GraphicAndType</mediaSource>{r}</file>
              <filter><effect><name>{text}</name><effectid>GraphicAndType</effectid></effect></filter></clipitem>""")
        graphics = "<track>" + "".join(items) + "</track>"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="seq-1">
    <name>合成</name><duration>{total}</duration>{r}
    <media>
      <video>
        <format><samplecharacteristics>{r}<width>1920</width><height>1080</height></samplecharacteristics></format>
        <track>
          <clipitem id="v-1"><name>src</name><enabled>TRUE</enabled><duration>{total}</duration>{r}
            <in>0</in><out>{total}</out><start>0</start><end>{total}</end>
            <pproTicksIn>0</pproTicksIn><pproTicksOut>{round(seconds * TICKS_PER_SECOND)}</pproTicksOut>
            <file id="file-1"><name>src</name><pathurl>{file_url(media_path)}</pathurl>{r}<duration>{total}</duration></file>
          </clipitem>
        </track>
        {graphics}
      </video>
      <audio>
        <track>
          <clipitem id="a-1"><name>src</name><enabled>TRUE</enabled><duration>{total}</duration>{r}
            <in>0</in><out>{total}</out><start>0</start><end>{total}</end>
            <pproTicksIn>0</pproTicksIn><pproTicksOut>{round(seconds * TICKS_PER_SECOND)}</pproTicksOut>
            <file id="file-1"/>
          </clipitem>
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>
"""
    Path(path).write_text(xml, encoding="utf-8")
    return Path(path)
```

`tests/test_fcpxml.py`:

```python
import sys
import unittest
import xml.etree.ElementTree as ET

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir
from xml_fixtures import file_url, write_wav, write_xmeml

sys.path.insert(0, str(PARTS / "fcpxml" / "server"))
import ppm_fcpxml as fx  # noqa: E402


class FcpXmlTests(unittest.TestCase):
    def setUp(self):
        d = temp_dir()
        self.wav = write_wav(d / "素材 1.wav")
        self.xml = write_xmeml(d / "seq.xml", self.wav, graphic_texts=["こんにちは", "まさかの大逆転！"])

    def test_load_reads_sequence_rate_not_first_rate_in_document(self):
        root = fx.load(self.xml).getroot()
        seq = fx.main_sequence(root)
        self.assertEqual(fx.rate_of(seq), (30, False))

    def test_only_first_reference_has_the_definition(self):
        root = fx.load(self.xml).getroot()
        self.assertEqual(set(fx.definitions(root)), {"file-1", "gfile-0", "gfile-1"})
        self.assertEqual(fx.dangling(root), [])

    def test_dangling_reference_is_detected_and_fixed(self):
        root = fx.load(self.xml).getroot()
        video_clip = root.find(".//video/track/clipitem")
        video_clip.remove(video_clip.find("file"))
        ET.SubElement(video_clip, "file", {"id": "file-1"})
        audio_file = root.find(".//audio/track/clipitem/file")
        ET.SubElement(audio_file, "name").text = "src"
        self.assertEqual(fx.dangling(root), ["file-1"])
        self.assertEqual(fx.ensure_first_definition(root), 2)
        self.assertEqual(fx.dangling(root), [])
        self.assertTrue(fx.is_definition(root.find(".//video/track/clipitem/file")))
        self.assertFalse(fx.is_definition(root.find(".//audio/track/clipitem/file")))

    def test_time_conversion_uses_declared_timebase(self):
        self.assertEqual(fx.seconds_to_frames(10, 30, True), 300)
        self.assertAlmostEqual(fx.frames_to_seconds(300, 30, True), 10.01, places=2)
        self.assertEqual(fx.ticks_per_frame(30, False), 8467200000)
        self.assertEqual(fx.ticks_per_frame(30, True), 8475667200)
        self.assertEqual(fx.seconds_to_frames(1, 24, True), 24)

    def test_clip_text_and_find_clip(self):
        seq = fx.main_sequence(fx.load(self.xml).getroot())
        second = fx.find_clip(seq, "video", 1, 75)
        self.assertEqual(fx.clip_text(second), "まさかの大逆転！")
        self.assertIsNone(fx.clip_text(fx.find_clip(seq, "video", 0, 0)))

    def test_media_path_mac_and_windows(self):
        el = ET.fromstring(f"<file><pathurl>{file_url(self.wav)}</pathurl></file>")
        self.assertEqual(fx.media_path(el).replace("\\", "/"), str(self.wav.resolve()).replace("\\", "/"))
        win = ET.fromstring("<file><pathurl>file://localhost/C%3a/Users/%E5%B1%B1%E7%94%B0/a%20b.mov</pathurl></file>")
        self.assertEqual(fx.media_path(win), "C:/" + "Users/山田/a b.mov")

    def test_load_rejects_entities_and_other_xml(self):
        bad = temp_dir() / "bad.xml"
        bad.write_text('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><xmeml/>', encoding="utf-8")
        with self.assertRaises(fx.XmlError):
            fx.load(bad)
        other = temp_dir() / "other.xml"
        other.write_text("<project/>", encoding="utf-8")
        with self.assertRaises(fx.XmlError):
            fx.load(other)

    def test_save_keeps_doctype(self):
        out = temp_dir() / "out.xml"
        fx.save(fx.load(self.xml), out)
        self.assertTrue(out.read_text(encoding="utf-8").startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>'))

    def test_read_texts_job_through_the_server(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "fcpxml" / "server"]))
        try:
            tpf = fx.ticks_per_frame(30, False)
            # 2 つ目はクリップの始まりではない位置（30 フレーム目）なので、本文は None になる
            _, start = server.call("/jobs/read_texts", {"xmlPath": str(self.xml), "clips": [{"trackIndex": 1, "startTicks": 75 * tpf}, {"trackIndex": 1, "startTicks": 30 * tpf}]})
            job = server.wait_job(start["jobId"])
            self.assertEqual(job["status"], "done", job)
            self.assertEqual([t["text"] for t in job["result"]["texts"]], ["まさかの大逆転！", None])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
```

`tests/js/fcpxml_panel.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

function setup({ before = 1, after = 2, exportOk = true } = {}) {
  const fake = makeFake();
  const seqs = Array.from({ length: before }, (_, i) => ({ name: `s${i}` }));
  const opened = [];
  fake.project.getSequences = async () => seqs.slice();
  fake.project.getRootItem = async () => ({ name: "root" });
  fake.project.importFiles = async () => { while (seqs.length < after) seqs.push({ name: `new${seqs.length}` }); return true; };
  fake.project.openSequence = async (s) => { opened.push(s); };
  fake.project.setActiveSequence = async () => {};
  fake.ppro.ProjectConverter = { async exportAsFinalCutProXML(seq, p, suppress) { fake.exported = { p, suppress }; return exportOk; } };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "fcpxml/lib/ppm-fcpxml.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  ctx.PPM.server = { tmpPath: (n) => `/tmp/ppm/${n}` };
  return { PPM: ctx.PPM, fake, opened };
}

test("書き出しは server の tmp に、suppressUI を付けて行う", async () => {
  const { PPM, fake } = setup();
  const p = await PPM.fcpxml.exportActiveSequence("a.xml");
  assert.equal(p, "/tmp/ppm/a.xml");
  assert.equal(fake.exported.suppress, true);
});

test("書き出しが false なら理由つきのエラー", async () => {
  const { PPM } = setup({ exportOk: false });
  await assert.rejects(PPM.fcpxml.exportActiveSequence("a.xml"), (e) => e.ppm && e.ppm.symptom.includes("書き出せません"));
});

test("読み込んで増えたシーケンスを開く", async () => {
  const { PPM, opened } = setup({ before: 1, after: 2 });
  const s = await PPM.fcpxml.importAndOpen("/tmp/ppm/out.xml");
  assert.equal(s.name, "new1");
  assert.equal(opened.length, 1);
});

test("増えなければ、手で読み込む案内を出す", async () => {
  const { PPM } = setup({ before: 1, after: 1 });
  await assert.rejects(PPM.fcpxml.importAndOpen("/tmp/ppm/out.xml"), (e) => e.ppm.next.includes("読み込み"));
});
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_fcpxml.py' -v`
Expected: FAIL（`No module named 'ppm_fcpxml'`）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/fcpxml/server/ppm_fcpxml.py`:

```python
"""Premiere が書き出す FCP7 XML（xmeml）を読み書きする。

実測の決まり（Cut & SRT の失敗から）:
- 同じ素材を何百のクリップが参照しても、<file> の完全な定義（子要素を持つ）は文書に 1 つだけ。残りは <file id="…"/>。
  一部だけを写すとその 1 つを落とし、Premiere は何も言わずに読み込みに失敗する → dangling() で書く前に確かめる
- 完全な定義かどうかは pathurl の有無ではなく「子要素を持つか」で見る（テロップは pathurl を持たない）
- 秒とフレームの換算は、宣言された timebase と ntsc で行う。実際の fps（29.998 など）は使わない
- シーケンスの rate は sequence 直下の <rate> を読む（文書の先頭にある別の rate を掴まない）
- ネストしたシーケンスも同じく、完全な定義は 1 回だけ（tag="sequence" で同じ関数が使える）
"""
from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

TICKS_PER_SECOND = 254016000000


class XmlError(ValueError):
    pass


def load(path) -> ET.ElementTree:
    text = Path(path).read_text(encoding="utf-8")
    if "<!ENTITY" in text:
        raise XmlError("XML に ENTITY の定義があります（安全のため読みません）")
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text, count=1)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise XmlError(f"XML が読めません: {e}") from None
    if root.tag != "xmeml":
        raise XmlError("Premiere の FCP7 XML（xmeml）ではありません。［ファイル］→［書き出し］→［Final Cut Pro XML］で書き出したものを使ってください")
    return ET.ElementTree(root)


def save(tree: ET.ElementTree, path) -> None:
    body = ET.tostring(tree.getroot(), encoding="unicode")
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + "\n")


def is_definition(el: ET.Element) -> bool:
    return len(list(el)) > 0


def definitions(root: ET.Element, tag: str = "file") -> Dict[str, ET.Element]:
    out: Dict[str, ET.Element] = {}
    for el in root.iter(tag):
        fid = el.get("id")
        if fid and is_definition(el) and fid not in out:
            out[fid] = el
    return out


def dangling(root: ET.Element, tag: str = "file") -> List[str]:
    """文書の順で、完全な定義より前に出てくる空の参照の id（Premiere はこれを解決できない）。"""
    seen, bad = set(), []
    for el in root.iter(tag):
        fid = el.get("id")
        if not fid:
            continue
        if is_definition(el):
            seen.add(fid)
        elif fid not in seen and fid not in bad:
            bad.append(fid)
    return bad


def ensure_first_definition(root: ET.Element, tag: str = "file") -> int:
    """完全な定義を、その id が文書の中で最初に出てくる場所へ移す。後ろの重複は空の参照にする。直した数を返す。"""
    elements = list(root.iter(tag))
    defs: Dict[str, ET.Element] = {}
    for el in elements:
        fid = el.get("id")
        if fid and is_definition(el) and fid not in defs:
            defs[fid] = copy.deepcopy(el)
    fixed = 0
    placed = set()
    for el in elements:
        fid = el.get("id")
        if not fid or fid not in defs:
            continue
        if fid not in placed:
            if not is_definition(el):
                for child in list(defs[fid]):
                    el.append(copy.deepcopy(child))
                fixed += 1
            placed.add(fid)
        elif is_definition(el):
            for child in list(el):
                el.remove(child)
            fixed += 1
    return fixed


def rate_of(el: ET.Element) -> Tuple[int, bool]:
    rate = el.find("rate")
    if rate is None:
        raise XmlError(f"<{el.tag}> の直下に <rate> がありません")
    timebase = int((rate.findtext("timebase") or "0").strip())
    ntsc = (rate.findtext("ntsc") or "FALSE").strip().upper() == "TRUE"
    if timebase <= 0:
        raise XmlError("timebase が 0 です")
    return timebase, ntsc


def fps(timebase: int, ntsc: bool) -> Fraction:
    return Fraction(timebase * 1000, 1001) if ntsc else Fraction(timebase)


def frames_to_seconds(frames: int, timebase: int, ntsc: bool) -> float:
    return float(Fraction(int(frames)) / fps(timebase, ntsc))


def seconds_to_frames(seconds: float, timebase: int, ntsc: bool) -> int:
    return int(round(Fraction(str(seconds)) * fps(timebase, ntsc)))


def ticks_per_frame(timebase: int, ntsc: bool) -> int:
    return int(Fraction(TICKS_PER_SECOND) / fps(timebase, ntsc))


def main_sequence(root: ET.Element) -> ET.Element:
    for seq in root.iter("sequence"):
        if is_definition(seq) and seq.find("media") is not None:
            return seq
    raise XmlError("XML にシーケンスがありません")


def tracks(seq: ET.Element, kind: str = "video") -> List[ET.Element]:
    media = seq.find("media")
    part = media.find(kind) if media is not None else None
    return list(part.findall("track")) if part is not None else []


def clipitems(track: ET.Element) -> List[ET.Element]:
    return list(track.findall("clipitem"))


def clip_range(ci: ET.Element) -> Tuple[int, int]:
    return int(ci.findtext("start") or "0"), int(ci.findtext("end") or "0")


def clip_text(ci: ET.Element) -> Optional[str]:
    """テロップ（グラフィック）の本文。<filter><effect><name>本文</name><effectid>GraphicAndType</effectid>。"""
    for eff in ci.iter("effect"):
        if (eff.findtext("effectid") or "").strip() == "GraphicAndType":
            return eff.findtext("name")
    return None


def find_clip(seq: ET.Element, kind: str, track_index: int, start_frame: int) -> Optional[ET.Element]:
    ts = tracks(seq, kind)
    if not 0 <= track_index < len(ts):
        return None
    for ci in clipitems(ts[track_index]):
        if clip_range(ci)[0] == int(start_frame):
            return ci
    return None


def media_path(file_el: ET.Element) -> Optional[str]:
    url = file_el.findtext("pathurl")
    if not url:
        return None
    path = unquote(urlparse(url.strip()).path)
    if re.match(r"^/[A-Za-z]:", path):
        path = path[1:]
    return path
```

`SKILL/parts/fcpxml/server/jobs/read_texts.py`:

```python
"""選んだクリップの位置から、テロップの本文を FCP7 XML で読む（UXP ではテロップの本文を直接読めない）。"""
import ppm_fcpxml as fx
from ppm_jobs import JobError, need

NAME = "read_texts"


def run(params, ctx):
    xml_path = need(params, "xmlPath")
    clips = need(params, "clips", list)
    try:
        seq = fx.main_sequence(fx.load(xml_path).getroot())
    except fx.XmlError as e:
        raise JobError("書き出した XML が読めません", str(e), "パネルからもう一度書き出してください") from None
    timebase, ntsc = fx.rate_of(seq)
    tpf = fx.ticks_per_frame(timebase, ntsc)
    texts = []
    for c in clips:
        frame = round(float(c["startTicks"]) / tpf)
        ci = fx.find_clip(seq, "video", int(c["trackIndex"]), frame)
        texts.append({"trackIndex": c["trackIndex"], "startTicks": c["startTicks"], "text": fx.clip_text(ci) if ci is not None else None})
    return {"texts": texts, "timebase": timebase, "ntsc": ntsc}
```

`SKILL/parts/fcpxml/lib/ppm-fcpxml.js`:

```js
/* ppm-fcpxml — パネル側の FCP7 XML の往復（書き出し → サーバーで加工 → 読み込んで新しいシーケンスを開く）。
 * ProjectConverter は Premiere 26.2 から。UXP にはクリップの分割が無いので、カットは「XML を作り直して読み込む」で行う。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function exportActiveSequence(fileName) {
    const { ppro } = PPM.modules();
    const { sequence } = await PPM.getProjectAndSequence();
    const path = PPM.server.tmpPath(fileName);
    const conv = ppro && ppro.ProjectConverter;
    if (!conv || typeof conv.exportAsFinalCutProXML !== "function") {
      throw PPM.err("FCP XML を書き出せません", "この Premiere には ProjectConverter がありません（26.2 から）", "Premiere を 26.2 以降に更新してください");
    }
    const ok = await PPM.resolve(conv.exportAsFinalCutProXML(sequence, path, true));
    if (!ok) throw PPM.err("FCP XML を書き出せません", "Premiere が書き出しを受け付けませんでした", "シーケンスを開き直してから、もう一度押してください");
    return path;
  }

  async function importAndOpen(path) {
    const { project } = await PPM.getProjectAndSequence();
    const before = (await project.getSequences()) || [];
    const rootItem = await project.getRootItem();
    const ok = await PPM.resolve(project.importFiles([path], true, rootItem, false));
    const after = (await project.getSequences()) || [];
    const fresh = after.filter((s) => before.indexOf(s) < 0 && !before.some((b) => b && s && b.name === s.name && b.guid && b.guid === s.guid));
    if (!ok || after.length <= before.length || !fresh.length) {
      throw PPM.err("XML を読み込めませんでした", "新しいシーケンスが増えませんでした", `Premiere の［ファイル］→［読み込み］で ${path} を手で読み込んでください`);
    }
    const seq = fresh[fresh.length - 1];
    await project.openSequence(seq);
    if (typeof project.setActiveSequence === "function") await PPM.resolve(project.setActiveSequence(seq));
    return seq;
  }

  PPM.fcpxml = { exportActiveSequence, importAndOpen };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/fcpxml/part.json`:

```json
{
  "name": "fcpxml",
  "description": "FCP7 XML の往復（書き出し・定義のぶら下がりの検査・宣言 timebase での換算・テロップの本文の読み取り・読み込み）",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["local-server"],
  "files": {"server/ppm_fcpxml.py": "server/ppm_fcpxml.py", "server/jobs/read_texts.py": "server/jobs/read_texts.py", "lib/ppm-fcpxml.js": "lib/ppm-fcpxml.js"},
  "scripts": ["lib/ppm-fcpxml.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "26.2",
  "pythonDeps": [],
  "knowledge": ["ref-fcp7-xml", "ref-ticktime"],
  "notes": "規則は Cut&SRT で実機確認済み。この部品の形（read_texts と importAndOpen）は Task 36 で確かめる"
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_fcpxml.py' -v && node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（fcpxml 9・JS 全部）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 fcpxml（定義は 1 回・宣言 timebase で換算・テロップの本文の読み取り・読み込み）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 18: 部品 silence-cut（無音カット）

**Files:**
- Create: `SKILL/parts/silence-cut/part.json`
- Create: `SKILL/parts/silence-cut/server/vendor/silence_cut.py`（移植元: Cut & SRT の `server/vendor/premiere_skills/scripts/silence_cut.py`。premiere-skills の正本の上位版で、実機で使われている物）
- Create: `SKILL/parts/silence-cut/server/vendor/NOTICE.md`
- Create: `SKILL/parts/silence-cut/server/jobs/silence_cut.py`
- Test: `tests/test_silence_cut.py`

**Interfaces:**
- Consumes: `tests/xml_fixtures.write_wav / write_xmeml`、`tests/server_helpers`
- Produces（ジョブ `silence_cut`）: params `{"xmlPath": str, "threshold": -48, "minSilence": 0.2, "padding": 2, "tracks": "A1"}` → `{"outputXml": str, "stdout": str}`。終了コード 3（カットする所が無い）・4（音声を解析できない）・5（映像が書き出されていない＝マルチカム）は、それぞれ理由つきの `JobError` にする
- vendored の `silence_cut.py` の使い方は変えない（`python3 silence_cut.py <xml> --output-dir <dir> --threshold … --min-silence … --padding … --tracks …`、出力は `<dir>/<元の名前>_カット済み.xml`）

- [ ] **Step 1: 写して、Windows で壊れる書き方を直す**

```bash
mkdir -p plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/silence-cut/server/vendor plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/silence-cut/server/jobs
cp "<作業場所>/projects/保存用/Premiere プラグイン/premiere-cut-srt-plugin/server/vendor/premiere_skills/scripts/silence_cut.py" plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/silence-cut/server/vendor/silence_cut.py
```

写した直後に、check.py の W003（文字コード）・W004（Mac 専用の場所）・P003（個人のパス）に当たる箇所を探す:

```bash
grep -n "text=True\|universal_newlines\|open(\|/Users\|/Applications\|/opt/homebrew" plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/silence-cut/server/vendor/silence_cut.py
```

見つかった行ごとに、`subprocess` の `text=True` には `encoding="utf-8", errors="replace"` を足し、テキストの `open(` には `encoding="utf-8"` を足す。Mac 専用の場所を探す処理は、`sys.platform` の分岐がある場合だけそのまま残す（分岐が無ければ Windows の場所の候補を足す）。直した行の一覧を `NOTICE.md` に書く:

`SKILL/parts/silence-cut/server/vendor/NOTICE.md`:

```markdown
# silence_cut.py について

- 出どころ: premiere-skills（fuuuuuuma/premiere-skills）の silence_cut.py を、Cut & SRT が実機で使っている上位版から写したもの。ライセンスはこのリポジトリと同じ MIT。
- 無音の判定は 20ms の RMS の包絡で前後を同じ基準で測る（silencedetect の前後の偏りをなくした版）。
- 終了コード: 3 = カットする所が無い（成功扱いにしない）、4 = 基準の音声を解析できない、5 = 書き出した XML に映像が無い（マルチカム）。
- このキットで変えたこと（Windows で文字化けして止まらないため）:
  - （直した行と内容をここに列挙する。例: 1234 行目 subprocess.run(..., text=True) に encoding="utf-8", errors="replace" を追加）
```

（このファイルの「直した行」の節は、grep の結果を見て実際に直した行で埋める。直す所が無ければ「直した所はありません（grep の結果 0 件）」と書く）

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_silence_cut.py`:

```python
import importlib.util
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir
from xml_fixtures import write_wav, write_xmeml

VENDOR = PARTS / "silence-cut" / "server" / "vendor" / "silence_cut.py"
HAS_DEPS = bool(shutil.which("ffmpeg")) and importlib.util.find_spec("numpy") is not None


def audio_ranges(xml_path):
    root = ET.parse(xml_path).getroot()
    return [(int(c.findtext("start")), int(c.findtext("end"))) for c in root.findall(".//media/audio/track/clipitem")]


@unittest.skipUnless(HAS_DEPS, "ffmpeg と numpy が要る")
class SilenceCutTests(unittest.TestCase):
    def setUp(self):
        d = temp_dir()
        self.wav = write_wav(d / "素材.wav")
        self.xml = write_xmeml(d / "元.xml", self.wav)
        self.out = d / "out"

    def run_vendor(self, *extra):
        return subprocess.run([sys.executable, str(VENDOR), str(self.xml), "--output-dir", str(self.out), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)

    def test_cuts_the_quiet_second(self):
        proc = self.run_vendor()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        produced = list(self.out.glob("*_カット済み.xml"))
        self.assertEqual(len(produced), 1)
        ranges = audio_ranges(produced[0])
        self.assertEqual(len(ranges), 2)
        self.assertLess(ranges[-1][1], 150)

    def test_no_cut_is_exit_code_3(self):
        proc = self.run_vendor("--threshold", "-70")
        self.assertEqual(proc.returncode, 3)

    def test_job_reports_reason_for_no_cut(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "silence-cut" / "server"]))
        try:
            _, start = server.call("/jobs/silence_cut", {"xmlPath": str(self.xml), "threshold": -70})
            job = server.wait_job(start["jobId"], timeout=600)
            self.assertEqual(job["status"], "error")
            self.assertIn("カットする所", job["error"]["message"])
            _, start = server.call("/jobs/silence_cut", {"xmlPath": str(self.xml)})
            job = server.wait_job(start["jobId"], timeout=600)
            self.assertEqual(job["status"], "done", job)
            self.assertTrue(job["result"]["outputXml"].endswith("_カット済み.xml"))
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_silence_cut.py' -v`
Expected: FAIL（`test_job_reports_reason_for_no_cut` がジョブ `silence_cut` を見つけられず 404。ffmpeg か numpy が無い環境では skip になるので、この Mac で必ず実行して FAIL を確かめる）

- [ ] **Step 4: ジョブと part.json を書く**

`SKILL/parts/silence-cut/server/jobs/silence_cut.py`:

```python
"""無音カット。書き出した FCP7 XML を、無音を詰めた新しい XML にする（元のシーケンスは触らない）。"""
import subprocess
import sys
from pathlib import Path

from ppm_jobs import JobError, need

NAME = "silence_cut"
VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "silence_cut.py"
REASONS = {
    3: ("カットする所が見つかりませんでした", "無音とみなす音量（閾値）が厳しすぎるか、間が短すぎます", "閾値を -45 くらいに上げるか、最小の無音の長さを短くしてもう一度試してください"),
    4: ("音声を解析できませんでした", "基準のトラックに音声が無いか、素材がオフラインです", "基準のトラック（A1 など）と、素材のリンクを確かめてください"),
    5: ("書き出した XML に映像がありません", "マルチカメラのシーケンスは FCP XML に映像が書き出されません", "マルチカメラを平らにしたシーケンスで試すか、ネストを使ってください"),
}


def run(params, ctx):
    xml_path = need(params, "xmlPath")
    out_dir = Path(ctx.tmp_dir) / "cut"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(VENDOR), xml_path, "--output-dir", str(out_dir),
           "--threshold", str(params.get("threshold", -48)), "--min-silence", str(params.get("minSilence", 0.2)),
           "--padding", str(params.get("padding", 2)), "--tracks", str(params.get("tracks", "A1"))]
    ctx.progress(10, "無音を探しています")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    if proc.returncode in REASONS:
        raise JobError(*REASONS[proc.returncode])
    if proc.returncode != 0:
        raise JobError("無音カットが失敗しました", (proc.stderr or proc.stdout)[-600:], "表示された内容を AI に伝えてください")
    produced = sorted(out_dir.glob(f"{Path(xml_path).stem}_カット済み*.xml"), key=lambda p: p.stat().st_mtime)
    if not produced:
        raise JobError("カットした XML が見つかりません", f"{out_dir} に出力がありません", "表示された内容を AI に伝えてください")
    ctx.progress(100, "できました")
    return {"outputXml": str(produced[-1]), "stdout": proc.stdout[-2000:]}
```

`SKILL/parts/silence-cut/part.json`:

```json
{
  "name": "silence-cut",
  "description": "無音カット（RMS の包絡で前後を同じ基準で測り、FCP7 XML を作り直す）。終了コードの約束つき",
  "status": "verified",
  "os": ["mac", "windows"],
  "requires": ["fcpxml", "media-tools"],
  "files": {"server/vendor/": "server/vendor/", "server/jobs/silence_cut.py": "server/jobs/silence_cut.py"},
  "scripts": [],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "26.2",
  "pythonDeps": ["numpy"],
  "knowledge": ["recipe-silence-cut", "feat-cutsrt-cut"],
  "notes": "パネルは PPM.fcpxml.exportActiveSequence → PPM.server.runJob(\"silence_cut\", {xmlPath}) → PPM.fcpxml.importAndOpen(outputXml)。BGM のトラックは tracks に入れない"
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_silence_cut.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_templates.py' -v`
Expected: PASS（silence-cut 3。この Mac では skip にならないこと）

部品を足した作業フォルダが検査で誤り 0 件であることも確かめる:

```bash
python3 - <<'EOF'
import sys, tempfile, pathlib
sys.path.insert(0, "plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts")
import new_plugin, add_part
from lib import checks
d = pathlib.Path(tempfile.mkdtemp()) / "cut test"
new_plugin.create_project("panel-server", d, "Cut Test")
add_part.add_part(d, "silence-cut")
errors = [f for f in checks.run_all(d, pathlib.Path("plugins/premiere-plugin-maker/skills/premiere-plugin-maker")) if f.severity == "error"]
print(errors or "誤り 0 件")
EOF
```

Expected: `誤り 0 件`（W003 などが出たら Step 1 に戻って vendored のファイルを直し、NOTICE.md に足す）

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 silence-cut（実機で使われている silence_cut.py を写し、Windows の文字コードを直したもの）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 19: 部品 transcribe-srt（文字起こしと SRT）

**Files:**
- Create: `SKILL/parts/transcribe-srt/part.json`、`SKILL/parts/transcribe-srt/server/ppm_transcribe.py`、`SKILL/parts/transcribe-srt/server/jobs/transcribe.py`
- Test: `tests/test_transcribe.py`

**Interfaces:**
- Produces（`ppm_transcribe`）:
  - `choose_engine(platform=sys.platform, machine=platform.machine(), has=importlib.util.find_spec) -> "mlx" | "faster" | None`（Apple シリコンの Mac で mlx_whisper があれば mlx、それ以外で faster_whisper があれば faster）
  - `install_hint(platform, machine) -> str`（入れる物とコマンド。入れる前に許可を取ること、モデルは初回に約 1.5GB をダウンロードすることを含む）
  - `srt_time(seconds: float) -> str`（`00:01:02,345`）
  - `split_lines(text: str, max_chars: int = 18) -> list[str]`（句読点・空白で切り、無ければ max_chars で切る。最大 2 行）
  - `to_srt(segments: list[{"start", "end", "text"}], max_chars=18) -> str`
  - `shift_segments(segments, keep_ranges: list[(src_start, src_end, timeline_start)]) -> list`（カット後のタイムラインに合わせる。残した区間に入る部分だけを、タイムラインの時刻へずらす）
  - `transcribe(path, language="ja", model=None) -> list[{"start", "end", "text"}]`
- Produces（ジョブ `transcribe`）: params `{"mediaPath": str, "language": "ja", "start": 秒（任意）, "duration": 秒（任意）, "maxChars": 18}` → `{"srtPath": str, "segments": int, "engine": str}`。エンジンが無ければ `install_hint` を next に入れた JobError
- 改行の決まり: ここでは機械的な改行だけにする。意味で区切る改行（LLM）は premiere-skills の /srt の作り方を `knowledge/features/feat-premiere-skills.md` に記録し、要望があればそれを元に足す

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_transcribe.py`:

```python
import sys
import unittest

from helpers import PARTS

sys.path.insert(0, str(PARTS / "transcribe-srt" / "server"))
import ppm_transcribe as tr  # noqa: E402


class TranscribeTests(unittest.TestCase):
    def test_engine_choice(self):
        has = lambda names: (lambda mod: object() if mod in names else None)
        self.assertEqual(tr.choose_engine("darwin", "arm64", has({"mlx_whisper", "faster_whisper"})), "mlx")
        self.assertEqual(tr.choose_engine("darwin", "x86_64", has({"mlx_whisper", "faster_whisper"})), "faster")
        self.assertEqual(tr.choose_engine("win32", "AMD64", has({"faster_whisper"})), "faster")
        self.assertIsNone(tr.choose_engine("win32", "AMD64", has(set())))

    def test_install_hint_mentions_consent_and_size(self):
        hint = tr.install_hint("win32", "AMD64")
        self.assertIn("faster-whisper", hint)
        self.assertIn("許可", hint)
        self.assertIn("GB", hint)
        self.assertIn("mlx-whisper", tr.install_hint("darwin", "arm64"))

    def test_srt_time(self):
        self.assertEqual(tr.srt_time(62.3456), "00:01:02,346")
        self.assertEqual(tr.srt_time(3600), "01:00:00,000")

    def test_split_lines(self):
        self.assertEqual(tr.split_lines("短い"), ["短い"])
        self.assertEqual(tr.split_lines("これは長い文です、ここで区切ると読みやすくなります", 14), ["これは長い文です、", "ここで区切ると読みやすくなります"])
        self.assertEqual(len(tr.split_lines("あ" * 50, 18)), 2)

    def test_to_srt(self):
        srt = tr.to_srt([{"start": 0, "end": 1.5, "text": "こんにちは"}, {"start": 1.5, "end": 3, "text": "  "}, {"start": 3, "end": 4, "text": "またね"}])
        self.assertEqual(srt, "1\n00:00:00,000 --> 00:00:01,500\nこんにちは\n\n2\n00:00:03,000 --> 00:00:04,000\nまたね\n")

    def test_shift_segments_follows_the_cut(self):
        segs = [{"start": 0.5, "end": 1.5, "text": "a"}, {"start": 2.2, "end": 2.8, "text": "消えた所"}, {"start": 3.5, "end": 4.5, "text": "b"}]
        keep = [(0.0, 2.0, 0.0), (3.0, 5.0, 2.0)]
        self.assertEqual(tr.shift_segments(segs, keep), [{"start": 0.5, "end": 1.5, "text": "a"}, {"start": 2.5, "end": 3.5, "text": "b"}])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_transcribe.py' -v`
Expected: FAIL（`No module named 'ppm_transcribe'`）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/transcribe-srt/server/ppm_transcribe.py`:

```python
"""文字起こしと SRT。Mac（Apple シリコン）は mlx-whisper、それ以外は faster-whisper。

- エンジンとモデルは自動では入れない。足りなければ install_hint() の内容を見せて、許可を取ってから入れる
- モデルは初回に約 1.5GB をダウンロードする（以降は手元に残る）
- Windows の NVIDIA の GPU は、CUDA の部品が無いと失敗するので CPU に切り替えて続ける
- 改行はここでは機械的に行う。意味で区切る改行は premiere-skills の /srt の作り方（知識 feat-premiere-skills）を使う
"""
from __future__ import annotations

import importlib.util
import platform as _platform
import re
import sys
from typing import Callable, List, Optional, Tuple

DEFAULT_MODEL = {"mlx": "mlx-community/whisper-large-v3-turbo", "faster": "large-v3-turbo"}
_BREAK_AFTER = "、。，．！？!?…）」』"


def choose_engine(platform: str = sys.platform, machine: Optional[str] = None, has: Callable = importlib.util.find_spec) -> Optional[str]:
    machine = machine if machine is not None else _platform.machine()
    if platform == "darwin" and machine == "arm64" and has("mlx_whisper"):
        return "mlx"
    if has("faster_whisper"):
        return "faster"
    return None


def install_hint(platform: str = sys.platform, machine: Optional[str] = None) -> str:
    machine = machine if machine is not None else _platform.machine()
    if platform == "darwin" and machine == "arm64":
        cmd = "python3 -m pip install mlx-whisper"
    elif platform == "win32":
        cmd = "py -3 -m pip install faster-whisper"
    else:
        cmd = "python3 -m pip install faster-whisper"
    return (f"文字起こしの部品が入っていません。入れるには: {cmd}（サーバーの install.py --with-deps でも入ります）。"
            "初回はモデル（約 1.5GB）をダウンロードします。入れる前に、利用者の許可を取ってください")


def srt_time(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_lines(text: str, max_chars: int = 18) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text] if text else []
    best = -1
    for i, ch in enumerate(text[: max_chars + 1]):
        if ch in _BREAK_AFTER or ch == " ":
            best = i
    cut = best + 1 if best >= 0 else max_chars
    first, rest = text[:cut].strip(), text[cut:].strip()
    return [first, rest] if rest else [first]


def to_srt(segments: List[dict], max_chars: int = 18) -> str:
    blocks = []
    n = 0
    for seg in segments:
        lines = split_lines(str(seg.get("text", "")), max_chars)
        if not lines:
            continue
        n += 1
        blocks.append(f"{n}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n" + "\n".join(lines) + "\n")
    return "\n".join(blocks)


def shift_segments(segments: List[dict], keep_ranges: List[Tuple[float, float, float]]) -> List[dict]:
    """カットで残した区間 (素材の始まり, 素材の終わり, タイムラインの始まり) に合わせて、字幕をタイムラインの時刻にずらす。"""
    out = []
    for seg in segments:
        for src_start, src_end, tl_start in keep_ranges:
            s, e = max(seg["start"], src_start), min(seg["end"], src_end)
            if e - s > 0.05:
                out.append({"start": round(tl_start + (s - src_start), 3), "end": round(tl_start + (e - src_start), 3), "text": seg["text"]})
    return out


def transcribe(path: str, language: str = "ja", model: Optional[str] = None) -> List[dict]:
    engine = choose_engine()
    if engine is None:
        raise RuntimeError(install_hint())
    if engine == "mlx":
        import mlx_whisper  # type: ignore
        result = mlx_whisper.transcribe(str(path), path_or_hf_repo=model or DEFAULT_MODEL["mlx"], language=language)
        return [{"start": float(s["start"]), "end": float(s["end"]), "text": s["text"].strip()} for s in result.get("segments", [])]
    from faster_whisper import WhisperModel  # type: ignore
    try:
        wm = WhisperModel(model or DEFAULT_MODEL["faster"], device="auto")
        segments, _ = wm.transcribe(str(path), language=language, vad_filter=True)
        return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    except Exception as e:  # noqa: BLE001  CUDA の部品が無いなど
        if "cublas" not in str(e).lower() and "cuda" not in str(e).lower():
            raise
        wm = WhisperModel(model or DEFAULT_MODEL["faster"], device="cpu", compute_type="int8")
        segments, _ = wm.transcribe(str(path), language=language, vad_filter=True)
        return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
```

`SKILL/parts/transcribe-srt/server/jobs/transcribe.py`:

```python
"""素材を文字起こしして SRT を作る。範囲（start・duration）を渡すと、その部分だけを起こす。"""
import tempfile
from pathlib import Path

import ppm_media
import ppm_transcribe as tr
from ppm_jobs import JobError, need

NAME = "transcribe"


def run(params, ctx):
    media = need(params, "mediaPath")
    if tr.choose_engine() is None:
        raise JobError("文字起こしの部品がありません", "mlx-whisper / faster-whisper のどちらも入っていません", tr.install_hint())
    ctx.progress(5, "音声を取り出しています")
    start, duration = params.get("start"), params.get("duration")
    wav = Path(tempfile.mkdtemp(dir=ctx.tmp_dir)) / "audio.wav"
    try:
        pcm = ppm_media.extract_pcm16(media, rate=16000, start=start, duration=duration)
    except ppm_media.MediaError as e:
        raise JobError("音声を取り出せませんでした", str(e), "素材のリンク切れと、ffmpeg が入っているかを確かめてください") from None
    import wave
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)
    ctx.progress(20, "文字起こしをしています（長い素材は数分かかります）")
    segments = tr.transcribe(str(wav), language=params.get("language", "ja"))
    if start:
        segments = [{**s, "start": s["start"] + float(start), "end": s["end"] + float(start)} for s in segments]
    out = Path(ctx.tmp_dir) / (Path(media).stem + ".srt")
    out.write_text(tr.to_srt(segments, int(params.get("maxChars", 18))), encoding="utf-8")
    return {"srtPath": str(out), "segments": len(segments), "engine": tr.choose_engine()}
```

`SKILL/parts/transcribe-srt/part.json`:

```json
{
  "name": "transcribe-srt",
  "description": "文字起こし（Mac は mlx-whisper、Windows は faster-whisper）と SRT、カット後のタイムラインへの合わせ込み",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["media-tools"],
  "files": {"server/ppm_transcribe.py": "server/ppm_transcribe.py", "server/jobs/transcribe.py": "server/jobs/transcribe.py"},
  "scripts": [],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": ["mlx-whisper; sys_platform == \"darwin\" and platform_machine == \"arm64\"", "faster-whisper; sys_platform != \"darwin\" or platform_machine != \"arm64\""],
  "knowledge": ["recipe-captions-srt", "feat-premiere-skills"],
  "notes": "モデルは初回に約 1.5GB をダウンロードする。入れる前に許可を取る。SRT はプロジェクトに読み込めるが、シーケンスへの配置は手作業か別の処理"
}
```

`missing_deps()`（Task 15 の install.py）は依存の行の `;` より前だけを見るので、環境の条件つきの行も読める。ただし条件に合わない OS の依存まで「足りない」と出るので、install.py の `missing_deps()` に環境の条件の判定を足す（Task 15 のファイルを直す）:

```python
def _applies(dep: str) -> bool:
    if ";" not in dep:
        return True
    marker = dep.split(";", 1)[1].strip()
    import platform as _p
    env = {"sys_platform": sys.platform, "platform_machine": _p.machine()}
    expr = marker
    for key, value in env.items():
        expr = expr.replace(key, repr(value))
    try:
        return bool(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307  requirements の環境の条件（自分のファイルだけ）
    except Exception:  # noqa: BLE001
        return True
```

`missing_deps()` の `for dep in requirements():` の直後に `if not _applies(dep): continue` を足す。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_transcribe.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_local_server.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（transcribe 6）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 transcribe-srt（エンジンの自動の選び分け・SRT・カット後への合わせ込み）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 20: 部品 mogrt-text（テロップの MOGRT 生成）

**Files:**
- Create: `SKILL/parts/mogrt-text/part.json`
- Create: `SKILL/parts/mogrt-text/server/mogrt/`（移植元: Effect & Design の `engine/` の `__init__.py` `build_mogrt.py` `style_tree.py` `textstyle_fb.py` `fonts.py` `cli.py`）
- Create: `SKILL/parts/mogrt-text/server/mogrt/styles/white-black.json`、`yellow-red-white.json`、`news-band.json`
- Create: `SKILL/parts/mogrt-text/server/jobs/build_mogrt.py`、`SKILL/parts/mogrt-text/server/jobs/list_fonts.py`
- Create: `SKILL/parts/mogrt-text/lib/ppm-mogrt.js`
- Test: `tests/test_mogrt_text.py`、`tests/js/mogrt_panel.test.js`

**Interfaces:**
- Produces（`mogrt.build_mogrt`）: `build(style: dict, text: str, out_path: str, name=None, duration=None, position=None, donor_path=None) -> {"mogrtPath", "name", "font", "durationSeconds", "donor"}`、`verify(path) -> {"ok", "errors"}`、`find_donor() -> str`（Mac は `/Applications/Adobe Premiere*/…/Contents/Essential Graphics/Basic Title.mogrt`、Windows は `%ProgramFiles%\Adobe\Adobe Premiere*\Essential Graphics\Basic Title.mogrt`、環境変数 `PPM_MOGRT_DONOR` で差し替え可。ベータでない新しい版を先に選ぶ）、`class BuildError(ValueError)`
- デザインの定義（style.json）の形（Effect & Design のテストと同じ）: `{"id", "name", "font"（PostScript 名）, "size", "tracking", "fill": "#RRGGBB", "strokes": [{"color", "width"}]（内側から順）, "shadow": {"color", "opacity", "angle", "distance", "size", "blur"} | null, "extra_shadows": [], "background": null, "position": {"x": 0.5, "y": 0.86}}`
- Produces（ジョブ `build_mogrt`）: params `{"style": dict か "styleName": "white-black", "items": [{"text", "duration", "name"}]}` → `{"mogrts": [{"text", "path", "durationSeconds"}], "warnings": [str]}`（書体が見つからないときは warnings に入れ、作るのは止めない）
- Produces（ジョブ `list_fonts`）: params `{}` → `{"fonts": [PostScript 名]}`
- Produces（`PPM.mogrt`、パネル側）: `insertAt(project, sequence, path, startSeconds, videoTrackIndex, audioTrackIndex) -> Promise<item | null>`（`SequenceEditor.insertMogrtFromPath` は Action を返さず取引に入れられない。取り消しは別の 1 回になる）、`replaceClip(project, sequence, clip: Clip, mogrtPath) -> Promise<{undoSteps}>`（元のクリップを外してから同じ位置に入れ、尺を合わせる。上書きに頼らない）
- Adobe の `Basic Title.mogrt` は**同梱しない**（利用者の Premiere の中にある物をドナーに使う）。テストは本物のドナーがあるときだけ走らせる

- [ ] **Step 1: 写して、Mac 専用の探し方と危ない経路を直す**

```bash
SRC="<作業場所>/projects/保存用/Premiere プラグイン/effect-design-extension/engine"
DST=plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/mogrt-text/server/mogrt
mkdir -p "$DST/styles" plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/mogrt-text/server/jobs plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/mogrt-text/lib
for f in __init__.py build_mogrt.py style_tree.py textstyle_fb.py fonts.py cli.py; do cp "$SRC/$f" "$DST/$f"; done
```

`build_mogrt.py` を次のとおり直す:

1. `DONOR_GLOB` と `find_donor()` を、OS ごとに探す形に置き換える:

```python
def _donor_candidates() -> list:
    env = os.environ.get("PPM_MOGRT_DONOR")
    if env:
        return [env] if os.path.exists(env) else []
    if sys.platform == "darwin":
        hits = glob.glob("/Applications/Adobe Premiere*/Adobe Premiere*.app/Contents/Essential Graphics/Basic Title.mogrt")
    elif sys.platform == "win32":
        base = os.environ.get("ProgramFiles", r"C:\Program Files")
        hits = glob.glob(os.path.join(base, "Adobe", "Adobe Premiere*", "Essential Graphics", "Basic Title.mogrt"))
    else:
        hits = []
    # ベータでない版を先に、その中で新しい版を先に
    return sorted(hits, key=lambda p: ("Beta" in p, p), reverse=False)[::-1] if hits else []


def find_donor() -> str:
    hits = [p for p in _donor_candidates() if "Beta" not in p] or _donor_candidates()
    if not hits:
        raise BuildError("Premiere の中の Basic Title.mogrt が見つかりません（Premiere が入っているか、PPM_MOGRT_DONOR でパスを渡してください）")
    return sorted(hits)[-1]
```

2. `"transplant"` の経路（`_apply_transplant_variant` と `STYLE_BLOCK` と、`build()` の `variant` 引数）を消し、常に blob 版にする。理由を先頭の説明に 1 行で残す（「2026 形式の部品へ丸ごと差し替える版は importMGT が Premiere ごと固まったので消した」）。`build()` の戻り値から `variant` を外す。
3. `from . import cli` と `main()` は残す（`python3 -m mogrt.build_mogrt --style … --text … --out …` で手でも作れる）。
4. 先頭の説明の「Cut&SRT」「Effect & Design」の名前は出どころとして残してよいが、個人のパスが無いことを `grep -n "/Users/" "$DST"/*.py` で確かめる（0 件）。

`fonts.py` に Mac 専用の場所（`~/Library/...`）だけを探す処理があれば、Windows の場所（`%APPDATA%\Adobe\CoreSync\plugins\livetype`、`%WINDIR%\Fonts`、`%LOCALAPPDATA%\Microsoft\Windows\Fonts`）を足す。

デザインの見本（3 つ。どれも自分で作った定義で、他人のテンプレートではない）:

`$DST/styles/white-black.json`:

```json
{"id": "white-black", "name": "白文字 黒縁", "font": "HiraginoSans-W7", "size": 110, "tracking": -10,
 "fill": "#FFFFFF", "strokes": [{"color": "#111111", "width": 18}],
 "shadow": {"color": "#000000", "opacity": 60, "angle": 135, "distance": 6, "size": 0, "blur": 10},
 "extra_shadows": [], "background": null, "position": {"x": 0.5, "y": 0.86}}
```

`$DST/styles/yellow-red-white.json`:

```json
{"id": "yellow-red-white", "name": "黄文字 赤白二重縁", "font": "HiraginoSans-W8", "size": 128, "tracking": -12,
 "fill": "#FFE24A", "strokes": [{"color": "#A3161B", "width": 14}, {"color": "#FFFFFF", "width": 26}],
 "shadow": {"color": "#000000", "opacity": 70, "angle": 135, "distance": 8, "size": 0, "blur": 14},
 "extra_shadows": [], "background": null, "position": {"x": 0.5, "y": 0.86}}
```

`$DST/styles/news-band.json`:

```json
{"id": "news-band", "name": "ニュース風の帯", "font": "HiraginoSans-W6", "size": 84, "tracking": 0,
 "fill": "#FFFFFF", "strokes": [],
 "shadow": null, "extra_shadows": [],
 "background": {"color": "#1F3A93", "opacity": 90, "size": 18}, "position": {"x": 0.5, "y": 0.88}}
```

（Windows には Hiragino が無い。ジョブは書体が無ければ warnings に入れ、`list_fonts` の結果から入っている書体に差し替えるよう AI に任せる）

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_mogrt_text.py`:

```python
import json
import sys
import unittest
import zipfile

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir

sys.path.insert(0, str(PARTS / "mogrt-text" / "server"))
from mogrt import build_mogrt, textstyle_fb  # noqa: E402

STYLES = PARTS / "mogrt-text" / "server" / "mogrt" / "styles"
try:
    DONOR = build_mogrt.find_donor()
except build_mogrt.BuildError:
    DONOR = ""


class StyleTests(unittest.TestCase):
    def test_sample_styles_have_the_documented_keys(self):
        for path in STYLES.glob("*.json"):
            style = json.loads(path.read_text(encoding="utf-8"))
            for key in ("id", "name", "font", "size", "fill", "strokes", "position"):
                self.assertIn(key, style, f"{path.name} に {key} がありません")

    def test_transplant_route_is_gone(self):
        src = (PARTS / "mogrt-text" / "server" / "mogrt" / "build_mogrt.py").read_text(encoding="utf-8")
        self.assertNotIn("_apply_transplant_variant", src)

    def test_donor_override_by_env(self):
        import os
        fake = temp_dir() / "Basic Title.mogrt"
        fake.write_bytes(b"x")
        old = os.environ.get("PPM_MOGRT_DONOR")
        os.environ["PPM_MOGRT_DONOR"] = str(fake)
        try:
            self.assertEqual(build_mogrt.find_donor(), str(fake))
        finally:
            if old is None:
                del os.environ["PPM_MOGRT_DONOR"]
            else:
                os.environ["PPM_MOGRT_DONOR"] = old


@unittest.skipUnless(DONOR, "Premiere の中の Basic Title.mogrt が無い")
class BuildTests(unittest.TestCase):
    def test_build_and_verify(self):
        style = json.loads((STYLES / "yellow-red-white.json").read_text(encoding="utf-8"))
        out = temp_dir() / "テロップ.mogrt"
        info = build_mogrt.build(style, "まさかの大逆転！", str(out), duration=3.0)
        self.assertTrue(build_mogrt.verify(str(out))["ok"])
        self.assertAlmostEqual(info["durationSeconds"], 3.0, places=3)
        with zipfile.ZipFile(out) as z:
            self.assertIn("definition.json", z.namelist())

    def test_job_builds_one_per_item(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "mogrt-text" / "server"]))
        try:
            _, start = server.call("/jobs/build_mogrt", {"styleName": "white-black", "items": [{"text": "一つ目", "duration": 2}, {"text": "二つ目", "duration": 1.5}]})
            job = server.wait_job(start["jobId"], timeout=120)
            self.assertEqual(job["status"], "done", job)
            self.assertEqual([m["text"] for m in job["result"]["mogrts"]], ["一つ目", "二つ目"])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
```

`tests/js/mogrt_panel.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake, TPS } = require("./fake_ppro");

function setup({ insertResult = [{ inserted: true }] } = {}) {
  const fake = makeFake();
  const calls = [];
  fake.ppro.SequenceEditor = {
    async getEditor() {
      return {
        insertMogrtFromPath(path, time, v, a) { calls.push({ path, seconds: time.seconds, v, a }); return insertResult; },
        createRemoveItemsAction(sel, ripple, type, shift) { if (arguments.length < 4) throw new Error("Not Enough Parameters"); return { __action: "remove", args: [sel, ripple, type, shift] }; },
      };
    },
  };
  fake.ppro.Constants.MediaType = { VIDEO: "video" };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "mogrt-text/lib/ppm-mogrt.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  return { PPM: ctx.PPM, fake, calls };
}

test("insertAt は取引の外で insertMogrtFromPath を呼ぶ", async () => {
  const { PPM, calls, fake } = setup();
  const { project, sequence } = await PPM.getProjectAndSequence();
  await PPM.mogrt.insertAt(project, sequence, "/tmp/a.mogrt", 2, 1, 0);
  assert.deepEqual(calls, [{ path: "/tmp/a.mogrt", seconds: 2, v: 1, a: 0 }]);
  assert.equal(fake.log.locked, 0);
});

test("空の結果は失敗として扱う", async () => {
  const { PPM } = setup({ insertResult: [] });
  const { project, sequence } = await PPM.getProjectAndSequence();
  await assert.rejects(PPM.mogrt.insertAt(project, sequence, "/tmp/a.mogrt", 0, 1, 0), (e) => e.ppm && e.ppm.symptom.includes("入れられません"));
});
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_mogrt_text.py' -v`
Expected: FAIL（`test_transplant_route_is_gone` か `No module named 'mogrt'`。Step 1 の直しが済んでいればジョブのテストが 404 で落ちる）

- [ ] **Step 4: ジョブ・パネル側・part.json を書く**

`SKILL/parts/mogrt-text/server/jobs/build_mogrt.py`:

```python
"""テロップの MOGRT を 1 本ずつ作る（Premiere の中の Basic Title.mogrt をドナーにして、文字のデザインを差し替える）。"""
import json
from pathlib import Path

from mogrt import build_mogrt, fonts
from ppm_jobs import JobError

NAME = "build_mogrt"
STYLES = Path(__file__).resolve().parent.parent / "mogrt" / "styles"


def _style(params):
    if isinstance(params.get("style"), dict):
        return params["style"]
    name = params.get("styleName", "white-black")
    path = STYLES / f"{name}.json"
    if not path.exists():
        raise JobError(f"デザイン「{name}」がありません", "", "使えるのは: " + ", ".join(sorted(p.stem for p in STYLES.glob("*.json"))))
    return json.loads(path.read_text(encoding="utf-8"))


def run(params, ctx):
    style = _style(params)
    items = params.get("items") or []
    if not items:
        raise JobError("作るテロップがありません", "items が空です", "選んだクリップの本文を渡してください")
    warnings = []
    try:
        installed = set(fonts.list_fonts()) if hasattr(fonts, "list_fonts") else set()
    except Exception:  # noqa: BLE001  書体の一覧が取れなくても作るのは止めない
        installed = set()
    if installed and style.get("font") not in installed:
        warnings.append(f"書体 {style.get('font')} が見つかりません。Premiere は別の書体で描きます（list_fonts で入っている書体を選べます）")
    out_dir = Path(ctx.tmp_dir) / "mogrt"
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for i, item in enumerate(items):
        if ctx.cancelled():
            return None
        ctx.progress(int(100 * i / len(items)), f"{i + 1}/{len(items)} 本目を作っています")
        path = out_dir / f"ppm_{i:03d}_{abs(hash(item['text'])) % 10**8}.mogrt"
        try:
            info = build_mogrt.build(style, item["text"], str(path), name=item.get("name"), duration=item.get("duration"))
        except build_mogrt.BuildError as e:
            raise JobError("テロップを作れませんでした", str(e), "Premiere が入っているか、デザインの定義を確かめてください") from None
        made.append({"text": item["text"], "path": info["mogrtPath"], "durationSeconds": info["durationSeconds"]})
    return {"mogrts": made, "warnings": warnings}
```

`SKILL/parts/mogrt-text/server/jobs/list_fonts.py`:

```python
"""入っている書体の PostScript 名の一覧（Adobe Fonts を含む）。"""
from mogrt import fonts

NAME = "list_fonts"


def run(params, ctx):
    return {"fonts": sorted(fonts.list_fonts()) if hasattr(fonts, "list_fonts") else []}
```

（写した `fonts.py` に一覧を返す関数が別の名前で入っている場合は、`list_fonts()` という名前で包む関数を `fonts.py` の末尾に足す。中身は既存の探し方をそのまま使う）

`SKILL/parts/mogrt-text/lib/ppm-mogrt.js`:

```js
/* ppm-mogrt — 作った MOGRT をタイムラインに入れる・テロップを差し替える。
 * - insertMogrtFromPath は Action を返さないので取引に入れられない（取り消しは別の 1 回）
 * - 同じトラックに重なると上書きされる／されないの記録が割れている → 上書きに頼らず、先に元を外してから入れる
 * - 削除の createRemoveItemsAction は引数 4 つが必須（26.3）。選択は sequence.getSelection() を使い、new TrackItemSelection は使わない */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function insertAt(project, sequence, path, startSeconds, videoTrackIndex, audioTrackIndex) {
    const { ppro } = PPM.modules();
    const editor = await ppro.SequenceEditor.getEditor(sequence);
    if (!editor || typeof editor.insertMogrtFromPath !== "function") {
      throw PPM.err("MOGRT を入れられません", "この Premiere には insertMogrtFromPath がありません", "Premiere を 25.6 以降に更新してください");
    }
    const r = await PPM.resolve(editor.insertMogrtFromPath(path, PPM.time(startSeconds), videoTrackIndex, audioTrackIndex || 0));
    if (!r || (Array.isArray(r) && r.length === 0)) {
      throw PPM.err("MOGRT を入れられません", "Premiere が何も返しませんでした（トラックのロックやファイルの壊れ）", "トラックのロックを外し、もう一度試してください");
    }
    return Array.isArray(r) ? r[0] : r;
  }

  async function replaceClip(project, sequence, clip, mogrtPath) {
    const { ppro } = PPM.modules();
    const editor = await ppro.SequenceEditor.getEditor(sequence);
    const live = await PPM.findClip(sequence, clip.kind, clip.trackIndex, clip.startTicks);
    if (!live) throw PPM.err("元のテロップが見つかりません", "選んだ後にタイムラインが変わりました", "テロップを選び直してから押してください");
    const sel = await sequence.getSelection();
    const current = (await PPM.resolve(sel.getTrackItems())) || [];
    for (const it of current) if (typeof sel.removeItem === "function") sel.removeItem(it);
    if (typeof sel.addItem === "function") sel.addItem(live);
    const videoType = (ppro.Constants.MediaType && (ppro.Constants.MediaType.VIDEO !== undefined ? ppro.Constants.MediaType.VIDEO : ppro.Constants.MediaType.Video));
    PPM.transact(project, "元のテロップを外す", (add) => {
      add("remove", () => editor.createRemoveItemsAction(sel, false, videoType, false));
    });
    await insertAt(project, sequence, mogrtPath, clip.startSeconds, clip.trackIndex, 0);
    let steps = 2;
    const placed = await PPM.findClip(sequence, "video", clip.trackIndex, clip.startTicks);
    if (placed) {
      const end = await placed.getEndTime();
      if (PPM.ticksOf(end) !== clip.endTicks) {
        PPM.transact(project, "長さを合わせる", (add) => { add("end", () => placed.createSetEndAction(PPM.timeFromTicks(clip.endTicks))); });
        steps += 1;
      }
    }
    return { undoSteps: steps };
  }

  PPM.mogrt = { insertAt, replaceClip };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/mogrt-text/part.json`:

```json
{
  "name": "mogrt-text",
  "description": "テロップの MOGRT を作る（Premiere の中の Basic Title.mogrt をドナーに、文字のデザインを差し替える）と、入れる・差し替える",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["fcpxml"],
  "files": {"server/mogrt/": "server/mogrt/", "server/jobs/build_mogrt.py": "server/jobs/build_mogrt.py", "server/jobs/list_fonts.py": "server/jobs/list_fonts.py", "lib/ppm-mogrt.js": "lib/ppm-mogrt.js"},
  "scripts": ["lib/ppm-mogrt.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "26.2",
  "pythonDeps": [],
  "knowledge": ["ref-mogrt", "ref-prtextstyle", "recipe-telop-restyle"],
  "notes": "Mac の生成は実機で確認済み。Windows はドナーの場所だけ利用者の報告で確認。差し替えの取り消しは 2〜3 回（MOGRT の挿入が取引に入らないため）"
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_mogrt_text.py' -v && node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（この Mac は Premiere があるので BuildTests も走る）

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 mogrt-text（ドナー差し替えの MOGRT 生成・Windows のドナー探し・挿入と差し替え）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 21: 部品 motion-bake（補間の焼き込み）

**Files:**
- Create: `SKILL/parts/motion-bake/part.json`、`SKILL/parts/motion-bake/lib/ppm-motion-bake.js`
- Create: `SKILL/parts/motion-bake/server/presets/`（移植元: KAZARU の `scripts/kazaru_core/prfpset_build.py` と、それが読む `templates/` の中身）
- Create: `tests/fixtures/motion_vectors.json`
- Test: `tests/js/motion_bake.test.js`、`tests/test_presets.py`

**Interfaces:**
- Produces（`PPM.motion`）: `easeBezier(x) -> number`、`fraction(interp, u) -> number`、`bakeTrack(keys: [{t, value, interp: "linear"|"hold"|"bezier"}], frameSeconds) -> [{t, value, interp: "linear"}]`（Premiere が描く曲がり方を、1 コマごとの直線のキーにする。位置などの `[x, y]` は空間の曲線もまねる。キーは最大 1200 本で、それを超えると何コマおきかにする）
- Produces（`presets`）: KAZARU の `prfpset_build` の使い方をそのまま（`.prfpset` の生成）。CLI は写した先の `python3 -m presets.prfpset_build --help` で確かめる
- 実測の式: 0→100 を 1 秒、bezier で t=0.5 は 43.75（左右非対称）。hold は次のキーの直前のコマまで一定

- [ ] **Step 1: 期待値を作る（移植元をそのまま走らせて、値を保存する）**

```bash
node -e '
const m = require("<作業場所>/projects/保存用/Premiere プラグイン/effect-design-extension/client/motion.js");
const cases = {
  scale_bezier: [[{t:0,value:100,interp:"bezier"},{t:1,value:110,interp:"linear"}], 1/30],
  opacity_hold: [[{t:0,value:0,interp:"hold"},{t:0.5,value:100,interp:"linear"}], 1/30],
  linear_two: [[{t:0,value:0,interp:"linear"},{t:1,value:100,interp:"linear"}], 1/30],
  position_path: [[{t:0,value:[0.2,0.5],interp:"bezier"},{t:0.5,value:[0.5,0.4],interp:"linear"},{t:1,value:[0.8,0.5],interp:"linear"}], 1/30]
};
const out = {};
for (const [k,[keys,frame]] of Object.entries(cases)) out[k] = { keys, frame, baked: m.bakeTrack(keys, frame) };
require("fs").writeFileSync("tests/fixtures/motion_vectors.json", JSON.stringify(out, null, 1));
console.log("ok", Object.keys(out).length);
'
```

Expected: `ok 4`（`tests/fixtures/` が無ければ先に `mkdir -p tests/fixtures`）。これは移植元のアルゴリズムで計算した値で、Premiere の実測式（調査 D §5.4）に合わせて作られたもの。

- [ ] **Step 2: 失敗するテストを書く**

`tests/js/motion_bake.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const vectors = require("../fixtures/motion_vectors.json");
const { loadParts, plain } = require("./load_parts");

const ctx = loadParts(["motion-bake/lib/ppm-motion-bake.js"]);
const M = ctx.PPM.motion;

test("Premiere の bezier の実測: 0→100 を 1 秒、t=0.5 で 43.75", () => {
  assert.ok(Math.abs(M.easeBezier(0.5) - 0.4375) < 1e-6);
  assert.equal(M.fraction("hold", 0.7), 0);
  assert.equal(M.fraction("linear", 0.7), 0.7);
});

for (const [name, v] of Object.entries(vectors)) {
  test(`移植元と同じ焼き込み: ${name}`, () => {
    assert.deepEqual(plain(M.bakeTrack(v.keys, v.frame)), v.baked);
  });
}

test("焼いたキーは全部 linear", () => {
  const baked = M.bakeTrack(vectors.scale_bezier.keys, 1 / 30);
  assert.ok(baked.every((k) => k.interp === "linear"));
  assert.ok(baked.length > 20);
});
```

`tests/test_presets.py`:

```python
import subprocess
import sys
import unittest

from helpers import PARTS


class PresetTests(unittest.TestCase):
    def test_prfpset_builder_runs(self):
        server = PARTS / "motion-bake" / "server"
        proc = subprocess.run([sys.executable, "-m", "presets.prfpset_build", "--help"], cwd=str(server),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `node --test tests/js/motion_bake.test.js`
Expected: FAIL（`ENOENT … ppm-motion-bake.js`）

- [ ] **Step 4: 実装を書く**

`SKILL/parts/motion-bake/lib/ppm-motion-bake.js`: 移植元 `effect-design-extension/client/motion.js` の 15 行目の `round` と、99〜182 行目（「---- 焼き込み」の説明のコメントと `var MAX_BAKED = 1200;` から、`bakeTrack` の終わりまで）を、そのまま次の包みの中に写す。中身は 1 文字も変えない（期待値は移植元で作ったので、変えると比較が落ちる）:

```js
/* ppm-motion-bake — Premiere が描く補間の曲がり方を、1 コマごとの直線のキーにする（Effect & Design の client/motion.js から移植）。
 * UXP では、キーを足すのと同じ取引の中で補間を変えられない（無言で効かない）。取引を分けると Cmd+Z が 2 回要るので、
 * 曲がり方を直線のキーに焼いて 1 回の取引で書く。
 * 実測の式（Premiere 26.5）: 区間の形は始まりのキーの補間だけで決まる。bezier の制御点は (0,0)(1/6,0)(5/6,5/6)(1,1)。
 * 位置などの [x, y] は道筋そのものが曲がる（中のキーの接線 = (次 − 前)/6）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  function round(v) { return Math.round(v * 1e6) / 1e6; }

  /* ここに motion.js の 99〜182 行目（「---- 焼き込み」の説明のコメントから、function bakeTrack の閉じかっこまで）を写す */

  PPM.motion = { easeBezier, fraction, bakeTrack };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

写す範囲は、写した後に `node --test tests/js/motion_bake.test.js` が通ることで確かめる（範囲が足りなければ `easeBezier` などが未定義で落ちる）。

KAZARU の `.prfpset` の生成器を写す:

```bash
KZ=~/ClaudeCode/projects/常時運用/kazaru/scripts/kazaru_core
P=plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts/motion-bake/server/presets
mkdir -p "$P"
cp "$KZ/prfpset_build.py" "$P/"
grep -n "^from \.\|^import \|templates" "$P/prfpset_build.py"
```

grep の結果で `prfpset_build.py` が読む同じフォルダのモジュール（`from . import …`）とテンプレート（`templates/…`）を、同じ相対の位置に写す。`$P/__init__.py` を空で作る。KAZARU の LICENSE（MIT）の著作権表示を `$P/NOTICE.md` に写す。

`SKILL/parts/motion-bake/part.json`:

```json
{
  "name": "motion-bake",
  "description": "Premiere の補間（bezier・hold・空間の曲線）を 1 コマごとの直線のキーに焼く。.prfpset（エフェクトプリセット）の生成も",
  "status": "verified",
  "os": ["mac", "windows"],
  "requires": ["ppro-kit"],
  "files": {"lib/ppm-motion-bake.js": "lib/ppm-motion-bake.js", "server/presets/": "server/presets/"},
  "scripts": ["lib/ppm-motion-bake.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["ref-keyframe-interpolation", "ref-prfpset", "recipe-keyframe-motion"],
  "notes": "PPM.motion.bakeTrack(keys, 1 / fps) の結果を PPM.keyframeActions に渡すと、取引 1 回（Cmd+Z 1 回）で同じ見た目になる"
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_presets.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（motion 6・presets 1）

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 motion-bake（Premiere の補間の実測式で 1 コマごとの直線キーに焼く・.prfpset の生成）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 22: 部品 cep-helper と雛形 cep-helper

**Files:**
- Create: `SKILL/parts/cep-helper/part.json`
- Create: `SKILL/parts/cep-helper/cep/CSXS/manifest.xml`、`cep/client/index.html`、`cep/client/main.js`、`cep/host/helper.jsx`、`cep/install_cep.py`
- Create: `SKILL/parts/cep-helper/server/ext/cep_relay.py`
- Create: `SKILL/parts/cep-helper/lib/ppm-cep.js`
- Create: `SKILL/templates/cep-helper/template.json`
- Test: `tests/test_cep_helper.py`、`tests/js/cep_client.test.js`

**Interfaces:**
- 何のための部品か: UXP に無い操作（タイムラインの再生・停止、クリップの分割）を、CEP の拡張から ExtendScript の QE DOM（非公式）で行う。**期限つき**（Adobe の予定では Premiere の CEP は 2028-12 に既定で無効、2029-12 に同梱終了）。Windows では動作未確認と明記する
- Adobe の `CSInterface.js` は**同梱しない**（Adobe の許諾が要る配布物）。CEP の中では `window.__adobe_cep__.evalScript(script, callback)` を直接使う
- サーバーの口（`server/ext/cep_relay.py`）:
  - CEP 側: `POST /cep/hello` `{"features": [...]}`（自分ができる命令を名乗る）、`POST /cep/next` → `{"command": {"id", "name", "args"}}` か `{}`、`POST /cep/result` `{"id", "ok", "result", "error"}`
  - パネル側: `GET /cep/status` → `{"connected": bool, "features": [...], "lastSeenMs"}`、`POST /cep/commands` `{"name", "args", "timeoutMs"}` → `{"ok", "result" | "error"}`（名乗っていない命令は送らずに 409。古いヘルパーが知らない命令を別の動きとして実行した事故があったため）
- Produces（`PPM.cep`）: `status() -> Promise<{connected, features}>`、`call(name, args) -> Promise<result>`（名乗っていない命令なら理由と代わりの手を出す）
- ExtendScript 側の命令（`helper.jsx`）: `ppmFeatures()`（`["play", "stop", "razor"]` を JSON 文字列で返す）、`ppmPlay(seconds, speed)`、`ppmStop()`、`ppmRazor(kind, trackIndex, seconds)`。どれも ES3（JSON が無いので自前で文字列にする）
- Produces（`install_cep.py`）: 既定は試し実行。`--apply` で、ユーザーの CEP の拡張フォルダへ写し、未署名の拡張を許す設定（Mac は `defaults write com.adobe.CSXS.<10〜13> PlayerDebugMode 1`、Windows は `reg add HKCU\Software\Adobe\CSXS.<10〜13> /v PlayerDebugMode /t REG_SZ /d 1 /f`）をする。**この設定はセキュリティの確かめを緩めるので、実行の前に利用者の明示の許可を取る**（SKILL.md に書く）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_cep_helper.py`:

```python
import json
import subprocess
import sys
import threading
import time
import unittest

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir

CEP = PARTS / "cep-helper" / "cep"


class CepFilesTests(unittest.TestCase):
    def test_no_adobe_csinterface_is_bundled(self):
        self.assertEqual(list(CEP.rglob("CSInterface*.js")), [])
        self.assertIn("__adobe_cep__", (CEP / "client" / "main.js").read_text(encoding="utf-8"))

    def test_manifest_declares_auto_start_and_node(self):
        xml = (CEP / "CSXS" / "manifest.xml").read_text(encoding="utf-8")
        self.assertIn("--enable-nodejs", xml)
        self.assertIn('<Host Name="PPRO"', xml)
        self.assertIn("{{APP_NAME}}", xml)

    def test_jsx_does_not_use_json(self):
        jsx = (CEP / "host" / "helper.jsx").read_text(encoding="utf-8")
        self.assertNotIn("JSON.", jsx)
        for fn in ("ppmFeatures", "ppmPlay", "ppmStop", "ppmRazor"):
            self.assertIn(f"function {fn}(", jsx)

    def test_installer_dry_run_does_nothing(self):
        import os
        env_home = temp_dir()
        proc = subprocess.run([sys.executable, str(CEP / "install_cep.py"), "--bundle-id", "com.ppm.test.cep"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                              env={**os.environ, "HOME": str(env_home), "USERPROFILE": str(env_home), "APPDATA": str(env_home / "AppData")})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PlayerDebugMode", proc.stdout)
        self.assertIn("試し実行", proc.stdout)
        self.assertFalse(any(env_home.rglob("manifest.xml")))


class CepRelayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(make_server_dir(extra_dirs=[PARTS / "cep-helper" / "server"]))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_unannounced_command_is_refused(self):
        code, data = self.server.call("/cep/commands", {"name": "razor", "args": {}, "timeoutMs": 500})
        self.assertEqual(code, 409)
        self.assertIn("名乗って", data["error"])

    def test_command_round_trip(self):
        self.server.call("/cep/hello", {"features": ["play", "stop"]})
        status = self.server.call("/cep/status")[1]
        self.assertTrue(status["connected"])
        result = {}

        def helper():
            for _ in range(50):
                _, nxt = self.server.call("/cep/next", {})
                if nxt.get("command"):
                    self.server.call("/cep/result", {"id": nxt["command"]["id"], "ok": True, "result": {"played": nxt["command"]["args"]["seconds"]}})
                    return
                time.sleep(0.05)

        t = threading.Thread(target=helper)
        t.start()
        code, data = self.server.call("/cep/commands", {"name": "play", "args": {"seconds": 3}, "timeoutMs": 5000})
        t.join()
        self.assertEqual(code, 200)
        self.assertEqual(data["result"], {"played": 3})

    def test_timeout_when_helper_is_silent(self):
        self.server.call("/cep/hello", {"features": ["stop"]})
        code, data = self.server.call("/cep/commands", {"name": "stop", "args": {}, "timeoutMs": 300})
        self.assertEqual(code, 504)


if __name__ == "__main__":
    unittest.main()
```

`tests/js/cep_client.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

function setup(status) {
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "cep-helper/lib/ppm-cep.js"]);
  const calls = [];
  ctx.PPM.server = { async call(path, opts) { calls.push({ path, opts }); return path === "/cep/status" ? status : { ok: true, result: { done: true } }; } };
  return { PPM: ctx.PPM, calls };
}

test("名乗っていない命令は送らず、代わりの手を出す", async () => {
  const { PPM, calls } = setup({ connected: true, features: ["play"] });
  await assert.rejects(PPM.cep.call("razor", {}), (e) => e.ppm && e.ppm.next.includes("Premiere を再起動"));
  assert.equal(calls.filter((c) => c.path === "/cep/commands").length, 0);
});

test("つながっていなければ、入れ方を案内する", async () => {
  const { PPM } = setup({ connected: false, features: [] });
  await assert.rejects(PPM.cep.call("play", {}), (e) => e.ppm.symptom.includes("補助"));
});

test("名乗った命令は送る", async () => {
  const { PPM, calls } = setup({ connected: true, features: ["play"] });
  const r = await PPM.cep.call("play", { seconds: 1 });
  assert.equal(r.done, true);
  assert.equal(calls.at(-1).opts.body.name, "play");
});
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_cep_helper.py' -v`
Expected: FAIL（部品のファイルが無い）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/cep-helper/server/ext/cep_relay.py`:

```python
"""CEP の補助（再生・停止・分割）とパネルの間の中継。補助は自分ができる命令を名乗り、名乗った命令だけを受け取る。"""
import threading
import time
import uuid

_lock = threading.Lock()
_state = {"features": [], "last_seen": 0.0, "queue": [], "results": {}}
_events = {}


def _hello(req, ctx):
    with _lock:
        _state["features"] = [str(f) for f in (req["body"].get("features") or [])]
        _state["last_seen"] = time.time()
    return 200, {"ok": True}


def _next(req, ctx):
    with _lock:
        _state["last_seen"] = time.time()
        if _state["queue"]:
            return 200, {"command": _state["queue"].pop(0)}
    return 200, {}


def _result(req, ctx):
    body = req["body"]
    cid = body.get("id")
    with _lock:
        _state["results"][cid] = body
        ev = _events.get(cid)
    if ev:
        ev.set()
    return 200, {"ok": True}


def _status(req, ctx):
    with _lock:
        age = (time.time() - _state["last_seen"]) * 1000 if _state["last_seen"] else None
        return 200, {"connected": age is not None and age < 5000, "features": list(_state["features"]), "lastSeenMs": age}


def _commands(req, ctx):
    body = req["body"]
    name = str(body.get("name") or "")
    with _lock:
        if name not in _state["features"]:
            return 409, {"error": f"補助が「{name}」を名乗っていません", "next": "Premiere を再起動すると、新しい補助が読み込まれます"}
        cid = uuid.uuid4().hex[:12]
        ev = threading.Event()
        _events[cid] = ev
        _state["queue"].append({"id": cid, "name": name, "args": body.get("args") or {}})
    ok = ev.wait(max(0.1, float(body.get("timeoutMs", 10000)) / 1000))
    with _lock:
        _events.pop(cid, None)
        res = _state["results"].pop(cid, None)
        if not ok:
            _state["queue"] = [c for c in _state["queue"] if c["id"] != cid]
    if not ok or res is None:
        return 504, {"error": "補助から返事がありません", "next": "Premiere を開いたままにし、補助が入っているか確かめてください"}
    if not res.get("ok"):
        return 200, {"ok": False, "error": res.get("error") or "補助の処理が失敗しました"}
    return 200, {"ok": True, "result": res.get("result")}


ROUTES = {
    ("POST", "/cep/hello"): _hello,
    ("POST", "/cep/next"): _next,
    ("POST", "/cep/result"): _result,
    ("GET", "/cep/status"): _status,
    ("POST", "/cep/commands"): _commands,
}
```

`SKILL/parts/cep-helper/cep/CSXS/manifest.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
  {{APP_NAME}} の補助（CEP）。UXP に無い「再生・停止・分割」を、ExtendScript の QE DOM で行う。
  画面を持たずに起動時から常駐する .auto と、読み込まれない環境向けの画面つきの .helper の 2 つ。
  Adobe の予定では Premiere の CEP は 2028-12 に既定で無効、2029-12 に同梱終了（期限つきの部品）。
-->
<ExtensionManifest Version="6.0" ExtensionBundleId="{{PLUGIN_ID}}.cep" ExtensionBundleVersion="{{VERSION}}" ExtensionBundleName="{{APP_NAME}} Helper">
  <ExtensionList>
    <Extension Id="{{PLUGIN_ID}}.cep.auto" Version="{{VERSION}}"/>
    <Extension Id="{{PLUGIN_ID}}.cep.helper" Version="{{VERSION}}"/>
  </ExtensionList>
  <ExecutionEnvironment>
    <HostList><Host Name="PPRO" Version="[23.0,99.9]"/></HostList>
    <LocaleList><Locale Code="All"/></LocaleList>
    <RequiredRuntimeList><RequiredRuntime Name="CSXS" Version="11.0"/></RequiredRuntimeList>
  </ExecutionEnvironment>
  <DispatchInfoList>
    <Extension Id="{{PLUGIN_ID}}.cep.auto">
      <DispatchInfo>
        <Resources>
          <MainPath>./client/index.html</MainPath>
          <ScriptPath>./host/helper.jsx</ScriptPath>
          <CEFCommandLine><Parameter>--allow-file-access-from-files</Parameter><Parameter>--enable-nodejs</Parameter></CEFCommandLine>
        </Resources>
        <Lifecycle>
          <AutoVisible>false</AutoVisible>
          <StartOn><Event>com.adobe.csxs.events.ApplicationActivate</Event><Event>applicationActivate</Event></StartOn>
        </Lifecycle>
        <UI><Type>Custom</Type><Geometry><Size><Height>1</Height><Width>1</Width></Size></Geometry><Icons/></UI>
      </DispatchInfo>
    </Extension>
    <Extension Id="{{PLUGIN_ID}}.cep.helper">
      <DispatchInfo>
        <Resources>
          <MainPath>./client/index.html</MainPath>
          <ScriptPath>./host/helper.jsx</ScriptPath>
          <CEFCommandLine><Parameter>--allow-file-access-from-files</Parameter><Parameter>--enable-nodejs</Parameter></CEFCommandLine>
        </Resources>
        <Lifecycle><AutoVisible>true</AutoVisible></Lifecycle>
        <UI><Type>Panel</Type><Menu>{{APP_NAME}} Helper</Menu><Geometry><Size><Height>90</Height><Width>240</Width></Size></Geometry><Icons/></UI>
      </DispatchInfo>
    </Extension>
  </DispatchInfoList>
</ExtensionManifest>
```

`SKILL/parts/cep-helper/cep/client/index.html`:

```html
<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><title>{{APP_NAME}} Helper</title></head>
<body style="background:#1e1e1e;color:#ccc;font-size:11px">
  <div id="status">補助を起動しています…</div>
  <script src="main.js"></script>
</body></html>
```

`SKILL/parts/cep-helper/cep/client/main.js`:

```js
/* {{APP_NAME}} の補助（CEP 側）。手元のサーバーに 0.4 秒ごとに命令を取りに行き、ExtendScript で実行して結果を返す。
 * - Adobe の CSInterface.js は同梱しない。window.__adobe_cep__.evalScript を直接使う
 * - CEP の Node では child_process の非同期の返事が来ないことがある。ここでは fs の同期読みだけを使う
 * - 起動したら、自分ができる命令を名乗る（古い補助に新しい命令を送らないため） */
(function () {
  "use strict";
  var APP = "{{APP_NAME}}";
  var nodeRequire = (window.cep_node && window.cep_node.require) || window.require;
  var fs = nodeRequire("fs");
  var os = nodeRequire("os");
  var statusEl = document.getElementById("status");

  function handshake() {
    var home = os.homedir();
    var file = os.platform() === "win32" ? home + "\\AppData\\Roaming\\" + APP + "\\server.json" : home + "/Library/Application Support/" + APP + "/server.json";
    return JSON.parse(fs.readFileSync(file, "utf8"));
  }

  function post(path, body, done) {
    var h;
    try { h = handshake(); } catch (e) { statusEl.textContent = "サーバーが動いていません"; done(null); return; }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://127.0.0.1:" + h.httpPort + path);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-PPM-Token", h.token);
    xhr.onload = function () { try { done(JSON.parse(xhr.responseText || "{}")); } catch (e) { done(null); } };
    xhr.onerror = function () { done(null); };
    xhr.send(JSON.stringify(body || {}));
  }

  function evalScript(script, done) {
    var answered = false;
    var timer = setTimeout(function () { if (!answered) { answered = true; done(null); } }, 15000);
    window.__adobe_cep__.evalScript(script, function (raw) {
      if (answered) return;
      answered = true;
      clearTimeout(timer);
      try { done(JSON.parse(raw)); } catch (e) { done({ ok: false, error: String(raw) }); }
    });
  }

  function quote(v) { return JSON.stringify(v === undefined ? null : v); }

  function run(command, done) {
    var a = command.args || {};
    var script;
    if (command.name === "play") script = "ppmPlay(" + quote(a.seconds) + "," + quote(a.speed || 1) + ")";
    else if (command.name === "stop") script = "ppmStop()";
    else if (command.name === "razor") script = "ppmRazor(" + quote(a.kind || "video") + "," + quote(a.trackIndex) + "," + quote(a.seconds) + ")";
    else { done({ ok: false, error: "知らない命令: " + command.name }); return; }
    evalScript(script, function (r) { done(r || { ok: false, error: "ExtendScript の返事がありません" }); });
  }

  function loop() {
    post("/cep/next", {}, function (data) {
      if (data && data.command) {
        var cmd = data.command;
        run(cmd, function (r) {
          post("/cep/result", { id: cmd.id, ok: !!(r && r.ok), result: r, error: r && r.error }, function () { setTimeout(loop, 50); });
        });
        return;
      }
      setTimeout(loop, 400);
    });
  }

  evalScript("ppmFeatures()", function (r) {
    var features = (r && r.features) || [];
    post("/cep/hello", { features: features }, function (ok) {
      statusEl.textContent = ok ? "補助は動いています（" + features.join("・") + "）" : "サーバーにつながりません";
      loop();
    });
  });
})();
```

`SKILL/parts/cep-helper/cep/host/helper.jsx`（Cut & SRT の `cep/host/playback.jsx` の再生と分割の候補の試し方を元に書いた、ES3 の ExtendScript）:

```js
/* {{APP_NAME}} の補助（ExtendScript 側）。QE DOM は非公式で、版によって在り処が違うので候補を順に試し、
 * どの呼び方で動いたかを戻り値に入れる。ES3 には JSON が無いので、文字列は自前で作る。 */
var PPM_TICKS = 254016000000;

function ppmEscape(text) {
    return String(text).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/[\r\n]/g, " ");
}

function ppmSerialize(obj) {
    var parts = [];
    for (var key in obj) {
        if (!obj.hasOwnProperty(key)) { continue; }
        var v = obj[key];
        if (v instanceof Array) {
            var items = [];
            for (var i = 0; i < v.length; i++) { items.push('"' + ppmEscape(v[i]) + '"'); }
            parts.push('"' + key + '":[' + items.join(",") + "]");
        } else if (typeof v === "boolean") {
            parts.push('"' + key + '":' + (v ? "true" : "false"));
        } else if (typeof v === "number") {
            parts.push('"' + key + '":' + v);
        } else {
            parts.push('"' + key + '":"' + ppmEscape(v) + '"');
        }
    }
    return "{" + parts.join(",") + "}";
}

function ppmQeSequence() {
    if (typeof app.enableQE === "function") { app.enableQE(); }
    if (typeof qe === "undefined" || !qe || !qe.project) { return null; }
    if (typeof qe.project.getActiveSequence === "function") { return qe.project.getActiveSequence(); }
    return qe.project.activeSequence || null;
}

function ppmFeatures() {
    return ppmSerialize({ ok: true, features: ["play", "stop", "razor"] });
}

function ppmSeek(seconds) {
    var seq = app.project ? app.project.activeSequence : null;
    if (!seq) { return false; }
    seq.setPlayerPosition(String(Math.round(seconds * PPM_TICKS)));
    return true;
}

function ppmPlay(seconds, speed) {
    var r = { ok: false, method: "", error: "" };
    try {
        if (seconds !== null && seconds !== undefined && seconds >= 0) { ppmSeek(seconds); }
        var qs = ppmQeSequence();
        if (qs && qs.player && typeof qs.player.play === "function") { qs.player.play(speed || 1); r.ok = true; r.method = "qe.sequence.player.play"; }
        else { r.error = "QE の再生が見つかりません"; }
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}

function ppmStop() {
    var r = { ok: false, method: "", error: "" };
    try {
        var qs = ppmQeSequence();
        if (qs && qs.player && typeof qs.player.stop === "function") { qs.player.stop(); r.ok = true; r.method = "qe.sequence.player.stop"; }
        else { r.error = "QE の停止が見つかりません"; }
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}

function ppmRazor(kind, trackIndex, seconds) {
    var r = { ok: false, method: "", error: "" };
    try {
        var qs = ppmQeSequence();
        if (!qs) { r.error = "QE のシーケンスがありません"; return ppmSerialize(r); }
        var track = kind === "audio" ? qs.getAudioTrackAt(trackIndex) : qs.getVideoTrackAt(trackIndex);
        if (!track || typeof track.razor !== "function") { r.error = "QE の razor が見つかりません"; return ppmSerialize(r); }
        var seq = app.project.activeSequence;
        var tpf = Number(seq.timebase);
        // フレームの境目ちょうどではなく 1/4 フレーム内側を渡す（境目の丸めで隣のフレームを切らないため）
        var ticks = Math.round(seconds * PPM_TICKS + tpf / 4);
        var time = new Time();
        time.ticks = String(ticks);
        track.razor(time.getFormatted(seq.getSettings().videoFrameRate, app.project.activeSequence.videoDisplayFormat));
        r.ok = true;
        r.method = "qe.track.razor";
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}
```

（分割は Cut & SRT でも実機未確認。Task 36 で「戻せる操作」として 1 か所だけ試し、結果を知識の状態に反映する）

`SKILL/parts/cep-helper/cep/install_cep.py`:

```python
#!/usr/bin/env python3
"""CEP の補助を入れる。既定は試し実行（何もしない）。--apply で実行する。

- ユーザーの CEP の拡張フォルダへ写す（Mac ~/Library/Application Support/Adobe/CEP/extensions、Windows %APPDATA%\\Adobe\\CEP\\extensions）
- 未署名の拡張を許す設定（PlayerDebugMode）を CSXS 10〜13 に入れる。セキュリティの確かめを緩める設定なので、必ず利用者の許可を取ってから --apply する
- 入れた後は Premiere の再起動が要る
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSXS = [10, 11, 12, 13]


def ext_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Adobe" / "CEP" / "extensions"
    return Path(os.environ.get("HOME", str(Path.home()))) / "Library" / "Application Support" / "Adobe" / "CEP" / "extensions"


def debug_commands() -> list:
    if sys.platform == "win32":
        return [["reg", "add", f"HKCU\\Software\\Adobe\\CSXS.{n}", "/v", "PlayerDebugMode", "/t", "REG_SZ", "/d", "1", "/f"] for n in CSXS]
    return [["defaults", "write", f"com.adobe.CSXS.{n}", "PlayerDebugMode", "1"] for n in CSXS]


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="CEP の補助を入れる")
    ap.add_argument("--bundle-id", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    target = ext_dir() / args.bundle_id
    cmds = debug_commands()
    print(f"・写す: {HERE} → {target}")
    for c in cmds:
        print("・未署名の拡張を許す設定: " + " ".join(c))
    if not args.apply:
        print("（試し実行です。何もしていません。PlayerDebugMode はセキュリティの確かめを緩める設定なので、許可を取ってから --apply してください）")
        return 0
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(HERE, target, ignore=shutil.ignore_patterns("install_cep.py", "__pycache__"))
    for c in cmds:
        subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("入れました。Premiere を再起動すると補助が動きます")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/cep-helper/lib/ppm-cep.js`:

```js
/* ppm-cep — パネルから CEP の補助（再生・停止・分割）を呼ぶ。補助が名乗った命令だけを送る。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function status() { return PPM.server.call("/cep/status"); }

  async function call(name, args) {
    const s = await status();
    if (!s.connected) {
      throw PPM.err("補助（CEP）が動いていません", "補助が入っていないか、Premiere を再起動していません",
        "作業フォルダの cep/install_cep.py で補助を入れ、Premiere を再起動してください（Windows では動作未確認）");
    }
    if ((s.features || []).indexOf(name) < 0) {
      throw PPM.err(`補助が「${name}」に対応していません`, "古い補助が動いています（新しい命令を知らない補助に送ると、別の動きをすることがあります）",
        "Premiere を再起動すると新しい補助が読み込まれます。分割なら代わりにマーカーを置いて手で切る方法もあります");
    }
    const r = await PPM.server.call("/cep/commands", { method: "POST", body: { name, args: args || {}, timeoutMs: 15000 } });
    if (!r.ok) throw PPM.err("補助の処理が失敗しました", String(r.error || ""), "Premiere の画面を前に出してから、もう一度試してください");
    return r.result;
  }

  PPM.cep = { status, call };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/cep-helper/part.json`:

```json
{
  "name": "cep-helper",
  "description": "UXP に無い再生・停止・クリップの分割を、CEP の補助（ExtendScript の QE DOM）で行う。期限つき（CEP は 2028-12 に既定で無効の予定）",
  "status": "partial",
  "os": ["mac"],
  "requires": ["local-server"],
  "files": {"cep/": "cep/", "server/ext/cep_relay.py": "server/ext/cep_relay.py", "lib/ppm-cep.js": "lib/ppm-cep.js"},
  "scripts": ["lib/ppm-cep.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["ref-cep-extendscript", "recipe-razor-workarounds"],
  "notes": "再生・停止は Cut&SRT で実機確認済み。分割は未確認。Windows は未確認。入れるときの PlayerDebugMode は利用者の明示の許可を取ってから"
}
```

`SKILL/templates/cep-helper/template.json`:

```json
{
  "name": "cep-helper",
  "description": "パネル＋手元のサーバー＋CEP の補助（再生・停止・分割。上級。UXP で足りないときだけ。期限つき）",
  "extends": "panel-server",
  "parts": ["cep-helper"],
  "minVersion": "25.6"
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_cep_helper.py' -v && node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_templates.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（cep 7・JS 全部・templates 2）。cep/ の JS は check.py のパネルの規則の対象外（Task 7 の `NON_PANEL_DIRS`）。

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 cep-helper（名乗った命令だけを送る中継・CSInterface を同梱しない）と雛形 cep-helper

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 23: 部品 mcp-bridge（AI からプラグインを操作する口）

**Files:**
- Create: `SKILL/parts/mcp-bridge/part.json`
- Create: `SKILL/parts/mcp-bridge/server/ppm_mcp.py`、`server/setup_mcp.py`、`server/ext/panel_queue.py`
- Create: `SKILL/parts/mcp-bridge/lib/ppm-agent-bridge.js`
- Test: `tests/test_mcp_bridge.py`、`tests/js/agent_bridge.test.js`

**Interfaces:**
- 仕組み: AI（Claude Code / Codex）→ MCP（標準入出力の JSON-RPC 2.0）→ `ppm_mcp.py` → 手元のサーバー（`server/ext/panel_queue.py`）→ パネルが 2 秒ごとに命令を取りに来る → Premiere。パネルを閉じていると届かない（504）
- サーバーの口: パネル側 `POST /panel/next` `{"commands": [{"name", "description"}]}` → `{"command": {"id", "name", "args"}}` か `{}`、`POST /panel/result` `{"id", "ok", "result", "error"}`。AI 側 `GET /panel/status` → `{"connected", "commands": [...]}`、`POST /panel/call` `{"name", "args", "timeoutMs"}` → `{"ok", "result" | "error"}`
- MCP の道具（どれも接頭辞なしの名前）: `ppm_health`（サーバーとパネルの状態）、`ppm_panel_commands`（パネルが受け付ける命令の一覧）、`ppm_panel_call`（`{"name", "args"}` で命令を呼ぶ）。プロトコルの版は `2025-06-18` / `2025-03-26` / `2024-11-05` から相手が求めたものを選ぶ
- Produces（`PPM.agent`、パネル側）: `register(name, description, handler)`、`start({intervalMs=2000})`、`stop()`。最初から入っている命令: `probe`（診断）、`get_selection`（選んだクリップ）、`sequence_overview`（トラックとクリップの一覧）、`log_tail`（ログの最後の 50 行）
- Produces（`setup_mcp.py`）: 既定は試し実行。`--apply` で `claude mcp add <名前> --scope user -- <python> <ppm_mcp.py>` と `codex mcp add <名前> -- <python> <ppm_mcp.py>` を、入っている方だけ実行する（先に remove してから add）。設定ファイルを手で書き換えない

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_mcp_bridge.py`:

```python
import json
import os
import subprocess
import sys
import threading
import time
import unittest

from helpers import PARTS
from server_helpers import LiveServer, make_server_dir


class McpBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = make_server_dir(extra_dirs=[PARTS / "mcp-bridge" / "server"])
        cls.server = LiveServer(cls.dir)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def rpc(self, messages):
        env = {**self.server.env}
        proc = subprocess.run([sys.executable, str(self.dir / "ppm_mcp.py")], input="\n".join(json.dumps(m) for m in messages) + "\n",
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
        return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]

    def test_initialize_and_list_tools(self):
        out = self.rpc([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(out[0]["result"]["protocolVersion"], "2025-03-26")
        names = [t["name"] for t in out[1]["result"]["tools"]]
        self.assertEqual(names, ["ppm_health", "ppm_panel_commands", "ppm_panel_call"])
        self.assertEqual(len(out), 2)

    def test_health_says_panel_is_closed(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "ppm_health", "arguments": {}}}])
        text = out[0]["result"]["content"][0]["text"]
        self.assertIn("パネル", text)

    def test_panel_call_round_trip(self):
        def panel():
            for _ in range(100):
                _, nxt = self.server.call("/panel/next", {"commands": [{"name": "get_selection", "description": "選んだクリップ"}]})
                if nxt.get("command"):
                    self.server.call("/panel/result", {"id": nxt["command"]["id"], "ok": True, "result": {"count": 2}})
                    return
                time.sleep(0.05)

        self.server.call("/panel/next", {"commands": [{"name": "get_selection", "description": "選んだクリップ"}]})
        t = threading.Thread(target=panel)
        t.start()
        out = self.rpc([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "ppm_panel_call", "arguments": {"name": "get_selection", "args": {}}}}])
        t.join()
        self.assertIn('"count": 2', out[0]["result"]["content"][0]["text"])

    def test_unknown_method_is_an_error(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 9, "method": "nope"}])
        self.assertEqual(out[0]["error"]["code"], -32601)


class SetupMcpTests(unittest.TestCase):
    def test_dry_run_shows_commands_and_changes_nothing(self):
        d = make_server_dir(extra_dirs=[PARTS / "mcp-bridge" / "server"])
        proc = subprocess.run([sys.executable, str(d / "setup_mcp.py")], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60, env={**os.environ, "PATH": ""})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("試し実行", proc.stdout)


if __name__ == "__main__":
    unittest.main()
```

`tests/js/agent_bridge.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

test("取りに行った命令を実行して結果を返し、命令の一覧を名乗る", async () => {
  const fake = makeFake();
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js", "ui-kit/lib/ppm-ui-kit.js", "mcp-bridge/lib/ppm-agent-bridge.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  const posts = [];
  let served = false;
  ctx.PPM.server = {
    async call(path, opts) {
      posts.push({ path, body: opts && opts.body });
      if (path === "/panel/next" && !served) { served = true; return { command: { id: "c1", name: "get_selection", args: {} } }; }
      return {};
    },
  };
  await ctx.PPM.agent.pollOnce();
  const result = posts.find((p) => p.path === "/panel/result");
  assert.equal(result.body.ok, true);
  assert.equal(result.body.result.count, 2);
  const names = posts[0].body.commands.map((c) => c.name);
  for (const n of ["probe", "get_selection", "sequence_overview", "log_tail"]) assert.ok(names.includes(n), n);
});

test("命令の失敗は ok:false とエラーの文で返す", async () => {
  const fake = makeFake({ noSequence: true });
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js", "ui-kit/lib/ppm-ui-kit.js", "mcp-bridge/lib/ppm-agent-bridge.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  const posts = [];
  ctx.PPM.server = { async call(path, opts) { posts.push({ path, body: opts && opts.body }); return path === "/panel/next" && posts.length === 1 ? { command: { id: "c2", name: "get_selection", args: {} } } : {}; } };
  await ctx.PPM.agent.pollOnce();
  const result = posts.find((p) => p.path === "/panel/result");
  assert.equal(result.body.ok, false);
  assert.match(result.body.error, /シーケンス/);
});
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_mcp_bridge.py' -v`
Expected: FAIL（部品のファイルが無い）

- [ ] **Step 3: 実装を書く**

`SKILL/parts/mcp-bridge/server/ext/panel_queue.py`:

```python
"""AI（MCP）とパネルの間の待ち行列。パネルは 2 秒ごとに命令を取りに来る（サーバーからパネルへは送れない）。"""
import threading
import time
import uuid

_lock = threading.Lock()
_state = {"commands": [], "last_seen": 0.0, "queue": [], "results": {}}
_events = {}


def _next(req, ctx):
    with _lock:
        cmds = req["body"].get("commands")
        if isinstance(cmds, list):
            _state["commands"] = [{"name": str(c.get("name")), "description": str(c.get("description", ""))} for c in cmds if isinstance(c, dict)]
        _state["last_seen"] = time.time()
        if _state["queue"]:
            return 200, {"command": _state["queue"].pop(0)}
    return 200, {}


def _result(req, ctx):
    body = req["body"]
    with _lock:
        _state["results"][body.get("id")] = body
        ev = _events.get(body.get("id"))
    if ev:
        ev.set()
    return 200, {"ok": True}


def _status(req, ctx):
    with _lock:
        age = (time.time() - _state["last_seen"]) if _state["last_seen"] else None
        return 200, {"connected": age is not None and age < 6, "commands": list(_state["commands"])}


def _call(req, ctx):
    body = req["body"]
    name = str(body.get("name") or "")
    with _lock:
        known = [c["name"] for c in _state["commands"]]
        if known and name not in known:
            return 404, {"error": f"パネルに「{name}」という命令はありません", "commands": known}
        cid = uuid.uuid4().hex[:12]
        ev = threading.Event()
        _events[cid] = ev
        _state["queue"].append({"id": cid, "name": name, "args": body.get("args") or {}})
    ok = ev.wait(max(0.1, float(body.get("timeoutMs", 30000)) / 1000))
    with _lock:
        _events.pop(cid, None)
        res = _state["results"].pop(cid, None)
        if not ok:
            _state["queue"] = [c for c in _state["queue"] if c["id"] != cid]
    if not ok or res is None:
        return 504, {"error": "パネルから返事がありません", "next": "Premiere でこのプラグインのパネルを開いてください"}
    return 200, {"ok": bool(res.get("ok")), "result": res.get("result"), "error": res.get("error")}


ROUTES = {
    ("POST", "/panel/next"): _next,
    ("POST", "/panel/result"): _result,
    ("GET", "/panel/status"): _status,
    ("POST", "/panel/call"): _call,
}
```

`SKILL/parts/mcp-bridge/server/ppm_mcp.py`:

```python
#!/usr/bin/env python3
"""AI（Claude Code / Codex）からプラグインを操作する MCP（標準入出力・JSON-RPC 2.0・1 行に 1 つ）。

手元のサーバーの server.json を読み、合言葉を付けて /panel/* を呼ぶ。標準ライブラリだけ。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
SUPPORTED = ["2025-06-18", "2025-03-26", "2024-11-05"]
TOOLS = [
    {"name": "ppm_health", "description": f"{APP} のサーバーとパネルがつながっているかを調べる（最初に呼ぶ）",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ppm_panel_commands", "description": "パネルが受け付ける命令の一覧（名前と説明）",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ppm_panel_call", "description": "パネルの命令を呼ぶ。Premiere を変える命令は、利用者の実行の指示があるときだけ使う",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "args": {"type": "object"}}, "required": ["name"]}},
]


def _server(path: str, body=None, timeout: float = 40.0):
    info = json.loads((ppm_paths.app_support(APP) / "server.json").read_text(encoding="utf-8"))
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{info['httpPort']}{path}", data=data, method="POST" if body is not None else "GET",
                                 headers={"Content-Type": "application/json", "X-PPM-Token": info["token"]})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def _text(obj) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, indent=1) if not isinstance(obj, str) else obj}]}


def call_tool(name: str, args: dict) -> dict:
    try:
        if name == "ppm_health":
            _, ping = _server("/ping")
            _, status = _server("/panel/status")
            note = "パネルはつながっています" if status.get("connected") else "パネルが開いていません。Premiere でこのプラグインのパネルを開いてください"
            return _text({"server": ping, "panel": status, "note": note})
        if name == "ppm_panel_commands":
            return _text(_server("/panel/status")[1].get("commands", []))
        if name == "ppm_panel_call":
            code, data = _server("/panel/call", {"name": args.get("name"), "args": args.get("args") or {}, "timeoutMs": 30000})
            return {**_text(data), "isError": code != 200 or not data.get("ok")}
    except FileNotFoundError:
        return {**_text("サーバーが動いていません（server.json がありません）。server の install を実行してください"), "isError": True}
    except (urllib.error.URLError, OSError) as e:
        return {**_text(f"サーバーにつながりません（{e}）"), "isError": True}
    return {**_text(f"知らない道具: {name}"), "isError": True}


def handle(msg: dict):
    method = msg.get("method")
    mid = msg.get("id")
    if mid is None:
        return None  # 通知には返事をしない
    if method == "initialize":
        want = (msg.get("params") or {}).get("protocolVersion")
        version = want if want in SUPPORTED else SUPPORTED[0]
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": version, "capabilities": {"tools": {}},
                                                       "serverInfo": {"name": f"{APP.lower()}-premiere", "version": CONFIG.get("version", "0")}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        return {"jsonrpc": "2.0", "id": mid, "result": call_tool(params.get("name"), params.get("arguments") or {})}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"知らない method: {method}"}}


def main() -> int:
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON が読めません"}}), flush=True)
            continue
        reply = handle(msg)
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/mcp-bridge/server/setup_mcp.py`:

```python
#!/usr/bin/env python3
"""MCP を Claude Code / Codex に登録する。既定は試し実行。--apply で、入っている方だけに登録する（先に外してから足す）。
設定ファイルは手で書き換えない（各 CLI の登録の命令に任せる）。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = json.loads((HERE / "config.json").read_text(encoding="utf-8"))["app"]
NAME = f"{APP.lower()}-premiere"


def plan(python: str, script: Path) -> list:
    cmds = []
    if shutil.which("claude"):
        cmds.append((["claude", "mcp", "remove", NAME, "--scope", "user"], False))
        cmds.append((["claude", "mcp", "add", NAME, "--scope", "user", "--", python, str(script)], True))
    if shutil.which("codex"):
        cmds.append((["codex", "mcp", "remove", NAME], False))
        cmds.append((["codex", "mcp", "add", NAME, "--", python, str(script)], True))
    return cmds


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="MCP を登録する")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    cmds = plan(sys.executable, HERE / "ppm_mcp.py")
    if not cmds:
        print("claude も codex も見つかりません。どちらかを入れてから実行してください（試し実行・何もしていません）")
        return 0
    for c, _ in cmds:
        print("・" + " ".join(c))
    if not args.apply:
        print("（試し実行です。何もしていません。登録するときは --apply を付けます）")
        return 0
    failed = False
    for c, must in cmds:
        r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if must and r.returncode != 0:
            failed = True
            print(f"[NG!] {' '.join(c)}\n{r.stdout}{r.stderr}")
    print("登録しました。新しいセッションを開くと道具（ppm_health など）が使えます" if not failed else "登録に失敗したものがあります")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

`SKILL/parts/mcp-bridge/lib/ppm-agent-bridge.js`:

```js
/* ppm-agent-bridge — AI（MCP）からの命令をパネルで受ける。2 秒ごとに手元のサーバーへ取りに行く。
 * 命令は register で足す。Premiere を変える命令を足すときは、取り消し 1 回で戻る作りにする（PPM.transact）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const handlers = {};
  const state = { timer: null, busy: false };

  function register(name, description, handler) { handlers[name] = { description, handler }; }

  function list() { return Object.keys(handlers).map((name) => ({ name, description: handlers[name].description })); }

  async function pollOnce() {
    if (state.busy) return;
    state.busy = true;
    try {
      const next = await PPM.server.call("/panel/next", { method: "POST", body: { commands: list() } });
      const cmd = next && next.command;
      if (!cmd) return;
      let body;
      try {
        const h = handlers[cmd.name];
        if (!h) throw new Error(`知らない命令: ${cmd.name}`);
        body = { id: cmd.id, ok: true, result: await h.handler(cmd.args || {}) };
      } catch (e) {
        body = { id: cmd.id, ok: false, error: e && e.ppm ? `${e.ppm.symptom}（${e.ppm.why}）` : String((e && e.message) || e) };
      }
      await PPM.server.call("/panel/result", { method: "POST", body });
    } finally {
      state.busy = false;
    }
  }

  function start(opts) {
    const ms = (opts && opts.intervalMs) || 2000;
    if (state.timer) return;
    const tick = () => { pollOnce().catch(() => {}).then(() => { state.timer = setTimeout(tick, ms); }); };
    tick();
  }

  function stop() { if (state.timer) clearTimeout(state.timer); state.timer = null; }

  register("probe", "診断（使える API・Premiere の版・ログの場所）", () => PPM.probe.run());
  register("get_selection", "選んだクリップ（名前・トラック・開始と終了の秒）", async () => {
    const { sequence } = await PPM.getProjectAndSequence();
    const clips = await PPM.getSelectedClips(sequence);
    return { count: clips.length, clips: clips.map((c) => ({ name: c.name, trackIndex: c.trackIndex, kind: c.kind, start: c.startSeconds, end: c.endSeconds })) };
  });
  register("sequence_overview", "シーケンスの映像トラックとクリップの一覧", async () => {
    const { sequence } = await PPM.getProjectAndSequence();
    const count = await PPM.resolve(sequence.getVideoTrackCount());
    const tracks = [];
    for (let i = 0; i < count; i++) {
      const items = await PPM.listTrackClips(sequence, "video", i);
      const clips = [];
      for (const it of items) clips.push(await PPM.describeClip(it));
      tracks.push({ index: i, clips: clips.map((c) => ({ name: c.name, start: c.startSeconds, end: c.endSeconds })) });
    }
    return { videoTracks: tracks };
  });
  register("log_tail", "パネルのログの最後の 50 行", async () => ({ lines: PPM.log ? PPM.log.lines().slice(-50) : [] }));

  PPM.agent = { register, list, pollOnce, start, stop };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);
```

`SKILL/parts/mcp-bridge/part.json`:

```json
{
  "name": "mcp-bridge",
  "description": "AI（Claude Code / Codex）からプラグインを操作する口（MCP → 手元のサーバー → パネルの待ち行列）。開発中の確かめにも使える",
  "status": "partial",
  "os": ["mac", "windows"],
  "requires": ["local-server", "probe"],
  "files": {"server/ppm_mcp.py": "server/ppm_mcp.py", "server/setup_mcp.py": "server/setup_mcp.py", "server/ext/panel_queue.py": "server/ext/panel_queue.py", "lib/ppm-agent-bridge.js": "lib/ppm-agent-bridge.js"},
  "scripts": ["lib/ppm-agent-bridge.js"],
  "styles": [],
  "permissions": {},
  "featureFlags": {},
  "entrypoints": [],
  "minVersion": "25.6",
  "pythonDeps": [],
  "knowledge": ["ref-mcp", "recipe-agent-mcp"],
  "notes": "index.js の boot() の中で PPM.agent.start() を呼ぶ。登録は server/setup_mcp.py（既定は試し実行）。パネルを閉じていると届かない"
}
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_mcp_bridge.py' -v && node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_parts.py' -v`
Expected: PASS（mcp 5・JS 全部）

- [ ] **Step 5: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 部品 mcp-bridge（AI からパネルの命令を呼ぶ MCP と待ち行列・登録は試し実行が既定）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 5: 知識の中身

この Phase は文章を書く作業なので、サブエージェント（必ず `model: sonnet`）に任せ、同時に走らせるのは 2 本までにする（利用の上限で止まった前例があるため）。親（この計画を進める側）は、各バッチの後に `kb.py check` を通し、数本を読んで質を確かめる。

**全バッチに共通の指示（サブエージェントへの依頼文にそのまま入れる）:**

1. 書く場所は `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/knowledge/<種類のフォルダ>/<id>.md`。1 件 1 ファイル。ファイル名は id と同じ。
2. 先頭項目は Task 5 の形（`id title kind tags os premiere status summary` は必須、`parts related` は任意）。`kind` は置き場所と一致させる（core/ は core、recipes/ は recipe、features/ は feature、usecases/ は usecase、platform/ は platform、reference/ は reference）。
3. `status` は根拠で決める: 実機で確かめた記録がある＝`verified`、一部だけ（Mac だけ・ある版だけ）＝`partial`、記録が無い＝`unverified`、後から訂正された古い主張＝`superseded`（本文の先頭に「訂正: 正しくは〜（id）」と書き、`related` に正しい方の id を入れる）。
4. `os` は当てはまる OS だけ（Mac だけの話なら `[mac]`）。`premiere` は当てはまる版（例 `">=26.3"`、分からなければ `">=25.6"`）。
5. 本文は日本語の平易な文。初心者が読んで分かる言葉にし、専門の言葉は初出で一言説明する。記号や略語で圧縮しない。
6. **公開物なので、個人名（作者・視聴者・取引先・出演者の名前）、個人のパス（`/Users/<名前>/` など）、鍵・トークン、チャンネル名、取引の情報を書かない。**人は「利用者」「視聴者」と書く。パスは `~/` や `%APPDATA%` の形にする。
7. 原文の丸写しをしない。要点を自分の言葉で書き、コードは必要な最小の断片だけにする。
8. 「出どころ」の節には、どのプラグインのどの記録か（例: 「Cut & SRT の失敗記録（2026-07-24）」「Adobe 公式の変更履歴（26.3）」）を書く。URL は Adobe 公式とフォーラムのものだけ書いてよい。
9. 記録どうしが食い違う所は、片方だけを書かない。両方と「キットの部品はどちらに合わせたか」を書く（調査 A §3.3、調査 E §3.3）。
10. 書き終えたら `python3 SKILL/scripts/kb.py build && python3 SKILL/scripts/kb.py check` を実行し、問題が 0 件になるまで直す。

**本文の型（種類ごと）:**

| 種類 | 節（この順） |
|---|---|
| core | 要点（3〜7 行の箇条書き）／詳しく／やってはいけないこと／出どころ |
| recipe | この型で作れるもの／前提／手順／確認／戻し方／使う部品／出どころ |
| feature | 何をする機能か／作り方／使った API と道具／つまずきと直し方／結果と今の状態／出どころ |
| usecase | 症状／原因／直し方／再発防止／出どころ |
| platform | 違いの表（項目・Mac・Windows・確度）／気を付けること／出どころ |
| reference | 仕様／例／注意／出どころ |

usecase の見本（この質で書く）:

```markdown
---
id: uc-uxp-action-outside-lock
title: 「The script object is no longer valid」で変更が失敗する
kind: usecase
tags: [UXP, 取引, Action, エラー, lockedAccess]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: Action を取引の外で作ったか、取引の中で await した。非同期の取得を先に済ませ、Action は取引の中で作る
parts: [ppro-kit]
related: [core-transactions]
---
## 症状

ボタンを押すと、タイムラインが変わらずに「The script object is no longer valid」というエラーが出る。値を読むだけの処理は動く。

## 原因

Premiere の取引（`project.lockedAccess` の中の `project.executeTransaction`）のコールバックは、完全に同期でなければならない。取引の外で（`await` を挟んで）Action を作り、中で足すだけにすると、Action が別の文脈のものになって無効になる。Premiere 26.3 からは、Action を lockedAccess の中で作ることが必須になった。

## 直し方

1. 非同期の取得（`getComponentChain`・`VideoFilterFactory.createComponent`・クリップの取り直し）を、取引の前に済ませる。
2. 取引の中では、Action を作って足すだけにする（`PPM.transact(project, "名前", (add) => { add("説明", () => clip.createSetEndAction(t)); })`）。
3. 足した効果の値を変えるときは、取引を分ける（足した効果は、取引が確定するまで設定項目を持たない）。

## 再発防止

- `check.py` の J001（取引の中の await）と J002（取引の外の Action）が止める。
- 部品 ppro-kit の `PPM.transact` を使う。

## 出どころ

- Cut & SRT・Effect & Design の実機の記録（Premiere 26.3・26.5）
- Adobe 公式の変更履歴（26.3 の破壊的な変更）と ESLint のプラグインの規則
```

### Task 24: 知識 core・platform・reference

**Files:**
- Create: `SKILL/knowledge/core/` の 11 件、`SKILL/knowledge/platform/` の 3 件、`SKILL/knowledge/reference/` の 9 件（下の表）
- Test: `tests/test_knowledge.py`

**Interfaces:**
- Produces: 下の表の id（ほかの Task の part.json・評価表・SKILL.md が参照する。id は変えない）

| id | 題 | 必ず入れること | 材料 |
|---|---|---|---|
| core-versions | Premiere と UXP の版の歴史と、最低版の決め方 | 25.2 ベータ（2024-12）→ 25.6 正式版（2025-11）→ 26.0 → 26.2（ProjectConverter・getVideoFrameRate・Hybrid）→ 26.3（Action は lockedAccess の中で必須・setSelection が同期）→ 26.5（WorkAreaUtils など）→ 27.0 ベータ（分割の API・MogrtText・ドラッグ&ドロップ）／CEP の予定（新規の受付停止 2027-12・既定で無効 2028-12・同梱終了 2029-12・ExtendScript は対象外）／minVersion は「使う API の最低版」で決める（api-since.json と check.py の J014）／確認日 2026-10-13 | 調査 G §1〜4、調査 A §2.3・§3.6、調査 W |
| core-capabilities | できること・できないことと代わりの手 | 表（頼まれた操作・API の状況・代わりの手）: 分割・別トラックへの移動・速度・字幕本文・プログラムモニターの再生・メニューのコマンド・トラックのターゲット・図形・マルチカム・テロップの本文の読み取り（FCP XML で読む）・リンクの解除・キーボードショートカット／代わりの手（FCP XML の作り直し・CEP 補助・MOGRT・利用者の手作業・Claude の画面操作）／「無いものは無いと言う。未検証の抜け道を動くと言わない」 | 調査 F §5.5、調査 A §3.5、調査 G §8（13） |
| core-transactions | 取引の作法（取り消し 1 回で戻す） | 3 段階の型／T1〜T12 の規則（戻り値 false・1 取引＝1 取り消し・1 つずつ足す・効果を足す取引と値の取引を分ける・時間変化の余分なキー・単独削除は同じ取引で足したキーを消せない・補間は同じ取引で変えられない・テキストの部品の手前に差す・トランジションは内部名と ticks・MOGRT の挿入は取引に入らない・取引の外で呼ぶもの・大量配置は件数を分ける）／ESLint の `@adobe/eslint-plugin-premierepro` | 調査 A §3.4、調査 G §3.3、調査 D §3.4〜3.5 |
| core-api-patterns | API の正しい使い方の型（用途別） | プロジェクトとシーケンス・タイムラインを読む（getTrackItems は引数 2 つ）・選択（getSelection を使い new TrackItemSelection は使わない）・クリップの操作・マーカー・書き出し（exportSequenceFrame は書き終わる前に返る）・プロジェクトの項目とビン・効果とキー（findParam の日英の表示名）・トランジション・MOGRT・UXP の host・ファイル・クリップボード・localStorage・ネットワーク／TickTime の読み方（ticksNumber を先に）／存在を確かめてから呼ぶ（doc 記載≠実装済み）／記録が割れている所（ticks・insertMogrtFromPath の上書き・setInPoint）と部品の選んだ側 | 調査 A §3.1〜3.3、調査 E §3 |
| core-ui-rules | UXP の画面の制約と直し方 | grid 不可・flex の子が潰れる（一覧の行に flex: 0 0 auto）・ドックの下のボタンに届かない（高さ 100% と min-height: 0）・sp-button が押せない・select のホイール・textarea の null・空欄の NaN・confirm が無い・重ね表示が透ける・MutationObserver が無い・複雑な SVG（PNG に焼く）・require の相対パス・起動は末尾で 1 回・title を隠す・ul/li は div・input file/color 不可／下見（Chromium）では出ない崩れがあること | 調査 A §4、調査 G §6、調査 C 付録 A（23・24） |
| core-manifest-permissions | manifest と権限の決め方 | 必須の項目・host は配列にしない・host.data（apiVersion 2・loadEvent startup。公式の文書には無いが実機で動いた形）・icons（species は文字列 "generic" で動いた）・権限ごとに「何をするとき足すか」（localFileSystem plugin/request/fullAccess・network（127.0.0.1 は "all" が要る）・clipboard・launchProcess・webview（domains は TLD のワイルドカードだけ効いた）・allowCodeGenerationFromStrings・enableAlerts）／id を変えるとショートカットの割り当てが消える | 調査 G §2.2、調査 A §2.1〜2.5、調査 E §2 |
| core-verification | 実機で確かめる作法 | 「完成と言ってよいのは利用者の Premiere で確かめた後だけ」／診断ボタン（probe）で API の有無を先に見る／logs.py でログを読む／コマを書き出して画で見る（プレイヘッドを置いてから）／1 回に 1 手順を頼む／テストが全部通っても実機だけ止まる型（UMD・child_process・存在しないプロパティ）／未確認は未確認と書く | 作者の記憶の「検証の鉄則」、調査 D §6、調査 F §5.4 |
| core-dev-loop | 開発中の読み込み（UDT）とつながらないとき | 開発者モードは 2 か所（UDT 側の settings.json・Premiere の設定→プラグイン）＋Premiere の再起動／Add Plugin → Load・Load & Watch・Reload・manifest を変えたら Unload → Load／ウィンドウ→UXP プラグイン／UDT が Premiere を見つけないとき／UDT を開いたまま plugins_workspace.json を書き換えない／直したのに変わらないとき（読み込み元の確認） | 調査 C §2、調査 G §5.1、調査 W |
| core-safety | 利用者のプロジェクトを守る | 取引 1 回＝取り消し 1 回を基本に／一括の前に保存を勧める・件数を伝えて確認／元のシーケンスを残す（カットは新しいシーケンスへ）／権限は最小／外部へ送る機能は相手先を示して同意／鍵は OS の保管庫／他人のテンプレート・有料素材を写さない／大量のクリップは件数を分ける（落ちる既知の問題） | 調査 F §5.4、設計書 §12、調査 G §8（5） |
| core-intake | 聞き取りと、要望から雛形・部品への対応 | 6 つの質問（何を・何に・どう動かす・結果・重い処理・誰が使う）／要望の型→雛形と部品の表（例: 選んだクリップに効果→panel＋ppro-kit、無音カット→panel-server＋silence-cut、字幕→panel-server＋transcribe-srt、テロップの差し替え→panel-server＋mogrt-text、ショートカット→panel-commands、分割・再生→cep-helper（期限つき）、AI から操作→mcp-bridge）／最低版の決め方 | 設計書 §5.1〜5.2、§7 |
| core-versioning-release | 版数と配布 | 版は manifest と build_info を同じに／同じ版で入れ直しても更新されない（上げるか、先に外す）／版を上げる基準（両方の OS に関わる変更）／.ccx は配る物だけを集める（UDT の Package は古い登録や余分なファイルを拾うことがある）／受け取る人の入れ方（ダブルクリック・UPIA）／Creative Cloud のサインインで登録が消える／Marketplace の審査の条件 | 調査 C §3・§6・§8、調査 G §5.2〜5.4 |
| platform-mac | Mac での場所と注意 | Premiere・ログ・UDT の設定・UPIA・UXP の登録簿と External・CEP の拡張フォルダと PlayerDebugMode・Adobe Fonts・Python（CEP から見える /usr/bin/python3 と CLT）・Homebrew の ffmpeg・launchd・保護フォルダ（書類・デスクトップ・ダウンロード）・Gatekeeper（bash にドラッグ）・Intel と Apple シリコン | 調査 W §1、調査 C §5、調査 D §7 |
| platform-windows | Windows での場所と注意 | 調査 W §1 の表を確度つきで全部（公式・案件の実機・見つからなかった）／Python install manager と py・Store の仮の python／cp932 と PYTHONUTF8 と encoding の明示／PowerShell 5.1 の BOM・実行ポリシー・.bat は英数字だけ／winget の ffmpeg と PATH の反映／タスク スケジューラ（サインイン時の自動起動は未確認）／OneDrive の同期対象を避ける／SmartScreen／UXP の `file:///C:/` の書き方／CUDA が無いときの CPU | 調査 W、調査 C §5.5 |
| platform-cross | Mac と Windows の両方で動かす書き方 | パスは環境変数と相対で・空白と日本語のパス・NFC と NFD・改行・文字コードの明示・実行ビットに頼らない・OS の分岐を 1 か所に・Mac 専用の場所だけを探さない（Windows で失敗した事故）・check.py の W 規則 | 調査 C 付録 A（14〜16・21）、記憶の「日本語の扱いの罠」 |
| ref-ticktime | TickTime と時間の単位 | 1 秒 = 254016000000 ticks／createWithSeconds・createWithTicks（文字列）／ticksNumber・ticks・seconds の揺れ／BigInt／フレームとの換算（宣言の timebase と ntsc）／ExtendScript のキーの時刻は素材時間（入点基準） | 調査 A §3.1、調査 D §2.2 |
| ref-fcp7-xml | FCP7 XML（xmeml）の決まり | 完全な定義は 1 回・ぶら下がりの検査・子要素で判定・sequence 直下の rate・宣言 timebase で換算（実 fps はクランプだけ）・フレームと pproTicks は同じ基準で書く・ネスト・マルチカム（映像が書き出されない・音声から作り直せる）・テロップの本文（GraphicAndType）・Premiere の書き出しは［ファイル］→［書き出し］→［Final Cut Pro XML］ | 記憶の「Premiere 拡張と XML の実測」、調査 B の XML の節 |
| ref-prtextstyle | .prtextstyle とソーステキストの blob | Premiere のプロジェクト XML であること・blob = 12 バイトのヘッダ＋FlatBuffer・フィールドの対応・既定値・線の位置・取り込みは本文だけ差し替える・Adobe Fonts の PostScript 名の探し方 | 記憶の「.prtextstyle/.prfpset の生成仕様」、調査 D §4.7〜4.9 |
| ref-prfpset | .prfpset（エフェクトプリセット） | 木の構造・Type 0/1/2（引き伸ばし・イン点・アウト点）・キーの書き方と補間の番号・点の接線・トランスフォームの ParameterID・アンカーの注意 | 同上 |
| ref-mogrt | MOGRT の中身とドナー差し替え | .mogrt = zip(definition.json + locale 別 .prgraphic)・ドナー（Premiere の中の Basic Title.mogrt）・ID の振り直しと `<First>` を振り直さない罠・locale ごとの尺の ticks・MasterClip が 2 つ・転植版は固まるので使わない・importMGT と insertMogrtFromPath の違い・上のトラックが無いと元を上書き | 調査 D §4 |
| ref-keyframe-interpolation | Premiere の補間の実測式と焼き込み | 時間の補間（区間の形は始まりのキーだけで決まる・bezier の制御点）・空間の補間（接線 1/6）・行き過ぎが約 2 倍の正体・UXP は同じ取引で補間を変えられない→焼く・2 キーの終わりの easein は効かない | 記憶、調査 D §5 |
| ref-cep-extendscript | CEP と ExtendScript と QE DOM | manifest.xml・.debug と CDP での観察・PlayerDebugMode（Mac・Windows）・拡張フォルダ・Node の罠（UMD・child_process）・ES3 の制約（JSON が無い）・QE DOM（非公式・日本語 UI の名前・matchName）・CSInterface.js は Adobe の配布物（同梱しない）・期限（2028-12・2029-12） | 調査 D §1〜2、調査 W |
| ref-local-server | 手元のサーバーの作り | 127.0.0.1 だけ・起動ごとの合言葉・握手のファイル（0600・待ち受け後に原子的に）・ジョブ（失敗も HTTP 200）・ポーリングの間隔と通信断の許容・常駐（launchd・タスク スケジューラ）・版ごとの runtime と同じ版の罠・ログが膨らむ（ポーリングを記録しない）・PATH の違い（Finder・launchd・常駐は最小の PATH） | 調査 A §1.3〜1.4、調査 C §5 |
| ref-mcp | MCP の口の作り | 標準入出力の JSON-RPC・道具の名前に接頭辞を付けない・プロトコルの版の選び方・パネルが取りに来る待ち行列・パネルを閉じていると届かない・登録は CLI の命令で（設定ファイルを手で書かない）・古い握手のファイルで 403 が続いた事故 | 調査 F §4.4・§5、調査 A §6 |

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_knowledge.py`:

```python
import unittest

from helpers import KNOWLEDGE, PARTS

import kb

REQUIRED_IDS = [
    "core-versions", "core-capabilities", "core-transactions", "core-api-patterns", "core-ui-rules",
    "core-manifest-permissions", "core-verification", "core-dev-loop", "core-safety", "core-intake",
    "core-versioning-release", "platform-mac", "platform-windows", "platform-cross", "ref-ticktime",
    "ref-fcp7-xml", "ref-prtextstyle", "ref-prfpset", "ref-mogrt", "ref-keyframe-interpolation",
    "ref-cep-extendscript", "ref-local-server", "ref-mcp",
]


class KnowledgeTests(unittest.TestCase):
    def test_check_passes(self):
        self.assertEqual(kb.check_all(KNOWLEDGE, PARTS), [])

    def test_required_ids_exist(self):
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        missing = [i for i in REQUIRED_IDS if i not in ids]
        self.assertEqual(missing, [])

    def test_body_has_the_sections_of_its_kind(self):
        sections = {"core": ["## 要点", "## 出どころ"], "recipe": ["## 前提", "## 手順", "## 確認", "## 戻し方"],
                    "feature": ["## 何をする機能か", "## 作り方", "## 結果と今の状態"], "usecase": ["## 症状", "## 原因", "## 直し方", "## 再発防止"],
                    "platform": ["## 出どころ"], "reference": ["## 仕様", "## 出どころ"]}
        for entry, body in kb.load(KNOWLEDGE):
            for s in sections[entry["kind"]]:
                self.assertIn(s, body, f"{entry['id']} に「{s}」がありません")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_knowledge.py' -v`
Expected: FAIL（`test_required_ids_exist` が 23 件の不足）

- [ ] **Step 3: サブエージェントに 2 バッチで書いてもらう**

バッチ 1（core の 11 件）とバッチ 2（platform 3 件・reference 9 件）を、それぞれ 1 本のサブエージェント（`model: sonnet`）に任せる。依頼文には「全バッチに共通の指示」「本文の型」「usecase の見本」「この Task の表のうち担当の行」「材料のファイルの絶対パス（調査 A〜G・W と `notes/`、`~/.claude/projects/<記憶のフォルダ>/memory/` の reference_premiere_extension_internals.md・feedback_cutsrt_plugin_gotchas.md・feedback_verification_principles.md）」を入れる。2 本は同時に走らせてよい。

- [ ] **Step 4: 親が確かめる**

Run: `python3 SKILL/scripts/kb.py build && python3 SKILL/scripts/kb.py check && python3 -m unittest discover -s tests -t tests -p 'test_knowledge.py' -v`
Expected: 問題 0 件・PASS

親は core-transactions・platform-windows・ref-fcp7-xml の 3 件を全文読み、(1) 個人名・個人のパスが無い、(2) 調査の事実と食い違わない、(3) 初心者が読める文、を確かめる。直す所があれば、そのサブエージェントに SendMessage で直してもらう。

- [ ] **Step 5: コミット（文書なので /verify は不要）**

```bash
git add -A
git commit -m "docs: 知識 core・platform・reference（版・できないこと・取引・API の型・画面・権限・確かめ方・OS の違い・形式の仕様）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 25: 知識 features（これまで作った機能の記録）

**Files:**
- Create: `SKILL/knowledge/features/` の 37 件（下の表）

**Interfaces:**
- Produces: 下の表の id。Cut & SRT にしか要らない機能（話者・顔の追従・画角・送るタブ・辞書）も、作り方・使った道具・つまずき・結果まで書く（利用者の指示「Cut&SRT にしか要らない機能もナレッジとして積み上げる」）

| id | 題 | 材料（主なもの） |
|---|---|---|
| feat-cutsrt-overview | Cut & SRT の全体の作り（パネル＋サーバー＋CEP 補助＋MCP・タブの構成・版の歴史） | 調査 A §1、記憶 project_premiere_cut_srt_plugin.md |
| feat-cutsrt-cut | 無音カット（XML の往復・包絡の検出・前後の余白・fps の規則・終了コード・マルチカムとネスト） | 調査 A、notes F1・F2・G1、記憶 feedback_cutsrt_plugin_gotchas.md §1〜4 |
| feat-cutsrt-telop-srt | テロップと字幕の生成（文字起こし→意味で区切る改行→SRT→配置・訳） | notes H1〜H6、記憶 project_premiere_skills_v6.md |
| feat-cutsrt-align | テロップの整列（カットの境目にそろえる） | 調査 E（caption-align）、notes |
| feat-cutsrt-design | デザインタブ（Effect & Design の UXP への移植・見本の PNG・差し替えと位置の写し） | 調査 A、記憶 project_premiere_cut_srt_plugin.md 2026-09-25 |
| feat-cutsrt-assets | 素材タブ（効果音・画像・動画・書体の検索・規約の扱い・ビンへの取り込み） | notes、記憶 |
| feat-cutsrt-web | Web タブ（パネル内のブラウザ・domains・履歴・ダウンロードの横取り） | 調査 A §4（27） |
| feat-cutsrt-send | 送るタブ（書き出し先の見張り・Drive・ギガファイル便・Frame.io・IRERU の落とし穴） | 記憶 2026-09-24〜25 |
| feat-cutsrt-speaker | 話者の振り分け（声紋・分離・Jev・前後の合成・確からしさのマーカー） | 記憶 2026-09-26〜27 |
| feat-cutsrt-pinmic | ピンマイクの自動切り替え（マイクごとの音量・持ち主の自動決定・分割は CEP） | 記憶 2026-09-30 |
| feat-cutsrt-direct-stamp | 演出: 顔についていくスタンプ（顔検出・コマの書き出し・配置） | 記憶 2026-10-05 |
| feat-cutsrt-direct-zoom | 演出: 囲んだ所へのズーム（四角のつまみ・キーの焼き込み） | 記憶 2026-10-05 |
| feat-cutsrt-direct-angle | 演出: 画角の変更（外部の生成サービスの CLI・見積もり・費用の確認） | 記憶 2026-10-05 |
| feat-cutsrt-clip-slots | クリップ棚（効果とキーごと保存・貼り付け・コマンドのショートカット） | 調査 A、調査 E |
| feat-cutsrt-fx-slots | FX スロット（効果の状態の保存と適用） | 調査 A、調査 E（effect-shortcut） |
| feat-cutsrt-split-fix | 分割・修正タブ（テロップの本文の修正・再生は CEP） | notes、調査 A §5 |
| feat-cutsrt-dictionary | 辞書（差分の学習・置換だけを登録する規則・本文の読み取り） | 記憶 feedback_cutsrt_plugin_gotchas.md §5〜6 |
| feat-cutsrt-mcp | MCP の 36 の道具とパネルの待ち行列 | 調査 A §6、調査 F §5 |
| feat-cutsrt-playback-helper | CEP の再生ヘルパー（名乗った命令だけ送る） | 調査 A §5 |
| feat-cutsrt-settings-diagnostics | 設定・診断・サポートパック・ログ | 調査 C、notes G10 |
| feat-cutsrt-install-update | 導入と更新（版ごとの runtime・sha256・常駐・.ccx・同じ版の罠・秘密らしい名前で部品が落ちる） | 調査 C |
| feat-cutsrt-ai-engines | AI のエンジンの連携（CLI の起動・確かめ方・標準入力・Antigravity の回帰） | 記憶 2026-08-25、notes |
| feat-cutsrt-filler-cut | フィラーカット（実験・既定はオフ） | 記憶 2026-09-24 |
| feat-cutsrt-shapes | 図形（MOGRT のドナーのバイナリの差し替え・凍結した理由） | 調査 A §3.5 |
| feat-ed-overview | Effect & Design の全体（CEP＋UXP 補助＋Python のエンジン・4 つの実行場所） | 調査 D §0 |
| feat-ed-design-apply | デザインの 1 クリックの差し替え（MOGRT の生成・importMGT・元を外す） | 調査 D §2.6・§4 |
| feat-ed-motion | アニメ（motion.json・ExtendScript のキー・UXP の焼き込み・トランスフォーム・残像） | 調査 D §5 |
| feat-ed-import-styles | 買った・作ったテキストスタイルの取り込み（本文だけ差し替え） | 調査 D §4.9 |
| feat-ed-catalog-previews | カタログと見本（見本の作り方・いちばん明るい瞬間） | 記憶 project_effect_design_extension.md |
| feat-ed-packaging | 配布パッケージ（make_package・AGENTS.package.md・書体の確認・xcode-select） | 調査 D §7 |
| feat-caption-align | caption-align（最小の UXP パネル・整列・setIn/setOut をグラフィックに使わない） | 調査 E §1.2 |
| feat-clip-clipboard | clip-clipboard（クリップのコピーと貼り付け・コマンド 10 個） | 調査 E §1.3 |
| feat-effect-shortcut | effect-shortcut（効果のスロット・取引の 3 段階） | 調査 E §1.4 |
| feat-silence-cut-plugin | silence-cut（初期の UXP＋Python・キーの送信で切る方式と、真似しないこと） | 調査 E §1.5・§6 |
| feat-kazaru | KAZARU（.prtextstyle と .prfpset を言葉から作る） | 調査 F §6 |
| feat-premiere-skills | premiere-skills（/cut と /srt の作り・終了コード・意味で区切る改行） | 調査 F §7、記憶 project_premiere_skills_v6.md |
| feat-premiere-agent-kit | premiere-agent-kit（MCP の登録・安全規約・逃げ道・トラブル表・画面操作） | 調査 F §5 |

- [ ] **Step 1: サブエージェントに 4 バッチで書いてもらう**

バッチは「Cut & SRT の前半（overview〜send の 8 件）」「Cut & SRT の後半（speaker〜shapes の 16 件）」「Effect & Design と小型 4 本（10 件）」「KAZARU・premiere-skills・premiere-agent-kit（3 件）」。2 本ずつ同時に走らせる。依頼文には共通の指示・本文の型・担当の行・材料の絶対パスを入れる。外部サービス（送るタブ・画角の変更）の記録は、規約と費用の注意を「つまずきと直し方」に必ず入れ、鍵の値やアカウントの情報は書かない。

- [ ] **Step 2: 親が確かめる**

Run: `python3 SKILL/scripts/kb.py build && python3 SKILL/scripts/kb.py check && python3 -m unittest discover -s tests -t tests -p 'test_knowledge.py' -v`
Expected: 問題 0 件・PASS

親は feat-cutsrt-speaker・feat-cutsrt-send・feat-ed-design-apply を全文読み、人名・チャンネル名・個人のパス・鍵が無いことを確かめる（`grep -rn "/Users/" SKILL/knowledge` が 0 件）。

- [ ] **Step 3: コミット**

```bash
git add -A
git commit -m "docs: 知識 features（Cut & SRT・Effect & Design・小型 4 本・KAZARU・premiere-skills・premiere-agent-kit の作り方と結果）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 26: 知識 usecases（失敗事例）

**Files:**
- Create: `SKILL/knowledge/usecases/` に、調査 B の全件（2026-10-13 の全文版で 185 件。汎用 183・固有 2）を 1 件も落とさずに取り込んだ usecase。同じ原因はまとめてよいので件数は 185 より少なくなりうるが、80 件は下回らない。下の「必ず作る id」40 件を含む

**Interfaces:**
- 材料: 調査 B（`B_failures_usecases.md`。仕上げ中なら `notes/F1_failures_1-297.txt` `notes/F2_failures_298-472.txt` と `notes/G*.txt` `notes/H*.txt`）、B の ID の一覧 `B_failures_usecases_trace.tsv`（列: `final_id` `writer_id` `title` `raw_note_slugs`。`final_id` が `C1-01` の形の ID）、調査 C の付録 A（事故 30 件）、調査 D §8、調査 G §8、調査 W
- 取り込みの対応表（公開物に入れない）: 各バッチは最後の報告に「B の ID ⇥ 作った usecase の id」を 1 行ずつ返す（まとめた ID は同じ usecase の id を書く）。親はそれを `<作業場所>/docs/superpowers/research/2026-10-13-premiere-plugin-maker/usecase_map.tsv` に集める
- id の付け方: `uc-<分野>-<短い英語>`。分野は `uxp` `ui` `fps` `xml` `mogrt` `cep` `server` `install` `windows` `mac` `ai` `verify` `dev`
- 重複は 1 件にまとめる（同じ原因なら 1 件。症状が違う場合は症状の節に両方書く）
- 古い主張（後で訂正されたもの）は `status: superseded` で残し、正しい方を `related` に入れる
- 「必ず作る id」（評価表と SKILL.md が使う）:

| id | 題（症状） |
|---|---|
| uc-uxp-action-outside-lock | 「The script object is no longer valid」で変更が失敗する |
| uc-uxp-get-track-items-args | getTrackItems が空・例外になる（引数が 2 つ要る） |
| uc-uxp-new-trackitemselection | 26.3 で選択の反映が「Connection to object lost」 |
| uc-uxp-remove-items-4-args | 削除の Action が「Not Enough Parameters」 |
| uc-uxp-getmediatype-guid | 映像か音声かの判定がいつも外れる |
| uc-uxp-export-frame-not-written | 書き出したコマの画像がまだ無い |
| uc-uxp-interp-same-transaction | キーの補間がイーズにならない |
| uc-uxp-effect-params-before-commit | 足した効果の値を設定できない |
| uc-uxp-transition-duration-ticks | トランジションの長さがずれる |
| uc-uxp-mogrt-overwrite-unclear | MOGRT を入れても元のテロップが残る／消える |
| uc-uxp-require-relative | 分けた JS が読み込めない |
| uc-uxp-init-tdz | 起動で ReferenceError（宣言前の const） |
| uc-ui-flex-rows-collapse | 一覧の行が中身より低く潰れて重なる |
| uc-ui-sp-button-inactive | 起動時から見えているボタンが押せない |
| uc-ui-select-wheel | select の値がホイールで勝手に変わる |
| uc-ui-textarea-null | 入力欄に "null" が混ざる・NaN で設定が壊れる |
| uc-ui-mutationobserver-missing | MutationObserver が無くて止まる |
| uc-fps-property-missing | 60fps なのに 30fps として扱われる |
| uc-fps-vfr-timebase | 最後の 100 秒だけカットされない（宣言の timebase と実 fps の食い違い） |
| uc-fps-mixed-ticks-basis | 終盤ほどカットがずれる（フレームと ticks の基準の混在） |
| uc-xml-dangling-file | XML を読み込んでも新しいシーケンスが出てこない |
| uc-xml-silence-asymmetric | カットの後ろに余韻が残りすぎる（検出の前後の偏り） |
| uc-mogrt-first-uuid | 作った MOGRT が空のグラフィックになる |
| uc-mogrt-importmgt-track-rounding | 上のトラックが無いと元のクリップを上書きする |
| uc-cep-unknown-command | 古い補助が新しい命令を別の動きとして実行する |
| uc-cep-node-exec-callback | CEP で外部コマンドの返事が来ない |
| uc-cep-umd-window | CEP で関数が未定義になる（UMD の判定） |
| uc-cep-qe-effect-locale | 日本語の Premiere で QE の効果が付かない |
| uc-cep-es3-json | ExtendScript で「JSON is undefined」 |
| uc-server-localhost-network-all | パネルから手元のサーバーにつながらない |
| uc-server-stale-handshake-403 | 403 がずっと続く（古い握手のファイル） |
| uc-install-same-version | 作り直して入れたのに古いまま |
| uc-install-cc-signin-wipes | Creative Cloud にサインインし直したらプラグインが消えた |
| uc-install-secret-name-dropped | 配った先でサーバーが起動しない（秘密らしい名前の部品が落ちた） |
| uc-install-udt-package-stale | UDT の Package が古い版を作る |
| uc-dev-edit-vs-runtime | 直したのに Premiere の動きが変わらない |
| uc-windows-cp932 | Windows で文字化けして止まる |
| uc-windows-mac-only-path | Windows でだけ「見つかりません」になる |
| uc-mac-bash-variable-japanese | Mac のインストーラが途中で止まる（$変数の直後の日本語） |
| uc-verify-keychain-test-left | 試した鍵が本物のキーチェーンに残った |

- [ ] **Step 1: サブエージェントに 3 バッチで書いてもらう**

バッチは「UXP・UI・fps・XML（必ず作る id のうち uc-uxp-* uc-ui-* uc-fps-* uc-xml-* と、材料の同じ分野の残り）」「MOGRT・CEP・サーバー・導入（uc-mogrt-* uc-cep-* uc-server-* uc-install-* と残り）」「Windows・Mac・AI・確かめ方・開発（uc-windows-* uc-mac-* uc-dev-* uc-verify-* uc-ai-* と残り）」。2 本ずつ走らせる。依頼文には共通の指示・本文の型・usecase の見本・必ず作る id の担当分・材料の絶対パス・「材料の汎用の事例は全部入れる。Cut & SRT 固有の事例は、ほかのプラグインでも起きうる形に一般化して入れる」・「担当の分野の B の ID（`B_failures_usecases_trace.tsv` の `final_id`）を全部受け持ち、最後に `B の ID<TAB>usecase の id` の対応表を返す」を入れる。

- [ ] **Step 2: 親が確かめる**

Run:

```bash
python3 SKILL/scripts/kb.py build && python3 SKILL/scripts/kb.py check
python3 SKILL/scripts/kb.py list --kind usecase | wc -l
python3 - "<作業場所>/docs/superpowers/research/2026-10-13-premiere-plugin-maker" <<'EOF'
# B の全 ID が、実在する usecase のどれかに取り込まれたかを確かめる
import csv, pathlib, sys
src = pathlib.Path(sys.argv[1])
ids = [r["final_id"] for r in csv.DictReader(open(src / "B_failures_usecases_trace.tsv", encoding="utf-8"), delimiter="\t")]
pairs = [line.split("\t") for line in (src / "usecase_map.tsv").read_text(encoding="utf-8").splitlines() if "\t" in line]
mapped = {b.strip(): uc.strip() for b, uc in pairs}
have = {p.stem for p in pathlib.Path("plugins/premiere-plugin-maker/skills/premiere-plugin-maker/knowledge/usecases").glob("*.md")}
print("取り込まれていない B の ID:", [i for i in ids if i not in mapped])
print("対応表にあるのに無い usecase:", sorted({uc for uc in mapped.values() if uc not in have}))
EOF
```

Expected: 問題 0 件。usecase が 80 件以上。2 つの一覧がどちらも `[]`。必ず作る id の 40 件がそろっている（`python3 SKILL/scripts/kb.py show uc-windows-cp932` などで数件を開いて確かめる）。落ちた ID があれば、その分野のバッチに足してもらう。

- [ ] **Step 3: コミット**

```bash
git add -A
git commit -m "docs: 知識 usecases（失敗事例 80 件以上・症状→原因→直し方→再発防止・古い主張は superseded で残す）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 27: 知識 recipes（要望の型ごとの作り方）

**Files:**
- Create: `SKILL/knowledge/recipes/` の 15 件（下の表）

| id | 題 | 使う雛形・部品 |
|---|---|---|
| recipe-batch-effect | 選んだクリップに一括で効果を足す | panel・ppro-kit（addEffect は取引 1 回、値の設定は別の取引） |
| recipe-keyframe-motion | キーで動きを付ける（ズーム・スライド・フェード） | panel・ppro-kit・motion-bake（zoom-button の見本） |
| recipe-markers-chapters | マーカーを打つ・チャプターの一覧を作る | panel・ppro-kit（addMarkers）。YouTube の概要欄の `0:00 題` の書き方も |
| recipe-telop-restyle | テロップのデザインを一括で差し替える | panel-server・fcpxml・mogrt-text（telop-restyle の見本） |
| recipe-silence-cut | 無音をカットする | panel-server・fcpxml・silence-cut（silence-cut の見本） |
| recipe-captions-srt | 文字起こしして字幕（SRT）を作る | panel-server・transcribe-srt。意味で区切る改行は feat-premiere-skills を元に |
| recipe-export-automation | 決まった設定で書き出す | panel・ppro-kit（EncoderManager.exportSequence・AME のキュー・H.265 は無効の記録・作業エリアの注意） |
| recipe-import-bins | 素材のフォルダを読み込んでビンに整理する | panel（importFiles・createBinAction は Action がビンを返さない） |
| recipe-commands-shortcuts | メニューのコマンドとショートカット | panel-commands（Mac のアプリのショートカットの割り当て・Windows は未確認） |
| recipe-local-server-heavy | 重い処理を手元のサーバーに任せる | panel-server（ジョブの書き方・導入・依存の入れ方の同意） |
| recipe-ai-integration | AI（CLI・API）と連携する | local-server・keychain（鍵は保管庫・標準入力で渡す・時間切れ・料金の確認） |
| recipe-agent-mcp | AI からプラグインを操作できるようにする | mcp-bridge（登録・安全規約・パネルを開いておく） |
| recipe-clip-slots | クリップや効果をコピーして貼る | panel-commands・ppro-kit（メタデータだけ保存・取り直し・同じ取引で足したキーは単独で消せない） |
| recipe-caption-align | テロップをカットの境目にそろえる | panel・ppro-kit（グラフィックに setIn/setOut を使わない・許容フレーム） |
| recipe-razor-workarounds | 分割・速度変更などできない操作の代わりの手 | fcpxml（作り直し）・cep-helper（期限つき）・手作業・画面操作（Claude）。27.0 ベータの分割の API の扱い |

- [ ] **Step 1: サブエージェントに 2 バッチで書いてもらう**

8 件と 7 件に分け、2 本同時に走らせる。依頼文には共通の指示・本文の型（recipe）・担当の行・材料（core と features の知識の該当する id、調査 A §3.2、調査 F §5.8 のレシピの型）を入れる。「手順」はスキルの道具の実際のコマンド（`new_plugin.py --template …`、`add_part.py …`、`check.py …`、`logs.py …`）で書き、「確認」は利用者の Premiere で何を見ればよいか、「戻し方」は取り消しの回数を書く。

- [ ] **Step 2: 親が確かめる**

Run: `python3 SKILL/scripts/kb.py build && python3 SKILL/scripts/kb.py check && python3 -m unittest discover -s tests -t tests -p 'test_knowledge.py' -v`
Expected: 問題 0 件・PASS

- [ ] **Step 3: コミット**

```bash
git add -A
git commit -m "docs: 知識 recipes（要望の型ごとの作り方 15 件・前提→手順→確認→戻し方）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 28: 検索の評価表と、部品と知識の突き合わせ

**Files:**
- Create: `SKILL/knowledge/eval/search_eval.json`
- Modify: `SKILL/knowledge/synonyms.json`（評価が通るまで足す）
- Test: `tests/test_search_eval.py`、`tests/test_parts_knowledge.py`

**Interfaces:**
- 評価表の形: `{"cases": [{"query": "言い回し", "os": "mac" | "windows" | null, "expect": "id"}]}`
- 基準（成功の基準 S4）: 30 件すべてで、`expect` の id が `kb.search(..., limit=5)` の上位 5 件に入る

- [ ] **Step 1: 評価表を書く**

`SKILL/knowledge/eval/search_eval.json`:

```json
{
  "note": "成功の基準 S4。言い回しは視聴者が頼みそうな言葉。expect が上位 5 件に入ること。",
  "cases": [
    {"query": "選んだクリップにゆっくりズームを付けたい", "os": null, "expect": "recipe-keyframe-motion"},
    {"query": "無音の所を自動でカットしたい", "os": null, "expect": "recipe-silence-cut"},
    {"query": "文字起こしして字幕を作りたい", "os": null, "expect": "recipe-captions-srt"},
    {"query": "テロップのデザインを全部同じにしたい", "os": null, "expect": "recipe-telop-restyle"},
    {"query": "テロップの長さをカットの境目にそろえたい", "os": null, "expect": "recipe-caption-align"},
    {"query": "よく使うエフェクトをボタン一つで当てたい", "os": null, "expect": "recipe-batch-effect"},
    {"query": "ショートカットキーで実行したい", "os": "mac", "expect": "recipe-commands-shortcuts"},
    {"query": "エフェクトをコピーして他のクリップに貼りたい", "os": null, "expect": "recipe-clip-slots"},
    {"query": "マーカーからチャプター一覧を作りたい", "os": null, "expect": "recipe-markers-chapters"},
    {"query": "決まった設定でボタン一つで書き出したい", "os": null, "expect": "recipe-export-automation"},
    {"query": "素材のフォルダを読み込んでビンに整理したい", "os": null, "expect": "recipe-import-bins"},
    {"query": "話している人ごとにテロップのトラックを分けたい", "os": null, "expect": "feat-cutsrt-speaker"},
    {"query": "顔に合わせてスタンプを動かしたい", "os": null, "expect": "feat-cutsrt-direct-stamp"},
    {"query": "クリップを分割したい", "os": null, "expect": "recipe-razor-workarounds"},
    {"query": "再生速度を変えたい", "os": null, "expect": "core-capabilities"},
    {"query": "プラグインが Premiere に読み込まれない", "os": null, "expect": "core-dev-loop"},
    {"query": "The script object is no longer valid と出る", "os": null, "expect": "uc-uxp-action-outside-lock"},
    {"query": "一覧の行が重なって表示される", "os": null, "expect": "uc-ui-flex-rows-collapse"},
    {"query": "60fps なのに 30fps として扱われる", "os": null, "expect": "uc-fps-property-missing"},
    {"query": "XML を読み込んでも新しいシーケンスが出てこない", "os": null, "expect": "uc-xml-dangling-file"},
    {"query": "作り直して入れたのに古いまま", "os": null, "expect": "uc-install-same-version"},
    {"query": "Creative Cloud にサインインし直したらプラグインが消えた", "os": null, "expect": "uc-install-cc-signin-wipes"},
    {"query": "パネルから手元のサーバーにつながらない", "os": null, "expect": "uc-server-localhost-network-all"},
    {"query": "Windows で文字化けして止まる", "os": "windows", "expect": "uc-windows-cp932"},
    {"query": "キーフレームの補間がイーズにならない", "os": null, "expect": "uc-uxp-interp-same-transaction"},
    {"query": "日本語の Premiere で効果が付かない", "os": null, "expect": "uc-cep-qe-effect-locale"},
    {"query": "直したのに Premiere の動きが変わらない", "os": null, "expect": "uc-dev-edit-vs-runtime"},
    {"query": "Windows 版も作りたい", "os": "windows", "expect": "platform-windows"},
    {"query": "どの版から使える API か知りたい", "os": null, "expect": "core-versions"},
    {"query": "Premiere の操作を取り消し一回で戻したい", "os": null, "expect": "core-transactions"}
  ]
}
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_search_eval.py`:

```python
import json
import unittest

from helpers import KNOWLEDGE

import kb


class SearchEvalTests(unittest.TestCase):
    def test_expected_entry_is_in_top_5(self):
        cases = json.loads((KNOWLEDGE / "eval" / "search_eval.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(cases), 30)
        items = kb.load(KNOWLEDGE)
        synonyms = kb.load_synonyms(KNOWLEDGE)
        misses = []
        for c in cases:
            ids = [e["id"] for _, e in kb.search(items, c["query"], synonyms, os_name=c["os"], limit=5)]
            if c["expect"] not in ids:
                misses.append(f"{c['query']} → {ids}（期待 {c['expect']}）")
        self.assertEqual(misses, [], "\n".join(misses))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_parts_knowledge.py`:

```python
import unittest

from helpers import KNOWLEDGE, PARTS

import add_part
import kb


class PartsKnowledgeTests(unittest.TestCase):
    def test_every_knowledge_id_in_part_json_exists(self):
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        missing = []
        for name in add_part.list_parts(PARTS):
            for k in add_part.load_part(name, PARTS)["knowledge"]:
                if k not in ids:
                    missing.append(f"{name}: {k}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストを走らせ、外れを直す**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_search_eval.py' -v`
Expected: はじめは外れが出る。外れごとに、(1) 期待の知識の title・tags・summary に、利用者の言い回しの言葉が入っているか、(2) synonyms.json の組に足りない言い換えがないか、を見て直す。検索の規則（kb.py の点数）は、同じ直しで 3 件以上が通るときだけ変える（1 件のための調整はしない）。全部通るまで繰り返す。

Run: `python3 -m unittest discover -s tests -t tests -p 'test_parts_knowledge.py' -v`
Expected: PASS（足りない id があれば、その知識を書くか part.json を直す）

- [ ] **Step 4: コミット**

```bash
git add -A
git commit -m "test: 検索の評価表（30 件が上位 5 件に入る）と、部品と知識の突き合わせ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 6: 完成サンプル

完成サンプルは、キットの道具で作った作業フォルダそのもの（`new_plugin.py` と `add_part.py` で作り、index.html と index.js だけを書き足す）。見本であり、キットの通しのテストでもある。

### Task 29: 完成サンプル zoom-button（選んだクリップにゆっくりズーム）

**Files:**
- Create: `SKILL/examples/zoom-button/`（道具で作る）
- Modify: `SKILL/examples/zoom-button/index.html`（入力欄）、`SKILL/examples/zoom-button/index.js`（処理）
- Test: `tests/test_examples.py`、`tests/js/example_zoom.test.js`

**Interfaces:**
- Consumes: `PPM.getProjectAndSequence / getSelectedClips / findParam / getFrameRate / transact / keyframeActions / secondsOf`、`PPM.motion.bakeTrack`、`PPM.ui.*`
- Produces: `onRun()`（選んだ映像のクリップごとに、モーションのスケールへ `from`→`to` を `seconds` 秒で、bezier を焼いたキーを打つ。取引 1 回＝取り消し 1 回）

- [ ] **Step 1: 道具で作る**

```bash
S=plugins/premiere-plugin-maker/skills/premiere-plugin-maker
python3 $S/scripts/new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン" --author example --dest $S/examples/zoom-button
python3 $S/scripts/add_part.py motion-bake --project $S/examples/zoom-button
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_examples.py`（全部の完成サンプルが検査で誤り 0 件。サンプルが増えるたびに自動で対象になる）:

```python
import unittest

from helpers import EXAMPLES, SKILL

from lib import checks


class ExampleTests(unittest.TestCase):
    def test_every_example_passes_check(self):
        names = sorted(p.name for p in EXAMPLES.iterdir() if (p / "manifest.json").exists())
        self.assertTrue(names)
        for name in names:
            with self.subTest(example=name):
                errors = [f for f in checks.run_all(EXAMPLES / name, SKILL) if f.severity == "error"]
                self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
```

`tests/js/example_zoom.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/zoom-button");

function load() {
  const fake = makeFake();
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  const scripts = [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1]);
  for (const s of scripts) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  return { fake, el };
}

test("押すと、選んだ映像のクリップのスケールに焼いたキーを取引 1 回で打つ", async () => {
  const { fake, el } = load();
  // 入力欄はパネルが押されたときに初めて読むことがあるので、el() で作ってから値を入れる
  el("from").value = "100";
  el("to").value = "110";
  el("seconds").value = "2";
  await el("run").h.click();
  assert.equal(fake.log.transactions.length, 1);
  const keys = fake.log.actions.filter((a) => a.__action === "addKeyframe");
  assert.ok(keys.length > 2 * 30 * 2 * 0.9, `キーの数 ${keys.length}`);
  assert.equal(el("result").attrs["data-state"], "ok");
});
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `node --test tests/js/example_zoom.test.js`
Expected: FAIL（入力欄 `from` が無く、押しても雛形の確認だけで取引が 0 回）

- [ ] **Step 4: 画面と処理を書く**

`SKILL/examples/zoom-button/index.html` の `<section class="ppm-page" id="page-main">` の中身を次に置き換える（ほかの行と印は触らない）:

```html
        <p class="ppm-hint">タイムラインで映像のクリップを選んでから押してください。</p>
        <div class="ppm-row">
          <div class="ppm-field"><label class="ppm-label" for="from">始め（%）</label><input id="from" class="ppm-input" type="number" value="100" /></div>
          <div class="ppm-field"><label class="ppm-label" for="to">終わり（%）</label><input id="to" class="ppm-input" type="number" value="110" /></div>
          <div class="ppm-field"><label class="ppm-label" for="seconds">秒</label><input id="seconds" class="ppm-input" type="number" value="2" /></div>
        </div>
        <button id="run" class="ppm-btn ppm-btn-primary" type="button">ゆっくりズームを付ける</button>
        <div id="result" class="ppm-result" data-state="idle"></div>
```

`SKILL/examples/zoom-button/index.js` の `onRun` を次に置き換える（ほかは雛形のまま）:

```js
async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "付けています…");
  try {
    const { project, sequence } = await PPM.getProjectAndSequence();
    const clips = (await PPM.getSelectedClips(sequence)).filter((c) => c.kind === "video");
    if (clips.length === 0) {
      throw PPM.err("映像のクリップが選ばれていません", "ズームは映像のクリップに付けます", "タイムラインで映像のクリップを選んでから、もう一度押してください");
    }
    const from = PPM.ui.numberValue($("from"), 100);
    const to = PPM.ui.numberValue($("to"), 110);
    const seconds = Math.max(0.1, PPM.ui.numberValue($("seconds"), 2));
    const fr = await PPM.getFrameRate(sequence);
    if (!fr.detected) PPM.log.warn("フレームレートを読めないので 30 コマで焼きます", {});
    const frame = 1 / (fr.detected ? fr.fps : 30);
    const keys = PPM.motion.bakeTrack([{ t: 0, value: from, interp: "bezier" }, { t: seconds, value: to, interp: "linear" }], frame);
    // 非同期の取得（スケールの項目・入点）は取引の前に全部済ませる
    const targets = [];
    for (const c of clips) {
      const found = await PPM.findParam(c.item, ["AE.ADBE Motion"], ["Scale", "スケール"]);
      if (!found) { PPM.log.warn("スケールが見つかりません", { name: c.name }); continue; }
      targets.push({ param: found.param, inPoint: PPM.secondsOf(await c.item.getInPoint()) });
    }
    if (targets.length === 0) {
      throw PPM.err("スケールの項目が見つかりません", "モーションの「スケール」を探せませんでした", "診断を押して、表示を AI に伝えてください");
    }
    const result = PPM.transact(project, "ゆっくりズームを付ける", (add) => {
      for (const t of targets) PPM.keyframeActions(add, t.param, t.inPoint, keys);
    });
    PPM.ui.showOk(out, `${targets.length} 本に付けました（取り消しは Cmd+Z / Ctrl+Z を 1 回）`);
    PPM.log.info("zoom ok", { clips: targets.length, keys: keys.length, warnings: result.warnings });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("zoom failed", { message: String((e && e.message) || e) });
  } finally {
    PPM.ui.busy($("run"), false);
  }
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_examples.py' -v`
Expected: PASS

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 完成サンプル zoom-button（bezier を焼いたキーを取引 1 回で打つ）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 30: 完成サンプル silence-cut（無音カット）

**Files:**
- Create: `SKILL/examples/silence-cut/`（道具で作る）
- Modify: `SKILL/examples/silence-cut/index.html`、`SKILL/examples/silence-cut/index.js`
- Test: `tests/js/example_silence.test.js`

**Interfaces:**
- Consumes: `PPM.server.connect / runJob`、`PPM.fcpxml.exportActiveSequence / importAndOpen`
- Produces: `onRun()`（いまのシーケンスを XML に書き出し → サーバーで無音カット → 新しいシーケンスとして読み込んで開く。元のシーケンスは触らない）

- [ ] **Step 1: 道具で作る**

```bash
S=plugins/premiere-plugin-maker/skills/premiere-plugin-maker
python3 $S/scripts/new_plugin.py --template panel-server --name "Silence Cut" --label "無音カット" --author example --dest $S/examples/silence-cut
python3 $S/scripts/add_part.py silence-cut --project $S/examples/silence-cut
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/js/example_silence.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/silence-cut");

test("書き出し → silence_cut のジョブ → 読み込んで開く、の順に呼ぶ", async () => {
  const fake = makeFake();
  const order = [];
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  for (const s of [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1])) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  ctx.PPM.server.connect = async () => { order.push("connect"); return {}; };
  ctx.PPM.server.runJob = async (kind, params) => { order.push(`job:${kind}:${params.threshold}`); return { outputXml: "/tmp/out_カット済み.xml" }; };
  ctx.PPM.fcpxml.exportActiveSequence = async () => { order.push("export"); return "/tmp/in.xml"; };
  ctx.PPM.fcpxml.importAndOpen = async (p) => { order.push(`import:${p}`); return { name: "新しいシーケンス" }; };
  el("threshold").value = "-45";
  await el("run").h.click();
  assert.deepEqual(order, ["connect", "export", "job:silence_cut:-45", "import:/tmp/out_カット済み.xml"]);
  assert.equal(el("result").attrs["data-state"], "ok");
});
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `node --test tests/js/example_silence.test.js`
Expected: FAIL（入力欄 `threshold` が無い）

- [ ] **Step 4: 画面と処理を書く**

`index.html` の `<section class="ppm-page" id="page-main">` の中身:

```html
        <p class="ppm-hint">いま開いているシーケンスの無音を詰めて、新しいシーケンスを作ります（元のシーケンスは触りません）。</p>
        <div class="ppm-row">
          <div class="ppm-field"><label class="ppm-label" for="threshold">無音とみなす音量（dB）</label><input id="threshold" class="ppm-input" type="number" value="-48" /></div>
          <div class="ppm-field"><label class="ppm-label" for="minSilence">最小の無音（秒）</label><input id="minSilence" class="ppm-input" type="number" value="0.2" /></div>
          <div class="ppm-field"><label class="ppm-label" for="padding">前後に残す（コマ）</label><input id="padding" class="ppm-input" type="number" value="2" /></div>
        </div>
        <button id="run" class="ppm-btn ppm-btn-primary" type="button">無音をカットする</button>
        <div id="result" class="ppm-result" data-state="idle"></div>
```

`index.js` の `onRun`:

```js
async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "カットしています…");
  try {
    await PPM.server.connect({ tries: 2, intervalMs: 1000 });
    PPM.ui.showInfo(out, "シーケンスを書き出しています…");
    const xmlPath = await PPM.fcpxml.exportActiveSequence(`ppm-cut-${Date.now()}.xml`);
    const result = await PPM.server.runJob("silence_cut", {
      xmlPath,
      threshold: PPM.ui.numberValue($("threshold"), -48),
      minSilence: PPM.ui.numberValue($("minSilence"), 0.2),
      padding: Math.round(PPM.ui.numberValue($("padding"), 2)),
    }, { onProgress: (p, m) => PPM.ui.showInfo(out, `${m || "処理中"}（${p}%）`) });
    const seq = await PPM.fcpxml.importAndOpen(result.outputXml);
    PPM.ui.showOk(out, `カットした新しいシーケンス「${seq && seq.name ? seq.name : ""}」を開きました（元のシーケンスはそのままです）`);
    PPM.log.info("cut ok", { output: result.outputXml });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("cut failed", { message: String((e && e.message) || e) });
  } finally {
    PPM.ui.busy($("run"), false);
  }
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_examples.py' -v`
Expected: PASS

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 完成サンプル silence-cut（XML の往復で新しいシーケンスへ・元は触らない）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 31: 完成サンプル telop-restyle（テロップのデザインを一括で差し替え）

**Files:**
- Create: `SKILL/examples/telop-restyle/`（道具で作る）
- Modify: `SKILL/examples/telop-restyle/index.html`、`SKILL/examples/telop-restyle/index.js`
- Test: `tests/js/example_telop.test.js`

**Interfaces:**
- Consumes: `PPM.getSelectedClips`、`PPM.server.connect / runJob`、`PPM.fcpxml.exportActiveSequence`、`PPM.mogrt.replaceClip`
- Produces: `onRun()`（選んだテロップの本文を XML で読み → 選んだデザインで MOGRT を作り → 1 本ずつ差し替える。本文が読めないクリップ（テロップでない物）は飛ばして件数を出す）

- [ ] **Step 1: 道具で作る**

```bash
S=plugins/premiere-plugin-maker/skills/premiere-plugin-maker
python3 $S/scripts/new_plugin.py --template panel-server --name "Telop Restyle" --label "テロップ一括デザイン" --author example --dest $S/examples/telop-restyle
python3 $S/scripts/add_part.py mogrt-text --project $S/examples/telop-restyle
```

- [ ] **Step 2: 失敗するテストを書く**

`tests/js/example_telop.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/telop-restyle");

test("本文が読めたテロップだけを、選んだデザインで差し替える", async () => {
  const fake = makeFake();
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  for (const s of [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1])) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  const jobs = [];
  const replaced = [];
  ctx.PPM.server.connect = async () => ({});
  ctx.PPM.fcpxml.exportActiveSequence = async () => "/tmp/in.xml";
  ctx.PPM.server.runJob = async (kind, params) => {
    jobs.push({ kind, params });
    if (kind === "read_texts") return { texts: [{ text: "一つ目" }, { text: null }] };
    return { mogrts: params.items.map((it, i) => ({ text: it.text, path: `/tmp/${i}.mogrt` })), warnings: [] };
  };
  ctx.PPM.mogrt.replaceClip = async (project, sequence, clip, p) => { replaced.push(p); return { undoSteps: 2 }; };
  el("style").value = "yellow-red-white";
  await el("run").h.click();
  assert.deepEqual(jobs.map((j) => j.kind), ["read_texts", "build_mogrt"]);
  assert.equal(jobs[1].params.styleName, "yellow-red-white");
  assert.deepEqual(replaced, ["/tmp/0.mogrt"]);
  assert.match(el("result").textContent, /1 本を差し替え/);
  assert.match(el("result").textContent, /1 本は本文を読めず/);
});
```

- [ ] **Step 3: テストが落ちることを確かめる**

Run: `node --test tests/js/example_telop.test.js`
Expected: FAIL（`style` の選択欄が無い）

- [ ] **Step 4: 画面と処理を書く**

`index.html` の `<section class="ppm-page" id="page-main">` の中身:

```html
        <p class="ppm-hint">タイムラインでテロップ（グラフィック）を選び、デザインを選んで押してください。本文はそのまま、見た目だけ差し替えます。</p>
        <div class="ppm-field">
          <label class="ppm-label" for="style">デザイン</label>
          <select id="style" class="ppm-input">
            <option value="white-black">白文字 黒縁</option>
            <option value="yellow-red-white">黄文字 赤白二重縁</option>
            <option value="news-band">ニュース風の帯</option>
          </select>
        </div>
        <button id="run" class="ppm-btn ppm-btn-primary" type="button">選んだテロップに当てる</button>
        <div id="result" class="ppm-result" data-state="idle"></div>
```

`index.js` の `onRun`（`boot()` の中に `PPM.ui.protectSelect($("style"));` も足す）:

```js
async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "差し替えています…");
  try {
    const { project, sequence } = await PPM.getProjectAndSequence();
    const clips = (await PPM.getSelectedClips(sequence)).filter((c) => c.kind === "video");
    if (clips.length === 0) {
      throw PPM.err("テロップが選ばれていません", "選んだテロップの見た目を差し替えます", "タイムラインでテロップを選んでから、もう一度押してください");
    }
    await PPM.server.connect({ tries: 2, intervalMs: 1000 });
    PPM.ui.showInfo(out, "本文を読んでいます…");
    const xmlPath = await PPM.fcpxml.exportActiveSequence(`ppm-telop-${Date.now()}.xml`);
    const read = await PPM.server.runJob("read_texts", { xmlPath, clips: clips.map((c) => ({ trackIndex: c.trackIndex, startTicks: c.startTicks })) });
    const targets = clips.map((c, i) => ({ clip: c, text: read.texts[i] && read.texts[i].text })).filter((t) => t.text);
    const skipped = clips.length - targets.length;
    if (targets.length === 0) {
      throw PPM.err("本文を読めるテロップがありません", "選んだクリップがテロップ（グラフィック）ではないか、本文が空です", "テロップを選び直してください");
    }
    const built = await PPM.server.runJob("build_mogrt", {
      styleName: PPM.ui.textValue($("style")) || "white-black",
      items: targets.map((t) => ({ text: t.text, duration: t.clip.endSeconds - t.clip.startSeconds })),
    }, { onProgress: (p, m) => PPM.ui.showInfo(out, `${m || "作っています"}（${p}%）`) });
    let steps = 0;
    for (let i = 0; i < targets.length; i++) {
      const r = await PPM.mogrt.replaceClip(project, sequence, targets[i].clip, built.mogrts[i].path);
      steps += r.undoSteps;
    }
    const lines = [`${targets.length} 本を差し替えました（元に戻すには Cmd+Z / Ctrl+Z を ${steps} 回）`];
    if (skipped) lines.push(`${skipped} 本は本文を読めず、飛ばしました`);
    if (built.warnings && built.warnings.length) lines.push(...built.warnings);
    PPM.ui.showOk(out, lines.join("\n"));
    PPM.log.info("restyle ok", { replaced: targets.length, skipped, steps });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("restyle failed", { message: String((e && e.message) || e) });
  } finally {
    PPM.ui.busy($("run"), false);
  }
}
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `node --test tests/js/*.test.js && python3 -m unittest discover -s tests -t tests -p 'test_examples.py' -v`
Expected: PASS

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "feat: 完成サンプル telop-restyle（本文を XML で読み、MOGRT を作って 1 本ずつ差し替え）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 7: スキル本体と公開物

### Task 32: SKILL.md と Codex の表示

**Files:**
- Modify: `SKILL/SKILL.md`（仮のものを全文に置き換える）
- Create: `SKILL/agents/openai.yaml`
- Test: `tests/test_skill_md.py`

**Interfaces:**
- Consumes: Task 24〜27 の知識の id、Task 4〜14 の道具の名前

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_skill_md.py`:

```python
import re
import unittest

from helpers import KNOWLEDGE, SCRIPTS, SKILL

import kb


class SkillMdTests(unittest.TestCase):
    def setUp(self):
        self.text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_length_and_frontmatter(self):
        self.assertLessEqual(len(self.text.splitlines()), 200)
        head = self.text.split("---", 2)[1]
        self.assertIn("name: premiere-plugin-maker", head)
        desc = re.search(r"description: (.+)", head).group(1)
        self.assertGreater(len(desc), 60)
        for word in ("Premiere", "プラグイン", "Windows", "Mac", "必ず使う"):
            self.assertIn(word, desc)

    def test_first_question_and_bootstrap_for_both_os(self):
        self.assertIn("Windows と Mac のどちらですか", self.text)
        self.assertIn("git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker", self.text)
        self.assertIn("Invoke-WebRequest", self.text)
        self.assertIn("py -3", self.text)

    def test_no_fragile_root_variable_or_client_prefix(self):
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT:-", self.text)
        self.assertNotIn("mcp__", self.text)

    def test_every_script_and_knowledge_id_exists(self):
        for name in set(re.findall(r"([a-z_]+\.py)", self.text)):
            if name in ("install.py",):
                continue
            self.assertTrue((SCRIPTS / name).exists(), name)
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        for kid in set(re.findall(r"\b((?:core|recipe|ref|platform|feat|uc)-[a-z0-9-]+)\b", self.text)):
            self.assertIn(kid, ids, kid)

    def test_codex_yaml(self):
        y = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$premiere-plugin-maker", y)
        self.assertIn("allow_implicit_invocation: true", y)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_skill_md.py' -v`
Expected: FAIL（仮の SKILL.md に OS の質問が無い）

- [ ] **Step 3: SKILL.md と openai.yaml を書く**

`SKILL/SKILL.md`（全文）:

````markdown
---
name: premiere-plugin-maker
description: Premiere（Premiere Pro）用のプラグインを、要望を聞いて作るスキル。UXP のパネル・メニューのコマンド・手元のサーバーで重い処理・CEP 補助（再生・分割）・AI から操作する口まで作れる。「Premiere のプラグインを作りたい」「Premiere でボタン一つで〜したい」「Premiere の拡張機能」「UXP のパネル」「.ccx」「プラグインが読み込まれない・動かない」などでは、明示されていなくても必ず使う。Mac と Windows の両方に対応し、過去の機能・失敗事例・版の知識と部品・雛形・機械の検査を使い、Premiere で動くことを確かめてから完成とする。
---

# Premiere のプラグインを作る

このスキルのフォルダを `<SKILL>` と書く（Claude Code は冒頭の「Base directory for this skill」、Codex はスキル一覧に出るパス）。道具はいつも `<SKILL>/scripts/` から呼び、作業フォルダには写さない。

- Mac: `python3 <SKILL>/scripts/<道具>.py …`
- Windows: `py -3 <SKILL>\scripts\<道具>.py …`（py が無ければ `python`）

## 0. 毎回、最初に

1. **OS を聞く**: 「お使いのパソコンは Windows と Mac のどちらですか？」（依頼に書いてあれば聞かない）。以降のコマンドとパスは、その OS の形で出す。
2. **一式があるか見る**: `<SKILL>/scripts/doctor.py` が無ければ、「公開リポジトリから一式を取ってきます」と伝えてから取ってくる。
   - Mac: `git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker ~/.premiere-plugin-maker/kit`（git が無ければ `mkdir -p ~/.premiere-plugin-maker && curl -L https://github.com/fuuuuuuma/premiere-plugin-maker/archive/refs/heads/main.tar.gz | tar xz -C ~/.premiere-plugin-maker`）
   - Windows（PowerShell）: `git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker "$env:USERPROFILE\.premiere-plugin-maker\kit"`（git が無ければ `Invoke-WebRequest https://github.com/fuuuuuuma/premiere-plugin-maker/archive/refs/heads/main.zip -OutFile "$env:TEMP\ppm.zip"; Expand-Archive "$env:TEMP\ppm.zip" "$env:USERPROFILE\.premiere-plugin-maker"`）
   - 以降の `<SKILL>` は、取ってきた場所の `plugins/premiere-plugin-maker/skills/premiere-plugin-maker`。
3. **診断**: `doctor.py --online`。`[NG!]` は直し方を 1 つずつ案内し、入れてよいか聞いてから進む。Premiere・Creative Cloud・UXP Developer Tools は利用者に入れてもらう。

## 1. 聞き取り（1 回に 1 問・選択肢つき）

1. 何をしたいか（1 文で）
2. 何に対してか（選んだクリップ／シーケンス全体／プロジェクトの素材／マーカー／書き出し）
3. どう動かすか（パネルのボタン／メニューのコマンド／キーの割り当て）
4. 結果（タイムラインが変わる／ファイルができる／見るだけ）
5. 重い処理があるか（音声の解析・文字起こし・AI・ファイルの生成）
6. 誰が使うか（自分だけ／ほかの人にも配る）

## 2. 知識を引く

- `kb.py search <要望の言葉> --os <mac か windows>` を実行し、上位を `kb.py show <id>` で読む。
- 結果が薄ければ `kb.py list --brief` を読み、意味で選ぶ。
- status が verified の知識を優先する。unverified の知識を使うときは「未確認です」と伝え、診断ボタンで確かめてから採用する。superseded は使わない。
- 部品がある機能は部品を使う。部品が無い機能（話者の振り分け・顔の追従など）は、features の記録を元に部品を組み合わせて作る。

## 3. できるかを判定

- `kb.py show core-capabilities` の表に当てる。できない操作（分割・速度の変更・字幕の本文の書き換え・プログラムモニターの再生など）は、そう伝えて代わりの手から選んでもらう。確かめていない抜け道を「動く」と言わない。
- 使う API の最低版は `core-versions` で確かめる（check.py の J014 も止める）。

## 4. 計画を見せて承認をもらう

作業フォルダに `plan.md` を書く。作るもの・雛形・部品・最低版・権限・確かめ方・できないことを平易な言葉で見せ、承認をもらってから作る。

## 5. 作る

1. 雛形を選ぶ（`kb.py show core-intake`）: panel／panel-commands／panel-server／cep-helper（上級・期限つき・Mac だけ）。一覧は `new_plugin.py --list`。
2. `new_plugin.py --template <雛形> --name "<英字の名前>" --label "<表示名>"`。既定の場所は Mac `~/PremierePlugins/<名前>`、Windows `%USERPROFILE%\PremierePlugins\<名前>`。既にあれば上書きしない。
3. 部品を足す: `add_part.py <部品> --project <作業フォルダ>`（一覧は `add_part.py --list`）。
4. `index.js` の `onRun` に処理を書く。型は `core-api-patterns` と `core-transactions`（取引の中で await しない・Action は取引の中で作る・戻り値を見る・1 回の取引で取り消し 1 回）。
5. `check.py <作業フォルダ>` の誤りが 0 件になるまで直す。注意は理由を読んで判断する。
6. サーバーの部品を使うなら、依存（Python の部品・モデル）を入れる前に、何をどれくらい入れるかを見せて許可を取る。

## 6. Premiere で確かめる（ここを通るまで完成と言わない）

1. 読み込み: UXP Developer Tools の［Add Plugin］で `manifest.json` を選び［Load］。直したら［Reload］、manifest を変えたら［Unload］→［Load］。開発者モードは UDT 側と Premiere 側（［設定］→［プラグイン］→ Premiere の再起動）の両方が要る（`core-dev-loop`）。
2. サーバーがあれば入れる: Mac は `server/install_mac.command`、Windows は `server\install_windows.bat`（`ref-local-server`）。
3. パネルの「診断」を押してもらい、`logs.py --project <作業フォルダ>` で結果を読む。使う API が missing なら、実装する前に手を変える。
4. 試してほしい操作は 1 回に 1 つ。結果を聞き、ログを読んでから次へ進む。
5. 見た目はコマの書き出し（`PPM.exportFrame`）か画面写真で確かめる。取り消し（Cmd+Z / Ctrl+Z）で戻ることも確かめる。

## 7. 直す・手元に残す

新しく分かったこと（新しい失敗と直し方など）は `kb.py note --title "…" --tags "…" --body "…"` で手元に残す。次回からの検索に出る。

## 8. 配る（ほかの人にも使ってもらうとき）

1. 版数を上げる。manifest と build_info を同じ版にする（`core-versioning-release`）。
2. `make_ccx.py <作業フォルダ> --bundle` で `dist/<名前>_v<版>/` を作る（.ccx・はじめにお読みください・サーバーの zip）。
3. 入れ直して確かめる: `install_ccx.py --reinstall <ccx のパス>`（既定は試し実行。実行は `--apply` を付ける）。
4. Adobe の Marketplace に出すなら、審査の条件を案内する（`core-versioning-release`）。

## 守ること

- 利用者のプロジェクトと素材を上書きしない。一括の変更の前は保存を勧め、件数を伝えて確認する（`core-safety`）。
- Premiere を変える処理は、取り消し 1 回で戻る作りを基本にする（`PPM.transact`）。
- 権限は最小にする。ネットに出る機能は相手先を示して同意を取る。鍵は OS の保管庫に置く（部品 keychain）。
- インストール・ダウンロード・課金・外部への送信・公開、CEP の PlayerDebugMode の設定、MCP の登録は、実行の前に許可を取る。
- 確かめていないことを「動きます」と言わない。未確認は未確認と書く（`core-verification`）。
- 他人のテンプレートや有料素材を写さない。Adobe の配布物（CSInterface.js・Basic Title.mogrt）を作業フォルダや配布物に入れない。

## いつ何を読むか

| こんなとき | 読む知識 |
|---|---|
| 何ができて何ができないか | core-capabilities |
| 版と最低版 | core-versions |
| 取引・取り消し | core-transactions |
| API の書き方 | core-api-patterns |
| 画面が崩れる | core-ui-rules |
| 権限 | core-manifest-permissions |
| 読み込めない・つながらない | core-dev-loop |
| 確かめ方 | core-verification |
| Windows で作る・配る | platform-windows・platform-cross |
| Mac で作る・配る | platform-mac |
| 時間・XML | ref-ticktime・ref-fcp7-xml |
| テロップ・MOGRT | ref-mogrt・ref-prtextstyle・recipe-telop-restyle |
| キー・補間 | ref-keyframe-interpolation・recipe-keyframe-motion |
| 重い処理・サーバー | ref-local-server・recipe-local-server-heavy |
| 再生・分割（CEP） | ref-cep-extendscript・recipe-razor-workarounds |
| AI から操作 | ref-mcp・recipe-agent-mcp |
| 配る | core-versioning-release |

## 終わりの報告の型

1. 何を作ったか（1 文）と作業フォルダの場所
2. Premiere で確かめたこと／まだ確かめていないこと
3. 使い方（ボタン・取り消しの回数）
4. 次にしてほしいこと（あれば 1 つ）
````

`SKILL/agents/openai.yaml`:

```yaml
interface:
  display_name: "Premiere Plugin Maker"
  short_description: "要望を聞いて Premiere のプラグインを作る（Mac / Windows）"
  brand_color: "#2B5BD7"
  default_prompt: "Use $premiere-plugin-maker to 要望を聞いて Premiere のプラグインを作ってください。"
policy:
  allow_implicit_invocation: true
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_skill_md.py' -v && python3 -m unittest discover -s tests -t tests -p 'test_package.py' -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add -A
git commit -m "docs: SKILL.md（OS を先に聞く・一式の取得・診断・聞き取り・知識・判定・計画・作る・確かめる・配る）と Codex の表示

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 33: README・導入用の文・保守の手引き・CI

**Files:**
- Modify: `README.md`、`CHANGELOG.md`
- Create: `docs/prompts-ja.md`、`docs/maintenance.md`
- Create: `.github/ISSUE_TEMPLATE/knowledge.md`、`.github/workflows/ci.yml`
- Test: `tests/test_docs.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_docs.py`:

```python
import re
import unittest

from helpers import REPO


class DocsTests(unittest.TestCase):
    def test_readme_has_install_for_both_clients_and_scope(self):
        t = (REPO / "README.md").read_text(encoding="utf-8")
        for s in ("claude plugin marketplace add fuuuuuuma/premiere-plugin-maker",
                  "claude plugin install premiere-plugin-maker@premiere-plugin-maker",
                  "codex plugin marketplace add fuuuuuuma/premiere-plugin-maker",
                  "codex plugin add premiere-plugin-maker@premiere-plugin-maker",
                  "## できないこと", "## 確かめた範囲", "## ライセンス"):
            self.assertIn(s, t)

    def test_internal_links_exist(self):
        for doc in [REPO / "README.md", REPO / "docs" / "prompts-ja.md", REPO / "docs" / "maintenance.md"]:
            for link in re.findall(r"\]\(([^)#]+)\)", doc.read_text(encoding="utf-8")):
                if link.startswith("http"):
                    continue
                self.assertTrue((doc.parent / link).exists(), f"{doc.name}: {link}")

    def test_ci_runs_on_mac_and_windows(self):
        ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("macos-latest", ci)
        self.assertIn("windows-latest", ci)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_docs.py' -v`
Expected: FAIL（README が仮のまま）

- [ ] **Step 3: 文書を書く**

`README.md`:

````markdown
# premiere-plugin-maker

AI（Claude Code / Codex）に頼むだけで、Premiere 用のプラグインを作れるスキルです。要望を聞き取り、これまでのプラグイン作りで分かった知識・失敗事例・部品を使って組み立て、Premiere で動くことを確かめてから完成にします。

- Mac と Windows の両方に対応（最初にどちらかを聞きます）
- パネルのボタン・メニューのコマンド・手元のサーバーでの重い処理（無音カット・文字起こし・テロップの生成）・CEP 補助（再生・分割）・AI から操作する口まで
- 作った物は機械の検査（過去に実機で起きた失敗の型）を通してから、Premiere で確かめます
- 配る準備（.ccx と「はじめにお読みください」）までできます

これは Adobe の公式のものではありません。

## 入れ方

Claude Code:

```bash
claude plugin marketplace add fuuuuuuma/premiere-plugin-maker
claude plugin install premiere-plugin-maker@premiere-plugin-maker
```

Codex:

```bash
codex plugin marketplace add fuuuuuuma/premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

入れた後は、新しいセッション（新しいタスク）で使えます。ターミナルを使わない人は、[導入用の文](docs/prompts-ja.md) をデスクトップアプリに貼ってください。

## 頼み方の例

> Premiere で、選んだクリップにボタン一つでゆっくりズームを付けるプラグインを作りたい

> 無音の所を自動でカットするパネルを作って（Windows です）

> 作ったプラグインが Premiere に出てこないので見てほしい

## 必要なもの

| もの | 必須か | 入れ方 |
|---|---|---|
| Premiere 25.6 以降（推奨 26.x） | 必須 | Creative Cloud デスクトップ |
| UXP Developer Tools | 必須（作っている間） | Creative Cloud デスクトップ →［すべてのアプリ］ |
| Python 3.9 以上 | 必須（スキルの道具） | Mac: 入っていなければ python.org、Windows: Python install manager |
| ffmpeg | 音声を扱うとき | Mac: `brew install ffmpeg`、Windows: `winget install --id Gyan.FFmpeg -e` |
| mlx-whisper / faster-whisper | 文字起こしをするとき | 使うときにスキルが案内します（入れる前に確認します） |

スキルは、これらを勝手には入れません。足りない物は、入れ方を見せて確認してから進みます。

## できないこと

Premiere の UXP の API に無い操作は作れません。代わりの手（FCP XML の作り直し・CEP 補助・手作業）を提案します。

- クリップの分割（CEP 補助で試せますが期限つき・Mac だけ）
- 再生速度の変更、字幕（キャプション）の本文の書き換え
- プログラムモニターの再生（CEP 補助で可能）、メニューのコマンドの実行
- Premiere のキーボードショートカットへの割り当て（Mac はシステム設定で可能）
- C++ を使うプラグイン（Hybrid）

## 確かめた範囲

- 道具のテスト: macOS と Windows（GitHub Actions）
- Premiere の実機: Mac の Premiere 26.5.2 で、完成サンプル 3 本（ズーム・無音カット・テロップの差し替え）を確認
- Windows の Premiere の実機では確かめていません。手順と検査は Windows 向けにも用意してあり、確かめていない所は知識に「未確認」と書いてあります

## 中身

- `plugins/premiere-plugin-maker/skills/premiere-plugin-maker/SKILL.md` — 手順
- `knowledge/` — 知識の棚（版・API の型・失敗事例・過去の機能の記録・OS の違い）
- `parts/` — 部品、`templates/` — 雛形、`examples/` — 完成サンプル、`scripts/` — 道具（Python の標準ライブラリだけ）

## 更新のしかた

```bash
claude plugin marketplace update premiere-plugin-maker
claude plugin update premiere-plugin-maker@premiere-plugin-maker
```

```bash
codex plugin marketplace upgrade premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

## ライセンス

MIT（[LICENSE](LICENSE)）。Adobe の配布物（CSInterface.js・Premiere の中の Basic Title.mogrt など）は同梱していません。MOGRT の生成は、利用者の Premiere の中にある Basic Title.mogrt を使います。
````

`docs/prompts-ja.md`:

````markdown
# デスクトップアプリに貼る文

## 入れる（Claude Code のデスクトップアプリ）

```
このプラグインを入れてください。終わったら、入ったかどうかを確かめて教えてください。
claude plugin marketplace add fuuuuuuma/premiere-plugin-maker
claude plugin install premiere-plugin-maker@premiere-plugin-maker
```

## 入れる（Codex のデスクトップアプリ）

```
このプラグインを入れてください。終わったら、入ったかどうかを確かめて教えてください。
codex plugin marketplace add fuuuuuuma/premiere-plugin-maker
codex plugin add premiere-plugin-maker@premiere-plugin-maker
```

## 作る（入れた後、新しいセッションで）

```
premiere-plugin-maker を使って、Premiere のプラグインを作りたいです。
作りたいもの: （例: 選んだクリップにボタン一つでゆっくりズームを付ける）
```
````

`docs/maintenance.md`:

```markdown
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
```

`.github/ISSUE_TEMPLATE/knowledge.md`:

```markdown
---
name: 知識の追加（新しい失敗と直し方）
about: プラグインを作っていて新しく分かったことを送る
---

名前・個人のパス・鍵・取引先の情報は書かないでください。

- 症状（何が起きたか）:
- 原因（分かれば）:
- 直し方:
- OS（Mac / Windows）と Premiere の版:
- どうやって確かめたか（実機で動いた・ログで見た・未確認）:
```

`.github/workflows/ci.yml`:

```yaml
name: tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Python tests
        run: python -m unittest discover -s tests -t tests -v
        env:
          PYTHONUTF8: "1"
      - name: JS tests
        shell: bash
        run: node --test tests/js/*.test.js
```

`CHANGELOG.md` の 0.1.0 の行を、入れた中身の要約（道具・部品・雛形・知識・サンプル）に書き直す。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_docs.py' -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add -A
git commit -m "docs: README・導入用の文・保守の手引き・知識の報告のひな形・CI（macOS / Windows）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 34: 公開物の衛生検査と、最後の機械の確認（成功の基準 S6）

**Files:**
- Create: `tests/test_hygiene.py`
- Create: `tests/local_denylist.txt`（git に入れない）
- Modify: `.gitignore`（`tests/local_denylist.txt` を足す）
- Modify: `docs/superpowers/specs/…design.md`、`docs/superpowers/plans/….md`（写しの個人のパスと調査資料のパスを置き換える）

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_hygiene.py`:

```python
import subprocess
import unittest
from pathlib import Path

from helpers import REPO

from lib import privacy

TEXT = {".md", ".py", ".js", ".json", ".html", ".css", ".txt", ".yml", ".yaml", ".xml", ".jsx", ".ps1", ".bat", ".command", ".sh", ".template", ".plist"}
FORBIDDEN_NAMES = {"CSInterface.js", "Basic Title.mogrt"}
FORBIDDEN_SUFFIXES = {".mogrt", ".prproj", ".aep", ".mp4", ".mov", ".wav", ".mp3", ".ttf", ".otf", ".zip", ".ccx", ".pyc"}
MAX_BYTES = 2_000_000


def tracked():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout.decode("utf-8")
        return [REPO / p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts]


class HygieneTests(unittest.TestCase):
    def test_no_personal_paths_or_tokens(self):
        bad = []
        for p in tracked():
            if p.suffix.lower() in TEXT:
                t = p.read_text(encoding="utf-8", errors="replace")
                bad += [f"{p.relative_to(REPO)}:{ln} {s}" for ln, s in privacy.personal_paths(t) + privacy.token_like(t)]
        self.assertEqual(bad, [])

    def test_no_denylisted_names(self):
        deny = REPO / "tests" / "local_denylist.txt"
        if not deny.exists():
            self.skipTest("tests/local_denylist.txt が無い（公開前は必ず置いて走らせる）")
        words = [w.strip() for w in deny.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]
        bad = []
        for p in tracked():
            if p.suffix.lower() in TEXT and p.name != "local_denylist.txt":
                t = p.read_text(encoding="utf-8", errors="replace")
                bad += [f"{p.relative_to(REPO)}: {w}" for w in words if w in t]
        self.assertEqual(bad, [])

    def test_no_adobe_files_media_or_big_files(self):
        bad = []
        for p in tracked():
            if p.name in FORBIDDEN_NAMES or p.suffix.lower() in FORBIDDEN_SUFFIXES or p.stat().st_size > MAX_BYTES:
                bad.append(str(p.relative_to(REPO)))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
```

`tests/local_denylist.txt`（git に入れない。公開してはいけない語を 1 行ずつ。中身は `~/.claude/projects/<記憶のフォルダ>/memory/` の記憶から、利用者・視聴者・出演者・取引先の名前、チャンネル名、個人のユーザー名を拾って書く）:

```
# 公開物に入れてはいけない語（このファイルは git に入れない）
<ユーザー名>
（以下、記憶から拾った名前とチャンネル名を 1 行ずつ）
```

`.gitignore` に足す:

```
tests/local_denylist.txt
```

- [ ] **Step 2: テストを走らせ、引っかかった所を直す**

Run: `python3 -m unittest discover -s tests -t tests -p 'test_hygiene.py' -v`
Expected: はじめは docs の写しの個人のパスで落ちる。次で置き換える:

```bash
python3 - <<'EOF'
import re, pathlib
for p in list(pathlib.Path("docs/superpowers").rglob("*.md")):
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"（作業用の調査資料。公開物では省略）`)]+", "（作業用の調査資料。公開物では省略）", t)
    t = t.replace("<作業場所>/", "<作業場所>/")
    t = t.replace("~/", "~/")
    t = t.replace("<記憶のフォルダ>", "<記憶のフォルダ>")
    t = t.replace("<ユーザー名>", "<ユーザー名>")
    for name in ("作者", "作者", "作者"):
        t = t.replace(name, "作者")
    p.write_text(t, encoding="utf-8")
EOF
```

ほかに引っかかった所（知識・部品）は、その文を書き直す（名前を「利用者」に、パスを `~/` に）。

- [ ] **Step 3: 全部の確認**

Run（どれも、このワークツリーの premiere-plugin-maker のフォルダで）:

```bash
python3 -m unittest discover -s tests -t tests -v
node --test tests/js/*.test.js
python3 plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts/kb.py check
claude plugin validate . --strict
for ex in zoom-button silence-cut telop-restyle; do python3 plugins/premiere-plugin-maker/skills/premiere-plugin-maker/scripts/check.py plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/$ex || exit 1; done
```

Expected: 全部 PASS・`問題はありません。`・`Validation passed`・3 本とも `誤り 0 件`。結果（件数）を作業メモに貼る。

- [ ] **Step 4: コミット**

```bash
git add -A
git commit -m "test: 公開物の衛生検査（個人のパス・鍵・名前・Adobe の配布物・大きなファイル）と写しの置き換え

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Phase 8: 確かめる

### Task 35: 視聴者役のリハーサル（成功の基準 S1）

**Files:**
- Create: `docs/rehearsal-2026-10.md`（リハーサルの記録。名前は書かない）
- Modify: つまずいた所の SKILL.md・知識・道具（その都度）

**Interfaces:**
- リハーサルは 6 本。1 本ごとに 1 体のサブエージェント（`model: sonnet`）が「利用者の役（下の台本どおりに答える）」と「作り手の役（SKILL.md のとおりに進める）」を両方受け持つ。同時に走らせるのは 2 本まで（3 回に分ける）

| # | OS | 頼み（設計書 §13.2） | 利用者の台本（聞かれたら答える） |
|---|---|---|---|
| R1 | Mac | 選んだクリップにゆっくりズームインを付けたい | 選んだクリップ／パネルのボタン／タイムラインが変わる／重い処理なし／自分だけ |
| R2 | Mac | 無音の所を自動でカットしたい | シーケンス全体／ボタン／新しいシーケンス／重い処理あり（音声）／自分だけ |
| R3 | Mac | 話している人ごとにテロップのトラックを分けたい | 選んだテロップ／ボタン／タイムラインが変わる／重い処理あり（AI 可）／自分だけ |
| R4 | Windows | よく使う効果をボタン 1 つで当てたい／ショートカットにしたい | 選んだクリップ／メニューのコマンド／タイムラインが変わる／なし／チームに配る |
| R5 | Windows | マーカーからチャプター一覧を作って、YouTube の概要欄に貼りたい | マーカー／ボタン／ファイルができる（文字）／なし／自分だけ |
| R6 | Windows | クリップを分割したい | 選んだクリップ／ボタン／タイムラインが変わる／なし／自分だけ |

- [ ] **Step 1: 依頼文を作る（6 本で共通の形）**

```
あなたは 2 役を受け持ちます。
(1) 作り手: 次のスキルの手順書をそのまま守って進めます: <リポジトリ>/plugins/premiere-plugin-maker/skills/premiere-plugin-maker/SKILL.md
    道具はそのスキルのフォルダの scripts/ から呼びます。作業フォルダは <一時フォルダ> の中に作ります。
(2) 利用者: 作り手から質問されたら、下の台本だけで答えます。台本に無いことは「おまかせします」と答えます。
    利用者の OS: <Mac か Windows>。頼み: 「<頼み>」。台本: <台本>
決まり:
- Windows の想定のときは、この Mac で Windows のコマンドを実行しません。作り手が出した Windows 向けの案内（コマンド・パス）を文章として残し、正しいかを最後に自分で点検します。道具は Mac のコマンドで動かしてかまいません。
- Premiere・UDT は動かしません。手順の「Premiere で確かめる」は、利用者に頼む文面を作るところまでにし、「未確認」と書きます。
- 何もインストールしません。ネットにもつなぎません（doctor.py は --online を付けずに実行）。
- 最後に次を報告します: (a) SKILL.md のどの手順で迷ったか・足りなかったか（行の番号つき）、(b) 引いた知識の id と、役に立ったか、(c) check.py の結果（誤り・注意の件数）、(d) 道具のエラー（全文）、(e) 作り手が「完成」と言わずに止まれたか、(f) Windows の想定なら、出した Windows の案内の誤り。
```

- [ ] **Step 2: 3 回に分けて走らせる**

R1・R4 → R2・R5 → R3・R6 の順に、2 本ずつ。

- [ ] **Step 3: 合格の基準で判定し、直す**

1 本ごとの合格: OS を最初に聞いた／計画を見せて承認を待った／check.py の誤り 0 件／「完成」と言わずに Premiere での確認を頼んだ／Windows の案内に誤りが無い／R6 は「分割は API に無い」と伝えて代わりの手を出した。落ちた本は、原因を SKILL.md・知識・道具のどれかで直し、その本だけもう一度走らせる。全部が合格するまで続ける。

- [ ] **Step 4: 記録とコミット**

`docs/rehearsal-2026-10.md` に、6 本の結果（合格・直した所・直したファイル）を書く。

```bash
git add -A
git commit -m "docs: 視聴者役のリハーサル 6 本（Mac 3・Windows 3）の結果と直し

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 36: Premiere の実機での確認（成功の基準 S2）— 利用者の許可が要る

**Files:**
- Modify: `SKILL/parts/*/part.json` の `status`、関係する知識の `status`（結果に合わせる）
- Create: 実機で新しく分かった知識（usecases）
- Create: `docs/device-check-2026-10.md`（確認の記録）

- [ ] **Step 1: 許可をもらう（AskUserQuestion で 1 問）**

聞くこと: 「この Mac の Premiere 26.5.2 で、完成サンプル 3 本を入れて試してよいですか？ 試すのは、使い捨てのテスト用のプロジェクト（合成した映像と音声を読み込んだもの）だけで、ふだんのプロジェクトには触りません。サーバーの常駐（launchd）を 1 つ足し、終わったら外します。」選択肢: 「試してよい（Recommended）」「今はしない」。

- [ ] **Step 2: テスト用の素材を作る**

```bash
mkdir -p ~/PremierePlugins/_test-media
ffmpeg -nostdin -v error -f lavfi -i "testsrc2=size=1920x1080:rate=30" -f lavfi -i "sine=frequency=440:sample_rate=48000" -filter_complex "[1:a]volume='if(between(t,2,3),0.002,1)':eval=frame[a]" -map 0:v -map "[a]" -t 6 -c:v libx264 -pix_fmt yuv420p -c:a aac ~/PremierePlugins/_test-media/test_talk.mp4
```

利用者に頼む（1 回に 1 つ）: 「Premiere で新しいプロジェクトを作り、`~/PremierePlugins/_test-media/test_talk.mp4` を読み込んで、それでシーケンスを作ってください。終わったら教えてください。」

- [ ] **Step 3: .ccx を作って入れる（UDT を使わない入れ方の確認も兼ねる）**

```bash
S=plugins/premiere-plugin-maker/skills/premiere-plugin-maker
for ex in zoom-button silence-cut telop-restyle; do python3 $S/scripts/make_ccx.py $S/examples/$ex; done
for ex in zoom-button silence-cut telop-restyle; do python3 $S/scripts/install_ccx.py --reinstall "$(ls $S/examples/$ex/dist/*.ccx)" --apply; done
```

サーバー（silence-cut と telop-restyle は同じ部品だが、アプリの名前が別なので 2 つ）を入れる。依存の numpy は、この Mac の python3 に入っているか `python3 -c "import numpy"` で確かめ、無ければ利用者に聞いてから `--with-deps` を付ける:

```bash
python3 $S/examples/silence-cut/server/install.py
python3 $S/examples/telop-restyle/server/install.py
```

- [ ] **Step 4: 1 本ずつ確かめる（利用者に 1 回に 1 つ頼み、ログで確かめる）**

| サンプル | 利用者に頼むこと | AI が確かめること |
|---|---|---|
| zoom-button | ［ウィンドウ］→［UXP プラグイン］→「ズームボタン」を開き、「診断」→ クリップを選んで「ゆっくりズームを付ける」→ Cmd+Z を 1 回 | `logs.py --project …zoom-button` に `zoom ok` とキーの数。診断の missing が無い。取り消しで戻ったかを利用者に聞く |
| silence-cut | 「無音カット」を開き「無音をカットする」 | ログに `cut ok`。新しいシーケンスの長さが約 5 秒（2〜3 秒の静かな所が詰まる）。元のシーケンスがそのまま |
| telop-restyle | テキストのテロップを 1 つ置いて選び、「黄文字 赤白二重縁」で「選んだテロップに当てる」→ 表示された回数だけ Cmd+Z | ログに `restyle ok`。テロップの本文が同じで見た目が変わったかを利用者に聞く（画面写真を頼んでもよい） |

失敗したら、`kb.py search <症状>` で知識を引き、原因を直して作り直す（make_ccx → install_ccx --reinstall）。新しく分かったことは usecases に足す。

- [ ] **Step 5: 片付けと状態の反映**

```bash
for ex in zoom-button silence-cut telop-restyle; do python3 $S/scripts/install_ccx.py --remove "$(python3 -c "import json;print(json.load(open('$S/examples/$ex/manifest.json'))['name'])")" --apply; done
python3 $S/examples/silence-cut/server/install.py --uninstall
python3 $S/examples/telop-restyle/server/install.py --uninstall
```

（片付けの前に利用者に「外してよいですか」と聞く。テスト用のプロジェクトは利用者に閉じてもらう）

実機で動いた部品の `status` を `verified` に、一部だけ（Mac だけ）なら `partial` にする。関係する知識の `status` も同じく直し、`kb.py build && kb.py check`。`docs/device-check-2026-10.md` に、日付・Premiere の版・3 本の結果・直した所を書く。

- [ ] **Step 6: コミット**

`/verify` を実行してから:

```bash
git add -A
git commit -m "test: Premiere 26.5.2（Mac）の実機で完成サンプル 3 本を確認し、部品と知識の状態を反映

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 37: 公開（成功の基準 S3・S5）— 利用者の確認が要る

- [ ] **Step 1: 公開の前の確認をもらう（AskUserQuestion で 1 問）**

見せること: 公開先 `github.com/fuuuuuuma/premiere-plugin-maker`（public・MIT）、入る物の一覧（`git ls-files` の要約）、衛生検査の結果、確かめた範囲。選択肢: 「公開する」「まだしない」。

- [ ] **Step 2: 公開する**

```bash
gh repo create fuuuuuuma/premiere-plugin-maker --public --description "要望を聞いて Premiere 用のプラグインを作るスキル（Claude Code / Codex・Mac / Windows）" --source . --remote origin --push
```

- [ ] **Step 3: CI を確かめる**

Run: `gh run list --repo fuuuuuuma/premiere-plugin-maker --limit 1` → 終わったら `gh run view <id> --repo fuuuuuuma/premiere-plugin-maker`
Expected: macos-latest・windows-latest とも成功。Windows だけ落ちたら、落ちたテストを直して push し直す（Windows の知見として usecases に足す）。

- [ ] **Step 4: 隔離した設定で入れてみる**

```bash
T=$(mktemp -d)
CLAUDE_CONFIG_DIR="$T/claude" claude plugin marketplace add fuuuuuuma/premiere-plugin-maker
CLAUDE_CONFIG_DIR="$T/claude" claude plugin install premiere-plugin-maker@premiere-plugin-maker
CLAUDE_CONFIG_DIR="$T/claude" claude plugin list
CODEX_HOME="$T/codex" codex plugin marketplace add fuuuuuuma/premiere-plugin-maker
CODEX_HOME="$T/codex" codex plugin add premiere-plugin-maker@premiere-plugin-maker
CODEX_HOME="$T/codex" codex plugin list
```

Expected: どちらにも `premiere-plugin-maker` が installed / enabled で出る。入った先のフォルダに `SKILL.md` `knowledge/` `parts/` `scripts/` があり、`tests/` と `README.md` は入っていない。

- [ ] **Step 5: 報告**

公開したリポジトリの URL を、単独の行で利用者に伝える。CI の結果と、隔離した設定での導入の結果も添える。

---

### Task 38: 記憶と引き継ぎ

- [ ] **Step 1: 記憶を書く**

`~/.claude/projects/<記憶のフォルダ>/memory/project_premiere_plugin_maker.md` を作る（形は記憶の決まりどおり）。中身: 何のスキルか（1 行）／場所（このワークツリーの `projects/常時運用/premiere-plugin-maker/`、独立した git、公開したなら URL）／版／確かめた範囲（Mac 実機・Windows 未確認）／次にすること（27.0 の正式版で分割の API を確かめる、Windows の利用者の報告を知識に反映）／**ワークツリーを片付ける前に、公開済みか git bundle の控えがあるかを確かめる**。

`MEMORY.md` の「動画編集・Premiere」の節に 1 行足す:

```
- [Premiere プラグインを作るスキル](project_premiere_plugin_maker.md) — premiere-plugin-maker。知識の棚＋部品＋雛形＋機械の検査。Mac 実機確認・Windows は手順のみ
```

- [ ] **Step 2: 控え（公開していない場合だけ）**

```bash
git bundle create ~/Codex/outputs/premiere-plugin-maker-$(date +%Y%m%d).bundle --all
```

- [ ] **Step 3: 中間ファイルの片付け**

リハーサルや実機確認で作った `.dump.txt` `.review.txt` などの中間ファイルを消す（キャッシュは残す）。テスト用の素材 `~/PremierePlugins/_test-media/` は、利用者に聞いてから消す。

---

## 実施メモ（進める側が書き足す）

- 計画から外れた所は、ここに「何を・なぜ・どう変えたか」を書く（保守的な方を選び、記録して続ける）。

