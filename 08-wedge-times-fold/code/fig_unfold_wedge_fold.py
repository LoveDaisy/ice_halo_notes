# 产出 ../img/unfold_wedge_fold.png（图 1「展开走廊：楔角折射 W + 折叠 M」）：六方柱俯视截面里光路 `3-4-5-7`（本篇主角
# 那一格——60° 楔 + 120° 折叠——的最短代表）的红色折线，与它在两个幽灵六边形里的展开直线（蓝）。展开之后走廊里只剩两个折射面：
# 真实截面的入射面 3（法向 n_a）与最后一个幽灵上的出射面 7（法向 M⁻¹n_b）；两面延长线交于楔顶，夹角就是楔角 A = 60°。
# 右上小图：展开直线的出射方向（蓝，楔角折射 W 的结果）与真实出射方向（红）从同一点出发，两者差一个绕 c 轴的 120° 旋转——这就是 M。
# 读者要看出：① 折线与直线是同一条光线（同入射点、同入射方向，脚本里机械核验）；② 展开后只剩首尾两个折射面，中间的反射面全变成
# 走廊里的「门」；③ 楔角由入射面法向与展开后出射面法向的夹角给出；④ 真实出射方向 = M · 展开出射方向。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Corridor, CrossSection, draw_raypath_2d, draw_rotation_arc, finish,
                             render_section, solve_raypath_2d, unfolded_tail)
from halo_notes.draw.geometry import unit
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.draw.scene2d import annotate_2d, draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "unfold_wedge_fold.png"
WIDTH, HEIGHT, DPI = 2400, 1500, 200
MARGIN = 0.5           # 取景：内容包围盒四周留白（世界单位）

PATHS = {"3-4-5-7": [3, 4, 5, 7]}
PRESET = PRESETS["default"]
UNFOLDED = LineStyle("accent_cool", linewidth=1.6, linestyle=":")   # 展开直线：蓝点线（沿 ch3 图 3.1）
FACE_ENTRY = LineStyle("accent_warm", linewidth=3.2)                 # 走廊里剩下的两个折射面：加粗描边
FACE_EXIT = LineStyle("accent_cool", linewidth=3.2)
EXTENSION = LineStyle("ink_soft", linewidth=0.9, linestyle="--")     # 两面延长到楔顶的虚线
NORMAL = LineStyle("ink", linewidth=1.3)
SECTION_ROT = 0.0      # 标准截面（3 朝右）：编号字形正立；光从右侧入射面 3 进、走廊向左上展开
WEDGE_DEG = 60.0
FOLD_DEG = 120.0


def angle_of(v) -> float:
    return float(np.degrees(np.arctan2(v[1], v[0])))


def draw_edge(ax, a, b, style: LineStyle) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], solid_capstyle="round", zorder=6, **PRESET.line_kwargs(style))


