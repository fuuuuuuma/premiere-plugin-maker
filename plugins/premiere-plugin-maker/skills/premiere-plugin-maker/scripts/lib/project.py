"""利用者のプラグインのフォルダの情報（.ppm/project.json）と、雛形の印の置き換え。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

from . import fsutil

PROJECT_FILE = Path(".ppm") / "project.json"


class ProjectError(ValueError):
    pass


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


def camel(slug: str) -> str:
    return "".join(w.capitalize() for w in slug.split("-") if w)


def new_info(name: str, label: Optional[str] = None, plugin_id: Optional[str] = None, author: Optional[str] = None,
             min_version: str = "25.6", template: str = "panel", kit_version: str = "") -> Dict:
    slug = slugify(name)
    if not slug:
        raise ProjectError("名前に英字を入れてください（例: Zoom Button）。日本語の表示名は --label で付けられます")
    shown = (label or name).strip()
    if any(c in shown for c in '"\\<>{}'):
        raise ProjectError("表示名に \" \\ < > { } は使えません")
    who = slugify(author or "").replace("-", "") or "ppm"
    pid = plugin_id or f"com.{who}.{slug.replace('-', '')}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", pid):
        raise ProjectError(f"id「{pid}」に使えない文字があります（英数字・ピリオド・ハイフンだけ）")
    return {"name": name.strip(), "label": shown, "slug": slug, "pluginId": pid, "panelId": "mainPanel",
            "appName": camel(slug), "logTag": slug, "version": "0.1.0", "minVersion": min_version,
            "template": template, "parts": [], "kitVersion": kit_version}


def placeholders(info: Dict) -> Dict[str, str]:
    return {"{{PLUGIN_ID}}": info["pluginId"], "{{PLUGIN_NAME}}": info["name"], "{{PANEL_ID}}": info["panelId"],
            "{{PANEL_LABEL}}": info["label"], "{{MIN_VERSION}}": info["minVersion"], "{{LOG_TAG}}": info["logTag"],
            "{{APP_NAME}}": info["appName"], "{{VERSION}}": info["version"], "{{SLUG}}": info["slug"]}


def substitute(text: str, mapping: Dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def load(project_dir) -> Dict:
    path = Path(project_dir) / PROJECT_FILE
    if not path.exists():
        raise ProjectError(f"{path} がありません。new_plugin.py で作ったフォルダを指定してください")
    return json.loads(path.read_text(encoding="utf-8"))


def save(project_dir, info: Dict) -> None:
    fsutil.atomic_write_text(Path(project_dir) / PROJECT_FILE, json.dumps(info, ensure_ascii=False, indent=2) + "\n")
