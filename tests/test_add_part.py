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

    def test_batch_files_are_written_with_crlf(self):
        src = self.kit / "parts" / "demo" / "server" / "run.bat"
        src.write_bytes(b"@echo off\nexit /b 0\n")
        add_part.add_part(self.dest, "demo", self.kit)
        self.assertEqual((self.dest / "server" / "run.bat").read_bytes(), b"@echo off\r\nexit /b 0\r\n")

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