def draw_normal(ax, foot, n, length: float, label: str, *, side: float = 1.0, pad: float = 0.22) -> None:
    """从 ``foot`` 沿外法向 ``n`` 画一支法向箭头并在旁边写标签（标签在箭头尖旁、``side`` 一侧偏 ``pad``）。"""
    tip = foot + n * length
    kw = PRESET.line_kwargs(NORMAL)
    ax.plot([foot[0], tip[0]], [foot[1], tip[1]], solid_capstyle="round", zorder=7, **kw)
    draw_arrowhead(ax, tip, n, length=PRESET.geom.arrow2d_length, width=PRESET.geom.arrow2d_width, color=kw["color"], z=8)
    p = np.array([-n[1], n[0]]) * side
    annotate_2d(ax, label, tip + n * 0.12 + p * pad, preset=PRESET, ha="center", va="center")


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    ax = fig.add_axes([0, 0, 1, 1])

    section = CrossSection(1.0).rotated(SECTION_ROT)
    faces = PATHS["3-4-5-7"]
    entry_face, exit_face = section.face(faces[0]), section.face(faces[-1])
    path = solve_raypath_2d(section, faces, tail=2.0, head=1.8)
    corridor = Corridor(section, path)
    last = corridor.ghosts[-1]

    # ---- 截面、幽灵、光路 ----
    render_section(ax, section, preset=PRESET, face_numbers=True)
    for ghost in corridor.ghosts:
        render_section(ax, ghost, preset=PRESET, variant="ghost", face_numbers=True)
    draw_raypath_2d(ax, path, preset=PRESET, semantic="ray2d", internal="ray_internal",
                    arrows=[(0, 0.4), (len(path.kinds) - 1, 0.85)], markers=True)
    straight = unfolded_tail(corridor.straight)
    draw_raypath_2d(ax, straight, preset=PRESET, semantic=UNFOLDED, arrows=[(len(straight.kinds) - 1, 0.85)], markers=True)

    # ---- 走廊里剩下的两个折射面：入射面（真实截面的 3）与展开后的出射面（最后一个幽灵的 7）----
    a, b = section.face_vertices(entry_face)
    c, d = last.face_vertices(last.face(faces[-1]))
    draw_edge(ax, a, b, FACE_ENTRY)
    draw_edge(ax, c, d, FACE_EXIT)
    n_a = section.normal(entry_face)
    n_b_unfolded = last.normal(last.face(faces[-1]))
    wedge = float(np.degrees(np.arccos(np.clip(-(n_a @ n_b_unfolded), -1, 1))))
    assert np.isclose(wedge, WEDGE_DEG, atol=1e-9), wedge
    draw_normal(ax, (a + b) / 2, n_a, 0.9, r"$\mathbf{n}_a$", side=1.0)
    draw_normal(ax, (c + d) / 2, n_b_unfolded, 0.9, r"$M^{-1}\mathbf{n}_b$", side=1.0, pad=0.55)   # 标签放在远离蓝色出射线的一侧

    # 两面延长到楔顶 + 楔角弧
    e1, e2 = unit(b - a), unit(d - c)
    A = np.array([e1, -e2]).T
    t = np.linalg.solve(A, c - a)
    apex = a + e1 * t[0]
    for p, q in ((a, b), (c, d)):
        near = min((p, q), key=lambda v: np.linalg.norm(v - apex))
        ax.plot([apex[0], near[0]], [apex[1], near[1]], zorder=5, **PRESET.line_kwargs(EXTENSION))
    r = 0.9
    a0 = angle_of(unit((a + b) / 2 - apex))
    a1 = angle_of(unit((c + d) / 2 - apex))
    if (a1 - a0) % 360 > 180:
        a0, a1 = a1, a0
    a1 = a0 + (a1 - a0) % 360
    assert np.isclose(a1 - a0, WEDGE_DEG, atol=1e-6)
    th = np.deg2rad(np.linspace(a0, a1, 48))
    arc = apex[None, :] + r * np.stack([np.cos(th), np.sin(th)], axis=1)
    ax.plot(arc[:, 0], arc[:, 1], zorder=7, **PRESET.line_kwargs("angle_mark"))
    annotate_2d(ax, f"楔角 $A={WEDGE_DEG:g}°$", apex + np.array([0.3, -0.55]), preset=PRESET, ha="left", va="center")

    # ---- 右上小图：W 给出的出射方向（蓝）与真实出射方向（红）差一个 120° 旋转 = M ----
    d_unfolded = unit(straight.points[-1] - straight.points[-2])
    d_real = unit(path.points[-1] - path.points[-2])
    rot = float((angle_of(d_real) - angle_of(d_unfolded)) % 360)
    assert np.isclose(min(rot, 360 - rot), FOLD_DEG, atol=1e-9), rot
    pts = np.vstack([section.vertices, *[g.vertices for g in corridor.ghosts], path.points, straight.points, apex[None, :]])
    origin = np.array([section.vertices[:, 0].max() + 5.0, corridor.ghosts[-1].vertices[:, 1].mean() - 0.2])   # 离楔角标签远一点，文字不打架
    L = 1.3
    for dvec, style in ((d_unfolded, LineStyle("accent_cool", linewidth=1.6)), (d_real, LineStyle("accent_warm", linewidth=1.6))):
        kw = PRESET.line_kwargs(style)
        tip = origin + dvec * L
        ax.plot([origin[0], tip[0]], [origin[1], tip[1]], solid_capstyle="round", zorder=7, **kw)
        draw_arrowhead(ax, tip, dvec, length=PRESET.geom.arrow2d_length, width=PRESET.geom.arrow2d_width, color=kw["color"], z=8)
    start, end = angle_of(d_unfolded), angle_of(d_unfolded) + (rot if rot <= 180 else rot - 360)
    draw_rotation_arc(ax, origin, 0.75, start, end, preset=PRESET)
    ax.plot([origin[0]], [origin[1]], "o", ms=3.5, color=PRESET.palette["ink"], zorder=8)
    annotate_2d(ax, r"$M$：绕 $c$ 轴转 $120°$", origin + np.array([0.55, -0.25]), preset=PRESET, ha="left", va="center")
    annotate_2d(ax, "展开直线的出射方向（$W$ 的结果）", origin + d_unfolded * (L + 0.2), preset=PRESET, ha="center", va="bottom",
                semantic=TextStyle("accent_cool", fontsize=15, family=CJK_SANS))
    annotate_2d(ax, "真实出射方向", origin + d_real * (L + 0.2), preset=PRESET, ha="center", va="top",
                semantic=TextStyle("accent_warm", fontsize=15, family=CJK_SANS))

    # 取景：内容包围盒（含 M 小图与文字大致范围）加留白，再按画布比例撑满
    pts = np.vstack([pts, origin + np.array([[3.2, 2.2], [-1.8, -2.1]])])
    lo, hi = pts.min(axis=0) - MARGIN, pts.max(axis=0) + MARGIN
    cx, cy = (lo + hi) / 2
    w, h = hi - lo
    if w / h < WIDTH / HEIGHT:
        w = h * WIDTH / HEIGHT
    else:
        h = w * HEIGHT / WIDTH
    finish(ax, (cx - w / 2, cx + w / 2), (cy - h / 2, cy + h / 2))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
