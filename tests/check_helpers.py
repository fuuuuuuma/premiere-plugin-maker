"""check.py のテスト用に、小さなプラグインのフォルダを作る。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from helpers import SKILL, temp_dir
from lib import checks

GOOD_MANIFEST = {
    "manifestVersion": 5,
    "id": "com.example.test",
    "name": "Test Plugin",
    "version": "0.1.0",
    "main": "index.html",
    "host": {"app": "premierepro", "minVersion": "25.6", "data": {"apiVersion": 2, "loadEvent": "startup"}},
    "entrypoints": [{"type": "panel", "id": "mainPanel", "label": {"default": "テスト"}}],
    "icons": [{"width": 24, "height": 24, "path": "icons/icon.png", "scale": [1, 2], "theme": ["all"], "species": "generic"}],
    "requiredPermissions": {"localFileSystem": "plugin"},
}

GOOD_HTML = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><title>T</title>
<link rel="stylesheet" href="panel.css" /></head>
<body><button id="run" type="button">実行</button><script src="index.js"></script></body></html>
"""

GOOD_JS = """let ppro = null;
try { ppro = require("premierepro"); } catch (e) {}
function boot() {}
if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", boot); } else { boot(); }
"""


def make_project(files=None, manifest=None) -> Path:
    root = temp_dir()
    data = copy.deepcopy(GOOD_MANIFEST) if manifest is None else manifest
    base = {"index.html": GOOD_HTML, "index.js": GOOD_JS, "panel.css": "title { display: none; }\n",
            "icons/icon.png": b"\x89PNG\r\n\x1a\n", "build_info.json": {"name": "Test Plugin", "version": "0.1.0"},
            ".ppm/project.json": {"name": "Test Plugin", "pluginId": "com.example.test"}}
    base.update(files or {})
    if data is not None:
        base.setdefault("manifest.json", data)
    for rel, content in base.items():
        if content is None:
            continue
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        elif isinstance(content, (dict, list)):
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")
    return root


def findings(root: Path):
    return checks.run_all(root, SKILL)


def rules(root: Path):
    return {f.rule for f in findings(root)}
