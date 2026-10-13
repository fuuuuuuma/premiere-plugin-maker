import unittest

from helpers import EXAMPLES, SKILL

from lib import checks


class ExampleTests(unittest.TestCase):
    def test_every_example_passes_check(self):
        names = sorted(p.name for p in EXAMPLES.iterdir() if (p / "manifest.json").exists())
        self.assertTrue(names)
        for name in names:
            with self.subTest(example=name):
                errors = [f for f in checks.run_all(EXAMPLES / name, SKILL) if f.severity == "error"]
                self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
