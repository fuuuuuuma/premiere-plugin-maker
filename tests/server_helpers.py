"""local-server の部品を一時フォルダに写して、本物のサーバーとして起動するテスト用の道具。"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from helpers import PARTS, temp_dir

SERVER_SRC = PARTS / "local-server" / "server"


def make_server_dir(jobs=None, ext=None, app="PpmTest", extra_dirs=()) -> Path:
    d = temp_dir() / "server"
    shutil.copytree(SERVER_SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    for src in extra_dirs:
        shutil.copytree(src, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    (d / "config.json").write_text(json.dumps({"app": app, "version": "0.1.0", "protocol": 1, "port": 0}), encoding="utf-8")
    for name, code in (jobs or {}).items():
        (d / "jobs" / f"{name}.py").write_text(code, encoding="utf-8")
    for name, code in (ext or {}).items():
        (d / "ext" / f"{name}.py").write_text(code, encoding="utf-8")
    return d


class LiveServer:
    def __init__(self, server_dir: Path, app="PpmTest"):
        self.root = temp_dir()
        self.env = {**os.environ, "PPM_APP_SUPPORT_ROOT": str(self.root / "support"),
                    "PPM_LOG_ROOT": str(self.root / "logs"), "PYTHONUTF8": "1"}
        self.proc = subprocess.Popen([sys.executable, str(server_dir / "ppm_server.py")], env=self.env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.handshake_path = self.root / "support" / app / "server.json"
        deadline = time.time() + 20
        while time.time() < deadline and not self.handshake_path.exists():
            if self.proc.poll() is not None:
                raise RuntimeError("サーバーが起動しませんでした: " + self.proc.stderr.read().decode("utf-8", "replace"))
            time.sleep(0.1)
        self.info = json.loads(self.handshake_path.read_text(encoding="utf-8"))

    def call(self, path, body=None, token=True):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-PPM-Token"] = self.info["token"]
        req = urllib.request.Request(f"http://127.0.0.1:{self.info['httpPort']}{path}", data=data,
                                     method="POST" if body is not None else "GET", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")

    def wait_job(self, job_id, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            _, job = self.call(f"/jobs/{job_id}")
            if job["status"] in ("done", "error", "cancelled"):
                return job
            time.sleep(0.1)
        raise AssertionError("ジョブが終わりませんでした")

    def stop(self):
        if self.proc.poll() is None:
            if sys.platform == "win32":
                self.proc.terminate()
            else:
                self.proc.send_signal(signal.SIGTERM)
            self.proc.wait(timeout=10)
        self.proc.stderr.close()
