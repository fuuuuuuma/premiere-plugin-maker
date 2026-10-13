import json
import unittest

from helpers import PARTS

import add_part
from lib import manifest as mf


class PartsTests(unittest.TestCase):
    def test_every_part_is_well_formed(self):
        names = add_part.list_parts(PARTS)
        self.assertTrue(names)
        for name in names:
            with self.subTest(part=name):
                raw = json.loads((PARTS / name / "part.json").read_text(encoding="utf-8"))
                self.assertEqual(raw["name"], name)
                self.assertFalse(set(raw) - add_part.PART_KEYS, f"知らない項目: {set(raw) - add_part.PART_KEYS}")
                part = add_part.load_part(name, PARTS)
                self.assertIn(part["status"], add_part.STATUSES)
                self.assertTrue(set(part["os"]) <= {"mac", "windows"})
                mf.version_tuple(part["minVersion"])
                targets = {dst for _, dst in add_part._expand_files(PARTS / name, part["files"])}
                for s in part["scripts"] + part["styles"]:
                    self.assertIn(s, targets, f"{s} が files にありません")
                for req in part["requires"]:
                    self.assertIn(req, names, f"requires の {req} がありません")
                for src in part["files"]:
                    self.assertTrue((PARTS / name / src).exists(), src)


if __name__ == "__main__":
    unittest.main()
