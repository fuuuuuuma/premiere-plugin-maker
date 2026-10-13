import json
import subprocess
import sys
import threading
import time
import unittest

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir

CEP = PARTS / "cep-helper" / "cep"


class CepFilesTests(unittest.TestCase):
    def test_no_adobe_csinterface_is_bundled(self):
        self.assertEqual(list(CEP.rglob("CSInterface*.js")), [])
        self.assertIn("__adobe_cep__", (CEP / "client" / "main.js").read_text(encoding="utf-8"))

    def test_manifest_declares_auto_start_and_node(self):
        xml = (CEP / "CSXS" / "manifest.xml").read_text(encoding="utf-8")
        self.assertIn("--enable-nodejs", xml)
        self.assertIn('<Host Name="PPRO"', xml)
        self.assertIn("{{APP_NAME}}", xml)

    def test_jsx_does_not_use_json(self):
        jsx = (CEP / "host" / "helper.jsx").read_text(encoding="utf-8")
        self.assertNotIn("JSON.", jsx)
        for fn in ("ppmFeatures", "ppmPlay", "ppmStop", "ppmRazor"):
            self.assertIn(f"function {fn}(", jsx)

    def test_installer_dry_run_does_nothing(self):
        import os
        env_home = temp_dir()
        proc = subprocess.run([sys.executable, str(CEP / "install_cep.py"), "--bundle-id", "com.ppm.test.cep"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                              env={**os.environ, "HOME": str(env_home), "USERPROFILE": str(env_home), "APPDATA": str(env_home / "AppData")})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PlayerDebugMode", proc.stdout)
        self.assertIn("試し実行", proc.stdout)
        self.assertFalse(any(env_home.rglob("manifest.xml")))


class CepRelayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(make_server_dir(extra_dirs=[PARTS / "cep-helper" / "server"]))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_unannounced_command_is_refused(self):
        code, data = self.server.call("/cep/commands", {"name": "razor", "args": {}, "timeoutMs": 500})
        self.assertEqual(code, 409)
        self.assertIn("名乗って", data["error"])

    def test_command_round_trip(self):
        self.server.call("/cep/hello", {"features": ["play", "stop"]})
        status = self.server.call("/cep/status")[1]
        self.assertTrue(status["connected"])
        result = {}

        def helper():
            for _ in range(50):
                _, nxt = self.server.call("/cep/next", {})
                if nxt.get("command"):
                    self.server.call("/cep/result", {"id": nxt["command"]["id"], "ok": True, "result": {"played": nxt["command"]["args"]["seconds"]}})
                    return
                time.sleep(0.05)

        t = threading.Thread(target=helper)
        t.start()
        code, data = self.server.call("/cep/commands", {"name": "play", "args": {"seconds": 3}, "timeoutMs": 5000})
        t.join()
        self.assertEqual(code, 200)
        self.assertEqual(data["result"], {"played": 3})

    def test_timeout_when_helper_is_silent(self):
        self.server.call("/cep/hello", {"features": ["stop"]})
        code, data = self.server.call("/cep/commands", {"name": "stop", "args": {}, "timeoutMs": 300})
        self.assertEqual(code, 504)


if __name__ == "__main__":
    unittest.main()
