"""テストの共通部品。パスの定数と、一時フォルダ・道具の起動。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "premiere-plugin-maker"
SKILL = PLUGIN / "skills" / "premiere-plugin-maker"
SCRIPTS = SKILL / "scripts"
KNOWLEDGE = SKILL / "knowledge"
PARTS = SKILL / "parts"
TEMPLATES = SKILL / "templates"
EXAMPLES = SKILL / "examples"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def temp_dir(prefix: str = "ppm-test-") -> Path:
    """空白と日本語を含む一時フォルダを作る（Review Focus 1）。"""
    base = Path(tempfile.mkdtemp(prefix=prefix))
    path = base / "作業 フォルダ"
    path.mkdir()
    return path


def run_script(name: str, *args: str, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """SKILL/scripts/<name> を別プロセスで起動する。出力は UTF-8 で受け取る。"""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=full_env,
        cwd=str(cwd) if cwd else None,
        timeout=120,
    )
