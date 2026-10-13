"""API の鍵を OS の保管庫に置く（平文のファイルには書かない）。Cut & SRT の keychain_store.py から移植。

- macOS   : ログインキーチェーン（`security` コマンド。サービス名 = config.json の app、アカウント = 鍵の名前）。
            値は `security -i` の標準入力で渡し、コマンドラインには載せない（ps で見えるため）。
- Windows : DPAPI（CryptProtectData、ユーザーごと）を ctypes で呼び、暗号化したものを
            %APPDATA%\\<app>\\secrets\\<name>.bin に置く。
- その他  : 保存しない（平文に逃げない）。

本物のキーチェーンへの書き込みを試すときは、使い捨てのキーチェーン（MacKeychainBackend の keychain= 引数）だけを使う。
メッセージは利用者向けの日本語で、鍵の値は決して含めない。Python 3.9 以上・標準ライブラリだけ。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SERVICE = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))["app"]

_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
# 改行・制御文字は入れない（`security -i` の 1 行に収めるため）。引用符と円記号は送る前に逃がす
_BAD_VALUE_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_VALUE_LENGTH = 512
SECURITY_BIN = "/usr/bin/security"
_SECURITY_NOT_FOUND = 44          # errSecItemNotFound exit status of the security command
_SUBPROCESS_TIMEOUT_S = 20


class SecretStoreError(RuntimeError):
    """The secret store could not be used. The message is safe to show (it never holds the value)."""


# ---------------------------------------------------------------- validation

def _check_name(name) -> str:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError("鍵の名前は英小文字で始まる英小文字・数字・_ と - の 32 字までです")
    return name


def normalize_value(name: str, value) -> str:
    """前後の空白を除き、保存できる形かを確かめる。"""
    if not isinstance(value, str):
        raise SecretStoreError("鍵が文字列ではありません")
    text = value.strip()
    if not text:
        raise SecretStoreError("鍵が空です")
    if len(text) > MAX_VALUE_LENGTH:
        raise SecretStoreError("鍵が長すぎます。貼り付けた内容を確かめてください")
    if _BAD_VALUE_RE.search(text):
        raise SecretStoreError("鍵に改行や制御文字が含まれています。コピーし直してください")
    return text


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------- backends

class MacKeychainBackend:
    """login keychain through /usr/bin/security. `keychain` (a path) is for tests with a throw-away keychain."""

    def __init__(self, keychain: str | None = None):
        self.keychain = keychain

    def _run(self, args: list[str], stdin: str | None = None):
        try:
            return subprocess.run([SECURITY_BIN, *args], input=stdin, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=_SUBPROCESS_TIMEOUT_S)
        except (OSError, subprocess.SubprocessError):
            # Do not echo the exception: it may carry the command line.
            raise SecretStoreError("キーチェーンを開けませんでした") from None

    def _tail(self) -> list[str]:
        return [self.keychain] if self.keychain else []

    def set(self, name: str, value: str) -> None:
        # 値を含むコマンドは `security -i` の標準入力で渡す。引用符と円記号は逃がす
        line = f"add-generic-password -U -s {_quote(SERVICE)} -a {name} -w {_quote(value)}"
        if self.keychain:
            line += " " + _quote(self.keychain)
        proc = self._run(["-i"], stdin=line + "\n")
        # `security -i` may exit 0 even when the command failed, so read it back to be sure.
        if proc.returncode != 0 or self.get(name) != value:
            raise SecretStoreError("鍵をキーチェーンに保存できませんでした")

    def get(self, name: str) -> str | None:
        proc = self._run(["find-generic-password", "-s", SERVICE, "-a", name, "-w", *self._tail()])
        if proc.returncode == 0:
            return (proc.stdout or "").rstrip("\r\n") or None
        if proc.returncode == _SECURITY_NOT_FOUND:
            return None
        raise SecretStoreError("キーチェーンから鍵を読めませんでした（キーチェーンがロックされている可能性があります）")

    def delete(self, name: str) -> None:
        proc = self._run(["delete-generic-password", "-s", SERVICE, "-a", name, *self._tail()])
        if proc.returncode not in (0, _SECURITY_NOT_FOUND):
            raise SecretStoreError("キーチェーンの鍵を消せませんでした")


class WindowsDpapiBackend:
    """DPAPI (current user) + a file under the app support folder. _protect/_unprotect are overridable."""

    def __init__(self, directory: str | None = None):
        self._directory = directory

    def directory(self) -> str:
        if self._directory:
            return self._directory
        # local-server の ppm_paths.app_support と同じ場所。ほかの部品に頼らず、この部品だけで決める
        root = os.environ.get("PPM_APP_SUPPORT_ROOT")
        base = Path(root) if root else Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        return str(base / SERVICE / "secrets")

    def path(self, name: str) -> str:
        return os.path.join(self.directory(), f"{name}.bin")

    def _protect(self, data: bytes) -> bytes:
        return _dpapi(data, protect=True)

    def _unprotect(self, data: bytes) -> bytes:
        return _dpapi(data, protect=False)

    def set(self, name: str, value: str) -> None:
        blob = self._protect(value.encode("utf-8"))
        os.makedirs(self.directory(), exist_ok=True)
        target = self.path(name)
        tmp = target + ".tmp"
        try:
            with open(tmp, "wb") as handle:
                handle.write(blob)
            os.replace(tmp, target)
        except OSError:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise SecretStoreError("鍵を保存できませんでした") from None

    def get(self, name: str) -> str | None:
        try:
            with open(self.path(name), "rb") as handle:
                blob = handle.read()
        except FileNotFoundError:
            return None
        except OSError:
            raise SecretStoreError("保存した鍵を読めませんでした") from None
        try:
            return self._unprotect(blob).decode("utf-8") or None
        except (OSError, ValueError):
            # Another Windows user / a restored profile cannot decrypt it. Ask for the key again.
            raise SecretStoreError("保存した鍵を開けませんでした。鍵を入れ直してください") from None

    def delete(self, name: str) -> None:
        try:
            os.remove(self.path(name))
        except FileNotFoundError:
            pass
        except OSError:
            raise SecretStoreError("保存した鍵を消せませんでした") from None


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    """CryptProtectData / CryptUnprotectData. Only runs on Windows."""
    import ctypes
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32      # type: ignore[attr-defined]
    kernel32 = ctypes.windll.kernel32    # type: ignore[attr-defined]
    buffer = ctypes.create_string_buffer(data, len(data))
    source = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    target = DataBlob()
    flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN
    if protect:
        ok = crypt32.CryptProtectData(ctypes.byref(source), None, None, None, None, flags, ctypes.byref(target))
    else:
        ok = crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, flags, ctypes.byref(target))
    if not ok:
        raise OSError("DPAPI failed")
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)


class UnsupportedBackend:
    """No OS secret store: refuse rather than write a plain-text file."""

    def _fail(self):
        raise SecretStoreError("この環境には鍵を安全に保管する仕組みがないため、鍵を保存できません")

    def set(self, name, value):
        self._fail()

    def get(self, name):
        self._fail()

    def delete(self, name):
        self._fail()


def _backend():
    """この OS の保管庫を選ぶ。テストはこの関数を偽物に差し替える。"""
    if sys.platform == "darwin":
        return MacKeychainBackend()
    if sys.platform == "win32":
        return WindowsDpapiBackend()
    return UnsupportedBackend()


# ---------------------------------------------------------------- public API

def set_secret(name: str, value: str) -> None:
    name = _check_name(name)
    _backend().set(name, normalize_value(name, value))


def get_secret(name: str) -> str | None:
    return _backend().get(_check_name(name))


def delete_secret(name: str) -> None:
    _backend().delete(_check_name(name))


def has_secret(name: str) -> bool:
    try:
        return bool(get_secret(name))
    except SecretStoreError:
        return False
