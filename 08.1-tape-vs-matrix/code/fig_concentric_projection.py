# 产出 ../img/concentric_projection.png（番外图 2「同心圆作图」）：改绘 TM2006 Fig. 4.5（p.48）的同心天球截面，并接上真实光路。
# 左栏：六方柱截面里真实追迹的幻日光路 `3-5`（solve_raypath_2d，与图 3 同款截面），入射段 / 晶体内部段 / 出射段各一个语义色，
# 另画面 3 上的反射段（淡虚线）；面 3、面 5 的外法向 n_3、n_5。
# 右栏：半径 1（空气）与 n（冰）两个同心圆。光点 = 光线反方向 × 所在介质折射率，每个光点用左栏对应线段的颜色：
# S = 入射段、S' = 面 3 反射段、R = 晶体内部段、H = 出射段。两次折射画成两支投影箭头：S → R 沿 n_3（内圆 → 外圆）、
# R → H 沿 n_5（外圆 → 内圆）；S、S'、R 共线于 n_3。
# 读者要看出：光点就是光线（反向、乘折射率）；折射就是沿界面法线的平行投影，两次投影合成 W。
# 取值：左栏光路取 60° 楔的对称（最小偏折）入射，只为让两段投影都清楚可见，不承载数值结论。右栏点由 concentric_projection
# 从入射光点逐次投影算出，单测再逐点对照左栏追迹出来的线段方向。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import CrossSection, annotate_2d, concentric_projection, draw_raypath_2d, finish, render_section, solve_raypath_2d
from halo_notes.draw.geometry import unit
from halo_notes.draw.raypath import N_ICE, SegmentKind, face_sequence, reflect
from halo_notes.draw.scene2d import draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

from _ex_fig import PRESET, SPOKE, TEXT15, direction, draw_arrow, draw_circle, draw_line, draw_point

OUT = Path(__file__).resolve().parent.parent / "img" / "concentric_projection.png"
WIDTH, HEIGHT, DPI = 3000, 1700, 200
LEFT_BOX, RIGHT_BOX = [0.01, 0.1, 0.40, 0.88], [0.42, 0.1, 0.57, 0.88]   # 右栏更宽：投影箭头所在的那一小片要放得开

PATHS = {"3-5": [3, 5]}
SECTION = CrossSection(1.0)
FACE_IN, FACE_OUT = 3, 5
INTERNAL_DEG = 150.0     # 冰内光线方向：与 -n_3（180°）、n_5（120°）各夹 30°——60° 楔的对称（最小偏折）入射
# 线段语义色：入射 / 内部 / 出射 / 面 3 反射
COLORS = {"S": "accent_warm", "R": "sample_2", "H": "accent_cool", "S'": "ink_soft"}
SEGMENT_OF = {"S": "入射段", "S'": "面 3 反射段", "R": "晶体内部段", "H": "出射段"}
REFLECTED_LEN = 1.3
LEFT_LIM = ((-2.25, 2.55), (-1.95, 2.0))
RIGHT_LIM = ((-1.45, 2.35), (-1.87, 1.45))
CIRCLE = LineStyle("ink_soft", linewidth=1.4)
INTERFACE = LineStyle("ink_faint", linewidth=1.4)
NORMAL = LineStyle("ink", linewidth=1.3)


def seg_style(key: str, width: float = 2.4) -> LineStyle:
    return LineStyle(COLORS[key], linewidth=width, linestyle="--" if key == "S'" else "-")


def raypath_35():
    """左栏：`3-5` 的真实光路（对称入射方向交给 solve_raypath_2d 原样试）与各段单位方向。"""
    n3 = SECTION.normal(SECTION.face(FACE_IN))
    d_inside = direction(INTERNAL_DEG)
    s = concentric_projection(-N_ICE * d_inside, n3, 1.0).refracted        # 由冰内方向反推入射光点（切向守恒）
    path = solve_raypath_2d(SECTION, PATHS["3-5"], prefer_direction=-s, tail=1.5, head=1.5)
    assert face_sequence(path) == PATHS["3-5"], face_sequence(path)
    dirs = {}
    for p0, p1, kind in path.segments():
        dirs[{SegmentKind.INCIDENT: "S", SegmentKind.INTERNAL: "R", SegmentKind.EXIT: "H"}[kind]] = unit(p1 - p0)
    dirs["S'"] = reflect(dirs["S"], n3)
    return path, dirs


