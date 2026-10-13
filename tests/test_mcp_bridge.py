import json
import os
import subprocess
import sys
import threading
import time
import unittest

from helpers import PARTS
from server_helpers import LiveServer, make_server_dir


class McpBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = make_server_dir(extra_dirs=[PARTS / "mcp-bridge" / "server"])
        cls.server = LiveServer(cls.dir)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def rpc(self, messages):
        env = {**self.server.env}
        proc = subprocess.run([sys.executable, str(self.dir / "ppm_mcp.py")], input="\n".join(json.dumps(m) for m in messages) + "\n",
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
        return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]

    def test_initialize_and_list_tools(self):
        out = self.rpc([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(out[0]["result"]["protocolVersion"], "2025-03-26")
        names = [t["name"] for t in out[1]["result"]["tools"]]
        self.assertEqual(names, ["ppm_health", "ppm_panel_commands", "ppm_panel_call"])
        self.assertEqual(len(out), 2)

    def test_health_says_panel_is_closed(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "ppm_health", "arguments": {}}}])
        text = out[0]["result"]["content"][0]["text"]
        self.assertIn("パネル", text)

    def test_panel_call_round_trip(self):
        def panel():
            for _ in range(100):
                _, nxt = self.server.call("/panel/next", {"commands": [{"name": "get_selection", "description": "選んだクリップ"}]})
                if nxt.get("command"):
                    self.server.call("/panel/result", {"id": nxt["command"]["id"], "ok": True, "result": {"count": 2}})
                    return
                time.sleep(0.05)

        self.server.call("/panel/next", {"commands": [{"name": "get_selection", "description": "選んだクリップ"}]})
        t = threading.Thread(target=panel)
        t.start()
        out = self.rpc([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "ppm_panel_call", "arguments": {"name": "get_selection", "args": {}}}}])
        t.join()
        self.assertIn('"count": 2', out[0]["result"]["content"][0]["text"])

    def test_unknown_method_is_an_error(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 9, "method": "nope"}])
        self.assertEqual(out[0]["error"]["code"], -32601)


class SetupMcpTests(unittest.TestCase):
    def test_dry_run_shows_commands_and_changes_nothing(self):
        d = make_server_dir(extra_dirs=[PARTS / "mcp-bridge" / "server"])
        proc = subprocess.run([sys.executable, str(d / "setup_mcp.py")], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60, env={**os.environ, "PATH": ""})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("試し実行", proc.stdout)


if __name__ == "__main__":
    unittest.main()
