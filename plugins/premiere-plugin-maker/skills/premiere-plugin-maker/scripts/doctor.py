#!/usr/bin/env python3
"""環境の診断。足りない物と直し方を表示する（何もインストールしない）。

使い方:
  Mac:     python3 <このスキル>/scripts/doctor.py [--json] [--online]
  Windows: py -3 <このスキル>\\scripts\\doctor.py [--json] [--online]
--online のときだけ、公開リポジトリの最新版の番号を 1 回読む。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, osinfo  # noqa: E402

SKILL_DIR = HERE.parent
VERSION_URL = "https://raw.githubusercontent.com/fuuuuuuma/premiere-plugin-maker/main/plugins/premiere-plugin-maker/skills/premiere-plugin-maker/VERSION"
MIN_PREMIERE = (25, 6, 0)


@dataclass
class Row:
    item: str
    ok: bool
    level: str
    detail: str
    fix: str = ""


def _vt(v: str):
    import re
    nums = [int(x) for x in re.findall(r"\d+", v)]
    return tuple(nums + [0] * (3 - len(nums)))[:3] if nums else (0, 0, 0)


def _read_kit_version() -> str:
    try:
        return (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as res:
        return res.read().decode("utf-8")


def collect(env, os_name: str, which: Callable[[str], Optional[str]] = shutil.which, online: bool = False,
            fetch: Optional[Callable[[str], str]] = None, kit_version: Optional[str] = None) -> List[Row]:
    rows: List[Row] = []
    rows.append(Row("OS", os_name in ("mac", "windows"), "情報", {"mac": "Mac", "windows": "Windows"}.get(os_name, os_name),
                    "" if os_name in ("mac", "windows") else "このスキルは Mac と Windows を対象にしています"))

    py_ok = sys.version_info >= (3, 9)
    rows.append(Row("Python", py_ok, "必須", sys.version.split()[0],
                    "" if py_ok else "Python 3.9 以上を入れてください（Mac: python.org か Homebrew、Windows: Python install manager）"))
    if os_name == "windows":
        alias = which("python") or ""
        has_py = bool(which("py"))
        store_stub = "WindowsApps" in alias
        rows.append(Row("Python（Windows）", has_py and not store_stub, "推奨",
                        ("py ランチャーがあります" if has_py else "py ランチャーが見つかりません")
                        + ("。python は Microsoft Store の仮の入口です" if store_stub else ""),
                        "" if has_py and not store_stub else
                        "python.org の Python install manager を入れ、以降は `py -3` で呼んでください。"
                        "python で Store が開くときは［設定］→［アプリ実行エイリアス］で python をオフにします"))

    installs = osinfo.premiere_installs(env, os_name)
    usable = [i for i in installs if i.version.endswith(".x") or _vt(i.version) >= MIN_PREMIERE]
    detail = "、".join(f"{i.name}（{i.version or '版不明'}）" for i in installs) or "見つかりません"
    rows.append(Row("Premiere", bool(usable), "必須", detail,
                    "" if usable else "Creative Cloud デスクトップから Premiere 25.6 以降（推奨 26.x）を入れてください"))

    udt = osinfo.udt_app(env, os_name)
    rows.append(Row("UXP Developer Tools", bool(udt), "必須", str(udt) if udt else "見つかりません",
                    "" if udt else "Creative Cloud デスクトップ →［すべてのアプリ］→「UXP Developer Tools」を入れてください（初回は管理者の許可が要ります）"))

    settings = osinfo.udt_settings_file(env, os_name)
    dev_ok = False
    try:
        dev_ok = bool(json.loads(settings.read_text(encoding="utf-8")).get("developer"))
    except (OSError, ValueError, AttributeError):
        dev_ok = False
    rows.append(Row("開発者モード（UDT 側）", dev_ok, "推奨", str(settings) if dev_ok else "まだ有効になっていません",
                    "" if dev_ok else "UXP Developer Tools を起動すると出る案内で Enable を押してください。"
                    "Premiere 側も［設定］→［プラグイン］で開発者モードをオンにして再起動します"))

    upia = osinfo.upia_path(env, os_name)
    rows.append(Row("プラグインの導入ツール（UPIA）", upia.exists(), "任意", str(upia) if upia.exists() else "見つかりません",
                    "" if upia.exists() else "Creative Cloud デスクトップに同梱されています。.ccx を配るときだけ要ります"))

    ffmpeg = which("ffmpeg")
    rows.append(Row("ffmpeg", bool(ffmpeg), "任意", ffmpeg or "見つかりません",
                    "" if ffmpeg else ("音声を扱う部品で要ります。Mac: brew install ffmpeg" if os_name == "mac"
                                       else "音声を扱う部品で要ります。Windows: winget install --id Gyan.FFmpeg -e（入れた後は新しい画面で確かめる）")))

    git = which("git")
    rows.append(Row("git", bool(git), "任意", git or "見つかりません", "" if git else "キットを取ってくる・更新するときに使います"))

    local = kit_version if kit_version is not None else _read_kit_version()
    if online:
        try:
            latest = (fetch or _fetch)(VERSION_URL).strip()
            newer = _vt(latest) > _vt(local)
            rows.append(Row("キットの版", not newer, "推奨", f"手元 {local} / 最新 {latest}",
                            "新しい版があります。Claude Code: claude plugin marketplace update premiere-plugin-maker → "
                            "claude plugin update premiere-plugin-maker@premiere-plugin-maker／Codex: codex plugin marketplace upgrade premiere-plugin-maker"
                            if newer else ""))
        except Exception:  # noqa: BLE001  ネットが無いときも診断は止めない
            rows.append(Row("キットの版", True, "情報", f"手元 {local}（最新の版は確かめられませんでした）", ""))
    else:
        rows.append(Row("キットの版", True, "情報", f"手元 {local}", ""))
    return rows


def _mark(row: Row) -> str:
    if row.ok:
        return "[OK ]"
    return "[NG!]" if row.level == "必須" else "[注意]"


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="Premiere プラグイン作りの環境を診断する")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--online", action="store_true")
    args = ap.parse_args(argv)
    os_name = osinfo.detect_os()
    rows = collect(os.environ, os_name, online=args.online)
    fatal = [r for r in rows if r.level == "必須" and not r.ok]
    if args.json:
        cli.print_json({"os": os_name, "ok": not fatal, "rows": [asdict(r) for r in rows]})
    else:
        for r in rows:
            print(f"{_mark(r)} {r.item}: {r.detail}")
            if r.fix and not r.ok:
                print(f"      直し方: {r.fix}")
        print()
        print("必須はそろっています。" if not fatal else "必須が足りません: " + "、".join(r.item for r in fatal))
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
