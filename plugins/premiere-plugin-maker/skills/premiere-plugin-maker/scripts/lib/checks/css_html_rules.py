"""CSS と HTML の検査（C001・C002・C004、H001〜H005）。"""
from __future__ import annotations

import re
from typing import List

from . import Finding, Project, rule

_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


@rule
def css_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.panel_files(".css"):
        raw = p.text(path)
        text = _CSS_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw)
        for m in re.finditer(r"display\s*:\s*(?:inline-)?grid|grid-template", text):
            out.append(Finding("C001", "error", p.rel(path), _line(text, m.start()), "CSS の grid を使っています",
                               "UXP は grid に対応していません", "flex（一覧は flex-wrap）で並べてください"))
        for m in re.finditer(r"position\s*:\s*fixed", text):
            out.append(Finding("C002", "warn", p.rel(path), _line(text, m.start()), "position: fixed を使っています",
                               "重ね表示の下にある入力欄が透けて前に出た記録があります", "重ねずに、元の中身を隠して出す形にしてください"))
        for m in re.finditer(r"(?<![\w-])(transition|animation)\s*:", text):
            out.append(Finding("C004", "warn", p.rel(path), _line(text, m.start()), f"{m.group(1)} を使っています",
                               "UXP では効かないことがあります", "動きに頼らない見た目にしてください"))
    return out


@rule
def html_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    css_all = "\n".join(p.text(x) for x in p.panel_files(".css"))
    perms = p.permissions()
    for path in p.panel_files(".html"):
        text = p.text(path)
        for m in re.finditer(r"<(?:script|img)\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']|<link\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']", text, re.I):
            ref = m.group(1) or m.group(2)
            if re.match(r"^(https?:|data:|plugin:|#)", ref):
                continue
            if not (path.parent / ref.split("?")[0]).exists():
                out.append(Finding("H001", "error", p.rel(path), _line(text, m.start()), f"読み込むファイル「{ref}」がありません",
                                   "その部分が動かず、パネルが空になることがあります", "ファイルを置くか、行を消してください"))
        for m in re.finditer(r"<(ul|ol|li)\b", text, re.I):
            out.append(Finding("H002", "warn", p.rel(path), _line(text, m.start()), f"<{m.group(1)}> を使っています",
                               "UXP では div として扱われ、点や番号が出ません", "div と CSS で並べてください"))
        if not perms.get("allowCodeGenerationFromStrings"):
            for m in re.finditer(r"<[^>]+\son[a-z]+\s*=", text, re.I):
                out.append(Finding("H003", "error", p.rel(path), _line(text, m.start()), "属性にイベント（onclick= など）を書いています",
                                   "allowCodeGenerationFromStrings が無いと動きません", "index.js で addEventListener を使ってください"))
        for m in re.finditer(r"<input\b[^>]*type\s*=\s*[\"']?(file|color)", text, re.I):
            out.append(Finding("H004", "warn", p.rel(path), _line(text, m.start()), f"<input type=\"{m.group(1)}\"> を使っています",
                               "UXP では使えません", "ファイルは require(\"uxp\").storage.localFileSystem.getFileForOpening() で選ばせてください"))
        if re.search(r"<title\b", text, re.I) and not re.search(r"title\s*\{[^}]*display\s*:\s*none", css_all):
            out.append(Finding("H005", "warn", p.rel(path), _line(text, text.lower().find("<title")), "<title> を隠していません",
                               "UXP では <title> の文字がパネルに出てしまいます", "CSS に title { display: none; } を書いてください"))
    return out
