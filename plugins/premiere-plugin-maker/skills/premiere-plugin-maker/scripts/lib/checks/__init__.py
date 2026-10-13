"""機械の検査の土台。規則は各モジュールの @rule で登録する。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .. import manifest as manifest_lib

SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".ppm"}
NON_PANEL_DIRS = {"server", "cep", "tests", "packaging"}


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    why: str
    fix: str


class Project:
    def __init__(self, root: Path, kit_dir: Path):
        self.root = Path(root)
        self.kit_dir = Path(kit_dir)
        self.manifest: Optional[dict] = None
        self.manifest_error: Optional[str] = None
        self._texts: Dict[Path, str] = {}
        try:
            self.manifest = manifest_lib.load(self.root / "manifest.json")
        except manifest_lib.ManifestError as e:
            self.manifest_error = str(e)

    def files(self, *suffixes: str) -> List[Path]:
        out = []
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            parts = p.relative_to(self.root).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            if suffixes and p.suffix.lower() not in suffixes:
                continue
            out.append(p)
        return out

    def panel_files(self, *suffixes: str) -> List[Path]:
        return [p for p in self.files(*suffixes) if p.relative_to(self.root).parts[0] not in NON_PANEL_DIRS]

    def text(self, path: Path) -> str:
        path = Path(path)
        if path not in self._texts:
            try:
                self._texts[path] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._texts[path] = ""
        return self._texts[path]

    def rel(self, path: Path) -> str:
        return Path(path).relative_to(self.root).as_posix()

    def min_version(self) -> str:
        return manifest_lib.min_version(self.manifest or {})

    def permissions(self) -> dict:
        return (self.manifest or {}).get("requiredPermissions") or {}

    def feature_flags(self) -> dict:
        return (self.manifest or {}).get("featureFlags") or {}

    def line_of(self, path: Path, needle: str) -> int:
        for i, line in enumerate(self.text(path).splitlines(), 1):
            if needle in line:
                return i
        return 0


RULES: List[Callable[[Project], List[Finding]]] = []


def rule(fn):
    RULES.append(fn)
    return fn


_IGNORE_RE = re.compile(r"ppm-ignore:\s*([A-Z][0-9]{3}(?:\s*,\s*[A-Z][0-9]{3})*)")


def _suppressed(lines: List[str], line_no: int, rule_name: str) -> bool:
    for ln in (line_no, line_no - 1):
        if 1 <= ln <= len(lines):
            m = _IGNORE_RE.search(lines[ln - 1])
            if m and rule_name in [x.strip() for x in m.group(1).split(",")]:
                return True
    return False


def run_all(root: Path, kit_dir: Path) -> List[Finding]:
    from . import manifest_rules  # noqa: F401  （登録のための import。Task 7・8 で残りを足す）
    project = Project(root, kit_dir)
    found: List[Finding] = []
    for fn in RULES:
        found.extend(fn(project))
    out = []
    for f in found:
        if f.line and f.file:
            lines = project.text(project.root / f.file).splitlines()
            if _suppressed(lines, f.line, f.rule):
                continue
        out.append(f)
    return sorted(out, key=lambda f: (f.severity != "error", f.file, f.line, f.rule))
