"""ジョブを書くときの共通部品。jobs/<名前>.py は NAME と run(params, ctx) を持つ。"""
from __future__ import annotations


class JobError(Exception):
    """利用者に見せる理由つきの失敗。パネルには「症状・なぜ・次の一手」で出る。"""

    def __init__(self, message: str, why: str = "", next_step: str = ""):
        super().__init__(message)
        self.why = why
        self.next_step = next_step


def need(params: dict, key: str, kind=str):
    """必須の引数を取り出す。無い・型が違うときは理由つきで止める。"""
    value = params.get(key)
    if value is None or (kind is not None and not isinstance(value, kind)):
        raise JobError(f"「{key}」が渡されていません", "パネルからサーバーへの呼び出しが足りません", "パネルを開き直してから、もう一度試してください")
    return value
