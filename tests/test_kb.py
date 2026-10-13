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
