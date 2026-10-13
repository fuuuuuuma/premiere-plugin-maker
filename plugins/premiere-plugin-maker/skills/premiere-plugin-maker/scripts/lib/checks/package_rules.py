"""配る物の検査（P002〜P006）。"""
from __future__ import annotations

import json
import re
from typing import List

from .. import privacy
from . import Finding, Project, rule

TEXT_SUFFIXES = (".js", ".json", ".html", ".css", ".md", ".py", ".txt", ".jsx", ".xml", ".ps1", ".bat", ".cmd",
                 ".command", ".sh", ".plist", ".template")


@rule
def package_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.files():
        if privacy.secret_like_name(path.name):
            out.append(Finding("P002", "error", p.rel(path), 0, f"秘密らしい名前のファイル「{path.name}」があります",
                               "鍵や合言葉のファイルが配布物に混ざると漏れます。名前だけで配布から外す仕組みに部品が消される事故もありました",
                               "鍵はファイルに書かず OS の保管庫へ。部品なら secret・token を含まない名前にしてください"))
    for path in p.files(*TEXT_SUFFIXES):
        text = p.text(path)
        for line, found in privacy.personal_paths(text):
            out.append(Finding("P003", "error", p.rel(path), line, f"個人のパス「{found}」が書かれています",
                               "受け取った人の PC には無いパスで、名前も漏れます", "~ や環境変数、プラグインのフォルダからの相対で書いてください"))
        for line, found in privacy.token_like(text):
            out.append(Finding("P003", "error", p.rel(path), line, f"鍵の形の文字列「{found}」があります",
                               "鍵がそのまま配られます", "鍵は消し、OS の保管庫か利用者の設定から読むようにしてください"))
        for m in re.finditer(r"\{\{[A-Z_]+\}\}", text):
            out.append(Finding("P005", "error", p.rel(path), text.count("\n", 0, m.start()) + 1, f"置き換え忘れの「{m.group(0)}」があります",
                               "雛形の印がそのまま残っています", "new_plugin.py か add_part.py で作り直すか、正しい値に書き換えてください"))
    info = p.root / "build_info.json"
    if p.manifest and info.exists():
        try:
            bv = json.loads(p.text(info)).get("version")
        except ValueError:
            bv = None
        if bv != p.manifest.get("version"):
            out.append(Finding("P004", "error", "build_info.json", 0, f"版が manifest.json（{p.manifest.get('version')}）と違います（{bv}）",
                               "画面に出る版と、Premiere が見る版がずれます", "両方を同じ版にしてください"))
    if not (p.root / ".ppm" / "project.json").exists():
        out.append(Finding("P006", "warn", ".ppm/project.json", 0, "この道具で作ったフォルダではありません",
                           "部品の追加（add_part.py）が使えません", "new_plugin.py で作ったフォルダに中身を移すと、部品と検査がそろいます"))
    return out
