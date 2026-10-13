"""Premiere が書き出す FCP7 XML（xmeml）を読み書きする。

実測の決まり（Cut & SRT の失敗から）:
- 同じ素材を何百のクリップが参照しても、<file> の完全な定義（子要素を持つ）は文書に 1 つだけ。残りは <file id="…"/>。
  一部だけを写すとその 1 つを落とし、Premiere は何も言わずに読み込みに失敗する → dangling() で書く前に確かめる
- 完全な定義かどうかは pathurl の有無ではなく「子要素を持つか」で見る（テロップは pathurl を持たない）
- 秒とフレームの換算は、宣言された timebase と ntsc で行う。実際の fps（29.998 など）は使わない
- シーケンスの rate は sequence 直下の <rate> を読む（文書の先頭にある別の rate を掴まない）
- ネストしたシーケンスも同じく、完全な定義は 1 回だけ（tag="sequence" で同じ関数が使える）
"""
from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

TICKS_PER_SECOND = 254016000000


class XmlError(ValueError):
    pass


def load(path) -> ET.ElementTree:
    text = Path(path).read_text(encoding="utf-8")
    if "<!ENTITY" in text:
        raise XmlError("XML に ENTITY の定義があります（安全のため読みません）")
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text, count=1)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise XmlError(f"XML が読めません: {e}") from None
    if root.tag != "xmeml":
        raise XmlError("Premiere の FCP7 XML（xmeml）ではありません。［ファイル］→［書き出し］→［Final Cut Pro XML］で書き出したものを使ってください")
    return ET.ElementTree(root)


def save(tree: ET.ElementTree, path) -> None:
    body = ET.tostring(tree.getroot(), encoding="unicode")
    with open(Path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + "\n")


def is_definition(el: ET.Element) -> bool:
    return len(list(el)) > 0


def definitions(root: ET.Element, tag: str = "file") -> Dict[str, ET.Element]:
    out: Dict[str, ET.Element] = {}
    for el in root.iter(tag):
        fid = el.get("id")
        if fid and is_definition(el) and fid not in out:
            out[fid] = el
    return out


def dangling(root: ET.Element, tag: str = "file") -> List[str]:
    """文書の順で、完全な定義より前に出てくる空の参照の id（Premiere はこれを解決できない）。"""
    seen, bad = set(), []
    for el in root.iter(tag):
        fid = el.get("id")
        if not fid:
            continue
        if is_definition(el):
            seen.add(fid)
        elif fid not in seen and fid not in bad:
            bad.append(fid)
    return bad


def ensure_first_definition(root: ET.Element, tag: str = "file") -> int:
    """完全な定義を、その id が文書の中で最初に出てくる場所へ移す。後ろの重複は空の参照にする。直した数を返す。"""
    elements = list(root.iter(tag))
    defs: Dict[str, ET.Element] = {}
    for el in elements:
        fid = el.get("id")
        if fid and is_definition(el) and fid not in defs:
            defs[fid] = copy.deepcopy(el)
    fixed = 0
    placed = set()
    for el in elements:
        fid = el.get("id")
        if not fid or fid not in defs:
            continue
        if fid not in placed:
            if not is_definition(el):
                for child in list(defs[fid]):
                    el.append(copy.deepcopy(child))
                fixed += 1
            placed.add(fid)
        elif is_definition(el):
            for child in list(el):
                el.remove(child)
            fixed += 1
    return fixed


def rate_of(el: ET.Element) -> Tuple[int, bool]:
    rate = el.find("rate")
    if rate is None:
        raise XmlError(f"<{el.tag}> の直下に <rate> がありません")
    timebase = int((rate.findtext("timebase") or "0").strip())
    ntsc = (rate.findtext("ntsc") or "FALSE").strip().upper() == "TRUE"
    if timebase <= 0:
        raise XmlError("timebase が 0 です")
    return timebase, ntsc


def fps(timebase: int, ntsc: bool) -> Fraction:
    return Fraction(timebase * 1000, 1001) if ntsc else Fraction(timebase)


def frames_to_seconds(frames: int, timebase: int, ntsc: bool) -> float:
    return float(Fraction(int(frames)) / fps(timebase, ntsc))


def seconds_to_frames(seconds: float, timebase: int, ntsc: bool) -> int:
    return int(round(Fraction(str(seconds)) * fps(timebase, ntsc)))


def ticks_per_frame(timebase: int, ntsc: bool) -> int:
    return int(Fraction(TICKS_PER_SECOND) / fps(timebase, ntsc))


def main_sequence(root: ET.Element) -> ET.Element:
    for seq in root.iter("sequence"):
        if is_definition(seq) and seq.find("media") is not None:
            return seq
    raise XmlError("XML にシーケンスがありません")


def tracks(seq: ET.Element, kind: str = "video") -> List[ET.Element]:
    media = seq.find("media")
    part = media.find(kind) if media is not None else None
    return list(part.findall("track")) if part is not None else []


def clipitems(track: ET.Element) -> List[ET.Element]:
    return list(track.findall("clipitem"))


def clip_range(ci: ET.Element) -> Tuple[int, int]:
    return int(ci.findtext("start") or "0"), int(ci.findtext("end") or "0")


def clip_text(ci: ET.Element) -> Optional[str]:
    """テロップ（グラフィック）の本文。<filter><effect><name>本文</name><effectid>GraphicAndType</effectid>。"""
    for eff in ci.iter("effect"):
        if (eff.findtext("effectid") or "").strip() == "GraphicAndType":
            return eff.findtext("name")
    return None


def find_clip(seq: ET.Element, kind: str, track_index: int, start_frame: int) -> Optional[ET.Element]:
    ts = tracks(seq, kind)
    if not 0 <= track_index < len(ts):
        return None
    for ci in clipitems(ts[track_index]):
        if clip_range(ci)[0] == int(start_frame):
            return ci
    return None


def media_path(file_el: ET.Element) -> Optional[str]:
    url = file_el.findtext("pathurl")
    if not url:
        return None
    path = unquote(urlparse(url.strip()).path)
    if re.match(r"^/[A-Za-z]:", path):
        path = path[1:]
    return path
