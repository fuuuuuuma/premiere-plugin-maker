#!/usr/bin/env python3
"""作ったプラグインを機械で検査する。過去に実機で起きた失敗を、実機に入れる前に止めるための門。

使い方:
  Mac:     python3 <このスキル>/scripts/check.py <プラグインのフォルダ> [--json] [--strict]
  Windows: py -3 <このスキル>\\scripts\\check.py <プラグインのフォルダ> [--json] [--strict]
誤りが 1 件でもあれば終了コード 1。誤りは必ず直す。注意は理由を読んで判断する。
1 行だけ規則を外すときは、その行か直前の行に「ppm-ignore: J010」のような注釈を書く。
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import checks, cli  # noqa: E402

SKILL_DIR = HERE.parent


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="プラグインを機械で検査する")
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.project).expanduser()
    if not (root / "manifest.json").exists():
        print(f"manifest.json が見つかりません: {root}\nプラグインのフォルダ（manifest.json がある所）を指定してください。")
        return 2
    found = checks.run_all(root, SKILL_DIR)
    errors = [f for f in found if f.severity == "error" or (args.strict and f.severity == "warn")]
    if args.json:
        cli.print_json({"ok": not errors, "errors": len(errors), "warnings": len(found) - len(errors),
                        "findings": [asdict(f) for f in found]})
    else:
        for file, group in groupby(sorted(found, key=lambda f: (f.file, f.line)), key=lambda f: f.file):
            print(f"■ {file}")
            for f in group:
                kind = "誤り" if f.severity == "error" or args.strict else "注意"
                where = f"{f.line} 行目" if f.line else "全体"
                print(f"  [{kind}] {where}（{f.rule}）: {f.message}")
                print(f"        なぜ: {f.why}")
                print(f"        直し方: {f.fix}")
        print(f"\n誤り {len(errors)} 件・注意 {len(found) - len(errors)} 件")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
