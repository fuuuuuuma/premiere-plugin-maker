"""最後のレビューで見つかった型を固定するテスト（CEP の拡張を消す・配る物の検査・壊れた manifest・MCP の登録）。"""
import json
import os
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from helpers import PARTS, SKILL, temp_dir

import add_part
import make_ccx
import new_plugin
from lib import manifest as mf

CEP_INSTALL = PARTS / "cep-helper" / "cep" / "install_cep.py"


def run_install_cep(home, *args):
    env = {**os.environ, "HOME": str(home), "APPDATA": str(home / "AppData")}
    return subprocess.run([sys.executable, str(CEP_INSTALL), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=60)


class CepInstallSafetyTests(unittest.TestCase):
    def setUp(self):
        self.home = temp_dir()
        self.ext = self.home / "Library" / "Application Support" / "Adobe" / "CEP" / "extensions"
        if sys.platform == "win32":
            self.ext = self.home / "AppData" / "Adobe" / "CEP" / "extensions"
        (self.ext / "com.other.vendor").mkdir(parents=True)
        (self.ext / "com.other.vendor" / "keep.txt").write_text("他社の拡張", encoding="utf-8")

    def test_empty_or_path_like_bundle_id_is_refused(self):
        for bad in ("", "..", "../x", "a/b", "/abs", "a\\b"):
            proc = run_install_cep(self.home, "--bundle-id", bad)
            self.assertEqual(proc.returncode, 2, (bad, proc.stdout + proc.stderr))
            self.assertIn("bundle-id", proc.stdout + proc.stderr)
        self.assertTrue((self.ext / "com.other.vendor" / "keep.txt").exists())

    def test_existing_folder_of_another_extension_is_not_replaced(self):
        proc = run_install_cep(self.home, "--bundle-id", "com.other.vendor", "--apply")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertTrue((self.ext / "com.other.vendor" / "keep.txt").exists())


class BundleSafetyTests(unittest.TestCase):
    def setUp(self):
        self.dest = temp_dir() / "配る サーバー"
        new_plugin.create_project("panel-server", self.dest, "Bundle Test", label="束ね")

    def test_secret_in_server_files_stops_the_bundle(self):
        (self.dest / "server" / "settings.json").write_text('{"key": "sk-ant-' + "a" * 30 + '"}\n', encoding="utf-8")
        with self.assertRaises(make_ccx.CcxError) as ctx:
            make_ccx.build_bundle(self.dest)
        self.assertIn("settings.json", str(ctx.exception))

    def test_personal_path_in_server_files_stops_the_bundle(self):
        (self.dest / "server" / "note.txt").write_text("/Users/" + "yamada/x/\n", encoding="utf-8")
        with self.assertRaises(make_ccx.CcxError):
            make_ccx.build_bundle(self.dest)

    def test_venv_models_logs_are_left_out_of_the_server_zip(self):
        for rel in (".venv/lib/x.py", "models/big.bin", "logs/a.log", "run.log"):
            p = self.dest / "server" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x")
        folder = make_ccx.build_bundle(self.dest)
        z = next(folder.glob("*_server_*.zip"))
        with zipfile.ZipFile(z) as f:
            names = f.namelist()
        self.assertFalse([n for n in names if "/.venv/" in n or "/models/" in n or n.endswith(".log")], names)
        self.assertIn("server/ppm_server.py", names)

    def test_readme_explains_the_server_when_there_is_one(self):
        folder = make_ccx.build_bundle(self.dest)
        text = (folder / "はじめにお読みください.txt").read_text(encoding="utf-8")
        self.assertIn("install_mac.command", text)
        self.assertIn("install_windows.bat", text)

    def test_readme_has_no_server_section_without_a_server(self):
        dest = temp_dir() / "パネルだけ"
        new_plugin.create_project("panel", dest, "Panel Only", label="パネル")
        folder = make_ccx.build_bundle(dest)
        text = (folder / "はじめにお読みください.txt").read_text(encoding="utf-8")
        self.assertNotIn("install_mac.command", text)


class BrokenManifestShapeTests(unittest.TestCase):
    def setUp(self):
        self.dest = temp_dir() / "壊れた 形"
        new_plugin.create_project("panel", self.dest, "Shape Test", label="形")
        self.path = self.dest / "manifest.json"
        self.data = mf.load(self.path)

    def write(self, **changes):
        data = dict(self.data)
        for k, v in changes.items():
            if v is None:
                data.pop(k, None)
            else:
                data[k] = v
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_add_part_stops_with_a_clear_error(self):
        for bad in ({"host": [self.data["host"]]}, {"requiredPermissions": []}, {"entrypoints": {}}):
            self.write(**bad)
            before = self.path.read_text(encoding="utf-8")
            with self.assertRaises(mf.ManifestError, msg=str(bad)):
                add_part.add_part(self.dest, "motion-bake")
            self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_make_ccx_stops_with_a_clear_error(self):
        for bad in ({"host": [self.data["host"]]}, {"id": None}, {"icons": "icons/icon.png"}):
            self.write(**bad)
            with self.assertRaises((mf.ManifestError, make_ccx.CcxError), msg=str(bad)):
                make_ccx.build_ccx(self.dest)

    def test_check_does_not_crash_on_wrong_types(self):
        from lib import checks
        self.write(icons="icons/icon.png")
        rules = {f.rule for f in checks.run_all(self.dest, SKILL)}
        self.assertTrue(rules)


class McpSetupTests(unittest.TestCase):
    def test_uses_the_resolved_path_of_the_cli(self):
        sys.path.insert(0, str(PARTS / "mcp-bridge" / "server"))
        server = temp_dir()
        (server / "config.json").write_text(json.dumps({"app": "PpmTest"}), encoding="utf-8")
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_mcp_t", PARTS / "mcp-bridge" / "server" / "setup_mcp.py")
        mod = importlib.util.module_from_spec(spec)
        with mock.patch("pathlib.Path.read_text", return_value='{"app": "PpmTest"}'):
            spec.loader.exec_module(mod)
        resolved = {"claude": r"C:\npm\claude.cmd", "codex": r"C:\npm\codex.cmd"}
        with mock.patch.object(mod.shutil, "which", side_effect=lambda n: resolved.get(n)):
            cmds = mod.plan("python", server / "ppm_mcp.py")
        self.assertEqual({c[0] for c, _ in cmds}, set(resolved.values()))


class CiFoundIssuesTests(unittest.TestCase):
    """公開後の CI（GitHub Actions）で見つかった型。"""

    def test_server_does_not_ask_dns_for_its_own_name(self):
        # 標準の HTTPServer は待ち受けの前に socket.getfqdn で自分の名前を DNS に聞く。GitHub の Mac ではこれが長く止まった
        import importlib.util
        import socket
        from server_helpers import make_server_dir
        d = make_server_dir()
        sys.path.insert(0, str(d))
        try:
            spec = importlib.util.spec_from_file_location("ppm_server_t", d / "ppm_server.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            with mock.patch.object(socket, "getfqdn", side_effect=AssertionError("getfqdn を呼んだ")):
                httpd = mod.make_httpd(0)
            try:
                self.assertEqual(httpd.server_address[0], "127.0.0.1")
            finally:
                httpd.server_close()
        finally:
            sys.path.remove(str(d))

    def test_keychain_on_windows_does_not_need_other_parts(self):
        # 鍵の保管の部品だけを置いたフォルダでも、Windows の置き場所を決められる（ppm_paths に頼らない）
        server = temp_dir() / "server"
        server.mkdir()
        (server / "config.json").write_text(json.dumps({"app": "PpmTest"}), encoding="utf-8")
        (server / "ppm_keychain.py").write_text((PARTS / "keychain" / "server" / "ppm_keychain.py").read_text(encoding="utf-8"), encoding="utf-8")
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import ppm_keychain as k; "
                "print(k.WindowsDpapiBackend().directory())")
        env = {**os.environ, "APPDATA": str(server / "AppData")}
        proc = subprocess.run([sys.executable, "-c", code, str(server)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(proc.stdout.strip()), server / "AppData" / "PpmTest" / "secrets")


if __name__ == "__main__":
    unittest.main()
