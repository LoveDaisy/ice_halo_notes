# 本章两张群表图（fig_c6_table.py / fig_d6_table_shade.py）共用的绘表函数：手工画格 + ax.text mathtext（不用 ax.table：
# LaTeX 与底色/框线控制差）。表头灰底 + 粗斜体，正文格斜体；可选给某个子块上色并加粗框（1.7 的 C6 子群块）。
from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from lumice_integral.symmetry.group import Element, latex, multiplication_table

matplotlib.use("Agg")
# 表头要粗斜体：mathtext 只有 custom 字体集能指定字重，正文格显式走 stix 常规斜体（同一字形家族）
plt.rcParams.update({
    "mathtext.fontset": "custom",
    "mathtext.it": "STIXGeneral:italic:bold",
    "mathtext.rm": "STIXGeneral:bold",
    "mathtext.bf": "STIXGeneral:bold",
    "mathtext.cal": "STIXGeneral:italic",
    "mathtext.sf": "STIXGeneral",
    "mathtext.tt": "STIXGeneral",
})
HEADER_FILL = "#E6E6E6"      # 旧图表头 (230,230,230)
GRID_COLOR = "#808080"       # 旧图 1.4 网格 (128,128,128)


def draw_group_table(ax, elems: list[Element], *, fontsize: float, grid_lw: float, frame_lw: float,
                     block: int | None = None, block_fill: str = "#FAC6C6", block_lw: float = 0.0) -> list[list[Element]]:
    """在 ax 上画 (n+1)×(n+1) 群表：第 0 行 / 第 0 列是表头，格 (i, j) = ``compose(elems[i-1], elems[j-1])``。
    ``block=k`` 时给左上 k×k 正文格（连同它们的表头，共 (k+1)×(k+1)）铺 ``block_fill`` 并加 ``block_lw`` 粗黑框。
    返回乘法表（脚本用来做机械核验）。坐标系：单位 = 一格，y 向下。"""
    n = len(elems)
    table = multiplication_table(elems)
    pad = 0.05  # 留出外框线宽的一半，免得粗框被画布边缘裁掉
    ax.set_xlim(-pad, n + 1 + pad)
    ax.set_ylim(n + 1 + pad, -pad)
    ax.set_aspect("equal")
    ax.axis("off")
    # 底色：表头灰、子块淡红
    for i in range(1, n + 1):
        ax.add_patch(Rectangle((0, i), 1, 1, facecolor=HEADER_FILL, edgecolor="none"))
        ax.add_patch(Rectangle((i, 0), 1, 1, facecolor=HEADER_FILL, edgecolor="none"))
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=HEADER_FILL, edgecolor="none"))
    if block:
        ax.add_patch(Rectangle((1, 1), block, block, facecolor=block_fill, edgecolor="none"))
    # 文字：表头粗斜体（custom 字体集），正文常规斜体（stix）
    for i, g in enumerate(elems, start=1):
        ax.text(0.5, i + 0.5, latex(g), ha="center", va="center", fontsize=fontsize)
        ax.text(i + 0.5, 0.5, latex(g), ha="center", va="center", fontsize=fontsize)
    for i, row in enumerate(table, start=1):
        for j, g in enumerate(row, start=1):
            ax.text(j + 0.5, i + 0.5, latex(g), ha="center", va="center", fontsize=fontsize, math_fontfamily="stix")
    # 网格与外框
    for k in range(n + 2):
        ax.plot([k, k], [0, n + 1], color=GRID_COLOR, lw=grid_lw, solid_capstyle="butt")
        ax.plot([0, n + 1], [k, k], color=GRID_COLOR, lw=grid_lw, solid_capstyle="butt")
    ax.add_patch(Rectangle((0, 0), n + 1, n + 1, facecolor="none", edgecolor="black", lw=frame_lw))
    if block and block_lw:
        ax.add_patch(Rectangle((0, 0), block + 1, block + 1, facecolor="none", edgecolor="black", lw=block_lw))
    return table
