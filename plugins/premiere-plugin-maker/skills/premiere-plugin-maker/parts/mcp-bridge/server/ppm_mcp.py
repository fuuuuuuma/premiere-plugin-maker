#!/usr/bin/env python3
"""AI（Claude Code / Codex）からプラグインを操作する MCP（標準入出力・JSON-RPC 2.0・1 行に 1 つ）。

手元のサーバーの server.json を読み、合言葉を付けて /panel/* を呼ぶ。標準ライブラリだけ。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
SUPPORTED = ["2025-06-18", "2025-03-26", "2024-11-05"]
TOOLS = [
    {"name": "ppm_health", "description": f"{APP} のサーバーとパネルがつながっているかを調べる（最初に呼ぶ）",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ppm_panel_commands", "description": "パネルが受け付ける命令の一覧（名前と説明）",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "ppm_panel_call", "description": "パネルの命令を呼ぶ。Premiere を変える命令は、利用者の実行の指示があるときだけ使う",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "args": {"type": "object"}}, "required": ["name"]}},
]


def _server(path: str, body=None, timeout: float = 40.0):
    info = json.loads((ppm_paths.app_support(APP) / "server.json").read_text(encoding="utf-8"))
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{info['httpPort']}{path}", data=data, method="POST" if body is not None else "GET",
                                 headers={"Content-Type": "application/json", "X-PPM-Token": info["token"]})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def _text(obj) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, indent=1) if not isinstance(obj, str) else obj}]}


def call_tool(name: str, args: dict) -> dict:
    try:
        if name == "ppm_health":
            _, ping = _server("/ping")
            _, status = _server("/panel/status")
            note = "パネルはつながっています" if status.get("connected") else "パネルが開いていません。Premiere でこのプラグインのパネルを開いてください"
            return _text({"server": ping, "panel": status, "note": note})
        if name == "ppm_panel_commands":
            return _text(_server("/panel/status")[1].get("commands", []))
        if name == "ppm_panel_call":
            code, data = _server("/panel/call", {"name": args.get("name"), "args": args.get("args") or {}, "timeoutMs": 30000})
            return {**_text(data), "isError": code != 200 or not data.get("ok")}
    except FileNotFoundError:
        return {**_text("サーバーが動いていません（server.json がありません）。server の install を実行してください"), "isError": True}
    except (urllib.error.URLError, OSError) as e:
        return {**_text(f"サーバーにつながりません（{e}）"), "isError": True}
    return {**_text(f"知らない道具: {name}"), "isError": True}


def handle(msg: dict):
    method = msg.get("method")
    mid = msg.get("id")
    if mid is None:
        return None  # 通知には返事をしない
    if method == "initialize":
        want = (msg.get("params") or {}).get("protocolVersion")
        version = want if want in SUPPORTED else SUPPORTED[0]
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": version, "capabilities": {"tools": {}},
                                                       "serverInfo": {"name": f"{APP.lower()}-premiere", "version": CONFIG.get("version", "0")}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        return {"jsonrpc": "2.0", "id": mid, "result": call_tool(params.get("name"), params.get("arguments") or {})}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"知らない method: {method}"}}


def main() -> int:
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON が読めません"}}), flush=True)
            continue
        reply = handle(msg)
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
