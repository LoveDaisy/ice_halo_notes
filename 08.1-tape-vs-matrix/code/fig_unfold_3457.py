# 产出 ../img/unfold_3457.png（番外图 2「`3-4-5-7` 的展开」）：六方柱俯视截面里光路 `3-4-5-7` 的真实折线（红），在面 4、面 5 上
# 依次镜像展开出两个幽灵六边形，展开直线（蓝点线）穿过走廊。展开后只剩首尾两个折射面：真实截面的入射面 3（法向 n_3）与最后
# 一个幽灵上的面 7——它的法向 M⁻¹n_7 恰好等于真实截面的 n_5，所以这条边画成「虚面」（虚线描边 + 标注 M⁻¹n_7 = n_5），与实面区分。
# 两面延长交于楔顶，楔角 60°。右上：展开出射方向（W 的结果）与真实出射方向差绕 c 轴 120° 的旋转 = M。右下小图：`3-5` 楔
#（幻日光路，无反射）同一个截面上的入射面 3 / 出射面 5，楔角同样 60°——展开后的楔就是它。
# 读者要看出：展开后的楔就是幻日 `3-5` 的那个 60° 楔；`3-4-5-7` 多出来的东西全在最后那次折叠 M 里，不在楔上。
# 机械核验就地断言（与 ch8 图 1 同一套走廊机制 `Corridor`），单测 code/tests/test_unfold_3457.py 独立复算 M、M⁻¹n_7、楔角。
# 本脚本改写自 08-wedge-times-fold/code/fig_unfold_wedge_fold.py（同一条光路、同一套 Corridor / unfolded_tail），差异是虚面标注与 3-5 小图。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Corridor, CrossSection, draw_raypath_2d, draw_rotation_arc, finish,
                             render_section, solve_raypath_2d, unfolded_tail)
from halo_notes.draw.geometry import unit
from halo_notes.draw.raypath import face_sequence
from halo_notes.draw.scene2d import annotate_2d, draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

OUT = Path(__file__).resolve().parent.parent / "img" / "unfold_3457.png"
WIDTH, HEIGHT, DPI = 2400, 1500, 200
MARGIN = 0.5           # 取景：内容包围盒四周留白（世界单位）

PATHS = {"3-4-5-7": [3, 4, 5, 7], "3-5": [3, 5]}
PRESET = PRESETS["default"]
UNFOLDED = LineStyle("accent_cool", linewidth=1.6, linestyle=":")   # 展开直线：蓝点线（沿 ch3 图 3.1 / ch8 图 1）
FACE_ENTRY = LineStyle("accent_warm", linewidth=3.2)                 # 入射面：实面，加粗描边
FACE_VIRTUAL = LineStyle("accent_cool", linewidth=3.2, linestyle=(0, (2.2, 1.4)))   # 展开后的出射面：虚面，虚线描边
EXTENSION = LineStyle("ink_soft", linewidth=0.9, linestyle="--")     # 两面延长到楔顶的虚线
NORMAL = LineStyle("ink", linewidth=1.3)
WEDGE_DEG = 60.0
FOLD_DEG = 120.0
INSET_BOX = (0.70, 0.03, 0.28, 0.36)   # 右下 3-5 小图（figure 比例）
TEXT15 = TextStyle("ink", fontsize=15, family=CJK_SANS)


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


def wedge_between(n_entry, n_exit) -> float:
    """入射面外法向与（展开后）出射面外法向 → 楔角（度）：两外法向夹角的补角。"""
    return float(np.degrees(np.arccos(np.clip(-(n_entry @ n_exit), -1, 1))))


def unfold_3457(section: CrossSection):
    """`3-4-5-7` 的真实折线、走廊、展开直线与首尾两面的几何（全部由 solve_raypath_2d / Corridor 算出，不手摆）。"""
    faces = PATHS["3-4-5-7"]
    path = solve_raypath_2d(section, faces, tail=2.0, head=1.8)
    assert face_sequence(path) == faces, face_sequence(path)
    corridor = Corridor(section, path)
    last = corridor.ghosts[-1]
    n_entry = section.normal(section.face(faces[0]))
    n_virtual = last.normal(last.face(faces[-1]))
    return path, corridor, n_entry, n_virtual


def draw_wedge(ax, a, b, c, d, radius: float, label_at, label: str) -> np.ndarray:
    """两面 AB / CD 延长到楔顶的虚线 + 楔角弧 + 标签；返回楔顶。"""
    e1, e2 = unit(b - a), unit(d - c)
    t = np.linalg.solve(np.array([e1, -e2]).T, c - a)
    apex = a + e1 * t[0]
    for p, q in ((a, b), (c, d)):
        near = min((p, q), key=lambda v: np.linalg.norm(v - apex))
        ax.plot([apex[0], near[0]], [apex[1], near[1]], zorder=5, **PRESET.line_kwargs(EXTENSION))
    a0 = angle_of(unit((a + b) / 2 - apex))
    a1 = angle_of(unit((c + d) / 2 - apex))
    if (a1 - a0) % 360 > 180:
        a0, a1 = a1, a0
    a1 = a0 + (a1 - a0) % 360
    assert np.isclose(a1 - a0, WEDGE_DEG, atol=1e-6)
    th = np.deg2rad(np.linspace(a0, a1, 48))
    arc = apex[None, :] + radius * np.stack([np.cos(th), np.sin(th)], axis=1)
    ax.plot(arc[:, 0], arc[:, 1], zorder=7, **PRESET.line_kwargs("angle_mark"))
    annotate_2d(ax, label, apex + np.asarray(label_at), preset=PRESET, ha="left", va="center")
    return apex


