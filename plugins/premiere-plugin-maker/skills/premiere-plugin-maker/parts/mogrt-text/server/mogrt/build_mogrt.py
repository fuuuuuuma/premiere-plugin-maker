"""style.json ＋ 本文 → Premiere 純正 .mogrt（同梱「Basic Title.mogrt」をドナーにして中身を差し替える）。

方式は Cut&SRT の shape_mogrt.py（2026-07-25 実機実証）を継承:
  .mogrt = zip(definition.json + locale 別 .prgraphic)。.prgraphic = zip(gzip(.prproj XML))
  definition.json の sourceInfoLocalized.<locale>.id は、その locale の .prgraphic の <Sequence ObjectUID> と一致必須
  UUID（ObjectUID/ObjectURef/ClipID/…）は 1 世代ごとに振り直す（同じだと 2 個目が 1 個目を置き換える）
方式: ドナーの 2018 形式部品を残し、ソーステキスト blob だけ FlatBuffer に差し替える。
  実機 2026-09-17: Premiere 26.5 で黄文字・赤白二重縁・影が正しく描かれた（UXP 挿入）
  2026 形式の部品へ丸ごと差し替える版は importMGT が Premiere ごと固まったので消した（premiere-plugin-maker への移植時）。

実測メモ（2026-09-17・本実装時）:
  タスクブリーフに記録された尺の絶対値（<End>1250160912000</End> ほか）は en_US 版
  （project.prgraphic）のものだった。ja_JP / ko_KR / ru_RU / zh_CN 版は同じ構造だが
  実測値が locale ごとに違う（例: ja_JP の <End> は 1249758720000）。そのためリテラル値を
  ハードコードする _set_duration は ja_JP 等で置換 0 件になり必ず失敗する。
  ここでは絶対値をハードコードせず、各 .prgraphic 自身から現在値を読み直して書き換える
  （VideoClip の特定は SubClip → Clip ObjectRef／MasterClip.Clips[0] を辿る。ObjectID の
  72/96 も locale・バージョン(2025/2026/Beta) 共通で固定だが、決め打ちにはしない）。
"""
from __future__ import annotations
import argparse, base64, glob, gzip, io, json, os, re, sys, uuid, zipfile
import xml.etree.ElementTree as ET

from . import style_tree, textstyle_fb as fb
from . import cli

HERE = os.path.dirname(os.path.abspath(__file__))
TICKS = 254016000000
UUID_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
NIL_UUID = "00000000-0000-0000-0000-000000000000"
# 振り直す UUID タグ。<First> は入れない: トラックグループの <First> は「メディア種別」の定数
# （映像 228cda18-3625-4d2d-951e-348879e4ed93 / 音声 80b8e3d5-6dca-4195-aefb-cb5f407ab009）で、
# 振り直すと <MediaType> と食い違い、グラフィックが層の無い空になる（実機 2026-09-17 で確定）。
ID_TAGS = ("ClipID", "ID")
_PARAM_RE = re.compile(r"<(\w*ComponentParam)\b[^>]*>.*?</\1>", re.S)
_COMP_RE = re.compile(r'<VideoFilterComponent ObjectID="(\d+)"[^>]*>.*?</VideoFilterComponent>', re.S)


class BuildError(ValueError):
    pass


def _donor_candidates() -> list:
    env = os.environ.get("PPM_MOGRT_DONOR")
    if env:
        return [env] if os.path.exists(env) else []
    if sys.platform == "darwin":
        hits = glob.glob("/Applications/Adobe Premiere*/Adobe Premiere*.app/Contents/Essential Graphics/Basic Title.mogrt")
    elif sys.platform == "win32":
        base = os.environ.get("ProgramFiles", r"C:\Program Files")
        hits = glob.glob(os.path.join(base, "Adobe", "Adobe Premiere*", "Essential Graphics", "Basic Title.mogrt"))
    else:
        hits = []
    # ベータでない版を先に、その中で新しい版を先に
    return sorted(hits, key=lambda p: ("Beta" in p, p), reverse=False)[::-1] if hits else []


def find_donor() -> str:
    hits = [p for p in _donor_candidates() if "Beta" not in p] or _donor_candidates()
    if not hits:
        raise BuildError("Premiere の中の Basic Title.mogrt が見つかりません（Premiere が入っているか、PPM_MOGRT_DONOR でパスを渡してください）")
    return sorted(hits)[-1]


