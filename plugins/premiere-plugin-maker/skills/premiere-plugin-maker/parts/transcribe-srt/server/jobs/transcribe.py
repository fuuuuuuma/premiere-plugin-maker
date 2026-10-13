"""素材を文字起こしして SRT を作る。範囲（start・duration）を渡すと、その部分だけを起こす。"""
import tempfile
from pathlib import Path

import ppm_media
import ppm_transcribe as tr
from ppm_jobs import JobError, need

NAME = "transcribe"


def run(params, ctx):
    media = need(params, "mediaPath")
    if tr.choose_engine() is None:
        raise JobError("文字起こしの部品がありません", "mlx-whisper / faster-whisper のどちらも入っていません", tr.install_hint())
    ctx.progress(5, "音声を取り出しています")
    start, duration = params.get("start"), params.get("duration")
    wav = Path(tempfile.mkdtemp(dir=ctx.tmp_dir)) / "audio.wav"
    try:
        pcm = ppm_media.extract_pcm16(media, rate=16000, start=start, duration=duration)
    except ppm_media.MediaError as e:
        raise JobError("音声を取り出せませんでした", str(e), "素材のリンク切れと、ffmpeg が入っているかを確かめてください") from None
    import wave
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)
    ctx.progress(20, "文字起こしをしています（長い素材は数分かかります）")
    segments = tr.transcribe(str(wav), language=params.get("language", "ja"))
    if start:
        segments = [{**s, "start": s["start"] + float(start), "end": s["end"] + float(start)} for s in segments]
    out = Path(ctx.tmp_dir) / (Path(media).stem + ".srt")
    out.write_text(tr.to_srt(segments, int(params.get("maxChars", 18))), encoding="utf-8")
    return {"srtPath": str(out), "segments": len(segments), "engine": tr.choose_engine()}
