"""知識ファイルの先頭項目（--- で囲んだ部分）を読み書きする。

標準ライブラリだけで読めるよう、YAML のごく一部だけを扱う:
  key: 値        key: "引用"        key: [a, b, c]        # 以降は注釈
入れ子・複数行の値・リストの中のカンマは書かない。
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Union

Value = Union[str, List[str]]


class FrontmatterError(ValueError):
    pass


def _strip_comment(raw: str) -> str:
    out = []
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or raw[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _value(raw: str, lineno: int) -> Value:
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise FrontmatterError(f"{lineno} 行目: [ の閉じ ] がありません")
        inner = raw[1:-1].strip()
        return [_unquote(x) for x in inner.split(",")] if inner else []
    return _unquote(raw)


def parse(text: str) -> Tuple[Dict[str, Value], str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("1 行目が --- ではありません（先頭項目がありません）")
    data: Dict[str, Value] = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:]).lstrip("\n")
            if body and not body.endswith("\n"):
                body += "\n"
            return data, body
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise FrontmatterError(f"{i + 1} 行目: 「キー: 値」の形ではありません")
        key, raw = line.split(":", 1)
        data[key.strip()] = _value(_strip_comment(raw).strip(), i + 1)
    raise FrontmatterError("先頭項目の閉じの --- がありません")


def dump(data: Dict[str, Value]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
            continue
        s = str(value)
        if any(c in s for c in ":#[]\"") or s != s.strip():
            s = '"' + s.replace('"', "'") + '"'
        lines.append(f"{key}: {s}")
    lines.append("---")
    return "\n".join(lines) + "\n"
