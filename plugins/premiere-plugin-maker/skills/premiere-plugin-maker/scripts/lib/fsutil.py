"""ファイル操作の共通部品。利用者のファイルを上書きしないことを最優先にする。"""
from __future__ import annotations

import os
import shutil
import unicodedata
from pathlib import Path
from typing import List


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def copy_new(src: Path, dst: Path) -> List[Path]:
    """src の中身を dst へ写す。dst に同じ名前のファイルが 1 つでもあれば、何も写さずに FileExistsError。"""
    src, dst = Path(src), Path(dst)
    files = sorted(p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    clashes = [dst / p.relative_to(src) for p in files if (dst / p.relative_to(src)).exists()]
    if clashes:
        raise FileExistsError("既にあるファイルは上書きしません: " + ", ".join(str(c) for c in clashes[:5]))
    copied: List[Path] = []
    for p in files:
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        copied.append(target)
    return copied


def nfc(text: str) -> str:
    """Finder や zip で NFD になった日本語を NFC にそろえる。"""
    return unicodedata.normalize("NFC", text)


def is_within(child: Path, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False
