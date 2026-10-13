"""アイコンの PNG を標準ライブラリだけで作る（角の丸い単色の四角）。"""
from __future__ import annotations

import hashlib
import struct
import zlib
from typing import Tuple

PALETTE = [(43, 91, 215), (63, 178, 107), (229, 83, 75), (230, 160, 40), (140, 90, 220), (40, 170, 190), (210, 80, 150), (110, 120, 135)]


def color_for(text: str) -> Tuple[int, int, int]:
    return PALETTE[hashlib.sha256(text.encode("utf-8")).digest()[0] % len(PALETTE)]


def _inside(x: int, y: int, size: int, r: int) -> bool:
    cx = min(max(x, r), size - 1 - r)
    cy = min(max(y, r), size - 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def rounded_icon(size: int, rgb: Tuple[int, int, int]) -> bytes:
    r = max(2, size // 5)
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            raw += bytes((rgb[0], rgb[1], rgb[2], 255 if _inside(x, y, size, r) else 0))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
