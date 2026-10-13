"""動作の確かめ用のジョブ（受け取った値をそのまま返す）。"""
NAME = "echo"


def run(params, ctx):
    ctx.progress(50, "受け取りました")
    return {"echo": params}
