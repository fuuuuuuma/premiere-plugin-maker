"""ffmpeg の場所探しと、音声の取り出し・音量の計算（標準ライブラリだけ）。

- Mac は /opt/homebrew/bin を先に見る（~/.local/bin などに Intel 専用の ffmpeg が混ざっている Mac があった）
- Windows は winget の別名リンク（%LOCALAPPDATA%\\Microsoft\\WinGet\\Links）も見る。開いたままの画面には PATH が反映されない
- 見つけた候補は実際に起動して確かめる（which で見つかっても動くとは限らない）
"""
from __future__ import annotations

import array
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional


class MediaError(RuntimeError):
    pass


def _candidates(name: str) -> List[str]:
    if sys.platform == "darwin":
        return [f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"]
    if sys.platform == "win32":
        links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
        return [str(links)]
    return []


def find_tool(name: str, which: Callable[[str], Optional[str]] = shutil.which, run=subprocess.run,
              extra: Optional[List[str]] = None) -> Optional[str]:
    candidates = (_candidates(name) if extra is None else extra) + [which(name) or ""]
    for path in candidates:
        if not path or (extra is None and not Path(path).exists() and path != which(name)):
            continue
        try:
            r = run([path, "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0:
            return path
    return None


def _tool(name: str) -> str:
    path = find_tool(name)
    if not path:
        hint = "brew install ffmpeg" if sys.platform == "darwin" else "winget install --id Gyan.FFmpeg -e（入れた後は新しい画面で）"
        raise MediaError(f"{name} が見つかりません。入れ方: {hint}")
    return path


def extract_pcm16(path, rate: int = 16000, start: Optional[float] = None, duration: Optional[float] = None) -> bytes:
    cmd = [_tool("ffmpeg"), "-nostdin", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"]
    r = subprocess.run(cmd, capture_output=True, timeout=3600)
    if r.returncode != 0:
        raise MediaError("音声を取り出せませんでした: " + r.stderr.decode("utf-8", "replace")[-500:])
    return r.stdout


def rms_db(samples, window: int) -> List[float]:
    """window 個ずつの音量（dBFS）。無音は -120.0。"""
    if not isinstance(samples, array.array):
        samples = array.array("h", samples)
    out = []
    for i in range(0, len(samples) - window + 1, window):
        chunk = samples[i:i + window]
        mean = sum(s * s for s in chunk) / window
        out.append(-120.0 if mean <= 0 else round(20 * math.log10(math.sqrt(mean) / 32768.0), 2))
    return out


def probe_duration(path) -> float:
    r = subprocess.run([_tool("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0:
        raise MediaError("長さを読めませんでした: " + r.stderr[-500:])
    return float(r.stdout.strip())
