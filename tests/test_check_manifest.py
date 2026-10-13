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
        # 末尾のカンマ。Python 3.13 以降はカンマの 2 行目、それより前は閉じかっこの 3 行目を指す
        root = make_project({"manifest.json": '{\n "id": "a",\n}\n'})
        fs = findings(root)
        self.assertEqual([f.rule for f in fs if f.severity == "error"], ["M001"])
        self.assertRegex(fs[0].message + fs[0].why, r"[23] 行目")

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
