#!/usr/bin/env python3
"""知識の棚を引く道具。

  kb.py search <言葉...> [--limit 5] [--os mac|windows] [--kind K] [--include-superseded] [--json]
  kb.py show <id>
  kb.py list [--kind K] [--os X] [--status S] [--brief] [--json]
  kb.py build                 index.json を作り直す
  kb.py check                 先頭項目・id の重複・関係の切れ・索引の古さを調べる（問題があれば終了コード 1）
  kb.py note --title T --tags a,b [--kind usecase] [--os mac,windows] (--body TEXT | --body-file F)

検索は機械的な一致（題・タグ・要約・本文）。結果が薄いときは list --brief を読み、意味で選ぶこと。
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import cli, frontmatter, fsutil, osinfo  # noqa: E402

SKILL_DIR = HERE.parent
KNOWLEDGE = SKILL_DIR / "knowledge"
PARTS = SKILL_DIR / "parts"
FOLDER_KIND = {"core": "core", "recipes": "recipe", "features": "feature", "usecases": "usecase",
               "platform": "platform", "reference": "reference"}
STATUSES = ("verified", "partial", "unverified", "superseded")
OSES = ("mac", "windows")
REQUIRED = ("id", "title", "kind", "tags", "os", "premiere", "status", "summary")
STATUS_WEIGHT = {"verified": 1.0, "partial": 0.9, "unverified": 0.8, "superseded": 0.5}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SPLIT_RE = re.compile(r"[\s、。・,，/／「」『』（）()]+")


def norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def _as_list(v) -> List[str]:
    if isinstance(v, list):
        return v
    return [v] if v else []


def read_entry(path: Path, base: Path, source: str) -> Tuple[Dict, str]:
    data, body = frontmatter.parse(path.read_text(encoding="utf-8"))
    entry = {k: data.get(k, "") for k in REQUIRED}
    entry["tags"] = _as_list(entry["tags"])
    entry["os"] = _as_list(entry["os"])
    entry["parts"] = _as_list(data.get("parts", []))
    entry["related"] = _as_list(data.get("related", []))
    entry["path"] = path.relative_to(base).as_posix() if source == "kit" else str(path)
    entry["source"] = source
    return entry, body


def load(knowledge_dir: Path = KNOWLEDGE, notes_dir: Optional[Path] = None) -> List[Tuple[Dict, str]]:
    items: List[Tuple[Dict, str]] = []
    for folder in FOLDER_KIND:
        d = Path(knowledge_dir) / folder
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                items.append(read_entry(p, Path(knowledge_dir), "kit"))
    if notes_dir and Path(notes_dir).is_dir():
        for p in sorted(Path(notes_dir).glob("*.md")):
            try:
                items.append(read_entry(p, Path(notes_dir), "note"))
            except frontmatter.FrontmatterError:
                continue
    return items


def build_index(knowledge_dir: Path = KNOWLEDGE) -> List[Dict]:
    return sorted((e for e, _ in load(knowledge_dir)), key=lambda e: (e["kind"], e["id"]))


def index_text(entries: List[Dict]) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=1) + "\n"


def load_synonyms(knowledge_dir: Path = KNOWLEDGE) -> List[List[str]]:
    p = Path(knowledge_dir) / "synonyms.json"
    if not p.exists():
        return []
    groups = json.loads(p.read_text(encoding="utf-8")).get("groups", [])
    return [[norm(w) for w in g] for g in groups]


def query_terms(query: str, synonyms: List[List[str]]) -> List[List[str]]:
    """言葉ごとに、同じ意味の言葉をまとめた組を返す（「無音カット」のような複合語は両方の組に広げる）。"""
    groups = []
    for raw in SPLIT_RE.split(norm(query)):
        if not raw:
            continue
        alts = {raw}
        for g in synonyms:
            if any(raw == w or (len(w) >= 2 and w in raw) for w in g):
                alts.update(g)
        groups.append(sorted(alts))
    return groups


def _has_cjk(s: str) -> bool:
    return any("\u3040" <= ch <= "\u9fff" for ch in s)


def _score(entry: Dict, body_n: str, alts: List[str]) -> float:
    title = norm(entry["title"])
    summary = norm(entry["summary"])
    tags = [norm(t) for t in entry["tags"]]
    best = 0.0
    for t in alts:
        s = 0.0
        if t in title:
            s += 6
        if any(t == tag for tag in tags):
            s += 6
        elif any(len(tag) >= 2 and (t in tag or tag in t) for tag in tags):
            s += 3
        if t in summary:
            s += 3
        if t in entry["id"]:
            s += 2
        s += min(body_n.count(t), 5) * 0.5
        if s == 0 and _has_cjk(t) and len(t) >= 3:
            grams = {t[i:i + 2] for i in range(len(t) - 1)}
            s += sum(0.5 for g in grams if g in title or g in summary)
        best = max(best, s)
    return best


def search(items, query: str, synonyms, os_name: Optional[str] = None, kind: Optional[str] = None,
           include_superseded: bool = False, limit: int = 5) -> List[Tuple[float, Dict]]:
    groups = query_terms(query, synonyms)
    results = []
    for entry, body in items:
        if entry["status"] == "superseded" and not include_superseded:
            continue
        if os_name and entry["os"] and os_name not in entry["os"]:
            continue
        if kind and entry["kind"] != kind:
            continue
        body_n = norm(body)
        total = sum(_score(entry, body_n, alts) for alts in groups)
        if total <= 0:
            continue
        results.append((round(total * STATUS_WEIGHT.get(entry["status"], 0.8), 2), entry))
    results.sort(key=lambda r: (-r[0], r[1]["id"]))
    return results[:limit]


def check_all(knowledge_dir: Path = KNOWLEDGE, parts_dir: Path = PARTS) -> List[str]:
    knowledge_dir, parts_dir = Path(knowledge_dir), Path(parts_dir)
    problems: List[str] = []
    seen: Dict[str, str] = {}
    items = []
    for folder, kind in FOLDER_KIND.items():
        d = knowledge_dir / folder
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            rel = p.relative_to(knowledge_dir).as_posix()
            try:
                entry, body = read_entry(p, knowledge_dir, "kit")
            except frontmatter.FrontmatterError as e:
                problems.append(f"{rel}: {e}")
                continue
            items.append(entry)
            for k in REQUIRED:
                if not entry[k]:
                    problems.append(f"{rel}: 先頭項目「{k}」がありません")
            if entry["id"] and not ID_RE.match(entry["id"]):
                problems.append(f"{rel}: id は英小文字・数字・ハイフンだけにします")
            if entry["id"] and p.stem != entry["id"]:
                problems.append(f"{rel}: ファイル名と id が違います（{entry['id']}）")
            if entry["kind"] and entry["kind"] != kind:
                problems.append(f"{rel}: kind が置き場所と違います（{folder}/ は {kind}）")
            if entry["status"] and entry["status"] not in STATUSES:
                problems.append(f"{rel}: status は {' / '.join(STATUSES)} のどれかです（{entry['status']}）")
            for o in entry["os"]:
                if o not in OSES:
                    problems.append(f"{rel}: os は mac / windows だけです（{o}）")
            if entry["id"] in seen:
                problems.append(f"{rel}: id が {seen[entry['id']]} と重複しています")
            seen.setdefault(entry["id"], rel)
            if len(body.strip()) < 40:
                problems.append(f"{rel}: 本文が短すぎます（40 文字未満）")
    for entry in items:
        for r in entry["related"]:
            if r not in seen:
                problems.append(f"{entry['path']}: related の {r} がありません")
        for part in entry["parts"]:
            if not (parts_dir / part / "part.json").exists():
                problems.append(f"{entry['path']}: parts の {part} がありません")
    index_path = knowledge_dir / "index.json"
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index_text(build_index(knowledge_dir)):
        problems.append("index.json が古いです。kb.py build を実行してください")
    return problems


def write_note(notes_dir: Path, title: str, tags: List[str], kind: str, oses: List[str], body: str,
               now: Optional[datetime.datetime] = None) -> Path:
    now = now or datetime.datetime.now()
    nid = "note-" + now.strftime("%Y%m%d-%H%M%S")
    first = body.strip().splitlines()[0][:80] if body.strip() else title
    data = {"id": nid, "title": title, "kind": kind, "tags": tags, "os": oses, "premiere": ">=25.6",
            "status": "unverified", "summary": first}
    path = Path(notes_dir) / f"{nid}.md"
    if path.exists():
        raise FileExistsError(f"同じ名前のノートがあります: {path}")
    fsutil.write_text(path, frontmatter.dump(data) + "\n" + body.strip() + "\n")
    return path


def _print_results(results) -> None:
    if not results:
        print("見つかりませんでした。言葉を変えるか、kb.py list --brief を読んで意味で選んでください。")
        return
    for n, (score, e) in enumerate(results, 1):
        print(f"{n}. [{e['kind']}/{e['status']}] {e['id']} — {e['title']}（{score}）")
        print(f"    {('knowledge/' + e['path']) if e['source'] == 'kit' else e['path']}")
        print(f"    要約: {e['summary']}")


def main(argv=None) -> int:
    cli.setup_stdio()
    ap = argparse.ArgumentParser(description="知識の棚を引く")
    ap.add_argument("--knowledge", default=str(KNOWLEDGE))
    ap.add_argument("--notes", default=None)
    ap.add_argument("--parts", default=str(PARTS))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("words", nargs="+")
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--os", choices=OSES)
    s.add_argument("--kind", choices=sorted(FOLDER_KIND.values()))
    s.add_argument("--include-superseded", action="store_true")
    s.add_argument("--json", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("id")
    ls = sub.add_parser("list")
    ls.add_argument("--kind", choices=sorted(FOLDER_KIND.values()))
    ls.add_argument("--os", choices=OSES)
    ls.add_argument("--status", choices=STATUSES)
    ls.add_argument("--brief", action="store_true")
    ls.add_argument("--json", action="store_true")
    sub.add_parser("build")
    sub.add_parser("check")
    nt = sub.add_parser("note")
    nt.add_argument("--title", required=True)
    nt.add_argument("--tags", required=True)
    nt.add_argument("--kind", default="usecase", choices=sorted(FOLDER_KIND.values()))
    nt.add_argument("--os", default="mac,windows")
    group = nt.add_mutually_exclusive_group(required=True)
    group.add_argument("--body")
    group.add_argument("--body-file")
    args = ap.parse_args(argv)

    knowledge = Path(args.knowledge)
    notes = Path(args.notes) if args.notes else osinfo.notes_dir(os.environ, osinfo.detect_os())

    if args.cmd == "build":
        fsutil.write_text(knowledge / "index.json", index_text(build_index(knowledge)))
        print(f"index.json を作りました（{len(build_index(knowledge))} 件）")
        return 0
    if args.cmd == "check":
        problems = check_all(knowledge, Path(args.parts))
        for p in problems:
            print("・" + p)
        print("問題はありません。" if not problems else f"{len(problems)} 件の問題があります。")
        return 1 if problems else 0
    if args.cmd == "note":
        body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
        path = write_note(notes, args.title, [t.strip() for t in args.tags.split(",") if t.strip()], args.kind,
                          [o.strip() for o in args.os.split(",") if o.strip()], body)
        print(f"手元のノートに残しました: {path}")
        return 0

    items = load(knowledge, notes)
    if args.cmd == "search":
        results = search(items, " ".join(args.words), load_synonyms(knowledge), os_name=args.os, kind=args.kind,
                         include_superseded=args.include_superseded, limit=args.limit)
        if args.json:
            cli.print_json([{"score": score, **e} for score, e in results])
        else:
            _print_results(results)
        return 0
    if args.cmd == "show":
        for e, body in items:
            if e["id"] == args.id:
                path = knowledge / e["path"] if e["source"] == "kit" else Path(e["path"])
                print(f"# {path}")
                print(path.read_text(encoding="utf-8"))
                return 0
        print(f"id が {args.id} の知識はありません。kb.py search で探してください。")
        return 1
    if args.cmd == "list":
        rows = [e for e, _ in items
                if (not args.kind or e["kind"] == args.kind)
                and (not args.os or not e["os"] or args.os in e["os"])
                and (not args.status or e["status"] == args.status)]
        if args.json:
            cli.print_json(rows)
        else:
            for e in rows:
                if args.brief:
                    print(f"{e['id']} | {e['kind']} | {e['status']} | {e['title']} — {e['summary']}")
                else:
                    print(f"{e['id']}\t{e['kind']}\t{e['status']}\t{e['title']}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
