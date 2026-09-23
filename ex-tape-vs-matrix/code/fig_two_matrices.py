# 产出 ../img/two_matrices.png（番外图 4「两张分类表并排」）。
# 左：改绘 TM2006 Fig. 12.1（p.141）的分类矩阵——列 = 楔角、行 = 取向类（片晶 / Parry / 柱晶 / Lowitz / 随机，TM2006 的行序）。
#     楔角画成一条连续的数轴（0° 到可透射上限 2·arcsin(1/n)），六棱柱的三档 {0°, 60°, 90°}（framework 定理 5，取自
#     signature.FAMILY_NAMES）按真实位置落在轴上，档与档之间的空当就是「换一种晶形还会有别的楔角」。
# 右：本系列的表（framework §5「行 = 光路类、列 = 姿态族」）——行 = 光路类 (M, 楔角)，取 phi_class_table(六棱柱) 的节选
#     （全 34 类见漫谈(8)），列 = 姿态族（随机 / 片晶 / 柱晶 / Parry / Lowitz，framework §5 的列序）。
# 两张表都用同一对语义色标出 `3-5`（紫）与 `3-4-5-7`（橙）：左表里二者都是 60° 楔、片晶取向，落进同一格；右表里二者是
# 不同的 Φ 类（A60-12：M = e；A60-10：M = R_z(±120°)），分居两行。格子里的晕名只填 60° 那一列 / `3-5` 那一行，取自
# framework §5「同一光路 × 五族 = 五种晕（3-5：圆晕 / 幻日 / 相切弧 / Parry 弧 / Lowitz 弧）」，其余格留空。
# 取向类 / 姿态族是示意标签，不是计算输出（图注也这样写）；楔角、Φ 类、节选行全部由 halo_notes.math.signature 算出。
# 读者要看出：左表的「行」是连续的楔角，右表的行是离散且有限的光路类；同样两条光路在左表同格、右表异格。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
from lumice_integral.geometry import HexPrism, fold_matrix
from matplotlib.patches import FancyBboxPatch, Rectangle

from halo_notes.draw import PRESETS, annotate_2d, finish, multi_panel
from halo_notes.draw.style import TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import A_MAX_DEG, FAMILY_NAMES, phi_class, phi_class_table, wedge_angle

OUT = Path(__file__).resolve().parent.parent / "img" / "two_matrices.png"
WIDTH, HEIGHT, DPI = 3600, 1650, 200

PATHS: dict = {}   # 本图没有光路，只有两张表
PRESET = PRESETS["default"]
CRYSTAL = HexPrism.from_ratio(1.0)
M_3457 = fold_matrix(CRYSTAL, [3, 4, 5, 7])
HIGHLIGHT = {"3-5": (np.eye(3), 3, 5, "sample_1"), "3-4-5-7": (M_3457, 3, 7, "sample_2")}   # 光路 → (M, 入面, 出面, 语义色)

TM_ROWS = ["片晶", "Parry", "柱晶", "Lowitz", "随机"]            # TM2006 Fig. 12.1 的取向类（行序照原图）
FAMILIES = ["随机", "片晶", "柱晶", "Parry", "Lowitz"]           # framework §5 的姿态族（列序照 framework）
HALOS_35 = {"随机": r"$22^\circ$ 晕", "片晶": "幻日", "柱晶": "切弧", "Parry": "Parry 弧", "Lowitz": "Lowitz 弧"}   # framework §5
HIGHLIGHT_ATTITUDE = "片晶"                                       # 两条光路都按片晶取向标（左表同一行、右表同一列）
EXCERPT = ["A0-01", "A0-02", "A60-09", "A60-10", "A60-11", "A60-12", "A90-01", "A90-16"]   # 右表节选的行（每个楔角都有）

# ---- 版面（各栏自己的数据坐标）----
L_SCALE = 0.085                     # 左表：楔角 1° 对应的横向长度
L_CELL_W, L_CELL_H = 1.9, 1.25
L_HEAD_W = 2.2                      # 行标题列宽
L_LIM = ((-3.65, 10.2), (-9.45, 2.45))      # 两栏取景宽高比 = 面板格子宽高比（≈1.164），两栏标题才等高
R_CELL_W, R_CELL_H = 1.55, 0.86
R_HEAD_W = 5.8
R_LIM = ((-6.0, 7.95), (-10.98, 1.0))
GRID_COLOR, HEAD_FILL = "ink_faint", "ice"
TEXT_HEAD = TextStyle("ink", fontsize=15, family=CJK_SANS, weight="bold")
TEXT_CELL = TextStyle("ink_soft", fontsize=13, family=CJK_SANS)
TEXT_NOTE = TextStyle("ink_soft", fontsize=13, family=CJK_SANS)
TEXT_ROW = TextStyle("ink", fontsize=13, family=CJK_SANS)


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


