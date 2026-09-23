# 产出 ../img/kaleidoscope_and_spheres.png（番外图 1「万花筒与同心球」）。
# 左栏：改绘 Tricker 1973 Fig. 4（p.3–4）的逐次镜像。沿晶体轴 R 俯视：六棱柱截面（面 3–8，n_3 = +x），六个侧面平移到过
# 晶体轴，成为三面镜（六个半平面 RA…RF，A 在 30°、逆时针每 60° 一个）。太阳 S_0 及其逐次镜像落在以 R 为极、过太阳的小圆上
#（俯视就是一个圆）。编号照 Tricker 原文：S_3 = S_0 关于 RB 的像、S_1 = S_3 关于 RC 的像；S_7 = S_0 关于 RA、S_2 = S_7 关于 RF；
# S_5 = S_1 关于 RD = S_2 关于 RE。一次 / 两次 / 三次反射三种语义色；每支弧箭头从源像走到新像，弧的中点正好跨过所用那面镜；
# 再标出 Tricker 的 ∠S_0RS_1 = ∠S_0RS_2 = 120°。
# 右栏：改绘 TM2006 Fig. 4.5（p.48）的同心天球截面。半径 1（空气）与 n（冰）两个同心圆；光点 = 光线反方向 × 介质折射率。
# 第一次折射（面 3，法向 n_3 = +x）：入射 S、反射 S'、折射 R 三点共线于一条平行于 n_3 的直线；第二次折射（面 5，法向 n_5）
# 把 R 沿 n_5 投回半径 1 的圆，得出射光点 H。两次投影合起来就是 W。
# 读者要看出：左——连续镜像合并成一个 M；右——折射就是沿法线的平行投影，两次合成 W。
# 取值：太阳方位 φ_0 = 70°（避开镜面 30°/90°/… 与面法向 0°/60°/…；六个像互不重叠）；右栏入射取 60° 楔的最小偏折对称入射
#（内部光线与两面法向各夹 30°），只为让两段投影都清楚可见，不承载数值结论。所有点由矩阵 / concentric_projection 算出，不手摆。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (FACE_COLORS, PRESETS, CrossSection, annotate_2d, concentric_projection, draw_flip_axis, finish,
                             multi_panel, render_section)
from halo_notes.draw.geometry import unit
from halo_notes.draw.raypath import N_ICE
from halo_notes.draw.scene2d import draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.math import reflection_group as rg

OUT = Path(__file__).resolve().parent.parent / "img" / "kaleidoscope_and_spheres.png"
WIDTH, HEIGHT, DPI = 3000, 1560, 200

PATHS: dict = {}   # 本图没有追迹光路：左栏是镜像点，右栏是光点投影
PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(face_number_colors=FACE_COLORS))
SECTION = CrossSection(1.0)

# ---- 左栏：Tricker 1973 的万花筒 ----
PLANES = {"A": 30.0, "B": 90.0, "C": 150.0, "D": 210.0, "E": 270.0, "F": 330.0}   # 半平面方位角（过晶体轴 R = z）
PHI0_DEG = 70.0          # 太阳方位角
POLAR_DEG = 40.0         # 太阳到晶体轴的角距（小圆的角半径；俯视图只用到方位，这个值只进 3D 验算）
# (新像, 源像, 所用半平面, 反射次数)：Tricker 1973 p.4 原文的编号与构造顺序
STEPS = [("S3", "S0", "B", 1), ("S1", "S3", "C", 2), ("S7", "S0", "A", 1), ("S2", "S7", "F", 2),
         ("S5", "S1", "D", 3), ("S5", "S2", "E", 3)]
CIRCLE_R = 2.0           # 俯视图里小圆的画面半径
ARC_R = 2.32             # 弧箭头的半径（圆外一圈）
ARC_GAP_DEG = 4.0        # 弧箭头起点离开源像的角度
AXIS_HALF, PLANE_LABEL_AT = 2.75, 2.98
ANGLE_R = 1.38           # 120° 角标半径（六边形与小圆之间）
LEFT_LIM = ((-3.82, 3.82), (-3.55, 3.9))    # 两栏取景宽高比 = 面板格子宽高比（≈1.026），两栏标题才等高
ORDER_COLORS = {0: "accent_warm", 1: "sample_1", 2: "sample_2", 3: "sample_3"}
ORDER_NAMES = {0: "太阳", 1: "一次反射", 2: "两次反射", 3: "三次反射"}

