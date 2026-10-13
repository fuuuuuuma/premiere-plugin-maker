"""OS ごとの場所を 1 か所に集める。

テストでは env・os_name・read_version を差し替え、Mac の上でも Windows の組み立てを試せる。
Windows の場所は必ず環境変数（USERPROFILE / APPDATA / LOCALAPPDATA / ProgramFiles / CommonProgramFiles）から作る。
Mac のシステム側（/Applications と /Library）は、テスト用に PPM_APPLICATIONS と PPM_SYSTEM_LIBRARY で差し替えられる。
"""
from __future__ import annotations

import os
import plistlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Mapping, Optional

KIT_DIR_NAME = ".premiere-plugin-maker"


def detect_os(sys_platform: Optional[str] = None) -> str:
    p = sys.platform if sys_platform is None else sys_platform
    if p == "darwin":
        return "mac"
    if p.startswith("win") or p == "cygwin":
        return "windows"
    return "linux"


def _env(env: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    return os.environ if env is None else env


def home(env: Optional[Mapping[str, str]], os_name: str) -> Path:
    e = _env(env)
    if os_name == "windows":
        return Path(e.get("USERPROFILE") or e.get("HOME") or str(Path.home()))
    return Path(e.get("HOME") or str(Path.home()))


def kit_home(env, os_name: str) -> Path:
    return home(env, os_name) / KIT_DIR_NAME


def notes_dir(env, os_name: str) -> Path:
    return kit_home(env, os_name) / "notes"


def default_projects_dir(env, os_name: str) -> Path:
    return home(env, os_name) / "PremierePlugins"


def python_command(os_name: str) -> str:
    return "py -3" if os_name == "windows" else "python3"


def _appdata(env, os_name: str) -> Path:
    e = _env(env)
    return Path(e.get("APPDATA") or (home(env, os_name) / "AppData" / "Roaming"))


def _localappdata(env, os_name: str) -> Path:
    e = _env(env)
    return Path(e.get("LOCALAPPDATA") or (home(env, os_name) / "AppData" / "Local"))


def _program_files(env) -> Path:
    return Path(_env(env).get("ProgramFiles") or r"C:\Program Files")


def _common_program_files(env) -> Path:
    e = _env(env)
    return Path(e.get("CommonProgramFiles") or (_program_files(env) / "Common Files"))


def _mac_applications(env) -> Path:
    return Path(_env(env).get("PPM_APPLICATIONS") or "/Applications")


def _mac_system_library(env) -> Path:
    return Path(_env(env).get("PPM_SYSTEM_LIBRARY") or "/Library")


@dataclass
class PremiereInstall:
    name: str
    path: str
    version: str
    beta: bool


def _version_key(version: str):
    nums = [int(x) for x in re.findall(r"\d+", version)]
    return tuple(nums + [0] * (3 - len(nums))) if nums else (0, 0, 0)


def _read_version(os_name: str, path: Path) -> str:
    if os_name == "mac":
        plist = path / "Contents" / "Info.plist"
        try:
            with open(plist, "rb") as f:
                return str(plistlib.load(f).get("CFBundleShortVersionString", ""))
        except (OSError, plistlib.InvalidFileException):
            return ""
    if os_name == "windows":
        return _read_windows_exe_version(path)
    return ""


def _read_windows_exe_version(folder: Path) -> str:
    """Windows の exe の版を読む（Windows の上だけ）。読めなければ空文字。"""
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return ""
    exes = sorted(folder.glob("Adobe Premiere*.exe"))
    if not exes:
        return ""
    exe = str(exes[0])
    size = ctypes.windll.version.GetFileVersionInfoSizeW(exe, None)
    if not size:
        return ""
    buf = ctypes.create_string_buffer(size)
    if not ctypes.windll.version.GetFileVersionInfoW(exe, 0, size, buf):
        return ""
    ptr = ctypes.c_void_p()
    length = wintypes.UINT()
    if not ctypes.windll.version.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(length)):
        return ""

    class VSFixedFileInfo(ctypes.Structure):
        _fields_ = [("sig", wintypes.DWORD), ("struc", wintypes.DWORD), ("ms", wintypes.DWORD), ("ls", wintypes.DWORD)]

    info = ctypes.cast(ptr, ctypes.POINTER(VSFixedFileInfo)).contents
    return f"{info.ms >> 16}.{info.ms & 0xFFFF}.{info.ls >> 16}"


