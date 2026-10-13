#!/usr/bin/env python3
"""雛形から新しいプラグインの作業フォルダを作る（既にあれば上書きしない）。

使い方:
  Mac:     python3 <このスキル>/scripts/new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン"
  Windows: py -3 <このスキル>\\scripts\\new_plugin.py --template panel --name "Zoom Button" --label "ズームボタン"
  任意: --dest <フォルダ>（既定 ~/PremierePlugins/<名前>）、--id、--author <英字>、--min-version、--json、--list
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import add_part  # noqa: E402
from lib import cli, fsutil, osinfo, png  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
TEXT_SUFFIXES = {".json", ".html", ".js", ".css", ".md", ".txt", ".py", ".jsx", ".xml", ".plist", ".template",
                 ".command", ".ps1", ".bat", ".sh"}


def resolve_template(name: str, templates_dir: Path) -> dict:
    chain = []
    seen = set()
    current = name
    while current:
        if current in seen:
            raise ValueError(f"雛形の extends が輪になっています: {current}")
        seen.add(current)
        path = templates_dir / current / "template.json"
        if not path.exists():
            available = ", ".join(sorted(p.parent.name for p in templates_dir.glob("*/template.json")))
            raise ValueError(f"雛形「{current}」はありません。使えるのは: {available}")
        data = json.loads(path.read_text(encoding="utf-8"))
        chain.append(data)
        current = data.get("extends")
    chain.reverse()
    parts = []
    for t in chain:
        for p in t.get("parts", []):
            if p not in parts:
                parts.append(p)
    min_version = max((t.get("minVersion", "25.6") for t in chain), key=mf.version_tuple)
    return {"name": name, "files": templates_dir / (chain[0].get("files") or "_base"), "parts": parts, "minVersion": min_version}


def create_project(template: str, dest, name: str, label=None, plugin_id=None, author=None, min_version=None,
                   kit_dir: Path = SKILL_DIR) -> dict:
    kit_dir = Path(kit_dir)
    tpl = resolve_template(template, kit_dir / "templates")
    kit_version = (kit_dir / "VERSION").read_text(encoding="utf-8").strip() if (kit_dir / "VERSION").exists() else ""
    info = projlib.new_info(name, label, plugin_id, author, min_version or tpl["minVersion"], template, kit_version)
    dest = Path(dest) if dest else osinfo.default_projects_dir(os.environ, osinfo.detect_os()) / info["slug"]
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"{dest} は既にあります（上書きしません）。別の名前にするか --dest で空のフォルダを指定してください")
    created = not dest.exists()
    try:
        dest.mkdir(parents=True, exist_ok=True)
        mapping = projlib.placeholders(info)
        for src in sorted(p for p in tpl["files"].rglob("*") if p.is_file()):
            target = dest / src.relative_to(tpl["files"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() in TEXT_SUFFIXES:
                fsutil.write_text(target, projlib.substitute(src.read_text(encoding="utf-8"), mapping))
            else:
                shutil.copy2(src, target)
        color = png.color_for(info["slug"])
        (dest / "icons").mkdir(exist_ok=True)
        (dest / "icons" / "icon.png").write_bytes(png.rounded_icon(24, color))
        (dest / "icons" / "icon@1x.png").write_bytes(png.rounded_icon(24, color))
        (dest / "icons" / "icon@2x.png").write_bytes(png.rounded_icon(48, color))
        projlib.save(dest, info)
        installed = []
        for part in tpl["parts"]:
            installed.extend(add_part.add_part(dest, part, kit_dir)["installed"])
        return {"dest": str(dest), "info": projlib.load(dest), "parts": installed}
    except Exception:
        if created:
            shutil.rmtree(dest, ignore_errors=True)
        raise


def _next_steps(dest: str, label: str, os_name: str) -> str:
    py = osinfo.python_command(os_name)
    sep = "\\" if os_name == "windows" else "/"
    return "\n".join([
        f"作りました: {dest}",
        "次にすること:",
        f"  1. UXP Developer Tools の［Add Plugin］で {dest}{sep}manifest.json を選ぶ",
        "  2. ［Load］を押す（直したら［Reload］。manifest.json を変えたら［Unload］→［Load］）",
        f"  3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{label}」を開く",
        f"  4. 「診断」を押し、{py} <このスキル>{sep}scripts{sep}logs.py --project \"{dest}\" で結果を読む",
    ])


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="雛形から新しいプラグインを作る")
    ap.add_argument("--template", default="panel")
    ap.add_argument("--name")
    ap.add_argument("--label")
    ap.add_argument("--dest")
    ap.add_argument("--id", dest="plugin_id")
    ap.add_argument("--author")
    ap.add_argument("--min-version")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    templates = SKILL_DIR / "templates"
    if args.list:
        for p in sorted(templates.glob("*/template.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            print(f"{data['name']}: {data.get('description', '')}")
        return 0
    if not args.name:
        print("--name に英字の名前を入れてください（例: --name \"Zoom Button\" --label \"ズームボタン\"）")
        return 3
    try:
        result = create_project(args.template, args.dest, args.name, args.label, args.plugin_id, args.author, args.min_version)
    except FileExistsError as e:
        print(str(e))
        return 2
    except (ValueError, projlib.ProjectError, add_part.PartError, mf.ManifestError) as e:
        print(str(e))
        return 3
    if args.json:
        cli.print_json(result)
    else:
        print(_next_steps(result["dest"], result["info"]["label"], osinfo.detect_os()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
