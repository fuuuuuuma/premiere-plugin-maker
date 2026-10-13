import unittest

from helpers import KNOWLEDGE, PARTS

import kb

REQUIRED_IDS = [
    "core-versions", "core-capabilities", "core-transactions", "core-api-patterns", "core-ui-rules",
    "core-manifest-permissions", "core-verification", "core-dev-loop", "core-safety", "core-intake",
    "core-versioning-release", "platform-mac", "platform-windows", "platform-cross", "ref-ticktime",
    "ref-fcp7-xml", "ref-prtextstyle", "ref-prfpset", "ref-mogrt", "ref-keyframe-interpolation",
    "ref-cep-extendscript", "ref-local-server", "ref-mcp",
]


class KnowledgeTests(unittest.TestCase):
    def test_check_passes(self):
        self.assertEqual(kb.check_all(KNOWLEDGE, PARTS), [])

    def test_required_ids_exist(self):
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        missing = [i for i in REQUIRED_IDS if i not in ids]
        self.assertEqual(missing, [])

    def test_body_has_the_sections_of_its_kind(self):
        sections = {"core": ["## 要点", "## 出どころ"], "recipe": ["## 前提", "## 手順", "## 確認", "## 戻し方"],
                    "feature": ["## 何をする機能か", "## 作り方", "## 結果と今の状態"], "usecase": ["## 症状", "## 原因", "## 直し方", "## 再発防止"],
                    "platform": ["## 出どころ"], "reference": ["## 仕様", "## 出どころ"]}
        for entry, body in kb.load(KNOWLEDGE):
            for s in sections[entry["kind"]]:
                self.assertIn(s, body, f"{entry['id']} に「{s}」がありません")


if __name__ == "__main__":
    unittest.main()
