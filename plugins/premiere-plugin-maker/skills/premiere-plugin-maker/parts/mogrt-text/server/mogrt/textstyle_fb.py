"""Premiere Pro テキストスタイル (ソーステキスト) の FlatBuffer を読み書きする。

参考ファイル 51 本の総当たり比較で確定したフィールド対応表 (SCHEMA) を単一の正典とし、
decode() は blob → 入れ子 dict、encode() は dict → blob (12 バイトヘッダ込み) を返す。
未知のフィールドは幅と生バイトのまま保持し、往復で失われないようにする。
"""
from __future__ import annotations

import hashlib
import struct

MAGIC = 0x11223344

# 型: 'u8' / 'u32' / 'f32' / 'str' / 'table:<kind>' / 'vec_table:<kind>' / 'vec_str'
SCHEMA: dict[str, dict[int, str]] = {
    "root": {0: "table:textparam", 4: "u8"},
    "textparam": {
        0: "vec_table:run", 1: "vec_str", 4: "u32", 5: "u32", 6: "f32",
        10: "table:color", 11: "u8", 12: "f32", 13: "f32", 14: "f32", 15: "f32", 16: "f32",
        17: "table:color", 18: "u8", 19: "f32", 20: "f32",
        23: "u32", 24: "u32", 26: "u8", 30: "u32", 34: "f32",
        37: "vec_table:shadow", 40: "table:gradient", 43: "u8", 44: "u8",
    },
    "run": {0: "str", 1: "table:style"},
    "style": {
        1: "f32", 2: "table:color", 4: "table:color", 5: "u8", 6: "f32", 7: "f32", 8: "f32",
        15: "u8", 17: "vec_table:stroke", 20: "u32", 21: "table:gradient", 22: "u32",
        23: "table:gradient", 24: "u32",
    },
    "stroke": {0: "table:color", 1: "u8", 2: "f32", 4: "table:gradient"},
    "shadow": {0: "table:color", 1: "u8", 2: "f32", 3: "f32", 4: "f32", 5: "f32", 6: "f32", 8: "table:gradient"},
    "gradient": {0: "f32", 1: "vec_table:cstop", 2: "vec_table:ostop"},
    "cstop": {0: "table:color", 1: "f32", 2: "f32"},
    "ostop": {0: "f32", 1: "f32", 2: "f32"},
    "color": {0: "u8", 1: "u8", 2: "u8"},
}

# 人が読める名前 (decode 結果のキーはこの名前。未知フィールドは f<番号>)
NAMES: dict[str, dict[int, str]] = {
    "root": {0: "textparam"},
    "textparam": {
        0: "runs", 1: "fonts", 4: "align", 5: "valign", 6: "leading",
        10: "shadow_color", 11: "shadow_visible", 12: "shadow_opacity", 13: "shadow_angle",
        14: "shadow_distance", 15: "shadow_size", 16: "shadow_blur",
        17: "bg_color", 18: "bg_visible", 19: "bg_opacity", 20: "bg_size",
        23: "flag23", 24: "flag24", 26: "flag26", 30: "stroke_count", 34: "flag34",
        37: "shadows", 40: "gradient40", 43: "flag43", 44: "flag44",
    },
    "run": {0: "text", 1: "style"},
    "style": {
        1: "size", 2: "fill", 4: "stroke_color", 5: "stroke_visible", 6: "stroke_width",
        7: "leading", 8: "tracking", 15: "italic", 17: "strokes", 20: "fill_type",
        21: "fill_gradient", 22: "flag22", 23: "stroke_gradient", 24: "flag24",
    },
    "stroke": {0: "color", 1: "visible", 2: "width", 4: "gradient"},
    "shadow": {0: "color", 1: "visible", 2: "opacity", 3: "angle", 4: "distance", 5: "size", 6: "blur", 8: "gradient"},
    "gradient": {0: "angle", 1: "colors", 2: "opacities"},
    "cstop": {0: "color", 1: "pos", 2: "mid"},
    "ostop": {0: "opacity", 1: "pos", 2: "mid"},
    "color": {0: "r", 1: "g", 2: "b"},
}
_REV = {kind: {v: k for k, v in d.items()} for kind, d in NAMES.items()}


