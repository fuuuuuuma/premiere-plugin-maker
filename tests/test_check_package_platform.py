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
