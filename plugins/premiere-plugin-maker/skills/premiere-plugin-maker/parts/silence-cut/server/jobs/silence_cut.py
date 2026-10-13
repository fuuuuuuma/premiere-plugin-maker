"""無音カット。書き出した FCP7 XML を、無音を詰めた新しい XML にする（元のシーケンスは触らない）。"""
import subprocess
import sys
from pathlib import Path

from ppm_jobs import JobError, need

NAME = "silence_cut"
VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "silence_cut.py"
REASONS = {
    3: ("カットする所が見つかりませんでした", "無音とみなす音量（閾値）が厳しすぎるか、間が短すぎます", "閾値を -45 くらいに上げるか、最小の無音の長さを短くしてもう一度試してください"),
    4: ("音声を解析できませんでした", "基準のトラックに音声が無いか、素材がオフラインです", "基準のトラック（A1 など）と、素材のリンクを確かめてください"),
    5: ("書き出した XML に映像がありません", "マルチカメラのシーケンスは FCP XML に映像が書き出されません", "マルチカメラを平らにしたシーケンスで試すか、ネストを使ってください"),
}


def run(params, ctx):
    xml_path = need(params, "xmlPath")
    out_dir = Path(ctx.tmp_dir) / "cut"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(VENDOR), xml_path, "--output-dir", str(out_dir),
           "--threshold", str(params.get("threshold", -48)), "--min-silence", str(params.get("minSilence", 0.2)),
           "--padding", str(params.get("padding", 2)), "--tracks", str(params.get("tracks", "A1"))]
    ctx.progress(10, "無音を探しています")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    if proc.returncode in REASONS:
        raise JobError(*REASONS[proc.returncode])
    if proc.returncode != 0:
        raise JobError("無音カットが失敗しました", (proc.stderr or proc.stdout)[-600:], "表示された内容を AI に伝えてください")
    produced = sorted(out_dir.glob(f"{Path(xml_path).stem}_カット済み*.xml"), key=lambda p: p.stat().st_mtime)
    if not produced:
        raise JobError("カットした XML が見つかりません", f"{out_dir} に出力がありません", "表示された内容を AI に伝えてください")
    ctx.progress(100, "できました")
    return {"outputXml": str(produced[-1]), "stdout": proc.stdout[-2000:]}
