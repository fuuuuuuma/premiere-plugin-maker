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
