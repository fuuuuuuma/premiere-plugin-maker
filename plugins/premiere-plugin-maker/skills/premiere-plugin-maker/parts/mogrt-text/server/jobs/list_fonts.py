"""入っている書体の PostScript 名の一覧（Adobe Fonts を含む）。"""
from mogrt import fonts

NAME = "list_fonts"


def run(params, ctx):
    return {"fonts": sorted(fonts.list_fonts()) if hasattr(fonts, "list_fonts") else []}
