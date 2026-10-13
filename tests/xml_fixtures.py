"""合成の音声と FCP7 XML を作る（実在の素材を使わずに、カットや本文の読み取りを試すため）。"""
from __future__ import annotations

import helpers  # noqa: F401  （scripts/ を import の道に足す）
import math
import struct
import wave
from pathlib import Path
from urllib.parse import quote

TICKS_PER_SECOND = 254016000000


def write_wav(path, parts=((2.0, 16000), (1.0, 55), (2.0, 16000)), rate=48000) -> Path:
    """(秒, 振幅) を順につないだ 440Hz の音。振幅 55 はおよそ -55dBFS（既定の閾値 -48dB では無音扱い）。"""
    samples = []
    for seconds, amp in parts:
        samples.extend(int(amp * math.sin(2 * math.pi * 440 * i / rate)) for i in range(int(rate * seconds)))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return Path(path)


def file_url(path) -> str:
    p = str(Path(path).resolve()).replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return "file://localhost" + quote(p)


def _rate(tb, ntsc):
    return f"<rate><timebase>{tb}</timebase><ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc></rate>"


def write_xmeml(path, media_path, seconds=5, tb=30, ntsc=False, graphic_texts=None) -> Path:
    total = int(round(seconds * (tb * 1000 / 1001 if ntsc else tb)))
    r = _rate(tb, ntsc)
    graphics = ""
    if graphic_texts:
        items = []
        step = total // len(graphic_texts)
        for i, text in enumerate(graphic_texts):
            s, e = i * step, (i + 1) * step
            items.append(f"""<clipitem id="g-{i}"><name>{text}</name><enabled>TRUE</enabled><duration>{e - s}</duration>{r}
              <start>{s}</start><end>{e}</end><in>0</in><out>{e - s}</out>
              <file id="gfile-{i}"><name>グラフィック</name><mediaSource>GraphicAndType</mediaSource>{r}</file>
              <filter><effect><name>{text}</name><effectid>GraphicAndType</effectid></effect></filter></clipitem>""")
        graphics = "<track>" + "".join(items) + "</track>"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="seq-1">
    <name>合成</name><duration>{total}</duration>{r}
    <media>
      <video>
        <format><samplecharacteristics>{r}<width>1920</width><height>1080</height></samplecharacteristics></format>
        <track>
          <clipitem id="v-1"><name>src</name><enabled>TRUE</enabled><duration>{total}</duration>{r}
            <in>0</in><out>{total}</out><start>0</start><end>{total}</end>
            <pproTicksIn>0</pproTicksIn><pproTicksOut>{round(seconds * TICKS_PER_SECOND)}</pproTicksOut>
            <file id="file-1"><name>src</name><pathurl>{file_url(media_path)}</pathurl>{r}<duration>{total}</duration></file>
          </clipitem>
        </track>
        {graphics}
      </video>
      <audio>
        <track>
          <clipitem id="a-1"><name>src</name><enabled>TRUE</enabled><duration>{total}</duration>{r}
            <in>0</in><out>{total}</out><start>0</start><end>{total}</end>
            <pproTicksIn>0</pproTicksIn><pproTicksOut>{round(seconds * TICKS_PER_SECOND)}</pproTicksOut>
            <file id="file-1"/>
          </clipitem>
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>
"""
    Path(path).write_text(xml, encoding="utf-8")
    return Path(path)
