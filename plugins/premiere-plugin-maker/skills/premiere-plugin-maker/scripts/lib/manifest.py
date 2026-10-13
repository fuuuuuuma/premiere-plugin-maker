"""UXP の manifest.json を読む・書く・部品の要る権限を足す。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

LFS_ORDER = ["plugin", "request", "fullAccess"]
CLIPBOARD_ORDER = ["read", "readAndWrite"]


class ManifestError(ValueError):
    pass


def load(path) -> Dict[str, Any]:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ManifestError(f"manifest.json が見つかりません: {path}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestError(
            f"manifest.json の {e.lineno} 行目 {e.colno} 文字目が JSON として読めません（{e.msg}）。"
            "コメントや末尾のカンマは書けません"
        ) from None
    if not isinstance(data, dict):
        raise ManifestError("manifest.json の一番外側が { } ではありません")
    return data


def save(path, data: Dict[str, Any]) -> None:
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def version_tuple(v: str) -> Tuple[int, int, int]:
    m = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(v).strip())
    if not m:
        raise ValueError(f"版数の形が違います: {v}")
    a, b, c = (int(x) if x else 0 for x in m.groups())
    return (a, b, c)


def min_version(data: Dict[str, Any]) -> str:
    host = data.get("host")
    return str(host.get("minVersion", "")) if isinstance(host, dict) else ""


def raise_min_version(data: Dict[str, Any], needed: str) -> bool:
    host = data.setdefault("host", {})
    current = host.get("minVersion")
    if not current or version_tuple(current) < version_tuple(needed):
        host["minVersion"] = needed
        return True
    return False


def merge_permissions(data: Dict[str, Any], perms: Dict[str, Any]) -> List[str]:
    """部品が要る権限を足す。弱い権限は強くするが、強い権限を弱めない。変えた項目名を返す。"""
    rp = data.setdefault("requiredPermissions", {})
    changed: List[str] = []
    for key, val in perms.items():
        if key == "localFileSystem":
            current = rp.get(key, "plugin")
            if LFS_ORDER.index(val) > LFS_ORDER.index(current) or key not in rp:
                rp[key] = max(val, current, key=LFS_ORDER.index)
                changed.append(key)
        elif key == "network":
            current = (rp.get("network") or {}).get("domains")
            want = val.get("domains")
            if current == "all":
                continue
            if want == "all":
                rp["network"] = {"domains": "all"}
                changed.append(key)
                continue
            merged = sorted(set(current or []) | set(want or []))
            if merged != (current or []):
                rp["network"] = {"domains": merged}
                changed.append(key)
        elif key == "clipboard":
            current = rp.get(key)
            if current is None or CLIPBOARD_ORDER.index(val) > CLIPBOARD_ORDER.index(current):
                rp[key] = val
                changed.append(key)
        elif key == "launchProcess":
            current = rp.get(key) or {"schemes": [], "extensions": []}
            new = {
                "schemes": sorted(set(current.get("schemes", [])) | set(val.get("schemes", []))),
                "extensions": sorted(set(current.get("extensions", [])) | set(val.get("extensions", []))),
            }
            if new != current:
                rp[key] = new
                changed.append(key)
        elif isinstance(val, bool):
            if val and not rp.get(key):
                rp[key] = True
                changed.append(key)
        elif rp.get(key) != val:
            rp[key] = val
            changed.append(key)
    return changed


def merge_feature_flags(data: Dict[str, Any], flags: Dict[str, bool]) -> List[str]:
    ff = data.setdefault("featureFlags", {})
    changed = []
    for key, val in flags.items():
        if val and not ff.get(key):
            ff[key] = True
            changed.append(key)
    return changed


def add_entrypoints(data: Dict[str, Any], entries: List[Dict[str, Any]]) -> List[str]:
    eps = data.setdefault("entrypoints", [])
    existing = {e.get("id") for e in eps}
    added = []
    for e in entries:
        if e.get("id") in existing:
            continue
        eps.append(e)
        existing.add(e.get("id"))
        added.append(e["id"])
    return added
