import helpers  # noqa: F401  （scripts/ を import の道に足す）
import unittest

from lib import frontmatter as fm


class FrontmatterTests(unittest.TestCase):
    def test_parse_scalars_lists_and_quotes(self):
        text = (
            "---\n"
            "id: ui-flex-rows-collapse\n"
            "title: 一覧の行が中身より低く潰れる\n"
            "tags: [画面, CSS, flex]\n"
            "premiere: \">=25.6\"\n"
            "status: verified   # 実機で確認\n"
            "---\n"
            "\n本文\n"
        )
        data, body = fm.parse(text)
        self.assertEqual(data["id"], "ui-flex-rows-collapse")
        self.assertEqual(data["tags"], ["画面", "CSS", "flex"])
        self.assertEqual(data["premiere"], ">=25.6")
        self.assertEqual(data["status"], "verified")
        self.assertEqual(body, "本文\n")

    def test_bom_and_empty_list(self):
        data, _ = fm.parse("\ufeff---\nrelated: []\n---\n")
        self.assertEqual(data["related"], [])

    def test_errors_say_which_line(self):
        with self.assertRaises(fm.FrontmatterError) as ctx:
            fm.parse("---\nid ui\n---\n")
        self.assertIn("2 行目", str(ctx.exception))
        with self.assertRaises(fm.FrontmatterError):
            fm.parse("本文だけ\n")
        with self.assertRaises(fm.FrontmatterError):
            fm.parse("---\nid: x\n")

    def test_dump_roundtrip(self):
        data = {"id": "x", "title": "a: b", "tags": ["c", "d"]}
        again, _ = fm.parse(fm.dump(data) + "本文\n")
        self.assertEqual(again, data)


if __name__ == "__main__":
    unittest.main()