# ---------------------------------------------------------------- XML 下請け

def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _text_component(xml: str) -> tuple[int, int, str]:
    hits = [(m.start(), m.end(), m.group(0)) for m in _COMP_RE.finditer(xml) if "AE.ADBE Text" in m.group(0)]
    if len(hits) != 1:
        raise BuildError(f"テキスト部品（AE.ADBE Text）が {len(hits)} 個あります（1 個のはず）")
    return hits[0]


def _param_refs(comp_block: str) -> list[str]:
    return re.findall(r'<Param Index="\d+" ObjectRef="(\d+)"/>', comp_block)


def _param_block(xml: str, oid: str) -> tuple[int, int, str]:
    # 属性値は " で囲われているため、閉じ引用符自体が oid の完全一致を保証する（\b は不要かつ
    # 引用符の直後に置くと非-単語文字どうしの境界になり常に不成立になるので付けない）。
    m = re.search(rf'<(\w*ComponentParam) ObjectID="{oid}"[^>]*>.*?</\1>', xml, re.S)
    if not m:
        raise BuildError(f"ObjectID={oid} のパラメータがありません")
    return m.start(), m.end(), m.group(0)


def _next_object_id(xml: str) -> int:
    return max(int(x) for x in re.findall(r'ObjectID="(\d+)"', xml)) + 1


def _set_blob(block: str, blob: bytes) -> str:
    b64 = base64.b64encode(blob).decode("ascii")
    out, n = re.subn(
        r'<StartKeyframeValue([^>]*?)BinaryHash="[^"]*"([^>]*)>.*?</StartKeyframeValue>',
        lambda m: f'<StartKeyframeValue{m.group(1)}BinaryHash="{fb.binary_hash(blob)}"{m.group(2)}>{b64}\n\t\t</StartKeyframeValue>',
        block, count=1, flags=re.S)
    if n != 1:
        raise BuildError("StartKeyframeValue を書き換えられません")
    return out


def _set_point(block: str, x: float, y: float) -> str:
    """Position の StartKeyframe。ドナー形式（x,y）か 2026 形式（x:y）かを見て同じ形式で書く。"""
    m = re.search(r"<StartKeyframe>([^<]*)</StartKeyframe>", block)
    if not m:
        raise BuildError("Position に StartKeyframe がありません")
    fields = m.group(1).split(",")
    if ":" in fields[1]:
        fields[1] = f"{x:g}:{y:g}"
    else:
        fields[1], fields[2] = f"{x:g}", f"{y:g}"
    return block[:m.start()] + f"<StartKeyframe>{','.join(fields)}</StartKeyframe>" + block[m.end():]


def _set_layer_name(xml: str, text: str) -> str:
    return re.sub(r"<InstanceName>[^<]*</InstanceName>", f"<InstanceName>{_esc(text[:40])}</InstanceName>", xml, count=1)


def _graphic_ids(xml: str) -> tuple[str, str, str]:
    """SubClip を起点に、グラフィック本体の (MasterClip UUID, アクティブ VideoClip の ObjectID,
    予備 VideoClip の ObjectID) を辿る。実測ではドナー全 locale・全バージョンで 72/96 固定だが、
    ObjectID の割り振りが将来変わっても参照関係から辿れるように決め打ちしない。"""
    m = re.search(r'<SubClip ObjectID="\d+"[^>]*>.*?</SubClip>', xml, re.S)
    if not m:
        raise BuildError("SubClip が見つかりません")
    sub = m.group(0)
    active_m = re.search(r'<Clip ObjectRef="(\d+)"/>', sub)
    uid_m = re.search(rf'<MasterClip ObjectURef="({UUID_RE})"/>', sub)
    if not (active_m and uid_m):
        raise BuildError("SubClip から Clip / MasterClip を特定できません")
    active_oid, uid = active_m.group(1), uid_m.group(1)
    mc_m = re.search(rf'<MasterClip ObjectUID="{uid}"[^>]*>.*?</MasterClip>', xml, re.S)
    if not mc_m:
        raise BuildError(f"MasterClip {uid} が見つかりません")
    spare_m = re.search(r'<Clip Index="0" ObjectRef="(\d+)"/>', mc_m.group(0))
    if not spare_m:
        raise BuildError("MasterClip の Clips[0] が見つかりません")
    return uid, active_oid, spare_m.group(1)