def fold_label(folds: tuple[int, ...]) -> str:
    """折叠 M 的标签：类里只有一个元素时写它本身，否则写一个代表（ch7 编号最大者）+「类」（共轭类，同一个 Φ 类）。"""
    rep = rg.by_number(folds[-1]).latex
    return rep if len(folds) == 1 else f"{rep} 类"


def pair_label(row) -> str:
    a, b = row.face_pairs[0]
    return f"{a}→{b}" + (" 等" if len(row.face_pairs) > 1 else "")


def cell(ax, x, y, w, h, *, fill: str | None = None) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=PRESET.palette[fill] if fill else "none",
                           edgecolor=PRESET.palette[GRID_COLOR], linewidth=1.0, zorder=1))


def badge(ax, center, text: str, color: str, *, height: float = 0.32) -> None:
    width = 0.17 * len(text) + 0.25
    x, y = center
    ax.add_patch(FancyBboxPatch((x - width / 2, y - height / 2), width, height, boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor=PRESET.palette[color], edgecolor="none", zorder=4))
    ax.text(x, y, text, ha="center", va="center", zorder=5, color=PRESET.palette["background"], fontsize=13,
            fontweight="bold", family=CJK_SANS)


def left_table(ax, hl: dict) -> None:
    wedges = sorted(FAMILY_NAMES)
    x_of = lambda a: a * L_SCALE  # noqa: E731  列中心 = 楔角在连续数轴上的位置
    # 连续的楔角数轴（0° → 可透射上限）
    axis_y = 1.35
    x_end = A_MAX_DEG * L_SCALE
    ax.annotate("", xy=(x_end + 0.35, axis_y), xytext=(-0.3, axis_y),
                arrowprops=dict(arrowstyle="-|>", color=PRESET.palette["ink_soft"], linewidth=1.2))
    for a in wedges:
        ax.plot([x_of(a)] * 2, [axis_y - 0.12, axis_y + 0.12], color=PRESET.palette["ink_soft"], linewidth=1.2)
        annotate_2d(ax, f"${a:g}^\\circ$", (x_of(a), axis_y + 0.22), preset=PRESET, ha="center", va="bottom", semantic=TEXT_HEAD)
    annotate_2d(ax, "楔角（连续量）", (x_end + 0.45, axis_y), preset=PRESET, ha="left", va="center", semantic=TEXT_NOTE)
    annotate_2d(ax, "六棱柱只有这三档；换晶形（如锥面）会落在空当里", (x_of(60) - 0.3, axis_y - 0.42), preset=PRESET,
                ha="center", va="center", semantic=TEXT_NOTE)
    # 表体
    top = 0.2
    for i, row in enumerate(TM_ROWS):
        y = top - (i + 1) * L_CELL_H
        cell(ax, -L_HEAD_W - L_CELL_W / 2 - 0.25, y, L_HEAD_W, L_CELL_H, fill=HEAD_FILL)
        annotate_2d(ax, row, (-L_HEAD_W / 2 - L_CELL_W / 2 - 0.25, y + L_CELL_H / 2), preset=PRESET, ha="center",
                    va="center", semantic=TEXT_HEAD)
        for a in wedges:
            cell(ax, x_of(a) - L_CELL_W / 2, y, L_CELL_W, L_CELL_H)
            if a == 60.0:   # 60° 列 = 3-5 这个楔在五种取向下的晕（framework §5）
                annotate_2d(ax, HALOS_35[row], (x_of(a), y + L_CELL_H * 0.78), preset=PRESET, ha="center", va="center",
                            semantic=TEXT_CELL)
    # 两条光路：楔角同为 60°、取向同为片晶，所以同一格
    for k, (name, info) in enumerate(hl.items()):
        i = TM_ROWS.index(info["attitude"])
        y = top - (i + 1) * L_CELL_H + L_CELL_H * (0.48 - 0.3 * k)
        badge(ax, (x_of(round(info["wedge"], 6)), y), name, info["color"])
    annotate_2d(ax, "取向类为示意标签（TM2006 Fig. 12.1 的行），非计算输出", (-L_HEAD_W - L_CELL_W / 2 - 0.25, top - 5 * L_CELL_H - 0.45),
                preset=PRESET, ha="left", va="top", semantic=TEXT_NOTE)
    annotate_2d(ax, "3-5 与 3-4-5-7：同为 $60^\\circ$ 楔、同为片晶，所以同一格", (-L_HEAD_W - L_CELL_W / 2 - 0.25, top - 5 * L_CELL_H - 1.0),
                preset=PRESET, ha="left", va="top", semantic=TextStyle("ink", fontsize=14, family=CJK_SANS))
    finish(ax, *L_LIM)


