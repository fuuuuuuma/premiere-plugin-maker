"""Adobe Fonts の列挙（KAZARU fonts.py の写し）と、cmap で「その文字がフォントにあるか」を判定する。
幅や画素での判定は禁止（全角は送り幅が一律・代替字形が黙って出る）。"""
from __future__ import annotations
import mmap, os, struct, sys

if sys.platform == "win32":
    ADOBE_DIR = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CoreSync", "plugins", "livetype")
    LOCAL_DIRS = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
                  os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
else:
    ADOBE_DIR = os.path.expanduser("~/Library/Application Support/Adobe/CoreSync/plugins/livetype")
    # 自分で入れた書体・システムの書体。買った・作ったスタイルはこちらの書体を使うことが多い（851 チカラ 2026-09-19）
    LOCAL_DIRS = [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts"]


def _u16(b, o): return struct.unpack_from(">H", b, o)[0]
def _u32(b, o): return struct.unpack_from(">I", b, o)[0]


def _face_offsets(data: bytes) -> list[int]:
    tag = data[:4]
    if tag == b"ttcf":
        n = _u32(data, 8)
        return [_u32(data, 12 + 4 * i) for i in range(min(n, 16))]
    if tag in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        return [0]
    raise ValueError("OpenType/TrueType フォントではありません")


def _table(data: bytes, off: int, name: bytes):
    num = _u16(data, off + 4)
    for i in range(num):
        rec = off + 12 + 16 * i
        if data[rec:rec + 4] == name:
            return _u32(data, rec + 8), _u32(data, rec + 12)
    return None


def _names(data: bytes, off: int) -> dict:
    t = _table(data, off, b"name")
    if not t:
        return {}
    name_off = t[0]
    count, str_off = _u16(data, name_off + 2), _u16(data, name_off + 4)
    best = {}
    for i in range(count):
        r = name_off + 6 + 12 * i
        pid, eid, lid, nid, ln, so = struct.unpack_from(">HHHHHH", data, r)
        if nid not in (1, 2, 6, 16, 17):
            continue
        raw = data[name_off + str_off + so: name_off + str_off + so + ln]
        try:
            s = raw.decode("utf-16-be") if pid in (0, 3) else raw.decode("mac_roman")
        except UnicodeDecodeError:
            continue
        best.setdefault((nid, lid), s)
    def pick(nid):
        for lid in (0x409, 0, 0x411):
            if (nid, lid) in best:
                return best[(nid, lid)]
        for (n, _l), v in best.items():
            if n == nid:
                return v
        return ""
    return {"ps": pick(6), "family": pick(16) or pick(1), "style": pick(17) or pick(2),
            "family_ja": best.get((16, 0x411)) or best.get((1, 0x411)) or ""}


def read_cmap(data: bytes, face_offset: int = 0) -> set[int]:
    """Unicode → glyph のある符号位置の集合。format 12（BMP 外込み）を優先し、無ければ format 4。"""
    t = _table(data, face_offset, b"cmap")
    if not t:
        raise ValueError("cmap テーブルがありません")
    base = t[0]
    n = _u16(data, base + 2)
    subs = []
    for i in range(n):
        pid, eid, off = struct.unpack_from(">HHI", data, base + 4 + 8 * i)
        subs.append((pid, eid, base + off))
    def rank(s):
        pid, eid, _ = s
        return {(3, 10): 0, (0, 4): 1, (0, 6): 1, (3, 1): 2, (0, 3): 3}.get((pid, eid), 9)
    codes: set[int] = set()
    for pid, eid, off in sorted(subs, key=rank):
        fmt = _u16(data, off)
        if fmt == 12:
            ngroups = _u32(data, off + 12)
            for g in range(ngroups):
                s, e, _gid = struct.unpack_from(">III", data, off + 16 + 12 * g)
                codes.update(range(s, min(e, 0x10FFFF) + 1))
            return codes
        if fmt == 4:
            segx2 = _u16(data, off + 6)
            seg = segx2 // 2
            ends = [_u16(data, off + 14 + 2 * i) for i in range(seg)]
            starts = [_u16(data, off + 16 + segx2 + 2 * i) for i in range(seg)]
            deltas = [_u16(data, off + 16 + 2 * segx2 + 2 * i) for i in range(seg)]
            ro_base = off + 16 + 3 * segx2
            ros = [_u16(data, ro_base + 2 * i) for i in range(seg)]
            for i in range(seg):
                if starts[i] == 0xFFFF:
                    continue
                for c in range(starts[i], ends[i] + 1):
                    if ros[i] == 0:
                        gid = (c + deltas[i]) & 0xFFFF
                    else:
                        addr = ro_base + 2 * i + ros[i] + 2 * (c - starts[i])
                        gid = _u16(data, addr)
                        if gid:
                            gid = (gid + deltas[i]) & 0xFFFF
                    if gid:
                        codes.add(c)
            return codes
    raise ValueError("対応する cmap サブテーブル（format 4/12）がありません")


def missing_chars(font_path: str, text: str, ps_name: str | None = None) -> list[str]:
    with open(font_path, "rb") as f:
        data = f.read()
    offsets = _face_offsets(data)
    if ps_name:
        matched = [o for o in offsets if _names(data, o).get("ps") == ps_name]
        if not matched:
            raise ValueError(f"フォント {font_path} に PostScript 名 {ps_name} のフェイスがありません")
        offsets = matched
    codes = read_cmap(data, offsets[0])
    return [ch for ch in text if ord(ch) not in codes and not ch.isspace()]


_SCAN: list[dict] | None = None     # 1 回の実行で 1 度だけ読む（デザインごとに全フォントを読み直すと 8 秒かかった）


def scan_adobe() -> list[dict]:
    global _SCAN
    if _SCAN is None:
        _SCAN = _scan_adobe()
    return [dict(f) for f in _SCAN]


def _scan_adobe() -> list[dict]:
    out, seen = [], set()
    if not os.path.isdir(ADOBE_DIR):
        return out
    for dp, _dn, fn in os.walk(ADOBE_DIR):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) < 20000:
                    continue
                with open(p, "rb") as fh:
                    data = fh.read()
                for off in _face_offsets(data):
                    nm = _names(data, off)
                    if nm.get("ps") and nm["ps"] not in seen:
                        seen.add(nm["ps"])
                        out.append(dict(nm, path=p))
            except (OSError, ValueError, struct.error):
                continue
    out.sort(key=lambda x: (x["family"], x["ps"]))
    return out


