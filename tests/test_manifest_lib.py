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
