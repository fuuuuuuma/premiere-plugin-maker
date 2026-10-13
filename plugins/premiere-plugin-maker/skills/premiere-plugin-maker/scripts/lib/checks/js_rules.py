"""パネルの JS の検査（J001〜J015、M010〜M012）。実機で踏んだ失敗の型を、読み込む前に止める。"""
from __future__ import annotations

import json
import re
from typing import List

from .. import jsscan
from .. import manifest as manifest_lib
from . import Finding, Project, rule


def _api_since(p: Project) -> dict:
    path = p.kit_dir / "knowledge" / "reference" / "api-since.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("apis", {})
    except (OSError, ValueError):
        return {}


def _finding(p, path, text, pos, rule_name, severity, message, why, fix):
    return Finding(rule_name, severity, p.rel(path), jsscan.line_of(text, pos), message, why, fix)


@rule
def js_rules(p: Project) -> List[Finding]:
    out: List[Finding] = []
    perms = p.permissions()
    flags = p.feature_flags()
    apis = _api_since(p)
    try:
        minv = manifest_lib.version_tuple(p.min_version() or "0")
    except ValueError:
        minv = (0, 0, 0)
    for path in p.panel_files(".js"):
        text = p.text(path)
        clean = jsscan.blank(text)
        spans = jsscan.callback_spans(clean)
        builders = jsscan.builder_spans(text, clean)

        for a, b, name in spans:
            for m in re.finditer(r"\bawait\b", clean[a:b]):
                out.append(_finding(p, path, text, a + m.start(), "J001", "error",
                                    f"取引（{name}）の中で await しています",
                                    "取引のコールバックは完全に同期でなければならず、await を挟むと Action が無効になり「The script object is no longer valid」で失敗します",
                                    "非同期の取得（getComponentChain・createComponent など）を取引の前に済ませ、中では Action を作って足すだけにしてください"))
        for m in re.finditer(r"\.\s*(create[A-Z]\w*Action)\s*\(", clean):
            if jsscan.inside(m.start(), spans) or jsscan.inside(m.start(), builders):
                continue
            out.append(_finding(p, path, text, m.start(), "J002", "warn", f"{m.group(1)} を取引の外で作っています",
                                "Premiere 26.3 から、Action は lockedAccess の中で作るのが必須です",
                                "PPM.transact の中で作るか、Action を作る関数の前に「// ppm: action-builder」と書いて取引の中から呼んでください"))
        for m in re.finditer(r"(\w+)\s*\.\s*getTrackItems\s*\(\s*\)", clean):
            if re.search("sel", m.group(1), re.I):
                continue
            out.append(_finding(p, path, text, m.start(), "J003", "error", "getTrackItems() を引数なしで呼んでいます",
                                "トラックの getTrackItems は (種類, 空も含めるか) の 2 つが必須で、無いと空の配列か例外になります",
                                "track.getTrackItems(ppro.Constants.TrackItemType.CLIP, false) のように呼んでください"))
        for m in re.finditer(r"new\s+(?:ppro\s*\.\s*)?TrackItemSelection\s*\(", clean):
            out.append(_finding(p, path, text, m.start(), "J004", "error", "new TrackItemSelection() を使っています",
                                "Premiere 26.3 では、後の setSelection が「Connection to object lost」で失敗します",
                                "await sequence.getSelection() で取った選択に addItem / removeItem してください"))
        for m in re.finditer(r"\b\w*[Ss]ettings\w*\s*\.\s*(videoFrameRate|frameRate|videoFrameRect|frameRect)\b(?!\s*\()", clean):
            rect = "Rect" in m.group(1)
            out.append(_finding(p, path, text, m.start(), "J005", "warn" if rect else "error",
                                f"シーケンス設定の {m.group(1)} をプロパティとして読んでいます",
                                "そのプロパティは存在せず、黙って undefined になります（30fps 決め打ちで壊した事故あり）",
                                "await settings.getVideoFrameRate() の .value を使い、読めなかったら既定値を詰めずに止めてください"))
        for m in re.finditer(r"require\s*\(\s*[\"']\.{1,2}/", text):
            out.append(_finding(p, path, text, m.start(), "J006", "error", "require を相対パスで使っています",
                                "UXP では require の相対パスが解決されず、分けたファイルが読み込めません",
                                "index.html の <script src> で順に読み込み、関数は PPM などのグローバルに載せてください"))
        if re.search(r"\bMutationObserver\b", clean) and not re.search(r"typeof\s+MutationObserver", clean):
            out.append(_finding(p, path, text, clean.find("MutationObserver"), "J007", "warn", "MutationObserver を確かめずに使っています",
                                "UXP には MutationObserver が無いことがあり、その場で止まります",
                                "typeof MutationObserver === \"function\" で分け、無ければ setInterval で見張ってください"))
        for m in re.finditer(r"(?<![\w.$])(alert|confirm|prompt)\s*\(", clean):
            enabled = bool(flags.get("enableAlerts"))
            out.append(_finding(p, path, text, m.start(), "J008", "warn" if enabled else "error", f"{m.group(1)}() を使っています",
                                "Premiere の UXP では featureFlags.enableAlerts が無いと使えず、あっても出ないことがあります",
                                "パネルの中に確認の表示を作る（2 回押しで確定など）か、PPM.ui の表示を使ってください"))
        for m in re.finditer(r"(^|[;{}\n])\s*(?:[\w$]+\s*\.\s*)*executeTransaction\s*\(", clean):
            out.append(_finding(p, path, text, m.end(), "J009", "warn", "executeTransaction の戻り値を見ていません",
                                "受け付けられなかったときは false が返り、見ないと「何も起きない」まま成功のように見えます",
                                "ok = project.executeTransaction(...) とし、false なら原因つきのエラーを出してください（PPM.transact はこれをします）"))
        for m in re.finditer(r"\.\s*ticks\b(?!Number)", clean):
            out.append(_finding(p, path, text, m.start(), "J010", "warn", "TickTime の .ticks を直接読んでいます",
                                "版によって .ticks が 0 や文字列になる記録があります",
                                "PPM.ticksOf(time) を使ってください（ticksNumber → ticks → seconds の順に読みます）"))
        if not perms.get("allowCodeGenerationFromStrings"):
            for m in re.finditer(r"(?<![\w.$])eval\s*\(|\bnew\s+Function\s*\(", clean):
                out.append(_finding(p, path, text, m.start(), "J011", "error", "eval / new Function を使っています",
                                    "manifest の allowCodeGenerationFromStrings が無いと使えません",
                                    "文字列からコードを作らない書き方にしてください（どうしても要るなら権限を足す）"))
        boot = re.search(r"document\s*\.\s*readyState", clean)
        if boot and jsscan.line_of(text, boot.start()) < 0.8 * max(1, text.count("\n") + 1):
            out.append(_finding(p, path, text, boot.start(), "J012", "warn", "起動の処理がファイルの末尾にありません",
                                "UXP は読み込みの途中で起動してしまうことがあり、後ろで宣言した const を踏んで止まります",
                                "起動の判定（document.readyState）と boot() の呼び出しをファイルの最後に置いてください"))
        if re.search(r"127\.0\.0\.1|localhost", text) and re.search(r"\bfetch\s*\(|XMLHttpRequest|WebSocket", clean):
            if (perms.get("network") or {}).get("domains") != "all":
                pos = text.find("127.0.0.1") if "127.0.0.1" in text else text.find("localhost")
                out.append(_finding(p, path, text, pos, "J013", "error", "手元のサーバーへ接続するのに network.domains が \"all\" ではありません",
                                    "個別の許可（http://127.0.0.1:3850 など）では、通信そのものが起きなかった記録があります（Premiere 26.3・Mac）",
                                    "manifest の requiredPermissions.network を {\"domains\": \"all\"} にし、サーバー側を 127.0.0.1 と合言葉で守ってください"))
        for name, info in apis.items():
            for m in re.finditer(r"\b" + re.escape(name) + r"\b", clean):
                try:
                    since = manifest_lib.version_tuple(info["since"])
                except (KeyError, ValueError):
                    continue
                if since <= minv:
                    continue
                beta = bool(info.get("beta"))
                out.append(_finding(p, path, text, m.start(), "J014", "warn" if beta else "error",
                                    f"{name} は Premiere {info['since']}{'（ベータ）' if beta else ''} からの API です",
                                    f"manifest の minVersion（{p.min_version()}）では読み込めても、この API が無くて止まります（{info.get('what', '')}）",
                                    f"minVersion を {info['since']} 以上にするか、typeof で確かめて無ければ別の手にしてください"
                                    if not beta else "ベータ版にしか無い API です。正式版で使えるまで、代わりの手を用意してください"))
                break
        for m in re.finditer(r"getMediaType\s*\(\s*\)\s*\)?\s*[!=]==?\s*\d", clean):
            out.append(_finding(p, path, text, m.start(), "J015", "warn", "getMediaType() を数値と比べています",
                                "getMediaType は Guid を返すので、数値との比較は常に偽になります",
                                "item.constructor.name が VideoClipTrackItem / AudioClipTrackItem かで分けてください（PPM.getSelectedClips の kind）"))
    out.extend(_permission_use(p))
    return out


