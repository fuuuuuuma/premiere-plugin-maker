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


class ExamplePartCopiesTests(unittest.TestCase):
    def test_part_files_in_examples_match_the_parts(self):
        # 部品を直したら、完成サンプルの中の写しも作り直す（古い写しを見本にされないため）
        import add_part
        from lib import project as projlib
        stale = []
        for ex in sorted(p for p in EXAMPLES.iterdir() if (p / ".ppm" / "project.json").exists()):
            info = projlib.load(ex)
            mapping = projlib.placeholders(info)
            for part in info.get("parts", []):
                pj = add_part.load_part(part, SKILL / "parts")
                for src, dst in add_part._expand_files(SKILL / "parts" / part, pj["files"]):
                    if (ex / dst).read_bytes() != add_part._render(src, mapping):
                        stale.append(f"{ex.name}/{dst}")
        self.assertEqual(stale, [])


if __name__ == "__main__":
    unittest.main()