def right_table(ax, hl: dict) -> None:
    rows, n_classes = excerpt_rows()
    x0 = 0.0
    col_x = {f: x0 + j * R_CELL_W for j, f in enumerate(FAMILIES)}
    top = 0.0
    for f, x in col_x.items():
        cell(ax, x, top, R_CELL_W, R_CELL_H, fill=HEAD_FILL)
        annotate_2d(ax, f, (x + R_CELL_W / 2, top + R_CELL_H / 2), preset=PRESET, ha="center", va="center",
                    semantic=TEXT_HEAD)
    cell(ax, -R_HEAD_W, top, R_HEAD_W, R_CELL_H, fill=HEAD_FILL)
    annotate_2d(ax, "光路类（入→出面、楔角、$M$）", (-R_HEAD_W / 2, top + R_CELL_H / 2), preset=PRESET, ha="center",
                va="center", semantic=TEXT_HEAD)
    by_row = {info["row"].id: (name, info) for name, info in hl.items()}
    y = top
    prev_wedge = None
    for r in rows:
        if prev_wedge is not None and r.wedge_deg != prev_wedge:
            y -= 0.28                                       # 楔角分组之间留一道缝
        prev_wedge = r.wedge_deg
        y -= R_CELL_H
        name, info = by_row.get(r.id, (None, None))
        cell(ax, -R_HEAD_W, y, R_HEAD_W, R_CELL_H)
        color = info["color"] if info else "ink"
        label = f"{r.id}  {pair_label(r)}  ${r.wedge_deg:g}^\\circ$  $M=${fold_label(r.folds)}"
        annotate_2d(ax, label, (-R_HEAD_W + 0.12, y + R_CELL_H / 2), preset=PRESET, ha="left", va="center",
                    semantic=TextStyle(color, fontsize=13, family=CJK_SANS, weight="bold" if info else "normal"),
                    math_fontfamily="cm")
        for f, x in col_x.items():
            cell(ax, x, y, R_CELL_W, R_CELL_H)
            if name == "3-5":
                annotate_2d(ax, HALOS_35[f], (x + R_CELL_W / 2, y + R_CELL_H * (0.74 if f == info["attitude"] else 0.5)),
                            preset=PRESET, ha="center", va="center", semantic=TEXT_CELL)
            if info and f == info["attitude"]:
                badge(ax, (x + R_CELL_W / 2, y + R_CELL_H * (0.3 if name == "3-5" else 0.5)), name, info["color"],
                      height=0.3)
    y -= 0.2
    annotate_2d(ax, "⋮", (-R_HEAD_W / 2, y - 0.1), preset=PRESET, ha="center", va="top", semantic=TEXT_HEAD)
    annotate_2d(ax, f"节选 {len(rows)} 行；六棱柱全表共 {n_classes} 类（见漫谈(8)）", (-R_HEAD_W, y - 0.75), preset=PRESET,
                ha="left", va="top", semantic=TEXT_NOTE)
    annotate_2d(ax, "姿态族为示意标签，非计算输出", (-R_HEAD_W, y - 1.2), preset=PRESET, ha="left", va="top",
                semantic=TEXT_NOTE)
    annotate_2d(ax, "3-5 与 3-4-5-7：同一个 $60^\\circ$ 楔、不同的折叠 $M$，所以分居两行", (-R_HEAD_W, y - 1.75), preset=PRESET,
                ha="left", va="top", semantic=TextStyle("ink", fontsize=14, family=CJK_SANS))
    finish(ax, *R_LIM)


def main() -> None:
    hl = highlight_classes()
    fig, axes = multi_panel(1, 2, WIDTH, HEIGHT, DPI, preset=PRESET, title_frac=0.09,
                            titles=["Tape 与 Moilanen 2006：楔角 × 取向类", "本系列：光路类 × 姿态族"])
    for ax in axes[0]:
        for t in ax.texts:
            t.set_fontfamily(CJK_SANS)
            t.set_fontsize(22)
    left_table(axes[0][0], hl)
    right_table(axes[0][1], hl)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
