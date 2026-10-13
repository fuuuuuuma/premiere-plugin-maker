"""style.json（設計書 §6）→ ソーステキスト FlatBuffer のツリー。KAZARU textstyle_build.spec_to_tree の写し。"""
from __future__ import annotations
import struct
from . import textstyle_fb as fb


def color(hexstr: str) -> dict:
    h = str(hexstr).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return {"r": int(h[0:2], 16), "g": int(h[2:4], 16), "b": int(h[4:6], 16)}


def gradient(g: dict) -> dict:
    stops = []
    for c, pos in g["stops"]:
        st = {"color": color(c), "mid": 0.5}
        if pos:
            st["pos"] = float(pos)
        stops.append(st)
    out = {"colors": stops, "opacities": [{"mid": 0.5}, {"pos": 1.0, "mid": 0.5}]}
    if g.get("angle") is not None and g.get("type") != "radial":     # 円形に角度は無い
        out["angle"] = float(g["angle"])
    return out


def spec_to_tree(s: dict, text: str) -> dict:
    strokes = list(s.get("strokes") or [])
    st: dict = {"size": float(s.get("size", 100))}
    fill = s.get("fill", "#ffffff")
    if isinstance(fill, dict) and "gradient" in fill:
        # 1 = 線形、2 = 円形（実機 2026-09-18: 円形にして保存したプロジェクトから読んだ）
        st["fill_type"] = 2 if fill["gradient"].get("type") == "radial" else 1
        st["fill_gradient"] = gradient(fill["gradient"])
    else:
        st["fill"] = color(fill)
        st["fill_gradient"] = {}
    if strokes:
        first = strokes[0]
        st["stroke_color"] = color(first["color"])
        st["stroke_visible"] = 1
        st["stroke_width"] = float(first["width"])
        extra = [{"color": color(k["color"]), "visible": 1, "width": float(k["width"]), "gradient": {}} for k in strokes[1:]]
        if extra:
            st["strokes"] = extra
    st["stroke_gradient"] = {}
    if s.get("tracking"):
        st["tracking"] = float(s["tracking"])
    if s.get("leading"):
        st["leading"] = float(s["leading"])
    if s.get("italic"):
        st["italic"] = 1
    tp: dict = {"runs": [{"text": text, "style": st}], "fonts": [s["font"]], "align": 2, "valign": 2}
    sh = s.get("shadow")
    if sh:
        tp.update({
            "shadow_color": color(sh.get("color", "#000000")), "shadow_visible": 1,
            "shadow_opacity": float(sh.get("opacity", 75)), "shadow_angle": float(sh.get("angle", 135)),
            "shadow_distance": float(sh.get("distance", 5)), "shadow_size": float(sh.get("size", 0)),
            "shadow_blur": float(sh.get("blur", 20)),
        })
    bg = s.get("background")
    if bg:
        tp.update({"bg_color": color(bg.get("color", "#000000")), "bg_visible": 1,
                   "bg_opacity": float(bg.get("opacity", 75)), "bg_size": float(bg.get("size", 20))})
    tp["flag23"] = 1
    tp["flag26"] = 1
    if len(strokes) > 1:
        tp["stroke_count"] = len(strokes)
    extra_sh = [{
        "color": color(e.get("color", "#000000")), "visible": 1, "opacity": float(e.get("opacity", 75)),
        "angle": float(e.get("angle", 135)), "distance": float(e.get("distance", 0)),
        "size": float(e.get("size", 0)), "blur": float(e.get("blur", 20)), "gradient": {},
    } for e in s.get("extra_shadows") or []]
    if extra_sh:
        tp["shadows"] = extra_sh
    tp["gradient40"] = {}
    tp["flag44"] = 1
    return {"textparam": tp}


def f32ify(x):
    if isinstance(x, float):
        return struct.unpack("<f", struct.pack("<f", x))[0]
    if isinstance(x, dict):
        return {k: f32ify(v) for k, v in x.items()}
    if isinstance(x, list):
        return [f32ify(v) for v in x]
    return x


def source_tree(style: dict, text: str) -> dict:
    """取り込んだスタイル（engine/import_style.py）: 元のデータの本文だけを差し替える。
    読み取った値で作り直すと、読めていない項目（縁の内側・外側など）が落ちて Premiere での見た目が変わる（実機 2026-09-19）。
    置き場所の基準はカタログの置き方に合わせて中央（align / valign = 2）にする。"""
    import base64
    tree = fb.decode(base64.b64decode(style["source"]["blob"]))
    tp = tree["textparam"]
    runs = tp.get("runs") or [{}]
    tp["runs"] = [{"text": text, "style": runs[0].get("style") or {}}]
    tp["align"] = 2
    tp["valign"] = 2
    return tree


def _same_bytes(tree):
    """比較用: 未知の項目は、後ろの詰め物（0）の幅の違いを同じとみなす。読み手は項目の幅から次の項目までを
    その項目の幅と推し量るので、1 バイトの項目を書き戻すと 4 バイトに見える（値は同じ。実物 94 本中 4 本）"""
    if isinstance(tree, dict):
        if "_raw" in tree and "_w" in tree:
            return {"_raw": tree["_raw"].rstrip("0") or "0"}
        return {k: _same_bytes(v) for k, v in tree.items()}
    if isinstance(tree, list):
        return [_same_bytes(x) for x in tree]
    return tree


def encode_style(style: dict, text: str) -> bytes:
    """style.json と本文から blob（12 バイトヘッダ込み）。往復一致を毎回確かめる（壊れた blob を出さない）。"""
    tree = source_tree(style, text) if style.get("source") else spec_to_tree(style, text)
    blob = fb.encode(tree)
    if _same_bytes(fb.strip_meta(fb.decode(blob))) != _same_bytes(fb.strip_meta(f32ify(tree))):
        raise ValueError(f"FlatBuffer の往復が一致しません: {style.get('name')}")
    return blob