def _rename_graphic(xml: str, name: str) -> str:
    """SubClip が参照する MasterClip（グラフィック本体）の Name だけを改名する。"""
    uid, _, _ = _graphic_ids(xml)
    pat = rf'(<MasterClip ObjectUID="{uid}"[^>]*>.*?)<Name>[^<]*</Name>'
    out, n = re.subn(pat, lambda m: f"{m.group(1)}<Name>{_esc(name)}</Name>", xml, count=1, flags=re.S)
    if n != 1:
        raise BuildError("MasterClip の Name を書き換えられません")
    return out


def _clip_block(xml: str, oid: str) -> tuple[int, int, str]:
    m = re.search(rf'<VideoClip ObjectID="{oid}"[^>]*>.*?</VideoClip>', xml, re.S)
    if not m:
        raise BuildError(f"VideoClip ObjectID={oid} が見つかりません")
    return m.start(), m.end(), m.group(0)


def _set_duration(xml: str, seconds: float) -> str:
    """TrackItem の尺・OriginalDuration・アクティブ/予備 VideoClip の OutPoint を書き換える。

    絶対値はハードコードしない: <End> の現在値を読み直し、それと一致する 2 件の
    <OriginalDuration> だけを対象にする（3 件目は無関係な巨大値で常に不一致）。
    VideoClip 側は _graphic_ids で特定した 2 個（アクティブ／予備）それぞれについて、
    元の「OutPoint - InPoint - 元の End」= 余白を測り、新しい尺でも同じ余白を保つ。
    置換件数が想定と違えば止める（黙って別の尺で出さない）。
    """
    d = int(round(seconds * TICKS))
    m = re.search(r"<End>(\d+)</End>", xml)
    if not m:
        raise BuildError("<End> が見つかりません")
    e0 = int(m.group(1))
    xml, n = re.subn(rf"<End>{e0}</End>", f"<End>{d}</End>", xml, count=1)
    if n != 1:
        raise BuildError(f"尺(End)の書き換えに失敗: {n} 件")
    xml, n = re.subn(rf"<OriginalDuration>{e0}</OriginalDuration>", f"<OriginalDuration>{d}</OriginalDuration>", xml)
    if n != 2:
        raise BuildError(f"尺(OriginalDuration)の書き換えに失敗: {e0} 一致が {n} 件（想定 2 件）")

    _, active_oid, spare_oid = _graphic_ids(xml)
    if active_oid == spare_oid:
        raise BuildError("アクティブ/予備の VideoClip が同一 ObjectID です")
    for oid in (active_oid, spare_oid):
        s, e, block = _clip_block(xml, oid)
        ip_m = re.search(r"<InPoint>(\d+)</InPoint>", block)
        op_m = re.search(r"<OutPoint>(\d+)</OutPoint>", block)
        if not (ip_m and op_m):
            raise BuildError(f"VideoClip ObjectID={oid} に InPoint/OutPoint がありません")
        ip0, op0 = int(ip_m.group(1)), int(op_m.group(1))
        pad = op0 - ip0 - e0                       # 元ファイルにあった余白を維持する
        new_op = ip0 + d + pad
        new_block, cnt = re.subn(rf"<OutPoint>{op0}</OutPoint>", f"<OutPoint>{new_op}</OutPoint>", block, count=1)
        if cnt != 1:
            raise BuildError(f"VideoClip ObjectID={oid} の OutPoint 書き換えに失敗")
        xml = xml[:s] + new_block + xml[e:]
    return xml


def _regenerate_ids(xml: str) -> str:
    targets: set[str] = set()
    for attr in ("ObjectUID", "ObjectURef"):
        targets.update(re.findall(attr + r'="(' + UUID_RE + r')"', xml))
    for tag in ID_TAGS:
        targets.update(re.findall(rf"<{tag}>({UUID_RE})</{tag}>", xml))
    targets.discard(NIL_UUID)
    mapping = {old: str(uuid.uuid4()) for old in targets}
    xml = re.sub(r'\b(ObjectUID|ObjectURef)="(' + UUID_RE + r')"', lambda m: f'{m.group(1)}="{mapping.get(m.group(2), m.group(2))}"', xml)
    for tag in ID_TAGS:
        xml = re.sub(rf"<{tag}>({UUID_RE})</{tag}>", lambda m, tag=tag: f"<{tag}>{mapping.get(m.group(1), m.group(1))}</{tag}>", xml)
    return xml


