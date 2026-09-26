# 产出 ../img/two_matrices.png（番外图 5「两张分类表并排」）。视觉语言照搬 ch8 图 3（08-wedge-times-fold/code/fig_phi_class_grid.py：
# 圆角框格子、左侧行标 + 小字注、顶部列组表头、讨论中的格子黄底），画法在 _ex_fig.py 的 grid_* 里，调色板 / 字体 / 折叠行标签
# 直接取自 ch8 脚本。
# 左：改绘 TM2006 Fig. 12.1（书页 p.131，PDF 第 141 页）的分类矩阵——原图就是两列：α = 60°（Δmin = 22°）与 α = 90°（Δmin = 46°），
#     行 = 取向类（片晶 / Parry / 柱晶 / Lowitz / 随机，原图行序），格内是原图的格名（22° plate arcs … 46° halo，译成中文）；
#     原图图注：六棱柱两列，锥晶要八列；只收纯折射晕。60° 列另加一行小字「如：…」，是 `3-5` 在该取向下的晕名，取自 framework §5
#     「同一光路 × 五族 = 五种晕（3-5：圆晕 / 幻日 / 相切弧 / Parry 弧 / Lowitz 弧）」。
# 右：本系列的表（framework §5「行 = 光路类、列 = 姿态族」）——行 = Φ 类，取 phi_class_table(六棱柱) 的节选（全 34 类见漫谈(8)），
#     行标主标签是该类的最短代表光路（ch8 data/signature_table.md，经 ch8 脚本的 load_rows 读），小字注 = 楔角 · 折叠 M 的中文说法（ch8 行注）· 入出面；
#     列 = 姿态族（随机 / 片晶 / 柱晶 / Parry / Lowitz，framework §5 的列序）。
# 两张表都用同一对语义色标出 `3-5`（紫）与 `3-4-5-7`（橙）：左表里二者都是 60° 楔、片晶取向，落进同一格；右表里二者是
# 不同的 Φ 类（A60-12：M = e；A60-10：M = R_z(±120°)），分居两行。`3-4-5-7` 含内反射、不在 TM2006 那张表的收录范围里，
# 左表里它的 chip 用虚线描边，图例交代。取向类 / 姿态族是示意标签，不是计算输出；楔角、Φ 类、节选行全部由 lumice_integral.symmetry.signature 算出。
# 读者要看出：同样两条光路在左表同格、右表异格——左表按楔角分列，右表按离散且有限的光路类分行。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from lumice_integral.geometry import HexPrism, fold_matrix

from lumice_integral.symmetry.signature import phi_class, phi_class_table, wedge_angle

from _ex_fig import CH8_GRID, GRID_PAL, grid_box, grid_chip, grid_header, grid_row_label, grid_text

OUT = Path(__file__).resolve().parent.parent / "img" / "two_matrices.png"
WIDTH, HEIGHT, DPI = 3600, 1480, 200

PATHS: dict = {}   # 本图没有光路，只有两张表
CRYSTAL = HexPrism.from_ratio(1.0)
M_3457 = fold_matrix(CRYSTAL, [3, 4, 5, 7])
HIGHLIGHT = {"3-5": (np.eye(3), 3, 5, "sample_1"), "3-4-5-7": (M_3457, 3, 7, "sample_2")}   # 光路 → (M, 入面, 出面, 语义色)
OUTSIDE_TM = {"3-4-5-7"}                                          # 含内反射，不在 TM2006 refraction halos 的收录范围 [TM2006 p.139]

TM_ROWS = ["片晶", "Parry", "柱晶", "Lowitz", "随机"]            # TM2006 Fig. 12.1 的取向类（行序照原图）
TM_WEDGES = [60.0, 90.0]                                          # TM2006 Fig. 12.1 的两列（六棱柱；锥晶要八列）
TM_COLUMNS = {60.0: ("60° 楔", "$\\Delta_{\\min}=22^\\circ$"), 90.0: ("90° 楔", "$\\Delta_{\\min}=46^\\circ$")}
TM_CELLS = {"片晶": "片晶弧", "Parry": "Parry 弧", "柱晶": "柱晶弧", "Lowitz": "Lowitz 弧", "随机": None}   # 原图 "22° plate arcs" 等

