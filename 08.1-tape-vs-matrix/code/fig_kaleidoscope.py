# 产出 ../img/kaleidoscope.png（番外图 1「万花筒」）：改绘 Tricker 1973 Fig. 4（p.3–4）的逐次镜像，拆成四个子图。
# 沿晶体轴 R 俯视：六棱柱截面（面 3–8，n_3 = +x），六个侧面平移到过晶体轴，成为三面镜（六个半平面 RA…RF，A 在 30°、
# 逆时针每 60° 一个）。太阳 S_0 及其逐次镜像落在以 R 为极、过太阳的小圆上（俯视就是一个圆）。编号照 Tricker 原文。
# (a)(b)(c) 每格只做一次镜像：S_0 —RB→ S_3 —RC→ S_1 —RD→ S_5，每格只画当前那面镜、只画当前这一步的一段弧，
# 之前的像淡画作上下文；(d) 合成：四个像一起，标出 Tricker 的 ∠S_0RS_1 = ∠S_0RS_2 = 120°，另一条链（RA→S_7、RF→S_2）淡画。
# 读者要看出：每一次反射就是一次镜像，逐次镜像合起来就是一个 M。
# 取值：太阳方位 φ_0 = 70°（避开镜面 30°/90°/… 与面法向 0°/60°/…；六个像互不重叠）。所有点由反射矩阵算出，不手摆。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import CrossSection, annotate_2d, draw_flip_axis, finish, multi_panel, render_section
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from lumice_integral.symmetry import reflection_group as rg

from _ex_fig import PRESET, SPOKE, TEXT15, azimuth, direction, draw_arc_arrow, draw_circle, draw_line, draw_point, unwrap_to

OUT = Path(__file__).resolve().parent.parent / "img" / "kaleidoscope.png"
WIDTH, HEIGHT, DPI = 4000, 1200, 200
TITLE_FRAC = 0.1

PATHS: dict = {}   # 本图没有追迹光路：画的是镜像点
SECTION = CrossSection(1.0)

PLANES = {"A": 30.0, "B": 90.0, "C": 150.0, "D": 210.0, "E": 270.0, "F": 330.0}   # 半平面方位角（过晶体轴 R = z）
PHI0_DEG = 70.0          # 太阳方位角
POLAR_DEG = 40.0         # 太阳到晶体轴的角距（小圆的角半径；俯视图只用到方位，这个值只进 3D 验算）
# (新像, 源像, 所用半平面, 反射次数)：Tricker 1973 p.4 原文的编号与构造顺序
STEPS = [("S3", "S0", "B", 1), ("S1", "S3", "C", 2), ("S7", "S0", "A", 1), ("S2", "S7", "F", 2),
         ("S5", "S1", "D", 3), ("S5", "S2", "E", 3)]
CHAIN = ["S0", "S3", "S1", "S5"]            # 子图 (a)(b)(c) 逐步推进的那条链
OTHER = ["S7", "S2"]                        # 另一条链：只在 (d) 淡画
# 子图：(标题, 本格做的那一步 = STEPS 下标；None 为合成格)
PANELS = [("(a) 关于 RB 镜像：一次反射", 0), ("(b) 再关于 RC 镜像：两次反射", 1),
          ("(c) 再关于 RD 镜像：三次反射", 4), ("(d) 合成：逐次镜像合成一个 $M$", None)]
CIRCLE_R = 2.0           # 俯视图里小圆的画面半径
ARC_R = 2.34             # 弧箭头的半径（圆外一圈）
ARC_GAP_DEG = 4.0        # 弧箭头起点离开源像的角度
AXIS_HALF, PLANE_LABEL_AT = 2.8, 3.05
ANGLE_R = 1.38           # 120° 角标半径（六边形与小圆之间）
XLIM = (-3.35, 3.35)
YLIM = (-3.55, 3.3)
FAINT_ALPHA = 0.3
ORDER_COLORS = {0: "accent_warm", 1: "sample_1", 2: "sample_2", 3: "sample_3"}
ORDER_NAMES = {0: "太阳", 1: "一次反射", 2: "两次反射", 3: "三次反射"}
FAINT_MIRROR = LineStyle("ink_faint", linewidth=1.0, linestyle="-.")
SMALL_CIRCLE = LineStyle("ink_soft", linewidth=1.2, linestyle="--")


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


def panel_content(k: int) -> dict:
    """第 ``k`` 格画什么：实画的镜面（半平面字母）、弧箭头（STEPS 条目）、实画 / 淡画的像、是否标 120°。出图与单测共用。"""
    step = PANELS[k][1]
    if step is None:
        return {"mirrors": [], "faint_mirrors": ["A", "F"], "arcs": [], "points": CHAIN, "faint_points": OTHER,
                "angles": ["S1", "S2"]}
    new, src, plane, _ = STEPS[step]
    done = CHAIN[:CHAIN.index(new) + 1]
    return {"mirrors": [plane], "faint_mirrors": [], "arcs": [STEPS[step]], "points": [src, new],
            "faint_points": [p for p in done if p not in (src, new)], "angles": []}


def sub_label(name: str) -> str:
    return f"$S_{name[1:]}$"


