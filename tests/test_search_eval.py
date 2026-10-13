import json
import unittest

from helpers import KNOWLEDGE

import kb


class SearchEvalTests(unittest.TestCase):
    def test_expected_entry_is_in_top_5(self):
        cases = json.loads((KNOWLEDGE / "eval" / "search_eval.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(cases), 30)
        items = kb.load(KNOWLEDGE)
        synonyms = kb.load_synonyms(KNOWLEDGE)
        misses = []
        for c in cases:
            ids = [e["id"] for _, e in kb.search(items, c["query"], synonyms, os_name=c["os"], limit=5)]
            if c["expect"] not in ids:
                misses.append(f"{c['query']} → {ids}（期待 {c['expect']}）")
        self.assertEqual(misses, [], "\n".join(misses))


if __name__ == "__main__":
    unittest.main()
