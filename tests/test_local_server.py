import importlib.util
import json
import os
import stat
import subprocess
import sys
import unittest

from server_helpers import LiveServer, make_server_dir

SLOW = "import time\nNAME = 'slow'\ndef run(params, ctx):\n    for _ in range(100):\n        if ctx.cancelled():\n            return None\n        time.sleep(0.05)\n    return {'ok': True}\n"
BOOM = "from ppm_jobs import JobError\nNAME = 'boom'\ndef run(params, ctx):\n    raise JobError('止めました', '理由です', '次の一手です')\n"
HELLO = "ROUTES = {('GET', '/hello'): lambda req, ctx: (200, {'hi': ctx['app']})}\n"


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LiveServer(make_server_dir(jobs={"slow": SLOW, "boom": BOOM}, ext={"hello": HELLO}))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_handshake_is_private_and_complete(self):
        info = self.server.info
        for key in ("pid", "httpPort", "token", "version", "protocol", "tmpDir", "serverDir"):
            self.assertIn(key, info)
        if sys.platform != "win32":
            self.assertEqual(stat.S_IMODE(os.stat(self.server.handshake_path).st_mode), 0o600)

    def test_token_is_required(self):
        self.assertEqual(self.server.call("/ping", token=False)[0], 403)
        code, data = self.server.call("/ping")
        self.assertEqual(code, 200)
        self.assertIn("echo", data["jobs"])

    def test_echo_job(self):
        code, start = self.server.call("/jobs/echo", {"テキスト": "こんにちは"})
        self.assertEqual(code, 202)
        job = self.server.wait_job(start["jobId"])
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["result"]["echo"]["テキスト"], "こんにちは")

    def test_unknown_job_and_route(self):
        self.assertEqual(self.server.call("/jobs/nope", {})[0], 404)
        self.assertEqual(self.server.call("/nope")[0], 404)

    def test_one_job_at_a_time_and_cancel(self):
        _, slow = self.server.call("/jobs/slow", {})
        self.assertEqual(self.server.call("/jobs/echo", {})[0], 409)
        self.server.call(f"/jobs/{slow['jobId']}/cancel", {})
        self.assertEqual(self.server.wait_job(slow["jobId"])["status"], "cancelled")

    def test_job_error_keeps_reason_and_http_200(self):
        _, start = self.server.call("/jobs/boom", {})
        job = self.server.wait_job(start["jobId"])
        self.assertEqual(job["status"], "error")
        self.assertEqual(job["error"], {"message": "止めました", "why": "理由です", "next": "次の一手です"})

    def test_extension_route(self):
        self.assertEqual(self.server.call("/hello"), (200, {"hi": "PpmTest"}))
        self.assertEqual(self.server.call("/hello", token=False)[0], 403)


class ShutdownTests(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "Windows の terminate は後始末を走らせない")
    def test_handshake_is_removed_on_stop(self):
        s = LiveServer(make_server_dir())
        s.stop()
        self.assertFalse(s.handshake_path.exists())


class InstallTests(unittest.TestCase):
    def load_install(self, server_dir):
        spec = importlib.util.spec_from_file_location("ppm_install_under_test", server_dir / "install.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_dry_run_changes_nothing(self):
        d = make_server_dir()
        support = d.parent / "support"
        env = {**os.environ, "PPM_APP_SUPPORT_ROOT": str(support), "PPM_LOG_ROOT": str(d.parent / "logs"), "PYTHONIOENCODING": "cp932"}
        proc = subprocess.run([sys.executable, str(d / "install.py"), "--dry-run"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("runtime", proc.stdout)
        self.assertIn("試し実行", proc.stdout)
        self.assertFalse(support.exists())

    def test_plist_escapes_paths(self):
        mod = self.load_install(make_server_dir())
        text = mod.plist_text("/opt/a&b/python3", mod.Path("/srv/ppm_server.py"))
        self.assertIn("/opt/a&amp;b/python3", text)
        self.assertIn("com.ppm.ppmtest.server", text)


if __name__ == "__main__":
    unittest.main()
