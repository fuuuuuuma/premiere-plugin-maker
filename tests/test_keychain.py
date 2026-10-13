import json
import subprocess
import sys
import unittest
from unittest import mock

from helpers import PARTS, temp_dir

SERVER = temp_dir() / "server"
SERVER.mkdir()
(SERVER / "config.json").write_text(json.dumps({"app": "PpmTest"}), encoding="utf-8")
src = (PARTS / "keychain" / "server" / "ppm_keychain.py").read_text(encoding="utf-8")
(SERVER / "ppm_keychain.py").write_text(src, encoding="utf-8")
sys.path.insert(0, str(SERVER))
import ppm_keychain  # noqa: E402


class MacKeychainTests(unittest.TestCase):
    """本物のキーチェーンには書かない。security の呼び出しを偽物に差し替えて、渡し方だけを確かめる。"""

    @unittest.skipUnless(sys.platform == "darwin", "Mac だけ")
    def test_value_goes_through_stdin_not_argv(self):
        calls = []

        def fake_run(cmd, **kw):
            calls.append((cmd, kw.get("input")))
            if "find-generic-password" in " ".join(cmd):
                return subprocess.CompletedProcess(cmd, 0, "秘密の値\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(ppm_keychain.subprocess, "run", side_effect=fake_run):
            ppm_keychain.set_secret("api", "秘密の値")
        for cmd, stdin in calls:
            self.assertNotIn("秘密の値", " ".join(cmd))
        self.assertTrue(any(stdin and "秘密の値" in stdin for _, stdin in calls))
        self.assertTrue(all("PpmTest" in " ".join(c) + (s or "") for c, s in calls))

    def test_bad_names_are_rejected(self):
        with self.assertRaises(ValueError):
            ppm_keychain.set_secret("名前に 空白", "x")


@unittest.skipUnless(sys.platform == "win32", "Windows だけ（DPAPI）")
class WindowsDpapiTests(unittest.TestCase):
    def test_roundtrip(self):
        ppm_keychain.set_secret("test-roundtrip", "値")
        try:
            self.assertEqual(ppm_keychain.get_secret("test-roundtrip"), "値")
        finally:
            ppm_keychain.delete_secret("test-roundtrip")
        self.assertFalse(ppm_keychain.has_secret("test-roundtrip"))


if __name__ == "__main__":
    unittest.main()
