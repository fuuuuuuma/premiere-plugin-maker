#!/usr/bin/env python3
"""作業フォルダに部品を足す。ファイルを写し、index.html の読み込みと manifest の権限・最低版をそろえる。

使い方:
  Mac:     python3 <このスキル>/scripts/add_part.py <部品> --project <作業フォルダ>
  Windows: py -3 <このスキル>\\scripts\\add_part.py <部品> --project <作業フォルダ>
  --list で使える部品の一覧。同じ部品を 2 回足しても何も変えない。利用者が書き換えたファイルは上書きしない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, fsutil  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
PART_KEYS = {"name", "description", "status", "os", "requires", "files", "scripts", "styles", "permissions",
             "featureFlags", "entrypoints", "minVersion", "pythonDeps", "knowledge", "notes"}
DEFAULTS = {"requires": [], "files": {}, "scripts": [], "styles": [], "permissions": {}, "featureFlags": {},
            "entrypoints": [], "minVersion": "25.6", "pythonDeps": [], "knowledge": [], "notes": "",
            "os": ["mac", "windows"], "status": "unverified"}
STATUSES = ("verified", "partial", "unverified")
SCRIPTS_END = "<!-- ppm:scripts-end -->"
STYLES_END = "<!-- ppm:styles-end -->"
TEXT_SUFFIXES = {".json", ".html", ".js", ".css", ".md", ".txt", ".py", ".jsx", ".xml", ".plist", ".template",
                 ".command", ".ps1", ".bat", ".sh"}


class PartError(ValueError):
    pass


def list_parts(parts_dir: Path = SKILL_DIR / "parts") -> List[str]:
    return sorted(p.parent.name for p in Path(parts_dir).glob("*/part.json"))


def load_part(name: str, parts_dir: Path = SKILL_DIR / "parts") -> Dict:
    path = Path(parts_dir) / name / "part.json"
    if not path.exists():
        raise PartError(f"部品「{name}」はありません。使えるのは: {', '.join(list_parts(parts_dir))}")
    data = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(data) - PART_KEYS
    if unknown:
        raise PartError(f"{path} に知らない項目があります: {', '.join(sorted(unknown))}")
    for key, value in DEFAULTS.items():
        data.setdefault(key, json.loads(json.dumps(value)))
    return data


def _expand_files(part_dir: Path, mapping: Dict[str, str]) -> List[Tuple[Path, str]]:
    out: List[Tuple[Path, str]] = []
    for src_rel, dst_rel in mapping.items():
        src = part_dir / src_rel
        if src.is_dir():
            for p in sorted(x for x in src.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix != ".pyc"):
                out.append((p, (Path(dst_rel) / p.relative_to(src)).as_posix()))
        elif src.is_file():
            out.append((src, dst_rel))
        else:
            raise PartError(f"部品のファイル {src} がありません")
    return out


def _render(src: Path, mapping: Dict[str, str]) -> bytes:
    if src.suffix.lower() in TEXT_SUFFIXES:
        return projlib.substitute(src.read_text(encoding="utf-8"), mapping).encode("utf-8")
    return src.read_bytes()


def _insert_tags(html: str, scripts: List[str], styles: List[str]) -> str:
    if scripts and SCRIPTS_END not in html:
        raise PartError(f"index.html に {SCRIPTS_END} の印がありません。雛形の index.html と同じ印を、index.js を読む行の上に戻してください")
    if styles and STYLES_END not in html:
        raise PartError(f"index.html に {STYLES_END} の印がありません。雛形と同じ印を <head> の中に戻してください")
    for s in scripts:
        tag = f'<script src="{s}"></script>'
        if tag not in html:
            html = html.replace(SCRIPTS_END, f"{tag}\n  {SCRIPTS_END}", 1)
    for s in styles:
        tag = f'<link rel="stylesheet" href="{s}">'
        if tag not in html:
            html = html.replace(STYLES_END, f"{tag}\n  {STYLES_END}", 1)
    return html


def add_part(project_dir, name: str, kit_dir: Path = SKILL_DIR, _stack=None) -> Dict:
    project_dir = Path(project_dir)
    kit_dir = Path(kit_dir)
    parts_dir = kit_dir / "parts"
    info = projlib.load(project_dir)
    result = {"part": name, "installed": [], "already": False, "files": [], "manifest": []}
    if name in info.get("parts", []):
        result["already"] = True
        return result
    stack = list(_stack or [])
    if name in stack:
        raise PartError("部品の requires が輪になっています: " + " → ".join(stack + [name]))
    part = load_part(name, parts_dir)
    manifest_path = project_dir / "manifest.json"
    mf.load(manifest_path)  # 壊れていたら ManifestError で止める（何も書き換えない）
    for req in part["requires"]:
        result["installed"].extend(add_part(project_dir, req, kit_dir, stack + [name])["installed"])
    info = projlib.load(project_dir)
    data = mf.load(manifest_path)
    mapping = projlib.placeholders(info)

    plan = []
    for src, dst_rel in _expand_files(parts_dir / name, part["files"]):
        content = _render(src, mapping)
        target = project_dir / dst_rel
        if target.exists():
            if target.read_bytes() == content:
                continue
            raise PartError(f"{dst_rel} は既にあり、中身が違います（上書きしません）。書き換えたなら、部品の中身と見比べて手で合わせてください")
        plan.append((target, content, src))
    html_path = project_dir / (data.get("main") or "index.html")
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    new_html = _insert_tags(html, part["scripts"], part["styles"]) if html_path.exists() else html

    changes = mf.merge_permissions(data, part["permissions"])
    changes += mf.merge_feature_flags(data, part["featureFlags"])
    entries = [json.loads(projlib.substitute(json.dumps(e, ensure_ascii=False), mapping)) for e in part["entrypoints"]]
    changes += [f"entrypoint:{x}" for x in mf.add_entrypoints(data, entries)]
    if part["minVersion"] and mf.raise_min_version(data, part["minVersion"]):
        changes.append(f"minVersion:{part['minVersion']}")
        info["minVersion"] = data["host"]["minVersion"]

    # ここから書き込む（確かめ終わってから）
    for target, content, src in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if src.suffix in (".command", ".sh"):
            target.chmod(0o755)
        result["files"].append(target.relative_to(project_dir).as_posix())
    if new_html != html:
        fsutil.write_text(html_path, new_html)
    mf.save(manifest_path, data)
    if part["pythonDeps"]:
        req = project_dir / "server" / "requirements.txt"
        lines = req.read_text(encoding="utf-8").splitlines() if req.exists() else []
        for dep in part["pythonDeps"]:
            if dep not in lines:
                lines.append(dep)
        fsutil.write_text(req, "\n".join(lines) + "\n")
    info["parts"] = info.get("parts", []) + [name]
    projlib.save(project_dir, info)
    result["manifest"] = changes
    result["installed"].append(name)
    return result


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="作業フォルダに部品を足す")
    ap.add_argument("part", nargs="?")
    ap.add_argument("--project")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    parts_dir = SKILL_DIR / "parts"
    if args.list or not args.part:
        for name in list_parts(parts_dir):
            p = load_part(name, parts_dir)
            print(f"{name}（{p['status']}・{'/'.join(p['os'])}）: {p['description']}")
        return 0
    if not args.project:
        print("--project に作業フォルダを指定してください")
        return 3
    try:
        r = add_part(Path(args.project).expanduser(), args.part)
    except (PartError, projlib.ProjectError, mf.ManifestError) as e:
        print(str(e))
        return 3
    if args.json:
        cli.print_json(r)
    elif r["already"]:
        print(f"{args.part} は既に入っています（何も変えていません）")
    else:
        print(f"足しました: {', '.join(r['installed'])}")
        if r["manifest"]:
            print(f"manifest の変更: {', '.join(r['manifest'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
