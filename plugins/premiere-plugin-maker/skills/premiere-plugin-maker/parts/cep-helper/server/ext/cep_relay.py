"""CEP の補助（再生・停止・分割）とパネルの間の中継。補助は自分ができる命令を名乗り、名乗った命令だけを受け取る。"""
import threading
import time
import uuid

_lock = threading.Lock()
_state = {"features": [], "last_seen": 0.0, "queue": [], "results": {}}
_events = {}


def _hello(req, ctx):
    with _lock:
        _state["features"] = [str(f) for f in (req["body"].get("features") or [])]
        _state["last_seen"] = time.time()
    return 200, {"ok": True}


def _next(req, ctx):
    with _lock:
        _state["last_seen"] = time.time()
        if _state["queue"]:
            return 200, {"command": _state["queue"].pop(0)}
    return 200, {}


def _result(req, ctx):
    body = req["body"]
    cid = body.get("id")
    with _lock:
        _state["results"][cid] = body
        ev = _events.get(cid)
    if ev:
        ev.set()
    return 200, {"ok": True}


def _status(req, ctx):
    with _lock:
        age = (time.time() - _state["last_seen"]) * 1000 if _state["last_seen"] else None
        return 200, {"connected": age is not None and age < 5000, "features": list(_state["features"]), "lastSeenMs": age}


def _commands(req, ctx):
    body = req["body"]
    name = str(body.get("name") or "")
    with _lock:
        if name not in _state["features"]:
            return 409, {"error": f"補助が「{name}」を名乗っていません", "next": "Premiere を再起動すると、新しい補助が読み込まれます"}
        cid = uuid.uuid4().hex[:12]
        ev = threading.Event()
        _events[cid] = ev
        _state["queue"].append({"id": cid, "name": name, "args": body.get("args") or {}})
    ok = ev.wait(max(0.1, float(body.get("timeoutMs", 10000)) / 1000))
    with _lock:
        _events.pop(cid, None)
        res = _state["results"].pop(cid, None)
        if not ok:
            _state["queue"] = [c for c in _state["queue"] if c["id"] != cid]
    if not ok or res is None:
        return 504, {"error": "補助から返事がありません", "next": "Premiere を開いたままにし、補助が入っているか確かめてください"}
    if not res.get("ok"):
        return 200, {"ok": False, "error": res.get("error") or "補助の処理が失敗しました"}
    return 200, {"ok": True, "result": res.get("result")}


ROUTES = {
    ("POST", "/cep/hello"): _hello,
    ("POST", "/cep/next"): _next,
    ("POST", "/cep/result"): _result,
    ("GET", "/cep/status"): _status,
    ("POST", "/cep/commands"): _commands,
}