def concentric_points(d_incident) -> dict[str, np.ndarray]:
    """右栏的光点：从入射光点 S = −d_incident（半径 1）出发，沿 n_3 投影到半径 n 得 R（同一直线上的镜像点是 S'），
    再沿 n_5 投影回半径 1 得 H。只用 concentric_projection，不读左栏的内部段 / 出射段。"""
    n3 = SECTION.normal(SECTION.face(FACE_IN))
    n5 = SECTION.normal(SECTION.face(FACE_OUT))
    first = concentric_projection(-unit(d_incident), n3, N_ICE)
    second = concentric_projection(first.refracted, n5, 1.0)
    return {"S": first.incident, "S'": first.reflected, "R": first.refracted, "H": second.refracted,
            "n_in": first.normal, "n_out": second.normal}


def draw_normal(ax, foot, n, length: float, label: str, offset=(0.0, 0.0)) -> None:
    tip = foot + n * length
    draw_line(ax, foot, tip, NORMAL, z=6)
    draw_arrowhead(ax, tip, n, length=PRESET.geom.arrow2d_length, width=PRESET.geom.arrow2d_width,
                   color=PRESET.palette["ink"], z=6)
    annotate_2d(ax, label, tip + n * 0.18 + np.asarray(offset), preset=PRESET, ha="center", va="center",
                semantic=TextStyle("ink", fontsize=17))


def left_panel(ax, path, dirs) -> None:
    render_section(ax, SECTION, preset=PRESET, face_numbers=[FACE_IN, FACE_OUT])
    draw_raypath_2d(ax, path, preset=PRESET, semantic=seg_style("S"), internal=seg_style("R"), exit=seg_style("H"),
                    arrows=[(0, 0.55), (1, 0.6), (2, 0.6)], markers=True)
    p_in = path.points[1]
    p_ref = p_in + dirs["S'"] * REFLECTED_LEN
    kw = PRESET.line_kwargs(seg_style("S'", 1.6))
    ax.plot([p_in[0], p_ref[0]], [p_in[1], p_ref[1]], zorder=5, **kw)
    draw_arrowhead(ax, p_ref, dirs["S'"], length=PRESET.geom.arrow2d_length, width=PRESET.geom.arrow2d_width,
                   color=kw["color"], z=5)
    for face, name in ((FACE_IN, r"$\mathbf{n}_3$"), (FACE_OUT, r"$\mathbf{n}_5$")):
        f = SECTION.face(face)
        a, b = SECTION.face_vertices(f)
        n = SECTION.normal(f)
        foot = (a + b) / 2 + unit(b - a) * (-0.45 if face == FACE_IN else -0.28)   # 避开面 3 上的入射 / 反射段
        draw_normal(ax, foot, n, 0.35 if face == FACE_IN else 0.55, name,
                    offset=(-0.12, -0.2) if face == FACE_IN else (0.0, 0.0))
    # 每段旁写上它对应的光点名（颜色 = 右栏同名光点）
    mids = {"S": path.points[0] * 0.45 + path.points[1] * 0.55, "R": (path.points[1] + path.points[2]) / 2,
            "H": path.points[2] * 0.4 + path.points[3] * 0.6, "S'": p_in + dirs["S'"] * REFLECTED_LEN * 0.6}
    for key, (dx, dy, ha, va) in {"S": (0.14, 0.08, "left", "bottom"), "R": (-0.5, -0.15, "center", "top"),
                                   "H": (0.25, 0.14, "center", "bottom"), "S'": (0.1, -0.06, "left", "top")}.items():
        name = {"S": r"$\mathbf{S}$", "S'": r"$\mathbf{S}'$", "R": r"$\mathbf{R}$", "H": r"$\mathbf{H}$"}[key]
        annotate_2d(ax, f"{SEGMENT_OF[key]} → {name}", mids[key] + np.array([dx, dy]), preset=PRESET, ha=ha, va=va,
                    semantic=TextStyle(COLORS[key], fontsize=16, family=CJK_SANS))
    finish(ax, *LEFT_LIM)


