#!/usr/bin/env python3
"""配る用の .ccx を作る（パネルが読むファイルだけを集め、毎回同じバイト列になるように固める）。

使い方:
  Mac:     python3 <このスキル>/scripts/make_ccx.py <作業フォルダ> [--out <ファイル>] [--bundle] [--json]
  Windows: py -3 <このスキル>\\scripts\\make_ccx.py <作業フォルダ> [--out <ファイル>] [--bundle] [--json]
--bundle は dist/<名前>_v<版>/ に .ccx・はじめにお読みください.txt・（あれば）サーバーの zip をまとめる。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, fsutil, privacy  # noqa: E402
from lib import manifest as mf  # noqa: E402
from lib import project as projlib  # noqa: E402

SKILL_DIR = HERE.parent
EXCLUDE_TOP = {"server", "cep", "tests", ".ppm", "dist", "node_modules", "packaging", ".git"}
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".js", ".json", ".html", ".css", ".txt", ".md", ".svg"}
DEFAULT_README = """{{PANEL_LABEL}}（{{PLUGIN_NAME}} v{{VERSION}}）の入れ方

■ Mac / Windows 共通
1. Creative Cloud デスクトップにサインインした状態で、{{PLUGIN_ID}}_{{VERSION}}.ccx をダブルクリックする
2. 確認の画面が出たら［インストール］を押す
3. Premiere の［ウィンドウ］→［UXP プラグイン］→「{{PANEL_LABEL}}」を開く

■ 出てこないとき
- Premiere を一度終了して、もう一度開く
- Creative Cloud にサインインし直した後は、入れ直しが要ることがあります
- 同じ版のまま入れ直しても更新されません。Creative Cloud デスクトップの［プラグイン］から一度削除してから入れてください
"""
SERVER_README = """
■ 手元のサーバー（このプラグインは重い処理を手元のサーバーに任せます）
1. 同じフォルダの {{APP_NAME}}_server_v{{VERSION}}.zip を、好きな場所に展開する（展開した場所は消さない）
2. Mac: ターミナルで「bash 」（後ろに空白）と打ち、展開した server フォルダの install_mac.command をドラッグして Enter
   Windows: 展開した server フォルダの install_windows.bat をダブルクリック
