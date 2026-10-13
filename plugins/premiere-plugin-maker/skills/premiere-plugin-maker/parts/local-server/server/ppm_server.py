#!/usr/bin/env python3
"""プラグイン用の手元のサーバー（127.0.0.1 だけで待つ）。

- 起動ごとに合言葉（token）を作り、server.json に書く（待ち受けを始めてから・0600・原子的に置き換え）
- パネルはヘッダー X-PPM-Token に合言葉を付けて呼ぶ。違えば 403
- 重い処理は「ジョブ」として 1 本ずつ動かす（POST /jobs/<種類> → GET /jobs/<id>）
- ジョブが失敗しても HTTP は 200 で {"status": "error"} を返す（通信の失敗と区別するため）
- 追加の口は server/ext/*.py の ROUTES に書く（mcp-bridge・cep-helper の部品が使う）
"""
from __future__ import annotations

import importlib
import json
import os
import secrets
import signal
import sys
import threading
import time
import traceback
import uuid
import socketserver
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402
from ppm_jobs import JobError  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
VERSION = CONFIG.get("version", "0.0.0")
PROTOCOL = int(CONFIG.get("protocol", 1))
TOKEN = secrets.token_hex(16)
APP_DIR = ppm_paths.app_support(APP)
TMP_DIR = APP_DIR / "tmp"
LOG_FILE = ppm_paths.log_dir(APP) / "server.log"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1_000_000:
        os.replace(LOG_FILE, LOG_FILE.with_name("server.log.1"))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


class Job:
    def __init__(self, kind: str, params: dict):
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.params = params
        self.status = "queued"
        self.percent = 0
        self.message = ""
        self.result = None
        self.error = None
        self.cancel_event = threading.Event()

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "status": self.status, "percent": self.percent,
                "message": self.message, "result": self.result, "error": self.error}


class JobContext:
    def __init__(self, job: Job):
        self._job = job
        self.tmp_dir = str(TMP_DIR)
        self.app = APP

    def progress(self, percent: float, message: str = "") -> None:
        self._job.percent = max(0, min(100, int(percent)))
        if message:
            self._job.message = message

    def cancelled(self) -> bool:
        return self._job.cancel_event.is_set()

    def log(self, msg: str) -> None:
        log(f"[{self._job.kind}] {msg}")


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = {}
        self.running = None

    def start(self, kind: str, params: dict, fn) -> Job:
        with self.lock:
            if self.running is not None and self.running.status in ("queued", "running"):
                raise RuntimeError("busy")
            job = Job(kind, params)
            self.jobs[job.id] = job
            self.running = job
        threading.Thread(target=self._run, args=(job, fn), daemon=True).start()
        return job

    def _run(self, job: Job, fn) -> None:
        job.status = "running"
        try:
            job.result = fn(job.params, JobContext(job))
            if job.cancel_event.is_set():
                job.status = "cancelled"
            else:
                job.status = "done"
                job.percent = 100
        except JobError as e:
            job.status = "error"
            job.error = {"message": str(e), "why": e.why, "next": e.next_step}
            log(f"[{job.kind}] error: {e}")
        except Exception as e:  # noqa: BLE001  想定外も理由を返す
            job.status = "error"
            job.error = {"message": f"{e}（{type(e).__name__}）", "why": "思わぬ失敗です",
                         "next": f"{LOG_FILE} の内容を AI に伝えてください"}
            log(f"[{job.kind}] crash: {traceback.format_exc()}")


STORE = Store()
JOBS = {}
ROUTES = {}


def load_modules(folder: str) -> list:
    mods = []
    for path in sorted((HERE / folder).glob("*.py")):
        if not path.name.startswith("_"):
            mods.append(importlib.import_module(f"{folder}.{path.stem}"))
    return mods