def premiere_installs(env, os_name: str, read_version: Optional[Callable[[str, Path], str]] = None) -> List[PremiereInstall]:
    """入っている Premiere を新しい版から順に返す。フォルダ名の揺れ（Premiere Pro / Premiere）に強いよう glob で探す。"""
    reader = read_version or _read_version
    found: List[PremiereInstall] = []
    if os_name == "mac":
        root = _mac_applications(env)
        for folder in sorted(root.glob("Adobe Premiere*")):
            if not folder.is_dir():
                continue
            apps = sorted(p for p in folder.glob("Adobe Premiere*.app") if p.is_dir())
            if not apps:
                continue
            found.append(PremiereInstall(folder.name, str(apps[0]), reader("mac", apps[0]), "Beta" in folder.name))
    elif os_name == "windows":
        root = _program_files(env) / "Adobe"
        for folder in sorted(root.glob("Adobe Premiere*")):
            if not folder.is_dir():
                continue
            version = reader("windows", folder)
            if not version:
                year = re.search(r"20(\d\d)", folder.name)
                version = f"{year.group(1)}.x" if year else ""
            found.append(PremiereInstall(folder.name, str(folder), version, "Beta" in folder.name))
    found.sort(key=lambda f: _version_key(f.version), reverse=True)
    return found


def udt_app(env, os_name: str) -> Optional[Path]:
    if os_name == "mac":
        candidate = _mac_applications(env) / "Adobe UXP Developer Tools"
    elif os_name == "windows":
        candidate = _program_files(env) / "Adobe" / "Adobe UXP Developer Tools"
    else:
        return None
    return candidate if candidate.exists() else None


def udt_settings_file(env, os_name: str) -> Path:
    if os_name == "windows":
        return _common_program_files(env) / "Adobe" / "UXP" / "Developer" / "settings.json"
    return _mac_system_library(env) / "Application Support" / "Adobe" / "UXP" / "Developer" / "settings.json"


def upia_path(env, os_name: str) -> Path:
    tail = Path("Adobe") / "Adobe Desktop Common" / "RemoteComponents" / "UPI" / "UnifiedPluginInstallerAgent"
    if os_name == "windows":
        return _common_program_files(env) / tail / "UnifiedPluginInstallerAgent.exe"
    return (_mac_system_library(env) / "Application Support" / tail
            / "UnifiedPluginInstallerAgent.app" / "Contents" / "MacOS" / "UnifiedPluginInstallerAgent")


def _sort_newest_first(dirs: List[Path]) -> List[Path]:
    def key(p: Path):
        if "Beta" in p.name:
            return (9999,)
        year = re.search(r"20(\d\d)", p.name)
        return (int(year.group(1)) if year else 0,)
    return sorted(dirs, key=key, reverse=True)


def uxp_log_dirs(env, os_name: str) -> List[Path]:
    """Premiere の UXP ログのフォルダ（存在するものだけ）。Windows の製品版の場所は公式に見つかっていないので候補を広めに見る。"""
    if os_name == "mac":
        base = home(env, os_name) / "Library" / "Logs" / "Adobe"
        dirs = [p for p in base.glob("Adobe Premiere*") if p.is_dir()]
        return _sort_newest_first(dirs)
    if os_name == "windows":
        roaming = _appdata(env, os_name) / "Adobe"
        dirs = [p / "Logs" for p in roaming.glob("*Premiere*") if (p / "Logs").is_dir()]
        temp = _localappdata(env, os_name) / "Temp" / "UXPLogs"
        if temp.is_dir():
            dirs.append(temp)
        return _sort_newest_first(dirs)
    return []


def plugin_storage_roots(env, os_name: str) -> List[Path]:
    """UXP のプラグインのデータフォルダが入る場所の候補（雛形のログ ppm-log.txt を探すため）。"""
    if os_name == "mac":
        return [home(env, os_name) / "Library" / "Application Support" / "Adobe" / "UXP" / "PluginsStorage"]
    if os_name == "windows":
        return [_appdata(env, os_name) / "Adobe" / "UXP" / "PluginsStorage",
                _localappdata(env, os_name) / "Adobe" / "UXP" / "PluginsStorage"]
    return []


def cep_extensions_dir(env, os_name: str) -> Path:
    if os_name == "windows":
        return _appdata(env, os_name) / "Adobe" / "CEP" / "extensions"
    return home(env, os_name) / "Library" / "Application Support" / "Adobe" / "CEP" / "extensions"


def adobe_fonts_dir(env, os_name: str) -> Path:
    if os_name == "windows":
        return _appdata(env, os_name) / "Adobe" / "CoreSync" / "plugins" / "livetype"
    return home(env, os_name) / "Library" / "Application Support" / "Adobe" / "CoreSync" / "plugins" / "livetype"