3. Premiere でパネルを開き直す。「サーバーが動いていません」と出たら、手順 2 をもう一度
"""
SERVER_SKIP_DIRS = {".venv", "venv", ".git", "models", "logs", "__pycache__", "node_modules"}
SERVER_SKIP_SUFFIXES = {".pyc", ".log"}


class CcxError(ValueError):
    pass


def _norm(rel: PurePosixPath) -> str:
    parts: List[str] = []
    for part in rel.parts:
        if part == "..":
            if not parts:
                raise CcxError(f"プラグインのフォルダの外を読もうとしています: {rel}")
            parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def _html_refs(text: str) -> List[str]:
    refs = re.findall(r"<(?:script|img)\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
    refs += re.findall(r"<link\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
    return [r.split("?")[0] for r in refs if not re.match(r"^(https?:|data:|plugin:|#)", r)]


def _css_refs(text: str) -> List[str]:
    return [r for r in re.findall(r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)", text) if not re.match(r"^(https?:|data:)", r)]


def collect_files(project_dir) -> List[str]:
    root = Path(project_dir)
    data = mf.load(root / "manifest.json")
    mf.require_shape(data, need_id=True)
    files = {"manifest.json"}
    queue = [data.get("main") or "main.js"]
    while queue:
        rel = queue.pop()
        if rel in files:
            continue
        if PurePosixPath(rel).parts and PurePosixPath(rel).parts[0] in EXCLUDE_TOP:
            raise CcxError(f"{rel} は配る物に入らない場所（{PurePosixPath(rel).parts[0]}/）にあります")
        path = root / rel
        if not path.is_file():
            raise CcxError(f"{rel} がありません（index.html か CSS が読みに行くファイルです）")
        files.add(rel)
        base = PurePosixPath(rel).parent
        if path.suffix.lower() == ".html":
            queue.extend(_norm(base / r) for r in _html_refs(path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".css":
            queue.extend(_norm(base / r) for r in _css_refs(path.read_text(encoding="utf-8")))
    for icon in data.get("icons") or []:
        p = icon.get("path")
        if not p:
            continue
        if not (root / p).is_file():
            raise CcxError(f"アイコン {p} がありません")
        files.add(p)
        stem = PurePosixPath(p)
        for scale in icon.get("scale") or []:
            candidate = (stem.parent / f"{stem.stem}@{scale}x{stem.suffix}").as_posix()
            if (root / candidate).is_file():
                files.add(candidate)
    if (root / "build_info.json").is_file():
        files.add("build_info.json")
    pkg = root / ".ppm" / "package.json"
    if pkg.is_file():
        for pattern in json.loads(pkg.read_text(encoding="utf-8")).get("include", []):
            for p in sorted(root.glob(pattern)):
                rel = p.relative_to(root).as_posix()
                if p.is_file() and PurePosixPath(rel).parts[0] not in EXCLUDE_TOP:
                    files.add(rel)
    return sorted(files, key=lambda x: (x != "manifest.json", x))


def _scan_text(root: Path, rel: str, problems: List[str]) -> None:
    text = (root / rel).read_text(encoding="utf-8", errors="replace")
    for line, found in privacy.personal_paths(text):
        problems.append(f"{rel} の {line} 行目: 個人のパス {found}")
    for line, found in privacy.token_like(text):
        problems.append(f"{rel} の {line} 行目: 鍵の形の文字列 {found}")


def validate(project_dir, files: List[str]) -> None:
    root = Path(project_dir)
    data = mf.load(root / "manifest.json")
    mf.require_shape(data, need_id=True)
    problems = []
    for rel in files:
        name = PurePosixPath(rel).name
        if privacy.secret_like_name(name):
            problems.append(f"{rel}: 秘密らしい名前のファイルは配りません")
        if Path(rel).suffix.lower() in TEXT_SUFFIXES:
            _scan_text(root, rel, problems)
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
            if re.search(r"\{\{[A-Z_]+\}\}", text):
                problems.append(f"{rel}: 置き換え忘れの {{{{…}}}} があります")
    info = root / "build_info.json"
    if info.is_file():
        bv = json.loads(info.read_text(encoding="utf-8")).get("version")
        if bv != data.get("version"):
            problems.append(f"build_info.json の版（{bv}）が manifest.json（{data.get('version')}）と違います")
    if problems:
        raise CcxError("配る前に直すことがあります:\n- " + "\n- ".join(problems))


def _write_zip(out: Path, entries) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, data, mode in entries:
            info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            info.external_attr = (mode & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    os.replace(tmp, out)
    return out


def build_ccx(project_dir, out_path: Optional[Path] = None) -> Path:
    root = Path(project_dir)
    files = collect_files(root)
    validate(root, files)
    data = mf.load(root / "manifest.json")
    out = Path(out_path) if out_path else root / "dist" / f"{data['id']}_{data['version']}.ccx"
    return _write_zip(out, [(rel, (root / rel).read_bytes(), 0o100644) for rel in files])


def build_bundle(project_dir) -> Path:
    root = Path(project_dir)
    info = projlib.load(root)
    data = mf.load(root / "manifest.json")
    folder = root / "dist" / f"{info['appName']}_v{data['version']}"
    folder.mkdir(parents=True, exist_ok=True)
    ccx = build_ccx(root, folder / f"{data['id']}_{data['version']}.ccx")
    template = root / "packaging" / "README-recipient.txt"
    text = template.read_text(encoding="utf-8") if template.is_file() else DEFAULT_README
    server = root / "server"
    if server.is_dir() and "install_mac.command" not in text:
        text = text.rstrip("\n") + "\n" + SERVER_README
    fsutil.write_text(folder / "はじめにお読みください.txt", projlib.substitute(text, projlib.placeholders({**info, "version": data["version"]})))
    if server.is_dir():
        entries, problems = [], []
        for p in sorted(x for x in server.rglob("*") if x.is_file()):
            if SERVER_SKIP_DIRS & set(p.relative_to(server).parts[:-1]) or p.suffix.lower() in SERVER_SKIP_SUFFIXES:
                continue
            rel = p.relative_to(root).as_posix()
            if privacy.secret_like_name(p.name):
                problems.append(f"{rel}: 秘密らしい名前のファイルは配りません")
            if p.suffix.lower() in TEXT_SUFFIXES | {".py", ".bat", ".command", ".ps1", ".sh", ".template", ".plist", ".cfg", ".ini", ".toml", ".yml", ".yaml"}:
                _scan_text(root, rel, problems)
            mode = 0o100755 if p.suffix in (".command", ".sh") else 0o100644
            entries.append((rel, p.read_bytes(), mode))
        if problems:
            raise CcxError("サーバーの zip に入れる前に直すことがあります:\n- " + "\n- ".join(problems))
        _write_zip(folder / f"{info['appName']}_server_v{data['version']}.zip", entries)
    return folder


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="配る用の .ccx を作る")
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--bundle", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.bundle:
            out = build_bundle(Path(args.project).expanduser())
        else:
            out = build_ccx(Path(args.project).expanduser(), Path(args.out) if args.out else None)
    except (CcxError, mf.ManifestError, projlib.ProjectError) as e:
        print(str(e))
        return 1
    if args.json:
        cli.print_json({"ok": True, "path": str(out)})
    else:
        print(f"作りました: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