def _u32(b, o): return struct.unpack_from("<I", b, o)[0]
def _i32(b, o): return struct.unpack_from("<i", b, o)[0]
def _u16(b, o): return struct.unpack_from("<H", b, o)[0]
def _f32(b, o): return struct.unpack_from("<f", b, o)[0]


class DecodeError(ValueError):
    pass


def _fields(b, pos):
    vt = pos - _i32(b, pos)
    if not (0 <= vt <= len(b) - 4):
        raise DecodeError(f"vtable out of range at {pos}")
    vsz, tsz = _u16(b, vt), _u16(b, vt + 2)
    nf = (vsz - 4) // 2
    offs = [(i, _u16(b, vt + 4 + 2 * i)) for i in range(nf)]
    present = sorted(o for _, o in offs if o)
    out = []
    for i, o in offs:
        if not o:
            continue
        nxt = min([x for x in present if x > o] + [tsz])
        out.append((i, o, nxt - o))
    return out, nf


def _decode_table(b, pos, kind):
    schema = SCHEMA[kind]
    names = NAMES[kind]
    fr, nf = _fields(b, pos)
    d: dict = {"_nf": nf}
    for i, o, w in fr:
        fp = pos + o
        t = schema.get(i)
        key = names.get(i, f"f{i}")
        if t is None:
            d[key] = {"_raw": b[fp:fp + w].hex(), "_w": w}
            continue
        if t == "u8":
            d[key] = b[fp]
        elif t == "u32":
            d[key] = _u32(b, fp)
        elif t == "f32":
            d[key] = _f32(b, fp)
        elif t == "str":
            tgt = fp + _u32(b, fp)
            n = _u32(b, tgt)
            d[key] = b[tgt + 4:tgt + 4 + n].decode("utf-8")
        elif t == "vec_str":
            tgt = fp + _u32(b, fp)
            n = _u32(b, tgt)
            lst = []
            for k in range(n):
                ep = tgt + 4 + 4 * k
                et = ep + _u32(b, ep)
                ln = _u32(b, et)
                lst.append(b[et + 4:et + 4 + ln].decode("utf-8"))
            d[key] = lst
        elif t.startswith("table:"):
            tgt = fp + _u32(b, fp)
            d[key] = _decode_table(b, tgt, t.split(":")[1])
        elif t.startswith("vec_table:"):
            tgt = fp + _u32(b, fp)
            n = _u32(b, tgt)
            lst = []
            for k in range(n):
                ep = tgt + 4 + 4 * k
                lst.append(_decode_table(b, ep + _u32(b, ep), t.split(":")[1]))
            d[key] = lst
    return d


def decode(blob: bytes) -> dict:
    size, zero, magic = struct.unpack_from("<III", blob, 0)
    if magic != MAGIC or size != len(blob) - 12 or zero != 0:
        raise DecodeError(f"header mismatch: size={size} len={len(blob)} magic={magic:#x}")
    root = 12 + _u32(blob, 12)
    return _decode_table(blob, root, "root")