def _permission_use(p: Project) -> List[Finding]:
    if p.manifest is None:
        return []
    perms = p.permissions()
    js_raw = "\n".join(p.text(x) for x in p.panel_files(".js"))
    js_clean = "\n".join(jsscan.blank(p.text(x)) for x in p.panel_files(".js"))
    html_text = "\n".join(p.text(x) for x in p.panel_files(".html"))
    out: List[Finding] = []
    # require("fs") の "fs" は文字列なので、元の文で探す（blank では消える）
    if perms.get("localFileSystem") == "fullAccess" and not re.search(r"require\s*\(\s*[\"']fs[\"']\s*\)|getEntryWithUrl|file:/", js_raw):
        out.append(Finding("M010", "warn", "manifest.json", 0, "localFileSystem が fullAccess ですが、絶対パスのファイル操作が見当たりません",
                           "権限が強いほど、受け取った人が入れるのをためらいます", "要らなければ \"plugin\" に下げてください"))
    # 通信の有無はコメントを除いた文で見る（コメントの中の fetch を数えない）
    uses_net = bool(re.search(r"\bfetch\s*\(|XMLHttpRequest|new\s+WebSocket", js_clean))
    if uses_net and not perms.get("network"):
        out.append(Finding("M011", "error", "manifest.json", 0, "通信しているのに network の権限がありません",
                           "許可していない相手への通信は失敗します", "requiredPermissions.network.domains に相手を書いてください（手元のサーバーなら \"all\"）"))
    if perms.get("network") and not uses_net:
        out.append(Finding("M011", "warn", "manifest.json", 0, "network の権限がありますが、通信が見当たりません",
                           "使わない権限は外す決まりです", "requiredPermissions.network を消してください"))
    if perms.get("allowCodeGenerationFromStrings") and not (re.search(r"(?<![\w.$])eval\s*\(|new\s+Function\s*\(", js_clean)
                                                           or re.search(r"\son[a-z]+\s*=", html_text)):
        out.append(Finding("M012", "warn", "manifest.json", 0, "allowCodeGenerationFromStrings が true ですが、使っていません",
                           "使わない権限は外す決まりです", "false にするか、行ごと消してください"))
    return out
