import helpers  # noqa: F401  （scripts/ を import の道に足す）
import unittest

from lib import jsscan


class JsscanTests(unittest.TestCase):
    def test_blank_keeps_length_and_newlines(self):
        src = 'a = "x // y"; // comment\nb = /re{1}/g; /* c\n d */ c = `t ${1}`;\n'
        out = jsscan.blank(src)
        self.assertEqual(len(out), len(src))
        self.assertEqual(out.count("\n"), src.count("\n"))
        self.assertNotIn("comment", out)
        self.assertNotIn("x // y", out)
        self.assertIn("b =", out)

    def test_callback_spans_arrow_function_and_expression(self):
        src = "project.lockedAccess(() => {\n project.executeTransaction((ca) => { ca.addAction(x); }, 'u');\n});\nPPM.transact(p, 'l', (add) => add('a', () => t.createSetEndAction(z)));\n"
        clean = jsscan.blank(src)
        names = [name for _, _, name in jsscan.callback_spans(clean)]
        self.assertEqual(names, ["lockedAccess", "executeTransaction", "transact"])
        start, end, _ = jsscan.callback_spans(clean)[2]
        self.assertIn("createSetEndAction", clean[start:end])

    def test_builder_spans(self):
        src = "// ppm: action-builder\nfunction keyActions(add, p) {\n  add('k', () => p.createAddKeyframeAction(kf));\n}\nfunction other() {}\n"
        spans = jsscan.builder_spans(src, jsscan.blank(src))
        self.assertEqual(len(spans), 1)
        self.assertIn("createAddKeyframeAction", src[spans[0][0]:spans[0][1]])
        self.assertNotIn("other", src[spans[0][0]:spans[0][1]])


if __name__ == "__main__":
    unittest.main()