FAMILIES = ["随机", "片晶", "柱晶", "Parry", "Lowitz"]           # framework §5 的姿态族（列序照 framework）
HALOS_35 = {"随机": "22° 晕", "片晶": "幻日", "柱晶": "切弧", "Parry": "Parry 弧", "Lowitz": "Lowitz 弧"}   # framework §5
HIGHLIGHT_ATTITUDE = "片晶"                                       # 两条光路都按片晶取向标（左表同一行、右表同一列）
EXCERPT = ["A0-01", "A0-02", "A60-09", "A60-10", "A60-11", "A60-12", "A90-01", "A90-16"]   # 右表节选的行（每个楔角都有）
FOLD_NOTE = {k: note for k, _, note in CH8_GRID.FOLD_ROWS}     # "#4/#6" → "绕 c 轴转 120°"（ch8 行标签的小字注；不混排 mathtext，免得中文掉字）

# ---- 版面（像素，y 向下）----
TITLE_Y = 58
HEADER_Y, HEADER_H = 150, 120                   # 列表头标题所在 y、表头高
TOP = HEADER_Y + 0.62 * HEADER_H + 8            # 第一行上沿
L_X0, L_LABEL_W, L_CELL_W, L_CELL_H = 40, 230, 450, 190
R_X0, R_LABEL_W, R_CELL_W, R_CELL_H = 1300, 590, 330, 118
R_GROUP_GAP = 22
DIVIDER_X = 1250


def highlight_classes() -> dict[str, dict]:
    """两条光路的楔角（signature.wedge_angle）与 Φ 类（signature.phi_class），以及 Φ 类在全类表里的行号。"""
    table = phi_class_table(CRYSTAL)
    out = {}
    for name, (M, a, b, color) in HIGHLIGHT.items():
        cls = phi_class(CRYSTAL, M, a, b)
        (row,) = [r for r in table if r.phi_class == cls]
        out[name] = {"wedge": wedge_angle(CRYSTAL, M, a, b), "class": cls, "row": row, "color": color,
                     "attitude": HIGHLIGHT_ATTITUDE}
    return out


def excerpt_rows():
    """右表节选：按 id 从全类表里取（不是手造的行）；返回 (节选行, 全表可透射类数)。"""
    table = phi_class_table(CRYSTAL)
    by_id = {r.id: r for r in table}
    rows = [by_id[i] for i in EXCERPT]
    return rows, sum(r.transmittable for r in table)


def representatives() -> dict[str, dict]:
    """类 id → ch8 signature_table.md 的最短代表光路与入出面对（ch8 脚本自己的解析器）。"""
    return {r["id"]: r for r in CH8_GRID.load_rows()}


def left_cells(hl: dict) -> dict[str, tuple[str, float]]:
    """左表：光路 → (取向类, 楔角列)。楔角取 signature 算出的值落到最近的列上。"""
    out = {}
    for name, info in hl.items():
        col = min(TM_WEDGES, key=lambda a: abs(a - info["wedge"]))
        assert abs(col - info["wedge"]) < 1e-9, (name, info["wedge"])
        out[name] = (info["attitude"], col)
    return out


def right_cells(hl: dict) -> dict[str, tuple[str, str]]:
    """右表：光路 → (Φ 类 id = 行, 姿态族 = 列)。"""
    return {name: (info["row"].id, info["attitude"]) for name, info in hl.items()}


