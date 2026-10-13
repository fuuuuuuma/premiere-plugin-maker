import subprocess
import unittest
from pathlib import Path

from helpers import REPO

from lib import privacy

TEXT = {".md", ".py", ".js", ".json", ".html", ".css", ".txt", ".yml", ".yaml", ".xml", ".jsx", ".ps1", ".bat", ".command", ".sh", ".template", ".plist"}
FORBIDDEN_NAMES = {"CSInterface.js", "Basic Title.mogrt"}
FORBIDDEN_SUFFIXES = {".mogrt", ".prproj", ".aep", ".mp4", ".mov", ".wav", ".mp3", ".ttf", ".otf", ".zip", ".ccx", ".pyc"}
MAX_BYTES = 2_000_000


def tracked():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout.decode("utf-8")
        return [REPO / p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts]


class HygieneTests(unittest.TestCase):
    def test_no_personal_paths_or_tokens(self):
        bad = []
        for p in tracked():
            if p.suffix.lower() in TEXT:
                t = p.read_text(encoding="utf-8", errors="replace")
                bad += [f"{p.relative_to(REPO)}:{ln} {s}" for ln, s in privacy.personal_paths(t) + privacy.token_like(t)]
        self.assertEqual(bad, [])

    def test_no_denylisted_names(self):
        deny = REPO / "tests" / "local_denylist.txt"
        if not deny.exists():
            self.skipTest("tests/local_denylist.txt が無い（公開前は必ず置いて走らせる）")
        words = [w.strip() for w in deny.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]
        bad = []
        for p in tracked():
            if p.suffix.lower() in TEXT and p.name != "local_denylist.txt":
                t = p.read_text(encoding="utf-8", errors="replace")
                bad += [f"{p.relative_to(REPO)}: {w}" for w in words if w in t]
        self.assertEqual(bad, [])

    def test_no_adobe_files_media_or_big_files(self):
        bad = []
        for p in tracked():
            if p.name in FORBIDDEN_NAMES or p.suffix.lower() in FORBIDDEN_SUFFIXES or p.stat().st_size > MAX_BYTES:
                bad.append(str(p.relative_to(REPO)))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