# ---------------------------------------------------------------- encoder
class _Builder:
    """前方組み立て式の最小 FlatBuffer ビルダー。親テーブルを先に置き、子は後ろに置く。"""

    def __init__(self):
        self.buf = bytearray()
        self.patches: list[tuple[int, int]] = []  # (uoffset位置, 対象位置)

    def align(self, n):
        while len(self.buf) % n:
            self.buf.append(0)

    def pos(self):
        return len(self.buf)

    def table(self, d: dict, kind: str) -> int:
        schema, rev = SCHEMA[kind], _REV[kind]
        items = []  # (fieldindex, type, value)
        for key, val in d.items():
            if key == "_nf":
                continue
            if key.startswith("f") and key[1:].isdigit():
                fi = int(key[1:])
            else:
                fi = rev[key]
            t = schema.get(fi)
            items.append((fi, t, val))
        nf = max([d.get("_nf", 0)] + [fi + 1 for fi, _, _ in items])
        # 幅順に並べる (4 バイト → 1 バイト)。未知フィールドは生バイトの幅。
        def width(t, v):
            if t is None:
                return v["_w"]
            return 1 if t == "u8" else 4
        items.sort(key=lambda x: (-width(x[1], x[2]), x[0]))
        # インライン領域のレイアウトを決める
        layout = {}
        off = 4
        for fi, t, v in items:
            w = width(t, v)
            if w >= 4:
                off = (off + 3) // 4 * 4
            layout[fi] = (off, w)
            off += w
        tsize = (off + 3) // 4 * 4
        # vtable (2 バイト境界) → テーブル (4 バイト境界・vtable の直後)
        self.align(2)
        vt = self.pos()
        vsz = 4 + 2 * nf
        self.buf += struct.pack("<HH", vsz, tsize)
        for i in range(nf):
            self.buf += struct.pack("<H", layout[i][0] if i in layout else 0)
        self.align(4)
        tpos = self.pos()
        self.buf += struct.pack("<i", tpos - vt)
        self.buf += bytes(tsize - 4)
        pending = []  # 子オブジェクト (後で書く)
        for fi, t, v in items:
            o, w = layout[fi]
            fp = tpos + o
            if t is None:
                self.buf[fp:fp + w] = bytes.fromhex(v["_raw"])
            elif t == "u8":
                self.buf[fp] = int(v) & 0xFF
            elif t == "u32":
                struct.pack_into("<I", self.buf, fp, int(v))
            elif t == "f32":
                struct.pack_into("<f", self.buf, fp, float(v))
            else:
                pending.append((fp, t, v))
        for fp, t, v in pending:
            if t == "str":
                self.patches.append((fp, self.string(v)))
            elif t == "vec_str":
                self.patches.append((fp, self.vec_str(v)))
            elif t.startswith("table:"):
                self.patches.append((fp, self.table(v, t.split(":")[1])))
            elif t.startswith("vec_table:"):
                self.patches.append((fp, self.vec_table(v, t.split(":")[1])))
        return tpos

    def string(self, s: str) -> int:
        self.align(4)
        p = self.pos()
        enc = s.encode("utf-8")
        self.buf += struct.pack("<I", len(enc)) + enc + b"\x00"
        return p

    def vec_str(self, lst: list[str]) -> int:
        self.align(4)
        p = self.pos()
        self.buf += struct.pack("<I", len(lst))
        slots = []
        for _ in lst:
            slots.append(self.pos())
            self.buf += b"\x00\x00\x00\x00"
        for slot, s in zip(slots, lst):
            self.patches.append((slot, self.string(s)))
        return p

    def vec_table(self, lst: list[dict], kind: str) -> int:
        self.align(4)
        p = self.pos()
        self.buf += struct.pack("<I", len(lst))
        slots = []
        for _ in lst:
            slots.append(self.pos())
            self.buf += b"\x00\x00\x00\x00"
        for slot, d in zip(slots, lst):
            self.patches.append((slot, self.table(d, kind)))
        return p

    def finish(self, root: int) -> bytes:
        for fp, tgt in self.patches:
            if tgt <= fp:
                raise ValueError("forward-offset invariant broken")
            struct.pack_into("<I", self.buf, fp, tgt - fp)
        self.align(4)
        return bytes(self.buf)


def encode(tree: dict) -> bytes:
    bld = _Builder()
    bld.buf += b"\x00\x00\x00\x00"  # root uoffset placeholder
    root = bld.table(tree, "root")
    body = bytearray(bld.finish(root))
    struct.pack_into("<I", body, 0, root)
    blob = struct.pack("<III", len(body), 0, MAGIC) + bytes(body)
    return blob


def binary_hash(blob: bytes) -> str:
    """BinaryHash 属性。末尾 8 桁 = blob 長 + 12 (参考ファイル全件で成立)。先頭 24 桁は md5 で代用。"""
    h = hashlib.md5(blob).hexdigest()[:24]
    tail = f"{len(blob) + 12:08x}"
    s = h + tail
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"


def strip_meta(tree):
    """比較用: _nf を除いた木を返す。"""
    if isinstance(tree, dict):
        return {k: strip_meta(v) for k, v in tree.items() if k != "_nf"}
    if isinstance(tree, list):
        return [strip_meta(x) for x in tree]
    return tree
