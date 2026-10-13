#!/usr/bin/env python3
"""手元のサーバーを入れる・外す・確かめる（Mac は launchd、Windows はタスク スケジューラ）。

  Mac:     python3 server/install.py [--dry-run] [--force] [--with-deps] | --uninstall | --status
  Windows: py -3 server\\install.py   （同じ）
- 版ごとの置き場所（runtime/<版>/）に写してから常駐させる。同じ版が既にあれば写さない（--force で置き換え）
- --with-deps のときだけ requirements.txt の依存を専用の環境（venv）に入れる。入れる前に利用者の許可を取ること
- 最後に server.json と /ping で、新しい版が動いていることを確かめる
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import venv
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ppm_paths  # noqa: E402

CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
APP = CONFIG["app"]
VERSION = CONFIG.get("version", "0.0.0")
LABEL = f"com.ppm.{APP.lower()}.server"
TASK = f"{APP} Server"


def _out(text: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print(text)


def runtime_dir() -> Path:
    return ppm_paths.app_support(APP) / "runtime" / VERSION


def venv_dir() -> Path:
    return ppm_paths.app_support(APP) / "venv" / VERSION


def requirements() -> list:
    req = HERE / "requirements.txt"
    if not req.exists():
        return []
    return [line.strip() for line in req.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def missing_deps() -> list:
    out = []
    for dep in requirements():
        name = dep.split(";")[0].split("[")[0]
        for sep in ("==", ">=", "<=", "~=", ">", "<"):
            name = name.split(sep)[0]
        module = name.strip().replace("-", "_")
        if importlib.util.find_spec(module) is None:
            out.append(dep)
    return out


def service_python(with_deps: bool) -> str:
    if with_deps:
        return str(venv_dir() / ("Scripts/pythonw.exe" if sys.platform == "win32" else "bin/python3"))
    if sys.platform == "win32":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        return str(pyw if pyw.exists() else sys.executable)
    return sys.executable


def plist_text(python: str, server: Path) -> str:
    tpl = (HERE / "launchd.plist.template").read_text(encoding="utf-8")
    values = {"__LABEL__": LABEL, "__PYTHON__": python, "__SERVER__": str(server), "__LOG_DIR__": str(ppm_paths.log_dir(APP))}
    for key, value in values.items():
        tpl = tpl.replace(key, escape(value))
    return tpl


def _ps(text: str) -> str:
    return text.replace("'", "''")


def _powershell(script: str) -> subprocess.CompletedProcess:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _startup_file() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / f"{APP}-server.pyw"


def register_service(python: str, server: Path, apply: bool, plan: list) -> None:
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        uid = os.getuid()
        plan.append(f"常駐の設定を書いて起動する: {plist}")
        if not apply:
            return
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(plist_text(python, server), encoding="utf-8")
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True)
        r = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{LABEL}"], capture_output=True)
    elif sys.platform == "win32":
        plan.append(f"タスク スケジューラに「{TASK}」を登録して起動する（サインインのたびに起動）")
        if not apply:
            return
        script = (f"$a = New-ScheduledTaskAction -Execute '{_ps(python)}' -Argument '\"{_ps(str(server))}\"';"
                  "$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME;"
                  "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0;"
                  f"Register-ScheduledTask -TaskName '{_ps(TASK)}' -Action $a -Trigger $t -Settings $s -Force | Out-Null;"
                  f"Start-ScheduledTask -TaskName '{_ps(TASK)}'")
        if _powershell(script).returncode != 0:
            # 登録できない環境（会社の PC の制限など）では、スタートアップに起動用のファイルを置き、今すぐ起動する
            startup = _startup_file()
            startup.parent.mkdir(parents=True, exist_ok=True)
            startup.write_text(f"import runpy\nrunpy.run_path({str(server)!r}, run_name='__main__')\n", encoding="utf-8")
            subprocess.Popen([python, str(server)], creationflags=0x00000008 | 0x00000200, close_fds=True)
            plan.append(f"タスクの登録ができなかったので、スタートアップに置きました: {startup}")
    else:
        plan.append("この OS には常駐の仕組みを用意していません。python3 server/ppm_server.py で起動してください")


def unregister_service() -> None:
    if sys.platform == "darwin":
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"], capture_output=True)
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        if plist.exists():
            plist.unlink()
    elif sys.platform == "win32":
        _powershell(f"Unregister-ScheduledTask -TaskName '{_ps(TASK)}' -Confirm:$false")
        if _startup_file().exists():
            _startup_file().unlink()


def ping(timeout: float = 3.0) -> dict:
    info = json.loads((ppm_paths.app_support(APP) / "server.json").read_text(encoding="utf-8"))
    req = urllib.request.Request(f"http://127.0.0.1:{info['httpPort']}/ping", headers={"X-PPM-Token": info["token"]})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def wait_ready(timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = ping()
            if data.get("version") == VERSION:
                return data
        except Exception:  # noqa: BLE001  まだ起動していない
            pass
        time.sleep(0.5)
    raise SystemExit(f"サーバーが応答しません。{ppm_paths.log_dir(APP)} のログを AI に伝えてください")


def write_current(dst: Path) -> None:
    path = ppm_paths.app_support(APP) / "runtime" / "current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".current.json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"version": VERSION, "runtimeDir": str(dst)}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="手元のサーバーを入れる・外す")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--with-deps", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(argv)
    if args.status:
        try:
            _out(f"動いています: {ping()}")
            return 0
        except Exception as e:  # noqa: BLE001
            _out(f"動いていません（{e}）")
            return 1
    if args.uninstall:
        unregister_service()
        _out("常駐を外しました（設定とログは残しています）")
        return 0
    plan = []
    apply = not args.dry_run
    dst = runtime_dir()
    copy_needed = args.force or not dst.exists()
    plan.append(f"写す: {HERE} → {dst}" if copy_needed else f"同じ版 {VERSION} が既にあるので写しません（置き換えるときは --force）: {dst}")
    deps = requirements()
    if args.with_deps and deps:
        plan.append(f"専用の環境を作って依存を入れる: {venv_dir()}（{', '.join(deps)}）")
    elif deps and missing_deps():
        plan.append(f"足りない依存: {', '.join(missing_deps())}（--with-deps で専用の環境に入れられます。入れる前に許可を取ってください）")
    python = service_python(args.with_deps and bool(deps))
    register_service(python, dst / "ppm_server.py", False, plan)
    _out("\n".join("・" + p for p in plan))
    if not apply:
        _out("（試し実行です。何もしていません）")
        return 0
    if args.with_deps and deps:
        venv.create(venv_dir(), with_pip=True)
        py = venv_dir() / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
        r = subprocess.run([str(py), "-m", "pip", "install", "-r", str(HERE / "requirements.txt")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            _out("依存を入れられませんでした:\n" + (r.stdout + r.stderr)[-3000:])
            return 1
    if copy_needed:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
    write_current(dst)
    register_service(python, dst / "ppm_server.py", True, [])
    data = wait_ready()
    _out(f"入れました。{APP} {data['version']} が動いています。パネルを開き直してください")
    return 0


if __name__ == "__main__":
    sys.exit(main())
