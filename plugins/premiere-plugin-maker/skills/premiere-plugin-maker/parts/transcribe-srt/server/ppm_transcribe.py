"""文字起こしと SRT。Mac（Apple シリコン）は mlx-whisper、それ以外は faster-whisper。

- エンジンとモデルは自動では入れない。足りなければ install_hint() の内容を見せて、許可を取ってから入れる
- モデルは初回に約 1.5GB をダウンロードする（以降は手元に残る）
- Windows の NVIDIA の GPU は、CUDA の部品が無いと失敗するので CPU に切り替えて続ける
- 改行はここでは機械的に行う。意味で区切る改行は premiere-skills の /srt の作り方（知識 feat-premiere-skills）を使う
"""
from __future__ import annotations

import importlib.util
import platform as _platform
import re
import sys
from typing import Callable, List, Optional, Tuple

DEFAULT_MODEL = {"mlx": "mlx-community/whisper-large-v3-turbo", "faster": "large-v3-turbo"}
_BREAK_AFTER = "、。，．！？!?…）」』"


def choose_engine(platform: str = sys.platform, machine: Optional[str] = None, has: Callable = importlib.util.find_spec) -> Optional[str]:
    machine = machine if machine is not None else _platform.machine()
    if platform == "darwin" and machine == "arm64" and has("mlx_whisper"):
        return "mlx"
    if has("faster_whisper"):
        return "faster"
    return None


def install_hint(platform: str = sys.platform, machine: Optional[str] = None) -> str:
    machine = machine if machine is not None else _platform.machine()
    if platform == "darwin" and machine == "arm64":
        cmd = "python3 -m pip install mlx-whisper"
    elif platform == "win32":
        cmd = "py -3 -m pip install faster-whisper"
    else:
        cmd = "python3 -m pip install faster-whisper"
    return (f"文字起こしの部品が入っていません。入れるには: {cmd}（サーバーの install.py --with-deps でも入ります）。"
            "初回はモデル（約 1.5GB）をダウンロードします。入れる前に、利用者の許可を取ってください")


def srt_time(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_lines(text: str, max_chars: int = 18) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text] if text else []
    best = -1
    for i, ch in enumerate(text[: max_chars + 1]):
        if ch in _BREAK_AFTER or ch == " ":
            best = i
    cut = best + 1 if best >= 0 else max_chars
    first, rest = text[:cut].strip(), text[cut:].strip()
    return [first, rest] if rest else [first]


def to_srt(segments: List[dict], max_chars: int = 18) -> str:
    blocks = []
    n = 0
    for seg in segments:
        lines = split_lines(str(seg.get("text", "")), max_chars)
        if not lines:
            continue
        n += 1
        blocks.append(f"{n}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n" + "\n".join(lines) + "\n")
    return "\n".join(blocks)


def shift_segments(segments: List[dict], keep_ranges: List[Tuple[float, float, float]]) -> List[dict]:
    """カットで残した区間 (素材の始まり, 素材の終わり, タイムラインの始まり) に合わせて、字幕をタイムラインの時刻にずらす。"""
    out = []
    for seg in segments:
        for src_start, src_end, tl_start in keep_ranges:
            s, e = max(seg["start"], src_start), min(seg["end"], src_end)
            if e - s > 0.05:
                out.append({"start": round(tl_start + (s - src_start), 3), "end": round(tl_start + (e - src_start), 3), "text": seg["text"]})
    return out


def transcribe(path: str, language: str = "ja", model: Optional[str] = None) -> List[dict]:
    engine = choose_engine()
    if engine is None:
        raise RuntimeError(install_hint())
    if engine == "mlx":
        import mlx_whisper  # type: ignore
        result = mlx_whisper.transcribe(str(path), path_or_hf_repo=model or DEFAULT_MODEL["mlx"], language=language)
        return [{"start": float(s["start"]), "end": float(s["end"]), "text": s["text"].strip()} for s in result.get("segments", [])]
    from faster_whisper import WhisperModel  # type: ignore
    try:
        wm = WhisperModel(model or DEFAULT_MODEL["faster"], device="auto")
        segments, _ = wm.transcribe(str(path), language=language, vad_filter=True)
        return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    except Exception as e:  # noqa: BLE001  CUDA の部品が無いなど
        if "cublas" not in str(e).lower() and "cuda" not in str(e).lower():
            raise
        wm = WhisperModel(model or DEFAULT_MODEL["faster"], device="cpu", compute_type="int8")
        segments, _ = wm.transcribe(str(path), language=language, vad_filter=True)
        return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
