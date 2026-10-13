import json
import unittest

from helpers import PLUGIN, REPO, SKILL


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PackageTests(unittest.TestCase):
    def test_names_are_the_same_everywhere(self):
        claude_mp = load(REPO / ".claude-plugin" / "marketplace.json")
        codex_mp = load(REPO / ".agents" / "plugins" / "marketplace.json")
        claude_pj = load(PLUGIN / ".claude-plugin" / "plugin.json")
        codex_pj = load(PLUGIN / ".codex-plugin" / "plugin.json")
        for name in (claude_mp["name"], codex_mp["name"], claude_pj["name"], codex_pj["name"],
                     claude_mp["plugins"][0]["name"], codex_mp["plugins"][0]["name"]):
            self.assertEqual(name, "premiere-plugin-maker")

    def test_versions_match(self):
        v1 = load(PLUGIN / ".claude-plugin" / "plugin.json")["version"]
        v2 = load(PLUGIN / ".codex-plugin" / "plugin.json")["version"]
        v3 = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(v1, r"^\d+\.\d+\.\d+$")
        self.assertEqual(v1, v2)
        self.assertEqual(v1, v3)

    def test_sources_point_to_the_plugin_folder(self):
        claude_mp = load(REPO / ".claude-plugin" / "marketplace.json")
        codex_mp = load(REPO / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual((REPO / claude_mp["plugins"][0]["source"]).resolve(), PLUGIN.resolve())
        self.assertEqual((REPO / codex_mp["plugins"][0]["source"]["path"]).resolve(), PLUGIN.resolve())
        self.assertEqual(codex_mp["plugins"][0]["policy"]["installation"], "AVAILABLE")

    def test_license_is_mit(self):
        self.assertIn("MIT License", (REPO / "LICENSE").read_text(encoding="utf-8"))

    def test_skill_md_frontmatter_has_only_name_and_description(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        head = text.split("---", 2)[1]
        keys = [line.split(":", 1)[0].strip() for line in head.strip().splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])


if __name__ == "__main__":
    unittest.main()
