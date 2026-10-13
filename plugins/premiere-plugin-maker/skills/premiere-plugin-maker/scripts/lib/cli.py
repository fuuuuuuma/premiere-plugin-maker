"""道具の共通の作法（標準出力の文字コード・JSON の出力）。"""
from __future__ import annotations

import json
import sys


def setup_stdio() -> None:
    """Windows の cp932 の画面やパイプでも、日本語で落ちないようにする。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))
