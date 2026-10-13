import re
import unittest

from helpers import REPO


class DocsTests(unittest.TestCase):
    def test_readme_has_install_for_both_clients_and_scope(self):
        t = (REPO / "README.md").read_text(encoding="utf-8")
        for s in ("claude plugin marketplace add fuuuuuuma/premiere-plugin-maker",
                  "claude plugin install premiere-plugin-maker@premiere-plugin-maker",
                  "codex plugin marketplace add fuuuuuuma/premiere-plugin-maker",
                  "codex plugin add premiere-plugin-maker@premiere-plugin-maker",
                  "## できないこと", "## 確かめた範囲", "## ライセンス"):
            self.assertIn(s, t)

    def test_internal_links_exist(self):
        for doc in [REPO / "README.md", REPO / "docs" / "prompts-ja.md", REPO / "docs" / "maintenance.md"]:
            for link in re.findall(r"\]\(([^)#]+)\)", doc.read_text(encoding="utf-8")):
                if link.startswith("http"):
                    continue
                self.assertTrue((doc.parent / link).exists(), f"{doc.name}: {link}")

    def test_ci_runs_on_mac_and_windows(self):
        ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("macos-latest", ci)
        self.assertIn("windows-latest", ci)


if __name__ == "__main__":
    unittest.main()
