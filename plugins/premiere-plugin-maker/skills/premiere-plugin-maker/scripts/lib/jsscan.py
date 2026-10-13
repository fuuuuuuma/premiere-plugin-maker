"""JS を「だいたい」読むための道具（構文木は作らない）。

blank() でコメントと文字列の中身を空白に置き換えてから正規表現で探すと、
文字列やコメントの中の言葉を誤って拾わない。長さと改行の位置は元と同じなので、行番号はそのまま使える。
"""
from __future__ import annotations

import re
from typing import List, Tuple

_REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^")
_PAIRS = {"(": ")", "{": "}", "[": "]"}


def blank(text: str) -> str:
    out = list(text)
    n = len(text)
    i = 0
    prev = ""

    def fill(a: int, b: int) -> None:
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            fill(i, j)
            i = j
            continue
        if c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            fill(i, j)
            i = j
            continue
        if c in "\"'`":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == c or (c != "`" and text[j] == "\n"):
                    break
                j += 1
            fill(i + 1, j)
            i = j + 1
            prev = c
            continue
        if c == "/" and (prev == "" or prev in _REGEX_PREV):
            j = i + 1
            in_class = False
            while j < n and text[j] != "\n":
                ch = text[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    break
                j += 1
            fill(i + 1, j)
            i = j + 1
            prev = "/"
            continue
        if not c.isspace():
            prev = c
        i += 1
    return "".join(out)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, max(pos, 0)) + 1


def match_close(clean: str, open_pos: int) -> int:
    opener = clean[open_pos]
    closer = _PAIRS.get(opener)
    if not closer:
        return -1
    depth = 0
    for k in range(open_pos, len(clean)):
        ch = clean[k]
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return k
    return -1


def callback_spans(clean: str, names=("lockedAccess", "executeTransaction", "transact")) -> List[Tuple[int, int, str]]:
    """`.名前(` と、受け手の無い `名前(` の両方を見る（ppro-kit の中の transact(…) の呼び出しも取引として扱う）。
    `function transact(` のような定義は除く。"""
    spans: List[Tuple[int, int, str]] = []
    pattern = re.compile(r"(?<![\w$])(?:[\w$]+\s*\.\s*)?(" + "|".join(names) + r")\s*\(")
    for m in pattern.finditer(clean):
        if re.search(r"function\s+$", clean[max(0, m.start() - 20):m.start()]):
            continue
        open_paren = m.end() - 1
        close_paren = match_close(clean, open_paren)
        if close_paren < 0:
            continue
        args = clean[open_paren + 1:close_paren]
        fm = re.search(r"=>|\bfunction\b", args)
        if not fm:
            continue
        start = open_paren + 1 + fm.end()
        if fm.group(0) == "function":
            brace = clean.find("{", start, close_paren)
            if brace < 0:
                continue
            spans.append((brace, match_close(clean, brace), m.group(1)))
            continue
        k = start
        while k < close_paren and clean[k].isspace():
            k += 1
        if k < close_paren and clean[k] == "{":
            spans.append((k, match_close(clean, k), m.group(1)))
        else:
            spans.append((k, close_paren, m.group(1)))
    return spans


def builder_spans(original: str, clean: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    for m in re.finditer(r"ppm:\s*action-builder", original):
        brace = clean.find("{", m.end())
        if brace < 0:
            continue
        end = match_close(clean, brace)
        if end > brace:
            spans.append((brace, end))
    return spans


def inside(pos: int, spans) -> bool:
    return any(a <= pos <= b for a, b, *_ in spans)
