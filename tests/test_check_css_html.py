import unittest

from check_helpers import GOOD_HTML, make_project, rules


class CssHtmlRuleTests(unittest.TestCase):
    def test_c001_grid(self):
        self.assertIn("C001", rules(make_project({"panel.css": ".a { display: grid; }\ntitle{display:none}"})))

    def test_c002_fixed_and_c004_animation(self):
        r = rules(make_project({"panel.css": "title{display:none}\n.o { position: fixed; transition: opacity 1s; }"}))
        self.assertIn("C002", r)
        self.assertIn("C004", r)

    def test_h001_missing_script(self):
        html = GOOD_HTML.replace('<script src="index.js"></script>', '<script src="lib/missing.js"></script><script src="index.js"></script>')
        self.assertIn("H001", rules(make_project({"index.html": html})))

    def test_h002_lists_and_h004_inputs(self):
        html = GOOD_HTML.replace("<body>", '<body><ul><li>a</li></ul><input type="file" />')
        r = rules(make_project({"index.html": html}))
        self.assertIn("H002", r)
        self.assertIn("H004", r)

    def test_h003_inline_handler(self):
        html = GOOD_HTML.replace('<button id="run"', '<button onclick="go()" id="run"')
        self.assertIn("H003", rules(make_project({"index.html": html})))

    def test_h005_title_not_hidden(self):
        self.assertIn("H005", rules(make_project({"panel.css": ".a { color: #fff; }"})))


if __name__ == "__main__":
    unittest.main()
