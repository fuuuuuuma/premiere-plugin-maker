import unittest

from helpers import temp_dir
from lib import fsutil


class FsutilTests(unittest.TestCase):
    def test_copy_new_refuses_when_any_target_exists_and_copies_nothing(self):
        src = temp_dir() / "src"
        (src / "lib").mkdir(parents=True)
        (src / "a.txt").write_text("a", encoding="utf-8")
        (src / "lib" / "b.js").write_text("b", encoding="utf-8")
        dst = temp_dir() / "dst"
        (dst / "lib").mkdir(parents=True)
        (dst / "lib" / "b.js").write_text("利用者の変更", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            fsutil.copy_new(src, dst)
        self.assertFalse((dst / "a.txt").exists())
        self.assertEqual((dst / "lib" / "b.js").read_text(encoding="utf-8"), "利用者の変更")

    def test_copy_new_copies_tree(self):
        src = temp_dir() / "src"
        (src / "lib").mkdir(parents=True)
        (src / "lib" / "b.js").write_text("b", encoding="utf-8")
        dst = temp_dir() / "dst"
        copied = fsutil.copy_new(src, dst)
        self.assertEqual([p.relative_to(dst).as_posix() for p in copied], ["lib/b.js"])

    def test_atomic_write_and_nfc(self):
        path = temp_dir() / "テスト.json"
        fsutil.atomic_write_text(path, "{}\n")
        self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")
        self.assertEqual(fsutil.nfc("か\u3099"), "が")

    def test_is_within(self):
        base = temp_dir()
        self.assertTrue(fsutil.is_within(base / "a" / "b", base))
        self.assertFalse(fsutil.is_within(base.parent, base))


if __name__ == "__main__":
    unittest.main()
