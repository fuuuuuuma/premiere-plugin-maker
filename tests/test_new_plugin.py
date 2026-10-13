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
