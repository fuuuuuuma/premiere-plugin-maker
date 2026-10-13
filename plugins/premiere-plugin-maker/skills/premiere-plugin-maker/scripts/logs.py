#!/usr/bin/env python3
"""プラグインのログを読む（AI が「Premiere で何が起きたか」を確かめるため）。

  logs.py --project <作業フォルダ> [--lines 80] [--grep 文字] [--json] [--list]
  logs.py --plugin-id com.example.x [--tag x]
  logs.py --file <診断ボタンが表示したログのパス>
探す場所: プラグインのデータフォルダの ppm-log.txt（Mac・Windows）と、Mac の UXP ログ（UXPLogs_*.log）の印の行。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402
from lib import project as projlib  # noqa: E402


def find_plugin_logs(env, os_name: str, plugin_id: str, file_name: str = "ppm-log.txt", max_depth: int = 7) -> List[Path]:
    found: List[Path] = []
    for root in osinfo.plugin_storage_roots(env, os_name):
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            if depth >= max_depth:
                dirnames[:] = []
            if file_name in filenames and plugin_id in Path(dirpath).as_posix():
                found.append(Path(dirpath) / file_name)
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def find_uxp_logs(env, os_name: str, limit: int = 1) -> List[Path]:
    files: List[Path] = []
    for d in osinfo.uxp_log_dirs(env, os_name):
        files.extend(p for p in d.glob("UXPLogs_*.log") if p.is_file())
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def tail(path: Path, lines: int = 80, grep: Optional[str] = None, marker: Optional[str] = None) -> List[str]:
    text = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    if marker:
        text = [line for line in text if marker in line]
    if grep:
        text = [line for line in text if grep in line]
    return text[-lines:]


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="プラグインのログを読む")
    ap.add_argument("--project")
    ap.add_argument("--plugin-id")
    ap.add_argument("--tag")
    ap.add_argument("--file")
    ap.add_argument("--lines", type=int, default=80)
    ap.add_argument("--grep")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    plugin_id, tag = args.plugin_id, args.tag
    if args.project:
        info = projlib.load(Path(args.project).expanduser())
        plugin_id = plugin_id or info.get("pluginId")
        tag = tag or info.get("logTag")
    marker = f"[{tag}]" if tag else None
    plugin_files = [Path(args.file)] if args.file else (find_plugin_logs(os.environ, os_name, plugin_id) if plugin_id else [])
    uxp_files = find_uxp_logs(os.environ, os_name) if marker else []
    result = {
        "plugin": [{"path": str(p), "lines": [] if args.list else tail(p, args.lines, args.grep)} for p in plugin_files[:1]],
        "uxp": [{"path": str(p), "lines": [] if args.list else tail(p, args.lines, args.grep, marker)} for p in uxp_files],
    }
    if args.json:
        cli.print_json(result)
    else:
        for kind, title in (("plugin", "プラグインのログ"), ("uxp", "Premiere の UXP ログ（印の行だけ）")):
            for item in result[kind]:
                print(f"■ {title}: {item['path']}")
                for line in item["lines"]:
                    print("  " + line)
    if not plugin_files and not any(item["lines"] for item in result["uxp"]):
        print("ログが見つかりませんでした。パネルの「診断」を押すと保存場所が表示されるので、その場所を --file で渡してください。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
