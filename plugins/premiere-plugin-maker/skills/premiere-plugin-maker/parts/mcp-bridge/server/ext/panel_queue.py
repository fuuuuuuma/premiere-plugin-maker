"""AI（MCP）とパネルの間の待ち行列。パネルは 2 秒ごとに命令を取りに来る（サーバーからパネルへは送れない）。"""
import threading
import time
import uuid

_lock = threading.Lock()
_state = {"commands": [], "last_seen": 0.0, "queue": [], "results": {}}
_events = {}


def _next(req, ctx):
    with _lock:
        cmds = req["body"].get("commands")
        if isinstance(cmds, list):
            _state["commands"] = [{"name": str(c.get("name")), "description": str(c.get("description", ""))} for c in cmds if isinstance(c, dict)]
        _state["last_seen"] = time.time()
        if _state["queue"]:
            return 200, {"command": _state["queue"].pop(0)}
    return 200, {}


def _result(req, ctx):
    body = req["body"]
    with _lock:
        _state["results"][body.get("id")] = body
        ev = _events.get(body.get("id"))
    if ev:
        ev.set()
    return 200, {"ok": True}


def _status(req, ctx):
    with _lock:
        age = (time.time() - _state["last_seen"]) if _state["last_seen"] else None
        return 200, {"connected": age is not None and age < 6, "commands": list(_state["commands"])}


def _call(req, ctx):
    body = req["body"]
    name = str(body.get("name") or "")
    with _lock:
        known = [c["name"] for c in _state["commands"]]
        if known and name not in known:
            return 404, {"error": f"パネルに「{name}」という命令はありません", "commands": known}
        cid = uuid.uuid4().hex[:12]
        ev = threading.Event()
        _events[cid] = ev
        _state["queue"].append({"id": cid, "name": name, "args": body.get("args") or {}})
    ok = ev.wait(max(0.1, float(body.get("timeoutMs", 30000)) / 1000))
    with _lock:
        _events.pop(cid, None)
        res = _state["results"].pop(cid, None)
        if not ok:
            _state["queue"] = [c for c in _state["queue"] if c["id"] != cid]
    if not ok or res is None:
        return 504, {"error": "パネルから返事がありません", "next": "Premiere でこのプラグインのパネルを開いてください"}
    return 200, {"ok": bool(res.get("ok")), "result": res.get("result"), "error": res.get("error")}


ROUTES = {
    ("POST", "/panel/next"): _next,
    ("POST", "/panel/result"): _result,
    ("GET", "/panel/status"): _status,
    ("POST", "/panel/call"): _call,
}