def draw_image(ax, name: str, az: float, order: int, *, faint: bool = False) -> None:
    alpha = FAINT_ALPHA if faint else 1.0
    draw_point(ax, direction(az) * CIRCLE_R, ORDER_COLORS[order], alpha=alpha)
    t = annotate_2d(ax, sub_label(name), direction(az) * (CIRCLE_R - 0.38), preset=PRESET, ha="center", va="center",
                    semantic=TextStyle(ORDER_COLORS[order], fontsize=18))
    t.set_alpha(alpha)


def draw_panel(ax, k: int, images: dict) -> None:
    spec = panel_content(k)
    az = {name: azimuth(v) for name, (v, _) in images.items()}
    render_section(ax, SECTION, preset=PRESET, face_numbers=True)
    draw_circle(ax, CIRCLE_R, SMALL_CIRCLE)
    ax.plot([0], [0], "o", ms=5, color=PRESET.palette["ink"], zorder=9)
    annotate_2d(ax, "$R$", (0.1, -0.2), preset=PRESET, ha="left", va="center", semantic=TextStyle("ink", fontsize=17))
    for letter in spec["mirrors"]:                    # 当前这面镜：整条镜面线（两个相对半平面）只画一次，标出所用半平面
        draw_flip_axis(ax, np.zeros(2), direction(PLANES[letter]), AXIS_HALF, preset=PRESET)
        annotate_2d(ax, f"R{letter}", direction(PLANES[letter]) * PLANE_LABEL_AT, preset=PRESET, ha="center",
                    va="center", semantic=TextStyle("ink", fontsize=18, weight="bold"))
    for letter in spec["faint_mirrors"]:
        draw_line(ax, np.zeros(2), direction(PLANES[letter]) * AXIS_HALF, FAINT_MIRROR, z=2)
        t = annotate_2d(ax, f"R{letter}", direction(PLANES[letter]) * PLANE_LABEL_AT, preset=PRESET, ha="center",
                        va="center", semantic=TextStyle("ink_soft", fontsize=16, weight="bold"))
        t.set_alpha(0.55)
    for new, src, plane, order in spec["arcs"]:       # 弧箭头：源像 → 新像，弧中点正好跨过所用镜面（镜像方位 = 2·镜面 − 源）
        a0, a1 = az[src], unwrap_to(az[new], az[src])
        assert np.isclose((a0 + a1) / 2 % 360, PLANES[plane] % 360, atol=1e-9), (new, src, plane)
        draw_arc_arrow(ax, ARC_R, a0 + np.sign(a1 - a0) * ARC_GAP_DEG, a1, ORDER_COLORS[order], linewidth=1.8)
    if spec["angles"]:                                # Tricker 1973 p.4：∠S_0RS_1 = ∠S_0RS_2 = 120°
        for name in ["S0", *spec["angles"]]:
            draw_line(ax, np.zeros(2), direction(az[name]) * CIRCLE_R, SPOKE, z=2)
        for name in spec["angles"]:
            a1 = unwrap_to(az[name], az["S0"])
            draw_arc_arrow(ax, ANGLE_R, az["S0"], a1, "ink_soft", both=True, linewidth=1.0)
            annotate_2d(ax, "120°", direction((az["S0"] + a1) / 2) * (ANGLE_R + 0.22), preset=PRESET, ha="center",
                        va="center", semantic=TextStyle("ink_soft", fontsize=15),
                        bbox=dict(boxstyle="round,pad=0.12", fc=PRESET.palette["background"], ec="none"))
        annotate_2d(ax, "两次镜像 $S_0\\to S_1$ = 绕 $R$ 转 $120°$\n三次镜像 $S_0\\to S_5$ = 一面镜", (0.0, -2.72),
                    preset=PRESET, ha="center", va="top", semantic=TEXT15, linespacing=1.5)
    for name in spec["faint_points"]:
        draw_image(ax, name, az[name], images[name][1], faint=True)
    for name in spec["points"]:
        draw_image(ax, name, az[name], images[name][1])
    finish(ax, XLIM, YLIM)


def draw_legend(fig) -> None:
    lg = fig.add_axes([0.0, 1.0 - 0.07, 1.0, 0.07])
    lg.set_axis_off()
    lg.set_xlim(0, 1)
    lg.set_ylim(0, 1)
    for i, order in enumerate((0, 1, 2, 3)):
        x = 0.33 + i * 0.1
        lg.plot([x], [0.45], "o", ms=11, color=PRESET.palette[ORDER_COLORS[order]],
                markeredgecolor=PRESET.palette["background"], markeredgewidth=1.4)
        lg.text(x + 0.008, 0.45, ORDER_NAMES[order], ha="left", va="center", **PRESET.text_kwargs(TEXT15))
    lg.text(0.01, 0.45, "沿晶体轴 $R$ 俯视；RA…RF：侧面平移到过 $R$ 的镜面", ha="left", va="center",
            **PRESET.text_kwargs(TEXT15))


def main() -> None:
    fig, axes = multi_panel(1, len(PANELS), WIDTH, HEIGHT, DPI, preset=PRESET, title_frac=TITLE_FRAC,
                            titles=[t for t, _ in PANELS])
    for ax in axes[0]:
        for t in ax.texts:
            t.set_fontfamily(CJK_SANS)
            t.set_fontsize(22)
    images = kaleidoscope_images()
    for k, ax in enumerate(axes[0]):
        draw_panel(ax, k, images)
    draw_legend(fig)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
