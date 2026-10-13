"""プリセット定義 (JSON) から Premiere Pro の .prfpset (エフェクトプリセット) を組み立てる。

CLI: python3 -m presets.prfpset_build <spec.json> <out.prfpset>（KAZARU の kazaru_core/prfpset_build.py から写した）
エフェクトは「トランスフォーム」(AE.ADBE Geometry2) を使う。位置は正規化座標
(0.5:0.5 が中央、1.0 が画面幅/高さ)。時間は秒。
キーフレーム補間: linear / easein / easeout / hold / auto(ベジェ)
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
GEOM_SKELETON = os.path.join(HERE, "templates", "geometry2_skeleton.xml")

TICKS = 254016000000          # 1 秒のティック数
ANCHOR_IN = 914456685542400   # 同梱プリセットと同じ基準時刻
START_T = -91445760000000000  # StartKeyframe の時刻 (固定)
VIDEO_MEDIA = "228cda18-3625-4d2d-951e-348879e4ed93"
CLS = {
    "Tree": "177f2841-dd5b-43bd-9d9a-79e231bd47dd",
    "BinTreeItem": "5e0f46fa-384f-4c09-bc53-0b8e2b7005b5",
    "EffectBinItem": "5f513d71-0018-4405-a10b-bf5597f99960",
    "TreeItem": "025f59ac-1f29-42c0-9897-ada1059bd547",
    "FilterPresetItem": "e56c9ba0-91cb-4f21-9174-c1b52448c6c9",
    "FilterPreset": "ee52a7d2-069e-47f7-aa30-e3e3286b65a3",
}
# トランスフォームのパラメータ名 → ParameterID
PARAM_ID = {
    "anchor": 1, "position": 2, "uniform": 11, "scale_h": 3, "scale_w": 4, "skew": 5, "skew_axis": 6,
    "rotation": 7, "opacity": 8, "use_comp_shutter": 9, "shutter": 10, "sampling": 12,
}
POINT_PARAMS = {"anchor", "position"}
BOOL_PARAMS = {"uniform", "use_comp_shutter"}
DEFAULTS = {"anchor": (0.5, 0.5), "position": (0.5, 0.5), "uniform": True, "scale_h": 100.0, "scale_w": 100.0,
            "skew": 0.0, "skew_axis": 0.0, "rotation": 0.0, "opacity": 100.0, "use_comp_shutter": True,
            "shutter": 0.0, "sampling": 0}
INTERP = {  # (温度補間コード, in_x, in_y, out_x, out_y)
    "linear": (0, 0.0, 0.166667, 0.0, 0.166667),
    "easeout": (4, 0.0, 0.333333, 0.0, 0.166667),   # このキーから出るとき緩やか
    "easein": (3, 0.0, 0.166667, 0.0, 0.333333),    # このキーへ入るとき緩やか
    "auto": (5, 0.0, 0.333333, 0.0, 0.333333),
    "hold": (6, 0.0, 0.166667, 0.0, 0.166667),
}
TYPE = {"scale": 0, "in": 1, "out": 2}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    return f"{v:.12f}".rstrip("0").rstrip(".") + ("." if float(v).is_integer() else "")


def kf_line(t_ticks: int, value, interp: str, point: bool) -> str:
    code, ix, iy, ox, oy = INTERP[interp]
    if point:
        val = f"{value[0]:.12f}:{value[1]:.12f}"
        return f"{t_ticks},{val},{code},0,{ix},{iy},{ox},{oy},5,4,0,0,0,0"
    return f"{t_ticks},{fmt(value)},{code},0,{ix},{iy},{ox},{oy}"


def start_line(value, point: bool) -> str:
    if point:
        return f"{START_T},{value[0]:.12f}:{value[1]:.12f},0,0,0,0,0,0,5,4,0,0,0,0"
    return f"{START_T},{fmt(value)},0,0,0,0,0,0"


class Doc:
    def __init__(self):
        self.parts: list[str] = []
        self.next_id = 1

    def new_id(self) -> int:
        i = self.next_id
        self.next_id += 1
        return i

    def add(self, s: str):
        self.parts.append(s)


def geometry_component(doc: Doc, name: str, tracks: dict, static: dict, duration: float, ptype: int) -> int:
    skel = open(GEOM_SKELETON, encoding="utf-8").read()
    blocks = re.findall(r"^\t<(VideoFilterComponent|PointComponentParam|VideoComponentParam) ObjectID=.*?^\t</\1>\n", skel, re.S | re.M)
    raw_blocks = [m.group(0) for m in re.finditer(r"^\t<([A-Za-z]+) ObjectID=.*?^\t</\1>\n?", skel, re.S | re.M)]
    comp = raw_blocks[0]
    params = raw_blocks[1:]
    assert len(params) == 12
    comp_id = doc.new_id()
    idmap = {re.search(r'ObjectID="(\d+)"', comp).group(1): str(comp_id)}
    for p in params:
        idmap[re.search(r'ObjectID="(\d+)"', p).group(1)] = str(doc.new_id())
    comp = re.sub(r'ObjectID="(\d+)"', lambda m: f'ObjectID="{idmap[m.group(1)]}"', comp)
    comp = re.sub(r'ObjectRef="(\d+)"', lambda m: f'ObjectRef="{idmap[m.group(1)]}"', comp)
    comp = comp.replace("<InstanceName>NAME</InstanceName>", f"<InstanceName>{esc(name)}</InstanceName>")
    doc.add(comp)
    dur_ticks = round(duration * TICKS)
    t0 = ANCHOR_IN if ptype != 2 else ANCHOR_IN + dur_ticks  # 末尾アンカーは終点基準
    id_to_name = {v: k for k, v in PARAM_ID.items()}
    for p in params:
        pid = int(re.search(r"<ParameterID>(\d+)</ParameterID>", p).group(1))
        pname = id_to_name[pid]
        point = pname in POINT_PARAMS
        p = re.sub(r'ObjectID="(\d+)"', lambda m: f'ObjectID="{idmap[m.group(1)]}"', p)
        value = static.get(pname, DEFAULTS[pname])
        if isinstance(DEFAULTS[pname], bool):
            value = bool(value)
        elif isinstance(DEFAULTS[pname], int):
            value = int(value)
        elif point:
            value = (float(value[0]), float(value[1]))
        else:
            value = float(value)
        keys = tracks.get(pname)
        if keys:
            lines = []
            for t, v, interp in keys:
                vv = (float(v[0]), float(v[1])) if point else float(v)
                if ptype == 2:
                    tt = t0 - dur_ticks + round(t * TICKS)
                    if abs(t - duration) < 1e-9:
                        tt = t0 - 1
                else:
                    tt = t0 + round(t * TICKS)
                lines.append(kf_line(tt, vv, interp, point))
            last = keys[-1][1]
            value = (float(last[0]), float(last[1])) if point else float(last)
            p = re.sub(r"<Keyframes></Keyframes>", "<Keyframes>" + ";".join(lines) + ";</Keyframes>", p)
            p = re.sub(r"<IsTimeVarying>false</IsTimeVarying>", "<IsTimeVarying>true</IsTimeVarying>", p)
        p = re.sub(r"<StartKeyframe>[^<]*</StartKeyframe>", "<StartKeyframe>" + start_line(value, point) + "</StartKeyframe>", p)
        doc.add(p)
    return comp_id


def preset_item(doc: Doc, spec: dict) -> int:
    ptype = TYPE[spec.get("anchor", "in")]
    duration = float(spec.get("duration", 0.5))
    tree_id, fpi_id, fp_id = doc.new_id(), doc.new_id(), doc.new_id()
    comp_id = geometry_component(doc, spec["name"], spec.get("tracks", {}), spec.get("static", {}), duration, ptype)
    dur_ticks = round(duration * TICKS)
    doc.add(f'''	<TreeItem ObjectID="{tree_id}" ClassID="{CLS['TreeItem']}" Version="3">
		<TreeItemBase Version="4">
			<Data ObjectRef="{fpi_id}"/>
			<Name>{esc(spec['name'])}</Name>
			<Node Version="1">
				<Properties Version="1">
					<MZ.EffectPresets.PresetUID>{uuid.uuid4()}</MZ.EffectPresets.PresetUID>
				</Properties>
			</Node>
			<Locked>false</Locked>
		</TreeItemBase>
	</TreeItem>
''')
    doc.add(f'''	<FilterPresetItem ObjectID="{fpi_id}" ClassID="{CLS['FilterPresetItem']}" Version="1">
		<EffectItem Version="1">
			<EffectFlavor>5</EffectFlavor>
			<EffectIsShorcut>false</EffectIsShorcut>
		</EffectItem>
		<FilterPreset ObjectRef="{fp_id}"/>
	</FilterPresetItem>
''')
    doc.add(f'''	<FilterPreset ObjectID="{fp_id}" ClassID="{CLS['FilterPreset']}" Version="2">
		<Node Version="1">
		</Node>
		<Type>{ptype}</Type>
		<Speed>1.000000000000000000000000</Speed>
		<Component ObjectRef="{comp_id}"/>
		<MediaType>{VIDEO_MEDIA}</MediaType>
		<FilterMatchName>AE.ADBE Geometry2</FilterMatchName>
		<AnchorOutPoint>{ANCHOR_IN + dur_ticks}</AnchorOutPoint>
		<Description>{esc(spec.get('description', ''))}</Description>
		<AnchorInPoint>{ANCHOR_IN}</AnchorInPoint>
	</FilterPreset>
''')
    return tree_id


def bin_item(doc: Doc, name: str, child_ids: list[int], presets_bin: bool = False, expanded: bool = True) -> int:
    bid, did = doc.new_id(), doc.new_id()
    items = "\n".join(f'\t\t\t<Item Index="{i}" ObjectRef="{c}"/>' for i, c in enumerate(child_ids))
    props = ""
    if presets_bin:
        props = '''
				<Properties Version="1">
					<HandlerEffects.EffectItemTree.PresetsBin>1</HandlerEffects.EffectItemTree.PresetsBin>
				</Properties>'''
    doc.add(f'''	<BinTreeItem ObjectID="{bid}" ClassID="{CLS['BinTreeItem']}" Version="4">
		<Items Version="1">
{items}
		</Items>
		<Sorted>true</Sorted>
		<Expanded>{'true' if expanded else 'false'}</Expanded>
		<TreeItemBase Version="4">
			<Data ObjectRef="{did}"/>
			<Name>{esc(name)}</Name>
			<Node Version="1">{props}
			</Node>
			<Locked>false</Locked>
		</TreeItemBase>
	</BinTreeItem>
''')
    doc.add(f'''	<EffectBinItem ObjectID="{did}" ClassID="{CLS['EffectBinItem']}" Version="1">
		<Flavor>1</Flavor>
	</EffectBinItem>
''')
    return bid


def build(spec: dict, out_path: str) -> dict:
    doc = Doc()
    tree_id, root_bin_id = doc.new_id(), doc.new_id()
    cat_ids = []
    n = 0
    for cat in spec["categories"]:
        pids = [preset_item(doc, p) for p in cat["presets"]]
        n += len(pids)
        cat_ids.append(bin_item(doc, cat["name"], pids, expanded=False))
    top_id = bin_item(doc, spec["bin"], cat_ids)
    presets_bin = bin_item(doc, "プリセット", [top_id], presets_bin=True)
    # Root bin (ObjectID 2) と Tree (ObjectID 1)
    root = f'''	<BinTreeItem ObjectID="{root_bin_id}" ClassID="{CLS['BinTreeItem']}" Version="4">
		<Items Version="1">
			<Item Index="0" ObjectRef="{presets_bin}"/>
		</Items>
		<Sorted>false</Sorted>
		<Expanded>false</Expanded>
		<TreeItemBase Version="4">
			<Name>Root</Name>
			<Node Version="1">
			</Node>
			<Locked>false</Locked>
		</TreeItemBase>
	</BinTreeItem>
'''
    tree = f'''	<Tree ObjectRef="{tree_id}"/>
	<Tree ObjectID="{tree_id}" ClassID="{CLS['Tree']}" Version="1">
		<Node Version="1">
		</Node>
		<RootBin ObjectRef="{root_bin_id}"/>
	</Tree>
'''
    xml = '﻿<?xml version="1.0" encoding="UTF-8"?>\n<PremiereData Version="3">\n' + tree + root + "".join(doc.parts) + "</PremiereData>\n"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(xml)
    return {"presets": n, "categories": len(spec["categories"]), "bytes": len(xml.encode("utf-8"))}


def verify(path: str) -> None:
    import xml.etree.ElementTree as ET
    ET.parse(path)
    xml = open(path, encoding="utf-8-sig").read()
    ids = re.findall(r'ObjectID="(\d+)"', xml)
    assert len(ids) == len(set(ids)), "ObjectID 重複"
    refs = set(re.findall(r'ObjectRef="(\d+)"', xml))
    assert refs <= set(ids), f"未解決 ObjectRef {sorted(refs - set(ids))[:5]}"
    print(f"verify OK: {path}")


USAGE = "使い方: python3 -m presets.prfpset_build <spec.json> <out.prfpset>（server/ のフォルダで実行する）"


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 2)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    print(build(spec, sys.argv[2]))
    verify(sys.argv[2])
