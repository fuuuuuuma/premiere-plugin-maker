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