class Handler(BaseHTTPRequestHandler):
    server_version = "ppm"

    def log_message(self, fmt, *args):  # 呼び出しのたびの記録はしない（ポーリングでログが膨らむ）
        pass

    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-PPM-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}

    def _dispatch(self, method: str) -> None:
        if not secrets.compare_digest(self.headers.get("X-PPM-Token", ""), TOKEN):
            return self._send(403, {"error": "合言葉が違います", "next": "パネルを開き直してください（サーバーを起動し直すと合言葉が変わります）"})
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        try:
            body = self._body() if method == "POST" else {}
        except ValueError:
            return self._send(400, {"error": "送られてきた JSON が読めません"})
        if method == "GET" and parts == ["ping"]:
            return self._send(200, {"ok": True, "app": APP, "version": VERSION, "protocol": PROTOCOL, "jobs": sorted(JOBS)})
        if method == "POST" and len(parts) == 2 and parts[0] == "jobs":
            fn = JOBS.get(parts[1])
            if fn is None:
                return self._send(404, {"error": f"ジョブ「{parts[1]}」はありません", "jobs": sorted(JOBS)})
            try:
                job = STORE.start(parts[1], body, fn)
            except RuntimeError:
                return self._send(409, {"error": "別の処理が動いています。終わるまで待ってください"})
            return self._send(202, {"jobId": job.id})
        if method == "GET" and len(parts) == 2 and parts[0] == "jobs":
            job = STORE.jobs.get(parts[1])
            return self._send(200, job.to_dict()) if job else self._send(404, {"error": "そのジョブはありません"})
        if method == "POST" and len(parts) == 3 and parts[0] == "jobs" and parts[2] == "cancel":
            job = STORE.jobs.get(parts[1])
            if job is None:
                return self._send(404, {"error": "そのジョブはありません"})
            job.cancel_event.set()
            return self._send(200, {"ok": True})
        handler = ROUTES.get((method, url.path))
        if handler is not None:
            code, obj = handler({"path": url.path, "query": parse_qs(url.query), "body": body},
                                {"token": TOKEN, "app": APP, "tmp_dir": str(TMP_DIR), "log": log})
            return self._send(code, obj)
        return self._send(404, {"error": "その口はありません"})

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def write_handshake(port: int) -> Path:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    data = {"pid": os.getpid(), "httpPort": port, "token": TOKEN, "version": VERSION, "protocol": PROTOCOL,
            "tmpDir": str(TMP_DIR), "serverDir": str(HERE)}
    path = APP_DIR / "server.json"
    tmp = APP_DIR / f".server.json.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    return path


def remove_handshake() -> None:
    path = APP_DIR / "server.json"
    try:
        if json.loads(path.read_text(encoding="utf-8")).get("pid") == os.getpid():
            path.unlink()
    except (OSError, ValueError):
        pass


def _stop(*_args):
    raise KeyboardInterrupt


class _Server(ThreadingHTTPServer):
    def server_bind(self):
        # 標準の HTTPServer は socket.getfqdn で自分の名前を DNS に聞く。ネットの設定によっては長く止まる（GitHub の Mac で 20 秒以上）。
        # 127.0.0.1 だけで待つので名前は要らない
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


def make_httpd(port: int) -> ThreadingHTTPServer:
    return _Server(("127.0.0.1", port), Handler)


def main() -> int:
    if sys.stdout is None or sys.stderr is None:  # pythonw（Windows の常駐）では標準出力が無い
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(LOG_FILE, "a", encoding="utf-8")
    for mod in load_modules("jobs"):
        if hasattr(mod, "NAME") and hasattr(mod, "run"):
            JOBS[mod.NAME] = mod.run
    for mod in load_modules("ext"):
        ROUTES.update(getattr(mod, "ROUTES", {}))
    port = int(os.environ.get("PPM_PORT") or CONFIG.get("port", 0))
    try:
        httpd = make_httpd(port)
    except OSError as e:
        log(f"待ち受けを始められません（{e}）。同じポートを別のサーバーが使っていないか確かめてください")
        return 1
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)
    write_handshake(httpd.server_address[1])
    log(f"started {APP} {VERSION} on 127.0.0.1:{httpd.server_address[1]} jobs={sorted(JOBS)} routes={sorted(p for _, p in ROUTES)}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        remove_handshake()
    return 0


if __name__ == "__main__":
    sys.exit(main())
