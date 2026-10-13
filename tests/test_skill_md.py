import re
import unittest

from helpers import KNOWLEDGE, SCRIPTS, SKILL

import kb


class SkillMdTests(unittest.TestCase):
    def setUp(self):
        self.text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_length_and_frontmatter(self):
        self.assertLessEqual(len(self.text.splitlines()), 200)
        head = self.text.split("---", 2)[1]
        self.assertIn("name: premiere-plugin-maker", head)
        desc = re.search(r"description: (.+)", head).group(1)
        self.assertGreater(len(desc), 60)
        for word in ("Premiere", "プラグイン", "Windows", "Mac", "必ず使う"):
            self.assertIn(word, desc)

    def test_first_question_and_bootstrap_for_both_os(self):
        self.assertIn("Windows と Mac のどちらですか", self.text)
        self.assertIn("git clone --depth 1 https://github.com/fuuuuuuma/premiere-plugin-maker", self.text)
        self.assertIn("Invoke-WebRequest", self.text)
        self.assertIn("py -3", self.text)

    def test_no_fragile_root_variable_or_client_prefix(self):
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT:-", self.text)
        self.assertNotIn("mcp__", self.text)

    def test_every_script_and_knowledge_id_exists(self):
        for name in set(re.findall(r"([a-z_]+\.py)", self.text)):
            if name in ("install.py",):
                continue
            self.assertTrue((SCRIPTS / name).exists(), name)
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        for kid in set(re.findall(r"\b((?:core|recipe|ref|platform|feat|uc)-[a-z0-9-]+)\b", self.text)):
            self.assertIn(kid, ids, kid)

    def test_codex_yaml(self):
        y = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$premiere-plugin-maker", y)
        self.assertIn("allow_implicit_invocation: true", y)


if __name__ == "__main__":
    unittest.main()
