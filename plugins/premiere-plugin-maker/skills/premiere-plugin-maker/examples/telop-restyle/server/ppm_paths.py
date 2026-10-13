"""OS ごとのサーバーの置き場所。配った先でも動くよう、キットの道具に頼らずここだけで完結させる。
テストでは PPM_APP_SUPPORT_ROOT と PPM_LOG_ROOT で置き場所を変えられる。"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _home() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    return Path(os.environ.get("HOME") or Path.home())


def app_support(app: str) -> Path:
    root = os.environ.get("PPM_APP_SUPPORT_ROOT")
    if root:
        return Path(root) / app
    if sys.platform == "darwin":
        return _home() / "Library" / "Application Support" / app
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or (_home() / "AppData" / "Roaming")) / app
    return _home() / ".local" / "share" / app


def log_dir(app: str) -> Path:
    root = os.environ.get("PPM_LOG_ROOT")
    if root:
        return Path(root) / app
    if sys.platform == "darwin":
        return _home() / "Library" / "Logs" / app
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or (_home() / "AppData" / "Local")) / app / "Logs"
    return _home() / ".local" / "state" / app / "logs"
