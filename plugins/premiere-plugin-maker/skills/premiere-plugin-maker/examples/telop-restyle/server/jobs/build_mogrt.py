"""テロップの MOGRT を 1 本ずつ作る（Premiere の中の Basic Title.mogrt をドナーにして、文字のデザインを差し替える）。"""
import json
from pathlib import Path

from mogrt import build_mogrt, fonts
from ppm_jobs import JobError

NAME = "build_mogrt"
STYLES = Path(__file__).resolve().parent.parent / "mogrt" / "styles"


def _style(params):
    if isinstance(params.get("style"), dict):
        return params["style"]
    name = params.get("styleName", "white-black")
    path = STYLES / f"{name}.json"
    if not path.exists():
        raise JobError(f"デザイン「{name}」がありません", "", "使えるのは: " + ", ".join(sorted(p.stem for p in STYLES.glob("*.json"))))
    return json.loads(path.read_text(encoding="utf-8"))


def run(params, ctx):
    style = _style(params)
    items = params.get("items") or []
    if not items:
        raise JobError("作るテロップがありません", "items が空です", "選んだクリップの本文を渡してください")
    warnings = []
    try:
        installed = set(fonts.list_fonts()) if hasattr(fonts, "list_fonts") else set()
    except Exception:  # noqa: BLE001  書体の一覧が取れなくても作るのは止めない
        installed = set()
    if installed and style.get("font") not in installed:
        warnings.append(f"書体 {style.get('font')} が見つかりません。Premiere は別の書体で描きます（list_fonts で入っている書体を選べます）")
    out_dir = Path(ctx.tmp_dir) / "mogrt"
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for i, item in enumerate(items):
        if ctx.cancelled():
            return None
        ctx.progress(int(100 * i / len(items)), f"{i + 1}/{len(items)} 本目を作っています")
        path = out_dir / f"ppm_{i:03d}_{abs(hash(item['text'])) % 10**8}.mogrt"
        try:
            info = build_mogrt.build(style, item["text"], str(path), name=item.get("name"), duration=item.get("duration"))
        except build_mogrt.BuildError as e:
            raise JobError("テロップを作れませんでした", str(e), "Premiere が入っているか、デザインの定義を確かめてください") from None
        made.append({"text": item["text"], "path": info["mogrtPath"], "durationSeconds": info["durationSeconds"]})
    return {"mogrts": made, "warnings": warnings}
