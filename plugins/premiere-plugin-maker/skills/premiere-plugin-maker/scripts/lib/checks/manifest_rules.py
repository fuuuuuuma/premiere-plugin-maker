"""manifest.json の検査（M001〜M009、M013）。M010〜M012 は使い方を見るので js_rules.py にある。"""
from __future__ import annotations

import re
from typing import List

from .. import manifest as manifest_lib
from . import Finding, Project, rule

REQUIRED_KEYS = ("manifestVersion", "id", "name", "version", "host", "entrypoints")


def _f(rule_name, severity, message, why, fix, line=0):
    return Finding(rule_name, severity, "manifest.json", line, message, why, fix)


@rule
def manifest_rules(p: Project) -> List[Finding]:
    if p.manifest_error:
        return [_f("M001", "error", "manifest.json が読めません", p.manifest_error,
                   "書かれている行を直してください。JSON にはコメント（// や /* */）と末尾のカンマは書けません")]
    if p.manifest is None:
        return []
    m = p.manifest
    out: List[Finding] = []
    for key in REQUIRED_KEYS:
        if key not in m:
            out.append(_f("M002", "error", f"manifest.json に「{key}」がありません",
                          "Premiere がプラグインとして読み込めません", f"雛形の manifest.json と同じ形で「{key}」を書いてください"))
    mv = m.get("manifestVersion")
    if mv is not None and mv != 5:
        if mv == 6:
            out.append(_f("M003", "warn", "manifestVersion が 6 です", "6 は C++ を使う Hybrid プラグイン用です",
                          "普通のパネルなら 5 にしてください"))
        else:
            out.append(_f("M003", "error", f"manifestVersion が {mv} です", "Premiere の UXP は 5 を読みます", "5 にしてください"))
    version = m.get("version")
    if version is not None and not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        out.append(_f("M004", "error", f"version が「{version}」です", "版数は 1.2.3 のように数字 3 つで書く決まりです",
                      "例: 0.1.0"))
    host = m.get("host")
    if host is not None:
        if isinstance(host, list):
            out.append(_f("M005", "error", "host が配列になっています", "配列は開発の確かめ専用で、配布や Marketplace の検証で落ちます",
                          '{"app": "premierepro", "minVersion": "25.6"} の形にしてください'))
        elif isinstance(host, dict):
            if host.get("app") != "premierepro":
                out.append(_f("M005", "error", f"host.app が「{host.get('app')}」です", "Premiere は小文字の premierepro です",
                              '"app": "premierepro" にしてください'))
            mvv = host.get("minVersion")
            try:
                if manifest_lib.version_tuple(str(mvv)) < (25, 6, 0):
                    out.append(_f("M006", "warn", f"minVersion が {mvv} です", "UXP の正式版は Premiere 25.6 からです（それより前はベータ版だけ）",
                                  "特に理由が無ければ 25.6 以上にしてください"))
            except ValueError:
                out.append(_f("M005", "error", f"minVersion「{mvv}」が版数の形ではありません", "読み込める版を決められません",
                              "例: 25.6 や 26.2"))
    eps = m.get("entrypoints")
    if isinstance(eps, list):
        seen = set()
        for e in eps:
            eid = e.get("id")
            if e.get("type") not in ("panel", "command"):
                out.append(_f("M007", "error", f"入口「{eid}」の type が「{e.get('type')}」です", "panel か command だけが使えます", "どちらかにしてください"))
            if eid in seen:
                out.append(_f("M007", "error", f"入口の id「{eid}」が重複しています", "どちらかが無視されます", "id を別の名前にしてください"))
            seen.add(eid)
            label = e.get("label")
            if not (isinstance(label, dict) and label.get("default")) and not isinstance(label, str):
                out.append(_f("M007", "error", f"入口「{eid}」に label がありません", "メニューに名前が出ません",
                              '"label": {"default": "表示名"} を書いてください'))
    for icon in m.get("icons") or []:
        path = icon.get("path")
        if path and not (p.root / path).exists():
            out.append(_f("M008", "error", f"アイコン「{path}」がありません", "読み込みで失敗したり、配布の検査で落ちたりします",
                          "そのパスに PNG を置くか、icons の行を直してください"))
    name = m.get("name")
    if isinstance(name, str) and any(ord(c) > 127 for c in name):
        out.append(_f("M009", "warn", "name に英数字以外が入っています", "Marketplace の条件は英数字だけで、文字化けの原因にもなります",
                      "name は英数字にし、日本語はパネルの label に書いてください"))
    main = m.get("main") or "main.js"
    if not (p.root / main).exists():
        out.append(_f("M013", "error", f"入口のファイル「{main}」がありません", "パネルが空のまま開きます",
                      "manifest の main を index.html などの実在するファイルにしてください"))
    return out