# ---- 右栏：TM2006 的同心圆 ----
FACE_IN, FACE_OUT = 3, 5
INTERNAL_DEG = 150.0     # 冰内光线方向：与 -n_3（180°）、n_5（120°）各夹 30°——60° 楔的对称（最小偏折）入射
RIGHT_LIM = ((-1.85, 2.15), (-2.0, 1.9))
CHORD = LineStyle("ink", linewidth=1.3)
CHORD2 = LineStyle("ink", linewidth=1.3, linestyle="--")
CIRCLE = LineStyle("ink_soft", linewidth=1.4)
SMALL_CIRCLE = LineStyle("ink_soft", linewidth=1.2, linestyle="--")
SPOKE = LineStyle("ink_faint", linewidth=0.9)
INTERFACE = LineStyle("ink", linewidth=2.2)
TEXT15 = TextStyle("ink", fontsize=15, family=CJK_SANS)


def direction(deg: float) -> np.ndarray:
    return np.array([np.cos(np.deg2rad(deg)), np.sin(np.deg2rad(deg))])


def azimuth(v) -> float:
    return float(np.degrees(np.arctan2(v[1], v[0])))


def kaleidoscope_images(phi0_deg: float = PHI0_DEG, polar_deg: float = POLAR_DEG) -> dict[str, tuple[np.ndarray, int]]:
    """三维太阳方向 S_0 与 Tricker 的逐次镜像：名字 → (单位向量, 反射次数)。半平面 RX 所在的镜面 = 过 z 轴、方位 PLANES[X]
    的平面，反射矩阵用 ``reflection_group.sxy``（与 ch7 同一个权威实现）。S_5 由两条路各算一次，必须重合。"""
    t, p = np.deg2rad(polar_deg), np.deg2rad(phi0_deg)
    images = {"S0": (np.array([np.sin(t) * np.cos(p), np.sin(t) * np.sin(p), np.cos(t)]), 0)}
    for new, src, plane, order in STEPS:
        v = rg.sxy(PLANES[plane]) @ images[src][0]
        if new in images:
            assert np.allclose(v, images[new][0], atol=1e-12), (new, src, plane)
            continue
        images[new] = (v, order)
    return images


def concentric_points() -> dict[str, np.ndarray]:
    """右栏的光点：S（入射）/ S'（反射）/ R（折射，半径 n）/ H（出射，半径 1）与两面法向。光点 = −光线方向 × 折射率。"""
    n_in, n_out = direction(0.0), direction(120.0)      # 面 3 / 面 5 外法向（ch3 约定：n_3 = +x，逆时针每 60° 一面）
    d_inside = direction(INTERNAL_DEG)
    # 冰内方向由 Snell 反推入射方向：切向分量守恒，|切向| = n·sin(内角)
    first_back = concentric_projection(-N_ICE * d_inside, n_in, 1.0)
    s = first_back.refracted
    first = concentric_projection(s, n_in, N_ICE)
    second = concentric_projection(first.refracted, n_out, 1.0)
    return {"S": first.incident, "S'": first.reflected, "R": first.refracted, "H": second.refracted,
            "n_in": first.normal, "n_out": second.normal}


def draw_line(ax, a, b, style: LineStyle, z: float = 4) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], solid_capstyle="round", zorder=z, **PRESET.line_kwargs(style))


def draw_circle(ax, r: float, style: LineStyle, center=(0.0, 0.0), z: float = 3) -> None:
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(center[0] + r * np.cos(th), center[1] + r * np.sin(th), zorder=z, **PRESET.line_kwargs(style))


def draw_arc_arrow(ax, r: float, start_deg: float, end_deg: float, color: str, *, both: bool = False,
                   linewidth: float = 1.5) -> None:
    """以原点为心、从 ``start_deg`` 走到 ``end_deg`` 的弧，末端（``both`` 时两端）带实心三角。"""
    geom = PRESET.geom
    L, W = geom.arrow2d_length, geom.arrow2d_width
    th = np.deg2rad(np.linspace(start_deg, end_deg, 96))
    arc = r * np.stack([np.cos(th), np.sin(th)], axis=1)
    step = r * abs(th[1] - th[0])
    cut = int(np.ceil(L / step))
    lo = cut if both else 0
    ax.plot(arc[lo:len(arc) - cut, 0], arc[lo:len(arc) - cut, 1], color=PRESET.palette[color], linewidth=linewidth,
            solid_capstyle="round", zorder=5)
    sgn = np.sign(end_deg - start_deg)
    ends = [(arc[-1], th[-1], sgn)] + ([(arc[0], th[0], -sgn)] if both else [])
    for tip, t, s in ends:
        tangent = np.array([-np.sin(t), np.cos(t)]) * s
        draw_arrowhead(ax, tip, tangent, length=L, width=W, color=PRESET.palette[color], z=5)


