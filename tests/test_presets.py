import subprocess
import sys
import unittest

from helpers import PARTS


class PresetTests(unittest.TestCase):
    def test_prfpset_builder_runs(self):
        server = PARTS / "motion-bake" / "server"
        proc = subprocess.run([sys.executable, "-m", "presets.prfpset_build", "--help"], cwd=str(server),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
