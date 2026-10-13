"""Windows で壊れる書き方と Python の構文の検査（W001〜W005、Y001）。"""
from __future__ import annotations

import re
from typing import List

from . import Finding, Project, rule

_MAC_ONLY = re.compile(r"/Applications/|~/Library|/Library/|/opt/homebrew")
_OS_BRANCH = re.compile(r"sys\.platform|platform\.system|os\.platform\(|process\.platform|darwin|osinfo\.|os_name")


def _call_text(text: str, start: int) -> str:
    depth = 0
    for k in range(start, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return text[start:k + 1]
    return text[start:]


@rule
def platform_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    for path in p.files(".ps1"):
        raw = path.read_bytes()
        if any(b > 127 for b in raw) and not raw.startswith(b"\xef\xbb\xbf"):
            out.append(Finding("W001", "error", p.rel(path), 0, "日本語を含む .ps1 に BOM がありません",
                               "Windows PowerShell 5.1 は BOM の無いファイルを ANSI として読み、文字化けして止まります",
                               "UTF-8（BOM 付き）で保存してください"))
    for path in p.files(".bat", ".cmd"):
        if any(b > 127 for b in path.read_bytes()):
            out.append(Finding("W002", "error", p.rel(path), 0, ".bat / .cmd に英数字以外が入っています",
                               "cmd は CP932 で読むので、日本語やパスが化けます", "英数字だけにし、日本語の処理は .ps1 か Python に任せてください"))
    for path in p.files(".py"):
        text = p.text(path)
        try:
            compile(text, str(path), "exec")
        except SyntaxError as e:
            out.append(Finding("Y001", "error", p.rel(path), e.lineno or 0, f"Python の構文の誤り: {e.msg}",
                               "このファイルは動きません", "示された行を直してください"))
            continue
        for m in re.finditer(r"subprocess\.(?:run|Popen|check_output|check_call)\s*\(", text):
            call = _call_text(text, m.end() - 1)
            if re.search(r"text\s*=\s*True|universal_newlines\s*=\s*True", call) and "encoding" not in call:
                out.append(Finding("W003", "error", p.rel(path), text.count("\n", 0, m.start()) + 1,
                                   "text=True なのに encoding がありません", "Windows では cp932 で読み書きされ、日本語や絵文字で止まります",
                                   "encoding=\"utf-8\", errors=\"replace\" を足してください"))
        for m in re.finditer(r"(?<![\w.])open\s*\(", text):
            call = _call_text(text, m.end() - 1)
            if "encoding" not in call and not re.search(r"[\"'][rwax+]*b[rwax+]*[\"']", call):
                out.append(Finding("W003", "warn", p.rel(path), text.count("\n", 0, m.start()) + 1,
                                   "テキストの open に encoding がありません", "Windows では cp932 になります", "encoding=\"utf-8\" を足してください"))
    for path in p.files(".py", ".js"):
        text = p.text(path)
        m = _MAC_ONLY.search(text)
        if m and not _OS_BRANCH.search(text):
            out.append(Finding("W004", "warn", p.rel(path), text.count("\n", 0, m.start()) + 1, f"Mac 専用の場所「{m.group(0)}」を書いています",
                               "Windows ではその場所が無く、黙って失敗します（Mac 専用の場所だけを探して Windows で失敗した事故あり）",
                               "OS で分けるか、Windows の場所（環境変数 APPDATA・ProgramFiles）も探してください"))
    for path in p.files(".command", ".sh"):
        text = p.text(path)
        for m in re.finditer(r"\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])", text):
            out.append(Finding("W005", "error", p.rel(path), text.count("\n", 0, m.start()) + 1, f"「{m.group(0)}」の直後に日本語が続いています",
                               "Mac の bash 3.2 は日本語の一部を変数名と読み、set -u で止まります（新しく入れた人のほぼ全員が踏んだ）",
                               "${変数} のように波かっこで囲んでください"))
    return out