def draw_inset_35(fig) -> None:
    """右下小图：同一截面上的幻日光路 `3-5`（无反射），入射面 3 与出射面 5 延长成 60° 楔。"""
    ins = fig.add_axes(INSET_BOX)
    section = CrossSection(1.0)
    path = solve_raypath_2d(section, PATHS["3-5"], tail=1.4, head=1.4)
    assert face_sequence(path) == PATHS["3-5"]
    render_section(ins, section, preset=PRESET, face_numbers=True)
    draw_raypath_2d(ins, path, preset=PRESET, semantic="ray2d", internal="ray_internal",
                    arrows=[(0, 0.4), (len(path.kinds) - 1, 0.8)], markers=True)
    f3, f5 = section.face(3), section.face(5)
    a, b = section.face_vertices(f3)
    c, d = section.face_vertices(f5)
    draw_edge(ins, a, b, FACE_ENTRY)
    draw_edge(ins, c, d, LineStyle("accent_cool", linewidth=3.2))
    assert np.isclose(wedge_between(section.normal(f3), section.normal(f5)), WEDGE_DEG, atol=1e-9)
    apex = draw_wedge(ins, a, b, c, d, 0.45, (0.12, -0.3), f"${WEDGE_DEG:g}°$")
    annotate_2d(ins, "对照：幻日光路 3-5\n同一个 $60°$ 楔", (0.0, -1.55), preset=PRESET, ha="center", va="top",
                semantic=TEXT15)
    pts = np.vstack([section.vertices, path.points, apex[None, :]])
    lo, hi = pts.min(axis=0) - 0.3, pts.max(axis=0) + 0.3
    lo[1] = min(lo[1], -2.25)
    hi[0] = max(hi[0], apex[0] + 0.8)
    finish(ins, (lo[0], hi[0]), (lo[1], hi[1]))


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    ax = fig.add_axes([0, 0, 1, 1])

    section = CrossSection(1.0)
    faces = PATHS["3-4-5-7"]
    path, corridor, n_entry, n_virtual = unfold_3457(section)
    last = corridor.ghosts[-1]

    # ---- 截面、幽灵、光路 ----
    render_section(ax, section, preset=PRESET, face_numbers=True)
    for ghost in corridor.ghosts:
        render_section(ax, ghost, preset=PRESET, variant="ghost", face_numbers=True)
    draw_raypath_2d(ax, path, preset=PRESET, semantic="ray2d", internal="ray_internal",
                    arrows=[(0, 0.4), (len(path.kinds) - 1, 0.85)], markers=True)
    straight = unfolded_tail(corridor.straight)
    draw_raypath_2d(ax, straight, preset=PRESET, semantic=UNFOLDED, arrows=[(len(straight.kinds) - 1, 0.85)], markers=True)

    # ---- 走廊里剩下的两个折射面：入射面 3（实面）与展开后的出射面 7（虚面，法向 M⁻¹n_7 = n_5）----
    a, b = section.face_vertices(section.face(faces[0]))
    c, d = last.face_vertices(last.face(faces[-1]))
    draw_edge(ax, a, b, FACE_ENTRY)
    draw_edge(ax, c, d, FACE_VIRTUAL)
    n5 = section.normal(section.face(5))
    assert np.allclose(n_virtual, n5, atol=1e-12), (n_virtual, n5)          # 虚面法向 = 真实截面的 n_5
    assert np.isclose(wedge_between(n_entry, n_virtual), WEDGE_DEG, atol=1e-9)
    draw_normal(ax, (a + b) / 2, n_entry, 0.9, r"$\mathbf{n}_3$", side=1.0)
    draw_normal(ax, (c + d) / 2, n_virtual, 0.9, "", side=1.0)
    virtual_label = (c + d) / 2 + n_virtual * 0.55 + np.array([-0.3, 0.0])   # 法向箭头左侧：避开右侧的蓝色展开直线
    annotate_2d(ax, r"$M^{-1}\mathbf{n}_7=\mathbf{n}_5$", virtual_label + np.array([0.0, 0.22]), preset=PRESET,
                ha="right", va="bottom")
    annotate_2d(ax, "虚面：展开后的面 7", virtual_label + np.array([0.0, 0.12]), preset=PRESET, ha="right", va="top",
                semantic=TextStyle("accent_cool", fontsize=15, family=CJK_SANS))
    apex = draw_wedge(ax, a, b, c, d, 0.9, (0.3, -0.55), f"楔角 ${WEDGE_DEG:g}°$")

    # ---- 右上：W 给出的出射方向（蓝）与真实出射方向（红）差一个 120° 旋转 = M ----
    d_unfolded = unit(straight.points[-1] - straight.points[-2])
    d_real = unit(path.points[-1] - path.points[-2])
    rot = float((angle_of(d_real) - angle_of(d_unfolded)) % 360)
    assert np.isclose(min(rot, 360 - rot), FOLD_DEG, atol=1e-9), rot
    pts = np.vstack([section.vertices, *[g.vertices for g in corridor.ghosts], path.points, straight.points, apex[None, :],
                     virtual_label + np.array([[-2.4, -0.4], [0.0, 0.8]])])
    origin = np.array([section.vertices[:, 0].max() + 5.0, corridor.ghosts[-1].vertices[:, 1].mean() + 0.6])
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

    pts = np.vstack([pts, origin + np.array([[3.2, 2.2], [-1.8, -2.1]])])
    lo, hi = pts.min(axis=0) - MARGIN, pts.max(axis=0) + MARGIN
    cx, cy = (lo + hi) / 2
    w, h = hi - lo
    if w / h < WIDTH / HEIGHT:
        w = h * WIDTH / HEIGHT
    else:
        h = w * HEIGHT / WIDTH
    finish(ax, (cx - w / 2, cx + w / 2), (cy - h / 2, cy + h / 2))
    draw_inset_35(fig)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
