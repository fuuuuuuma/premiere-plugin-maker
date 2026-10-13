#!/usr/bin/env python3
"""CEP の補助を入れる。既定は試し実行（何もしない）。--apply で実行する。

- ユーザーの CEP の拡張フォルダへ写す（Mac ~/Library/Application Support/Adobe/CEP/extensions、Windows %APPDATA%\\Adobe\\CEP\\extensions）
- 未署名の拡張を許す設定（PlayerDebugMode）を CSXS 10〜13 に入れる。セキュリティの確かめを緩める設定なので、必ず利用者の許可を取ってから --apply する
- 入れた後は Premiere の再起動が要る
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSXS = [10, 11, 12, 13]


def ext_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Adobe" / "CEP" / "extensions"
    return Path(os.environ.get("HOME", str(Path.home()))) / "Library" / "Application Support" / "Adobe" / "CEP" / "extensions"


def debug_commands() -> list:
    if sys.platform == "win32":
        return [["reg", "add", f"HKCU\\Software\\Adobe\\CSXS.{n}", "/v", "PlayerDebugMode", "/t", "REG_SZ", "/d", "1", "/f"] for n in CSXS]
    return [["defaults", "write", f"com.adobe.CSXS.{n}", "PlayerDebugMode", "1"] for n in CSXS]


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="CEP の補助を入れる")
    ap.add_argument("--bundle-id", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    target = ext_dir() / args.bundle_id
    cmds = debug_commands()
    print(f"・写す: {HERE} → {target}")
    for c in cmds:
        print("・未署名の拡張を許す設定: " + " ".join(c))
    if not args.apply:
        print("（試し実行です。何もしていません。PlayerDebugMode はセキュリティの確かめを緩める設定なので、許可を取ってから --apply してください）")
        return 0
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(HERE, target, ignore=shutil.ignore_patterns("install_cep.py", "__pycache__"))
    for c in cmds:
        subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("入れました。Premiere を再起動すると補助が動きます")
    return 0


if __name__ == "__main__":
    sys.exit(main())
