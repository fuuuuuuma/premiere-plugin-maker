import subprocess
import unittest
import zipfile

from helpers import temp_dir

import install_ccx


def fake_ccx():
    path = temp_dir() / "a.ccx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", '{"name": "Ship Test", "id": "com.ppm.shiptest", "version": "0.1.0"}')
    return path


class FakeRunner:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        code, out = self.outputs.pop(0)
        return subprocess.CompletedProcess(cmd, code, out, "")


class InstallCcxTests(unittest.TestCase):
    def test_command_shapes(self):
        self.assertEqual(install_ccx.upia_command("mac", "/u", "install", "/x.ccx"), ["/u", "--install", "/x.ccx"])
        self.assertEqual(install_ccx.upia_command("windows", "C:/u.exe", "remove", "Ship Test"), ["C:/u.exe", "/remove", "Ship Test"])
        self.assertEqual(install_ccx.upia_command("mac", "/u", "list"), ["/u", "--list", "all"])

    def test_plugin_name_from_ccx(self):
        self.assertEqual(install_ccx.plugin_name_in_ccx(fake_ccx()), "Ship Test")

    def test_dry_run_runs_nothing(self):
        runner = FakeRunner([])
        code = install_ccx.main(["--install", str(fake_ccx())], runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(runner.calls, [])

    def test_apply_reinstall_removes_then_installs_and_tolerates_remove_failure(self):
        runner = FakeRunner([(1, "status -406"), (0, "Installation Successful")])
        code = install_ccx.main(["--reinstall", str(fake_ccx()), "--apply", "--upia", "/u"], runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual([c[1] for c in runner.calls], ["--remove", "--install"] if install_ccx.osinfo.detect_os() != "windows" else ["/remove", "/install"])

    def test_apply_install_failure_is_reported(self):
        runner = FakeRunner([(1, "Error code -1")])
        code = install_ccx.main(["--install", str(fake_ccx()), "--apply", "--upia", "/u"], runner=runner)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
