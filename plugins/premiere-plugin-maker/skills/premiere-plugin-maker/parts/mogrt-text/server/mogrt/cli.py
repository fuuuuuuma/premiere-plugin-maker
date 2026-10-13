"""エンジンの CLI 共通の作法。

パネル（CEP）は execFileSync で呼ぶ。終了コードが 0 でないと Node が例外を投げ、
利用者には「Command failed: …」という読めない文言だけが出る（実機 2026-09-18）。
だから **どんな入力でも stdout は JSON 1 行・終了コードは 0**。失敗は本文の ok:false と日本語の理由で伝える。
細かい原因（traceback）は stderr へ回す（パネルがログに残す）。
"""
from __future__ import annotations
import json, sys, traceback


def fail(reason: str) -> dict:
    return {"ok": False, "error": reason}


def run(fn, what: str) -> int:
    """fn() の結果（dict）を JSON で出す。例外は日本語の理由に直す。戻り値は常に 0。"""
    try:
        result = fn()
    except SystemExit:                                   # argparse の使い方エラー（--help も含む）
        result = fail(f"{what}: 引数が足りないか、間違っています")
    except FileNotFoundError as e:
        result = fail(f"{what}: ファイルが見つかりません（{e.filename}）")
    except PermissionError as e:
        result = fail(f"{what}: ファイルを読み書きできません（{e.filename}）")
    except UnicodeDecodeError:
        result = fail(f"{what}: ファイルの文字コードを読めません（UTF-8 で保存し直してください）")
    except json.JSONDecodeError as e:
        result = fail(f"{what}: JSON が壊れています（{e.lineno} 行目 {e.colno} 文字目）")
    except MemoryError:
        result = fail(f"{what}: ファイルが大きすぎて読めません")
    except RecursionError:
        result = fail(f"{what}: ファイルの入れ子が深すぎて読めません")
    except Exception as e:                               # 想定外。落とさず理由を返す（型名を添える）
        traceback.print_exc(file=sys.stderr)
        result = fail(f"{what}: {e}（{type(e).__name__}）")
    if not isinstance(result, dict):
        result = fail(f"{what}: 結果を作れませんでした")
    print(json.dumps(result, ensure_ascii=False))
    return 0
