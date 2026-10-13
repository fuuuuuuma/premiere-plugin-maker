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