def draw_point(ax, xy, color: str, size: float = 11.0, z: float = 8) -> None:
    ax.plot([xy[0]], [xy[1]], "o", ms=size, color=PRESET.palette[color], markeredgecolor=PRESET.palette["background"],
            markeredgewidth=1.4, zorder=z)


def sub_label(name: str) -> str:
    return f"$S_{name[1:]}$"


def left_panel(ax) -> None:
    images = kaleidoscope_images()
    render_section(ax, SECTION, preset=PRESET, face_numbers=True)
    c = np.zeros(2)
    for letter, deg in PLANES.items():
        if deg < 180:                                   # 一面镜 = 两个相对的半平面，整条线只画一次
            draw_flip_axis(ax, c, direction(deg), AXIS_HALF, preset=PRESET)
        annotate_2d(ax, letter, direction(deg) * PLANE_LABEL_AT, preset=PRESET, ha="center", va="center",
                    semantic=TextStyle("ink_soft", fontsize=17, weight="bold"))
    draw_circle(ax, CIRCLE_R, SMALL_CIRCLE)
    ax.plot([0], [0], "o", ms=5, color=PRESET.palette["ink"], zorder=9)
    annotate_2d(ax, "$R$", (0.1, -0.2), preset=PRESET, ha="left", va="center", semantic=TextStyle("ink", fontsize=17))
    az = {k: azimuth(v) for k, (v, _) in images.items()}
    # 弧箭头：源像 → 新像；弧中点就是所用镜面（镜像的方位 = 2·镜面 − 源），颜色取新像的反射次数
    for new, src, plane, order in STEPS:
        a0, a1 = az[src], az[new]
        mid = PLANES[plane]
        while a1 - a0 > 180:
            a1 -= 360
        while a1 - a0 < -180:
            a1 += 360
        assert np.isclose((a0 + a1) / 2 % 360, mid % 360, atol=1e-9), (new, src, plane)
        a0 += np.sign(a1 - a0) * ARC_GAP_DEG           # 起点离开源像一点：同一源像发出的两支弧不连成一条
        draw_arc_arrow(ax, ARC_R, a0, a1, ORDER_COLORS[order])
    # 120°：∠S_0RS_1 与 ∠S_0RS_2（Tricker 1973 p.4）
    for k in ("S1", "S2"):
        draw_line(ax, c, direction(az[k]) * CIRCLE_R, SPOKE, z=2)
    draw_line(ax, c, direction(az["S0"]) * CIRCLE_R, SPOKE, z=2)
    for k in ("S1", "S2"):
        a1 = az[k]
        while a1 - az["S0"] > 180:
            a1 -= 360
        while a1 - az["S0"] < -180:
            a1 += 360
        draw_arc_arrow(ax, ANGLE_R, az["S0"], a1, "ink_soft", both=True, linewidth=1.0)
        m = (az["S0"] + a1) / 2
        annotate_2d(ax, "120°", direction(m) * (ANGLE_R + 0.2), preset=PRESET, ha="center", va="center",
                    semantic=TextStyle("ink_soft", fontsize=14),
                    bbox=dict(boxstyle="round,pad=0.12", fc=PRESET.palette["background"], ec="none"))
    for k, (v, order) in images.items():
        p = direction(az[k]) * CIRCLE_R
        draw_point(ax, p, ORDER_COLORS[order])
        annotate_2d(ax, sub_label(k), direction(az[k]) * (CIRCLE_R - 0.36), preset=PRESET, ha="center", va="center",
                    semantic=TextStyle(ORDER_COLORS[order], fontsize=17))
    # 图例
    for i, order in enumerate((0, 1, 2, 3)):
        y = -3.35
        x = -3.6 + i * 1.95
        draw_point(ax, (x, y), ORDER_COLORS[order], size=11)
        annotate_2d(ax, ORDER_NAMES[order], (x + 0.15, y), preset=PRESET, ha="left", va="center", semantic=TEXT15)
    annotate_2d(ax, "沿晶体轴 $R$ 俯视；RA…RF：侧面平移到过 $R$ 的镜面", (-3.6, 3.8), preset=PRESET, ha="left",
                va="top", semantic=TEXT15)
    finish(ax, *LEFT_LIM)


