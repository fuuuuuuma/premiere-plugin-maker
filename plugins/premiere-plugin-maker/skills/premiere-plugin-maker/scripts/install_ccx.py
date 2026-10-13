#!/usr/bin/env python3
"""Adobe の導入ツール（UPIA）で .ccx を入れる・外す・一覧を見る。既定は試し実行（コマンドを見せるだけ）。

使い方:
  Mac:     python3 <このスキル>/scripts/install_ccx.py --reinstall <ファイル.ccx> --apply
  Windows: py -3 <このスキル>\\scripts\\install_ccx.py --reinstall <ファイル.ccx> --apply
  --install <ccx> / --reinstall <ccx>（先に外してから入れる）/ --remove <プラグイン名> / --list
同じ版数のまま入れ直しても更新されないことがあるので、作り直したら --reinstall を使う。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402


def upia_command(os_name: str, upia, action: str, arg=None) -> List[str]:
    prefix = "/" if os_name == "windows" else "--"
    cmd = [str(upia), prefix + action]
    if action == "list":
        cmd.append("all")
    elif arg is not None:
        cmd.append(str(arg))
    return cmd


def plugin_name_in_ccx(path) -> str:
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("manifest.json").decode("utf-8"))["name"]


def run(cmds, runner) -> List[dict]:
    results = []
    for cmd, must_succeed in cmds:
        proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        out = (proc.stdout or "") + (proc.stderr or "")
        ok = proc.returncode == 0 or "successful" in out.lower()
        results.append({"command": cmd, "ok": ok, "required": must_succeed, "output": out.strip()})
    return results


def main(argv=None, runner=subprocess.run) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="UPIA で .ccx を入れる・外す")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--install")
    group.add_argument("--reinstall")
    group.add_argument("--remove")
    group.add_argument("--list", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--upia")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    upia = Path(args.upia) if args.upia else osinfo.upia_path(os.environ, os_name)
    cmds = []
    if args.list:
        cmds.append((upia_command(os_name, upia, "list"), True))
    elif args.remove:
        cmds.append((upia_command(os_name, upia, "remove", args.remove), True))
    else:
        ccx = Path(args.install or args.reinstall).expanduser().resolve()
        if args.reinstall:
            cmds.append((upia_command(os_name, upia, "remove", plugin_name_in_ccx(ccx)), False))
        cmds.append((upia_command(os_name, upia, "install", ccx), True))
    if not args.apply:
        print("試し実行です（まだ何もしていません）。実行するときは --apply を付けます:")
        for cmd, _ in cmds:
            print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
        return 0
    if not upia.exists() and not args.upia:
        print(f"UPIA が見つかりません: {upia}\nCreative Cloud デスクトップを入れてください。.ccx のダブルクリックでも入れられます。")
        return 1
    results = run(cmds, runner)
    failed = [r for r in results if r["required"] and not r["ok"]]
    if args.json:
        cli.print_json({"ok": not failed, "results": results})
    else:
        for r in results:
            print(("[OK ] " if r["ok"] else ("[NG!] " if r["required"] else "[注意] ")) + " ".join(r["command"]))
            if r["output"]:
                print("      " + r["output"].replace("\n", "\n      "))
        if not failed:
            print("入れました。Premiere の［ウィンドウ］→［UXP プラグイン］に出ないときは、Premiere を再起動してください。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
