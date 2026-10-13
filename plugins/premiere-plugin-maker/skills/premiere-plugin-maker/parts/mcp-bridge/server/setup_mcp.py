#!/usr/bin/env python3
"""MCP を Claude Code / Codex に登録する。既定は試し実行。--apply で、入っている方だけに登録する（先に外してから足す）。
設定ファイルは手で書き換えない（各 CLI の登録の命令に任せる）。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = json.loads((HERE / "config.json").read_text(encoding="utf-8"))["app"]
NAME = f"{APP.lower()}-premiere"


def plan(python: str, script: Path) -> list:
    cmds = []
    if shutil.which("claude"):
        cmds.append((["claude", "mcp", "remove", NAME, "--scope", "user"], False))
        cmds.append((["claude", "mcp", "add", NAME, "--scope", "user", "--", python, str(script)], True))
    if shutil.which("codex"):
        cmds.append((["codex", "mcp", "remove", NAME], False))
        cmds.append((["codex", "mcp", "add", NAME, "--", python, str(script)], True))
    return cmds


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="MCP を登録する")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    cmds = plan(sys.executable, HERE / "ppm_mcp.py")
    if not cmds:
        print("claude も codex も見つかりません。どちらかを入れてから実行してください（試し実行・何もしていません）")
        return 0
    for c, _ in cmds:
        print("・" + " ".join(c))
    if not args.apply:
        print("（試し実行です。何もしていません。登録するときは --apply を付けます）")
        return 0
    failed = False
    for c, must in cmds:
        r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if must and r.returncode != 0:
            failed = True
            print(f"[NG!] {' '.join(c)}\n{r.stdout}{r.stderr}")
    print("登録しました。新しいセッションを開くと道具（ppm_health など）が使えます" if not failed else "登録に失敗したものがあります")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