def right_panel(ax, pts) -> None:
    s, s_ref, r, h, n3, n5 = pts["S"], pts["S'"], pts["R"], pts["H"], pts["n_in"], pts["n_out"]
    draw_circle(ax, 1.0, CIRCLE)
    draw_circle(ax, N_ICE, CIRCLE)
    annotate_2d(ax, "半径 1（空气）", direction(62) * 0.72, preset=PRESET, ha="center", va="center", semantic=TEXT15)
    annotate_2d(ax, f"半径 $n={N_ICE:g}$（冰）", direction(118) * (N_ICE + 0.13), preset=PRESET, ha="center",
                va="center", semantic=TEXT15)
    ax.plot([0], [0], "o", ms=4, color=PRESET.palette["ink"], zorder=9)
    for p in (s, s_ref, r, h):                               # 光点 = 从球心出发的向量（方向 × 折射率）
        draw_line(ax, (0, 0), p, SPOKE, z=2)
    draw_normal(ax, np.array([1.5, 0.7]), n3, 0.35, r"$\mathbf{n}_3$", offset=(0.08, 0.0))
    draw_normal(ax, np.array([1.5, 0.7]), n5, 0.35, r"$\mathbf{n}_5$", offset=(-0.02, 0.02))
    # S'、S、R 所在的那条直线（平行于 n_3）：淡画整条，S → R 这一段是投影箭头
    ext = 0.2
    draw_line(ax, s_ref - n3 * ext, r + n3 * ext, INTERFACE, z=3)
    u = unit(h - r)
    draw_line(ax, r - u * ext, h + u * ext, INTERFACE, z=3)
    gap = 0.07
    draw_arrow(ax, s + unit(r - s) * gap, r - unit(r - s) * gap, "ink", linewidth=2.0, z=7, head=0.7)
    draw_arrow(ax, r + unit(h - r) * gap, h - unit(h - r) * gap, "ink", linewidth=2.0, z=7, head=0.7)
    annotate_2d(ax, r"沿 $\mathbf{n}_3$ 投影", (s + r) / 2 + np.array([0.12, -0.1]), preset=PRESET, ha="right",
                va="top", semantic=TextStyle("ink", fontsize=16, family=CJK_SANS))
    annotate_2d(ax, r"沿 $\mathbf{n}_5$ 投影", (r + h) / 2 + np.array([0.12, 0.0]), preset=PRESET, ha="left",
                va="center", semantic=TextStyle("ink", fontsize=16, family=CJK_SANS))
    labels = {"S": ((-0.05, 0.08), "right", "bottom"), "S'": ((0.0, 0.1), "center", "bottom"),
              "R": ((0.08, -0.08), "left", "top"), "H": ((-0.1, 0.05), "right", "bottom")}
    for key, p in (("S", s), ("S'", s_ref), ("R", r), ("H", h)):
        off, ha, va = labels[key]
        name = {"S": r"$\mathbf{S}$", "S'": r"$\mathbf{S}'$", "R": r"$\mathbf{R}$", "H": r"$\mathbf{H}$"}[key]
        draw_point(ax, p, COLORS[key])
        annotate_2d(ax, f"{name} {SEGMENT_OF[key]}", p + np.array(off), preset=PRESET, ha=ha, va=va,
                    semantic=TextStyle(COLORS[key], fontsize=16, family=CJK_SANS))
    annotate_2d(ax, r"光点 = 光线反方向 × 折射率；$\mathbf{S},\mathbf{S}',\mathbf{R}$ 共线于 $\mathbf{n}_3$",
                (-1.4, -1.55), preset=PRESET, ha="left", va="center", semantic=TEXT15)
    annotate_2d(ax, r"$\mathbf{S}\to\mathbf{R}\to\mathbf{H}$：两次沿法线投影，合成 $W$", (-1.4, -1.78), preset=PRESET,
                ha="left", va="center", semantic=TEXT15)
    finish(ax, *RIGHT_LIM)


def main() -> None:
    fig = matplotlib.pyplot.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    axes = []
    for box, title in ((LEFT_BOX, "真实光路 3-5：三段光线"), (RIGHT_BOX, "同心圆：光点与两次投影")):
        ax = fig.add_axes(box)
        ax.set_axis_off()
        fig.text(box[0] + box[2] / 2, box[1] / 2, title, ha="center", va="center", family=CJK_SANS,
                 **{k: v for k, v in PRESET.text_kwargs("panel_title").items() if k != "family"})
        axes.append(ax)
    path, dirs = raypath_35()
    left_panel(axes[0], path, dirs)
    right_panel(axes[1], concentric_points(dirs["S"]))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
