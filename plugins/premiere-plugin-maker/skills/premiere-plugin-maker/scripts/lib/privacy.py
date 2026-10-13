"""公開物・配布物に個人情報や鍵が混ざっていないかを見る（check.py とキット自体の衛生検査で共有）。"""
from __future__ import annotations

import re
from typing import List, Tuple

PLACEHOLDER_USERS = {"<name>", "name", "you", "user", "username", "USER", "USERNAME", "%USERNAME%", "example",
                     "runner", "runneradmin", "Shared", "Public", "<user>", "<username>", "<ユーザー名>"}
# 名前の部分に ( ) [ ] を含めないのは、この正規表現の文字列そのもの（このファイル）を個人のパスと見誤らないため
_MAC = re.compile(r"/Users/([^/\s\"'`<>()\[\]]+)/")
_HOME = re.compile(r"/home/([^/\s\"'`<>()\[\]]+)/")
_WIN = re.compile(r"[A-Za-z]:\\{1,2}Users\\{1,2}([^\\/\s\"'`<>()\[\]]+)")
_TOKENS = re.compile(r"(?:ghp_|github_pat_|gho_|sk-proj-|sk-ant-|xox[bp]-|AKIA)[A-Za-z0-9_\-]{16,}")
_SECRET_NAME = re.compile(r"(secret|token|credential|password|passwd)", re.I)


def personal_paths(text: str) -> List[Tuple[int, str]]:
    found: List[Tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for rx in (_MAC, _HOME, _WIN):
            for m in rx.finditer(line):
                if m.group(1) not in PLACEHOLDER_USERS and not m.group(1).startswith(("{", "$", "%")):
                    found.append((i, m.group(0)))
                    break
            else:
                continue
            break
    return found


def secret_like_name(name: str) -> bool:
    if name in (".env", "ready") or name.startswith(".env."):
        return True
    return bool(_SECRET_NAME.search(name))


def token_like(text: str) -> List[Tuple[int, str]]:
    return [(i, m.group(0)[:12] + "…") for i, line in enumerate(text.splitlines(), 1) for m in _TOKENS.finditer(line)]
