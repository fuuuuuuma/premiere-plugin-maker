import helpers  # noqa: F401  （scripts/ を import の道に足す）
import unittest

from lib import privacy


class PrivacyTests(unittest.TestCase):
    def test_personal_paths(self):
        # 実名に見える見本は実行時に組み立てる（このファイル自体が Task 34 の衛生検査に引っかからないように）
        who = "yama" + "da"
        text = f"a /Users/{who}/Desktop/x\nb /Users/Shared/ok\nc C:\\Users\\{who}\\AppData\nd /Users/<name>/ok\ne /home/{who}/x"
        found = [line for line, _ in privacy.personal_paths(text)]
        self.assertEqual(found, [1, 3, 5])

    def test_secret_names_and_tokens(self):
        self.assertTrue(privacy.secret_like_name("my_secret_store.py"))
        self.assertTrue(privacy.secret_like_name(".env"))
        self.assertTrue(privacy.secret_like_name("ready"))
        self.assertFalse(privacy.secret_like_name("keychain_store.py"))
        self.assertEqual(len(privacy.token_like("x = 'ghp_" + "a" * 36 + "'")), 1)


if __name__ == "__main__":
    unittest.main()