_LOCAL: dict | None = None


def _scan_local() -> dict:
    """PostScript 名 → 書体。ファイルは mmap で開き、見出しと name 表だけを読む（システムの書体は大きい）"""
    out: dict = {}
    for base in LOCAL_DIRS:
        if not os.path.isdir(base):
            continue
        for dp, _dn, fn in os.walk(base):
            for f in fn:
                if not f.lower().endswith((".ttf", ".otf", ".ttc", ".otc")):
                    continue
                p = os.path.join(dp, f)
                try:
                    with open(p, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as data:
                        for off in _face_offsets(data):
                            nm = _names(data, off)
                            if nm.get("ps") and nm["ps"] not in out:
                                out[nm["ps"]] = dict(nm, path=p)
                except (OSError, ValueError, struct.error):
                    continue
    return out


def find(ps_name: str) -> dict | None:
    """Adobe Fonts を先に、無ければ自分で入れた書体・システムの書体から探す（どちらも 1 回の実行で 1 度だけ読む）"""
    global _SCAN, _LOCAL
    if _SCAN is None:
        _SCAN = _scan_adobe()
    for f in _SCAN:
        if f["ps"] == ps_name:
            return dict(f)
    if _LOCAL is None:
        _LOCAL = _scan_local()
    face = _LOCAL.get(ps_name)
    return dict(face) if face else None


def list_fonts() -> list[str]:
    """入っている書体の PostScript 名の一覧（Adobe Fonts と、自分で入れた書体・システムの書体）。"""
    global _SCAN, _LOCAL
    if _SCAN is None:
        _SCAN = _scan_adobe()
    if _LOCAL is None:
        _LOCAL = _scan_local()
    return sorted({f["ps"] for f in _SCAN} | set(_LOCAL))