def sequence_uid(xml: str) -> str:
    m = re.search(r'<Sequence ObjectUID="(' + UUID_RE + r')"', xml)
    if not m:
        raise BuildError("<Sequence ObjectUID> がありません")
    return m.group(1)


# ---------------------------------------------------------------- 部品の差し替え

def _apply_blob_variant(xml: str, blob: bytes, x: float, y: float) -> str:
    cs, ce, comp = _text_component(xml)
    refs = _param_refs(comp)
    s, e, blk = _param_block(xml, refs[0])          # Source Text
    xml = xml[:s] + _set_blob(blk, blob) + xml[e:]
    s, e, blk = _param_block(xml, refs[2])          # Position（ParameterID 3）
    xml = xml[:s] + _set_point(blk, x, y) + xml[e:]
    return xml


# ---------------------------------------------------------------- definition.json / 出力

def _patch_definition(raw: bytes, name: str, text: str, font: str, seq_uids: dict, seconds: float) -> bytes:
    d = json.loads(raw.decode("utf-8"))
    d["capsuleID"] = str(uuid.uuid4())
    d["capsuleName"] = name
    for e in d.get("capsuleNameLocalized", {}).get("strDB", []):
        e["str"] = name
    for c in d.get("clientControls") or []:
        if c.get("type") == 6:
            for e in (c.get("value") or {}).get("strDB", []):
                e["str"] = text
    if isinstance(d.get("usedFontsLocalized"), dict):
        d["usedFontsLocalized"] = {k: [font] for k in d["usedFontsLocalized"]}
    src = d.get("sourceInfoLocalized") or {}
    if not src:
        raise BuildError("definition.json に sourceInfoLocalized がありません")
    for locale, info in src.items():
        if locale not in seq_uids:
            raise BuildError(f"locale {locale} の .prgraphic を生成できていません")
        info["id"] = seq_uids[locale]
        # duration だけ書き換える。outpoint/workoutpoint はドナー実測で duration と無関係
        # （全 locale で outpoint={"scale":1,"value":-400000}, workoutpoint={"scale":1,"value":0}）
        # なのでここで上書きすると inpoint/workinpoint（未変更）と矛盾する。ドナーの値のまま残す。
        if isinstance(info.get("duration"), dict) and "scale" in info["duration"]:
            info["duration"] = {"scale": 12000, "value": int(round(seconds * 12000))}
    return json.dumps(d, ensure_ascii=False).encode("utf-8")


def _locale_of(name: str) -> str:
    stem = name[:-len(".prgraphic")]
    return stem[len("project_"):] if stem.startswith("project_") else "en_US"


def _read_inner(zbytes: bytes) -> tuple[str, str]:
    with zipfile.ZipFile(io.BytesIO(zbytes)) as g:
        inner = g.namelist()[0]
        return inner, gzip.decompress(g.read(inner)).decode("utf-8")