def left_table(ax, hl: dict) -> None:
    cells = left_cells(hl)
    x_col = L_X0 + L_LABEL_W
    w_all = len(TM_WEDGES) * L_CELL_W
    grid_text(ax, x_col + w_all / 2 - L_LABEL_W / 2, TITLE_Y, "Tape 与 Moilanen 2006：楔角 × 取向类", 15, weight="bold")
    for j, a in enumerate(TM_WEDGES):
        grid_header(ax, x_col + j * L_CELL_W, L_CELL_W, HEADER_Y, *TM_COLUMNS[a], HEADER_H)
    for i, row in enumerate(TM_ROWS):
        y0 = TOP + i * L_CELL_H
        grid_row_label(ax, x_col - 30, y0 + L_CELL_H / 2, row, None, main_size=13.5, bold=True)
        if i:
            ax.plot([L_X0, x_col + w_all], [y0, y0], color=GRID_PAL["ink_faint"], lw=0.7)
        for j, a in enumerate(TM_WEDGES):
            here = [n for n, cell in cells.items() if cell == (row, a)]
            x0 = x_col + j * L_CELL_W
            cx = x0 + L_CELL_W / 2
            grid_box(ax, x0, y0, L_CELL_W, L_CELL_H, kind="star" if here else "dashed")
            name = f"{22 if a == 60 else 46}° " + (TM_CELLS[row] or "晕")
            grid_text(ax, cx, y0 + L_CELL_H * (0.2 if here else 0.4), name, 14.5)
            if a == 60.0:
                grid_text(ax, cx, y0 + L_CELL_H * (0.47 if here else 0.64), f"如：{HALOS_35[row]}", 10.5, "accent_cool")
            for k, path in enumerate(here):                   # 同格的 chip 左右并排
                dx = (k - (len(here) - 1) / 2) * 150
                grid_chip(ax, cx + dx, y0 + L_CELL_H * 0.77, path, hl[path]["color"], dashed=path in OUTSIDE_TM)
    y = TOP + len(TM_ROWS) * L_CELL_H + 40
    for k, line in enumerate(["原图注：六棱柱两列，锥晶要八列；只收纯折射晕",
                              "黄底：3-5 与 3-4-5-7 同为 60° 楔、同为片晶，落进同一格",
                              "虚线框：3-4-5-7 含内反射，不在原表收录范围里，",
                              "　　　　这里按两根轴替它找个位置",
                              "「如：」= 3-5 在该取向下的晕名（本系列 framework §5）"]):
        grid_text(ax, L_X0, y + k * 38, line, 10.5, "ink_soft", ha="left")


def right_table(ax, hl: dict) -> None:
    rows, n_classes = excerpt_rows()
    reps = representatives()
    cells = right_cells(hl)
    x_col = R_X0 + R_LABEL_W
    w_all = len(FAMILIES) * R_CELL_W
    grid_text(ax, x_col + w_all / 2 - R_LABEL_W / 2, TITLE_Y, "本系列：光路类 × 姿态族", 15, weight="bold")
    for j, fam in enumerate(FAMILIES):
        grid_header(ax, x_col + j * R_CELL_W, R_CELL_W, HEADER_Y, fam, None, HEADER_H)
    y0 = TOP
    prev = None
    for r in rows:
        if prev is not None and r.wedge_deg != prev:
            y0 += R_GROUP_GAP
        if prev is not None:
            ax.plot([R_X0, x_col + w_all], [y0, y0], color=GRID_PAL["ink_faint"], lw=0.7)
        prev = r.wedge_deg
        rep = reps[r.id]
        star_path = next((n for n, (cid, _) in cells.items() if cid == r.id), None)
        note = f"{r.wedge_deg:g}° 楔 · {FOLD_NOTE[rep['folds']]} · {rep['faces'].replace('→', ' → ')}"
        grid_row_label(ax, x_col - 30, y0 + R_CELL_H / 2, rep["path"], note, main_size=14, bold=star_path is not None)
        for j, fam in enumerate(FAMILIES):
            cx = x_col + j * R_CELL_W + R_CELL_W / 2
            if star_path is not None and cells[star_path][1] == fam:
                grid_box(ax, x_col + j * R_CELL_W, y0, R_CELL_W, R_CELL_H, kind="star")
            if star_path == "3-5":
                grid_text(ax, cx, y0 + R_CELL_H * (0.3 if fam == cells["3-5"][1] else 0.5), HALOS_35[fam], 11.5,
                          "ink_soft")
            if star_path is not None and cells[star_path][1] == fam:
                grid_chip(ax, cx, y0 + R_CELL_H * (0.66 if star_path == "3-5" else 0.5), star_path,
                          hl[star_path]["color"])
        y0 += R_CELL_H
    grid_text(ax, R_X0 + R_LABEL_W - 30, y0 + 22, "⋮", 16, "ink_soft", ha="right")
    y = y0 + 80
    for k, line in enumerate([f"节选 {len(rows)} 行；六棱柱全表共 {n_classes} 类（见漫谈(8)）。姿态族为示意标签，非计算输出",
                              "黄底：3-5 与 3-4-5-7 是同一个 60° 楔、不同的折叠 M，分居两行"]):
        grid_text(ax, R_X0, y + k * 38, line, 10.5, "ink_soft", ha="left")


def main() -> None:
    hl = highlight_classes()
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(GRID_PAL["background"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(HEIGHT, 0)
    ax.set_axis_off()
    left_table(ax, hl)
    ax.plot([DIVIDER_X, DIVIDER_X], [TITLE_Y - 20, HEIGHT - 40], color=GRID_PAL["ink_faint"], lw=1.0)
    right_table(ax, hl)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
