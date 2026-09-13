# 产出 ../img/grid_6x2.png：12 = 6 种 xy 操作 × 2 种 z 符号（正文第 90–96 行的网格图）。2 行 × 6 列：列 = $e$、$R_z(+120°)$、
# $R_z(-120°)$、$S_{90°}$、$S_{30°}$、$S_{-30°}$（正文第 92 行的列序），行 = $z=+1$（上）、$z=-1$（下）。每格：六边形截面，
# 面编号随 xy 操作走（旋转 = `symmetry.rotate` 转 ±2 格，反射 = 沿不变线翻转 `symmetry.flip`，编号字形随之转 / 镜像）；旋转格画弧形
# 箭头 + 角度、反射格画反射轴（点划线）、下行格右下加一个「上下翻转」小标记；格下三行小字：#编号（ch3 笔记）、柱晶取向晕名、
# 片晶取向晕名——全部从 `halo_notes.math.reflection_group` 权威表查，脚本不抄一份。读者要看出：12 的结构 = 3 类 xy（不动 / 转 / 翻）
# × 2 种 z；同一行里同一类 xy 操作的格子是一个共轭类；#11 在 $e$ 列下行、#2 在 $S_{90°}$ 列上行，相距很远。
# 反射列的翻转轴映射（plan 附注推导，脚本与 test_figures 都用 face_permutation 对 reflection_group 矩阵机械核验）：
# $S_{90°}$ → 过顶点 4|5 的轴（面 3/6 的镜子），$S_{30°}$ → 顶点 3|4（面 5/8），$S_{-30°}$ → 顶点 5|6（面 4/7）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (FACE_COLORS, PRESETS, CrossSection, FlipAxis, draw_flip_axis, draw_flip_marker,
                             draw_rotation_arc, face_permutation, finish, flip, multi_panel, render_section, rotate)
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.math import reflection_group as rg

OUT = Path(__file__).resolve().parent.parent / "img" / "grid_6x2.png"
WIDTH, HEIGHT, DPI = 4500, 2100, 200

PATHS: dict = {}   # 本图没有光路，只有对称操作
PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(
        face_number_colors=FACE_COLORS,
        panel_title=TextStyle("ink", fontsize=11.5, family=CJK_SANS),   # 格下三行小字（中文；最长的晕名 15 字要塞进 700 px）
        symmetry_mark=LineStyle("slate", linewidth=2.6, alpha=0.85),     # 弧箭头 / 双向箭头压在编号之上要看得清（1.3 的淡灰在小格里太弱）
        symmetry_spoke=LineStyle("slate", linewidth=1.0, alpha=0.5)))
COLUMNS = rg.XY_ORDER                          # ("e", "r+", "r-", "s90", "s30", "s-30")
ROWS = (+1, -1)
FLIP_AXES = {"s90": FlipAxis.vertex(4, 5), "s30": FlipAxis.vertex(3, 4), "s-30": FlipAxis.vertex(5, 6)}
ROTATION_STEPS = {"e": 0, "r+": 2, "r-": -2}   # rotate(section, k) 转 k·60°
SPOKE_DEG, ARC_RADIUS, SPOKE_LEN = -30.0, 0.45, 0.9   # 弧箭头：参考方向指向右下顶点（同 1.3），半径 / 辐条长
FLIP_MARKER_AT, FLIP_MARKER_SIZE = (1.15, -0.85), 0.42
XLIM, YLIM = (-1.45, 1.45), (-1.25, 1.25)
TITLE_FRAC, HEADER_FRAC = 0.30, 0.09           # 格下文字带 / 顶部列头带（figure 高度比例）
BASE = CrossSection(1.0)


def transformed_section(xy: str) -> CrossSection:
    """xy 操作作用后的截面：旋转列转 ±120°，反射列沿不变线翻转，$e$ 原样。"""
    if xy in ROTATION_STEPS:
        return rotate(BASE, ROTATION_STEPS[xy])
    return flip(BASE, FLIP_AXES[xy])


def halo_label(e: rg.Element) -> str:
    return f"#{e.number}\n柱晶：{e.column_halo}\n片晶：{e.plate_halo}"


def build_cells() -> list[dict]:
    """行优先的 12 格：(xy, z) → 权威表元素 + 变换后的截面 + 格下文字；顺手机械核验截面置换 == 矩阵对面法向的作用。"""
    cells = []
    for z in ROWS:
        for xy in COLUMNS:
            e = rg.by_xy_z(xy, z)
            section = transformed_section(xy)
            perm = face_permutation(BASE, section)
            M = rg.XY_MATRIX[xy]
            for k in range(3, 9):
                target = int(np.argmin([np.linalg.norm(M @ rg.NORMALS[k] - rg.NORMALS[j]) for j in range(3, 9)])) + 3
                assert perm[target] == k, (xy, k, perm)
            cells.append({"xy": xy, "z": z, "element": e, "section": section, "title": halo_label(e)})
    assert sorted(c["element"].number for c in cells) == list(range(1, 13))
    return cells


CELLS = build_cells()


def main() -> None:
    fig, axes = multi_panel(2, 6, WIDTH, HEIGHT, DPI, preset=PRESET, titles=[c["title"] for c in CELLS],
                            title_frac=TITLE_FRAC)
    # 顶部列头（xy 符号）与左侧行头（z 符号）：figure 坐标；把两行整体下压 HEADER_FRAC 给列头留位置
    for r in range(2):
        for c in range(6):
            x0, y0, w, h = axes[r][c].get_position().bounds
            axes[r][c].set_position([x0 * 0.97 + 0.03, y0 * (1 - HEADER_FRAC), w * 0.97, h * (1 - HEADER_FRAC)])
    for c, xy in enumerate(COLUMNS):
        x0, _, w, _ = axes[0][c].get_position().bounds
        fig.text(x0 + w / 2, 1 - HEADER_FRAC / 2, rg.XY_LATEX[xy], ha="center", va="center", math_fontfamily="cm",
                 **PRESET.text_kwargs(TextStyle("ink", fontsize=24)))
    for r, z in enumerate(ROWS):
        _, y0, _, h = axes[r][0].get_position().bounds
        fig.text(0.02, y0 + h / 2, f"$z={z:+d}$", ha="center", va="center", math_fontfamily="cm", rotation=90,
                 **PRESET.text_kwargs(TextStyle("ink", fontsize=24)))
    for cell, ax in zip(CELLS, (a for row in axes for a in row)):
        xy, z = cell["xy"], cell["z"]
        render_section(ax, cell["section"], preset=PRESET, face_numbers=True)
        c0 = BASE.centroid()
        if xy in ROTATION_STEPS:
            draw_rotation_arc(ax, c0, ARC_RADIUS, SPOKE_DEG, SPOKE_DEG + 60.0 * ROTATION_STEPS[xy], preset=PRESET,
                              spokes=SPOKE_LEN)
        else:
            draw_flip_axis(ax, c0, FLIP_AXES[xy].direction(BASE), 1.3, preset=PRESET, arrow_at=1.1, arrow_half=0.3)
        if z < 0:
            draw_flip_marker(ax, FLIP_MARKER_AT, preset=PRESET, size=FLIP_MARKER_SIZE)
        finish(ax, XLIM, YLIM)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