def _write_inner(inner_name: str, xml: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as g:
        g.writestr(inner_name, gzip.compress(xml.encode("utf-8")))
    return buf.getvalue()


def build(style: dict, text: str, out_path: str, name: str | None = None, duration: float | None = None,
          position: tuple | None = None, donor_path: str | None = None) -> dict:
    text = str(text or "").strip()
    if not text:
        raise BuildError("本文が空です")
    name = name or str(style.get("name") or style.get("id") or "Effect & Design")
    pos = position or (float((style.get("position") or {}).get("x", 0.5)), float((style.get("position") or {}).get("y", 0.86)))
    blob = style_tree.encode_style(style, text)
    donor = donor_path or find_donor()

    with zipfile.ZipFile(donor) as zin:
        names = zin.namelist()
        if "definition.json" not in names or "project.prgraphic" not in names:
            raise BuildError(f"ドナーの中身が想定と違います: {names}")
        # 尺省略時の既定値はドナー（en_US 版）の現在値を実測して使う（リテラル定数を置かない）
        _, default_xml = _read_inner(zin.read("project.prgraphic"))
        default_end = re.search(r"<End>(\d+)</End>", default_xml)
        if not default_end:
            raise BuildError("ドナーの project.prgraphic に <End> がありません")
        seconds = float(duration) if duration else int(default_end.group(1)) / TICKS

        prgraphics, seq_uids = {}, {}
        for n in names:
            if not n.endswith(".prgraphic"):
                continue
            inner, xml = _read_inner(zin.read(n))
            xml = _apply_blob_variant(xml, blob, *pos)
            xml = _set_layer_name(xml, text)
            xml = _rename_graphic(xml, name)
            if duration:
                xml = _set_duration(xml, seconds)
            xml = _regenerate_ids(xml)
            prgraphics[n] = _write_inner(inner, xml)
            seq_uids[_locale_of(n)] = sequence_uid(xml)
        definition = _patch_definition(zin.read("definition.json"), name, text, style["font"], seq_uids, seconds)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            zout.writestr("definition.json", definition)
            for n, data in prgraphics.items():
                zout.writestr(n, data)
            if "thumb.png" in names:
                zout.writestr("thumb.png", zin.read("thumb.png"))
    v = verify(out_path)
    if not v["ok"]:
        raise BuildError("生成物の検査に失敗: " + "; ".join(v["errors"]))
    return {"mogrtPath": out_path, "name": name, "font": style["font"],
            "durationSeconds": round(seconds, 4), "donor": donor}


def verify(path: str) -> dict:
    """XML 整形式 / ObjectID 一意 / 参照解決 / テキスト部品 1 個 / blob 復号 / locale id 連結。"""
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            d = json.loads(z.read("definition.json"))
            for n in names:
                if not n.endswith(".prgraphic"):
                    continue
                _, xml = _read_inner(z.read(n))
                try:
                    ET.fromstring(xml.encode("utf-8"))
                except ET.ParseError as e:
                    errors.append(f"{n}: XML が壊れています ({e})")
                    continue
                ids = re.findall(r'ObjectID="(\d+)"', xml)
                if len(ids) != len(set(ids)):
                    errors.append(f"{n}: ObjectID が重複")
                refs = set(re.findall(r'ObjectRef="(\d+)"', xml))
                if not refs <= set(ids):
                    errors.append(f"{n}: 未解決の ObjectRef {sorted(refs - set(ids))[:5]}")
                try:
                    _, _, comp = _text_component(xml)
                    first = _param_refs(comp)[0]
                    blk = _param_block(xml, first)[2]
                    b64 = re.search(r"<StartKeyframeValue[^>]*>([^<]*)<", blk).group(1)
                    fb.decode(base64.b64decode(b64.strip()))
                except Exception as e:
                    errors.append(f"{n}: テキスト部品/blob の検査に失敗 ({e})")
                    continue
                loc = _locale_of(n)
                want = (d.get("sourceInfoLocalized") or {}).get(loc, {}).get("id")
                if want != sequence_uid(xml):
                    errors.append(f"{n}: definition の id とシーケンス UID が不一致")
            if not any(n.endswith(".prgraphic") for n in names):
                errors.append("prgraphic がありません")
    except Exception as e:
        errors.append(f"開けません ({e})")
    return {"ok": not errors, "errors": errors}


def main(argv=None) -> int:
    def go():
        ap = argparse.ArgumentParser()
        ap.add_argument("--style", required=True); ap.add_argument("--text", required=True); ap.add_argument("--out", required=True)
        ap.add_argument("--duration", type=float); ap.add_argument("--name")
        ap.add_argument("--x", type=float); ap.add_argument("--y", type=float)
        a = ap.parse_args(argv)
        with open(a.style, encoding="utf-8") as f:
            style = json.load(f)
        if not isinstance(style, dict):
            return cli.fail("デザインの定義が壊れています（style.json がオブジェクトではありません）")
        pos = (a.x, a.y) if a.x is not None and a.y is not None else None
        return build(style, a.text, a.out, name=a.name, duration=a.duration, position=pos)
    return cli.run(go, "デザインを組み立てられません")


if __name__ == "__main__":
    sys.exit(main())