def right_panel(ax) -> None:
    pts = concentric_points()
    s, s_ref, r, h = pts["S"], pts["S'"], pts["R"], pts["H"]
    n_in, n_out = pts["n_in"], pts["n_out"]
    draw_circle(ax, 1.0, CIRCLE)
    draw_circle(ax, N_ICE, CIRCLE)
    annotate_2d(ax, "半径 1（空气）", direction(165) * 0.5, preset=PRESET, ha="center", va="center", semantic=TEXT15)
    annotate_2d(ax, f"半径 $n={N_ICE:g}$（冰）", direction(128) * (N_ICE + 0.16), preset=PRESET, ha="center", va="center",
                semantic=TEXT15)
    ax.plot([0], [0], "o", ms=4, color=PRESET.palette["ink"], zorder=9)
    # 第一次折射的界面（面 3，平移到过球心）+ 法向箭头
    t = np.array([-n_in[1], n_in[0]])
    draw_line(ax, -t * 1.45, t * 1.45, INTERFACE, z=4)
    annotate_2d(ax, "面 3（入射面，平移到过球心）", t * 1.45 + np.array([0.06, 0.0]), preset=PRESET, ha="left", va="top",
                semantic=TEXT15)
    for normal, name, at in ((n_in, r"$\mathbf{n}_3$", np.array([0.0, 0.42])),
                             (n_out, r"$\mathbf{n}_5$", np.array([0.0, 0.42]))):
        tip = at + normal * 0.55
        draw_line(ax, at, tip, LineStyle("ink", linewidth=1.3), z=6)
        draw_arrowhead(ax, tip, normal, length=PRESET.geom.arrow2d_length, width=PRESET.geom.arrow2d_width,
                       color=PRESET.palette["ink"], z=6)
        annotate_2d(ax, name, tip + normal * 0.16, preset=PRESET, ha="center", va="center",
                    semantic=TextStyle("ink", fontsize=16))
    # 两条投影线：S'—S—R 平行于 n_3（实线），R—H 平行于 n_5（虚线），各向外延一点
    ext = 0.25
    draw_line(ax, s_ref - n_in * ext, r + n_in * ext, CHORD, z=5)
    u = unit(h - r)
    draw_line(ax, r - u * ext, h + u * ext, CHORD2, z=5)
    # 从球心到各光点的淡辐条（光点 = 方向 × 半径）
    for p in (s, s_ref, r, h):
        draw_line(ax, (0, 0), p, SPOKE, z=2)
    labels = [(s, r"$\mathbf{S}$", "accent_warm", (0.0, -0.13), "入射", "center", "top"),
              (s_ref, r"$\mathbf{S}'$", "ink_soft", (0.0, -0.13), "反射", "center", "top"),
              (r, r"$\mathbf{R}$", "sample_2", (0.1, -0.1), "折射", "left", "top"),
              (h, r"$\mathbf{H}$", "accent_cool", (0.12, 0.02), "出射", "left", "bottom")]
    for p, name, color, off, word, ha, va in labels:
        draw_point(ax, p, color)
        annotate_2d(ax, f"{name} {word}", p + np.array(off), preset=PRESET, ha=ha, va=va,
                    semantic=TextStyle(color, fontsize=16, family=CJK_SANS))
    annotate_2d(ax, r"$\mathbf{S},\ \mathbf{S}',\ \mathbf{R}$ 共线于 $\mathbf{n}_3$ 方向", (-1.8, -1.62), preset=PRESET,
                ha="left", va="center", semantic=TEXT15)
    annotate_2d(ax, r"$\mathbf{S}\to\mathbf{R}\to\mathbf{H}$：两次沿法线投影 $=W$", (-1.8, -1.86), preset=PRESET,
                ha="left", va="center", semantic=TEXT15)
    finish(ax, *RIGHT_LIM)


def main() -> None:
    fig, axes = multi_panel(1, 2, WIDTH, HEIGHT, DPI, preset=PRESET, title_frac=0.09,
                            titles=["万花筒：逐次镜像合成 $M$", "同心圆：两次投影合成 $W$"])
    for ax in axes[0]:
        for t in ax.texts:
            t.set_fontfamily(CJK_SANS)
    left_panel(axes[0][0])
    right_panel(axes[0][1])
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
