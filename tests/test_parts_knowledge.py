import unittest

from helpers import KNOWLEDGE, PARTS

import add_part
import kb


class PartsKnowledgeTests(unittest.TestCase):
    def test_every_knowledge_id_in_part_json_exists(self):
        ids = {e["id"] for e, _ in kb.load(KNOWLEDGE)}
        missing = []
        for name in add_part.list_parts(PARTS):
            for k in add_part.load_part(name, PARTS)["knowledge"]:
                if k not in ids:
                    missing.append(f"{name}: {k}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
