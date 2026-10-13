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
