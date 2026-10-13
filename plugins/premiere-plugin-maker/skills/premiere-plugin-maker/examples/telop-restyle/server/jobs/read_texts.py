"""選んだクリップの位置から、テロップの本文を FCP7 XML で読む（UXP ではテロップの本文を直接読めない）。"""
import ppm_fcpxml as fx
from ppm_jobs import JobError, need

NAME = "read_texts"


def run(params, ctx):
    xml_path = need(params, "xmlPath")
    clips = need(params, "clips", list)
    try:
        seq = fx.main_sequence(fx.load(xml_path).getroot())
    except fx.XmlError as e:
        raise JobError("書き出した XML が読めません", str(e), "パネルからもう一度書き出してください") from None
    timebase, ntsc = fx.rate_of(seq)
    tpf = fx.ticks_per_frame(timebase, ntsc)
    texts = []
    for c in clips:
        frame = round(float(c["startTicks"]) / tpf)
        ci = fx.find_clip(seq, "video", int(c["trackIndex"]), frame)
        texts.append({"trackIndex": c["trackIndex"], "startTicks": c["startTicks"], "text": fx.clip_text(ci) if ci is not None else None})
    return {"texts": texts, "timebase": timebase, "ntsc": ntsc}
