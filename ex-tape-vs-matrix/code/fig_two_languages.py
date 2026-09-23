# 产出 ../img/two_languages.png（番外图 3「`3-5` 和 `3-4-5-7` 的语言对照」）。数据只读 ../data/crosscheck_a_*.csv（互证 A 的产出），
# 不重算光点；只做读取、坐标换算与绘图。三块：
# (a) `3-5`（M = I，Φ = W）：A60-12 组 1000 个随机姿态 × 太阳方向里可达的全部样本，按各自的太阳画在「以太阳为心」的极坐标上
#     （半径 = 到太阳的角距 Δ，方位 = 从太阳量起的 bearing τ，crosscheck_bridge.s_centered）。空心圈 = Tape 两次平行投影，
#     实心点 = 本系列 H = −RΦ(−R⁻¹S)；每一对都重合。
# (b) 片晶 `3-4-5-7`：以天顶为心的天空图（半径 = 天顶角，方位 = 方位角；太阳都在方位 0°）。灰点 = `3-5` 光点 H_35（由 CSV 的
#     Rule 1 列反转 zrot(−120°) 得到），整体绕天顶转 120°（Rule 1）得空心圈，与本系列真值 H_3457（实心点）重合。
# (c) 柱晶 `3-4-5-7`：同一张天空图。强行绕天顶转 120° 的空心圈与真值实心点分离（细线连起每一对）；真值是 H_35 绕水平的
#     晶体 c 轴 R·c 转 120°（RMR⁻¹，本系列的共轭式），单测逐点核对。
# 读者要看出：(a) 两套语言同一个点；(b) 片晶下 Rule 1 恰好恢复 M；(c) 柱晶下同一 Rule 1 不再适用，而本系列的共轭式仍成立。
# 图上不标任何精度数字（issue 硬约束）；刻度圈只标角度，用来读位置。
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from crosscheck_bridge import s_centered
from halo_notes.draw import PRESETS, annotate_2d, finish, multi_panel
from halo_notes.draw.scene2d import draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from tape_halo_function import zrot

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE.parent / "img" / "two_languages.png"
WIDTH, HEIGHT, DPI = 3600, 1500, 200

PATHS: dict = {}   # 本图没有光路，只有天球上的光点
PRESET = PRESETS["default"]
FILES = {"a": "crosscheck_a_A60-12.csv", "b": "crosscheck_a_A60-10_plate.csv", "c": "crosscheck_a_A60-10_column_negative.csv"}
TAPE_COLS = {"a": ("Hx_tape", "Hy_tape", "Hz_tape"), "b": ("Hx_rule1", "Hy_rule1", "Hz_rule1"),
             "c": ("Hx_rule1", "Hy_rule1", "Hz_rule1")}
MATRIX_COLS = ("Hx_matrix", "Hy_matrix", "Hz_matrix")
FOLD_DEG = 120.0
A_RINGS = (20, 40, 60)                  # (a) 到太阳角距的刻度圈（度）
SKY_RINGS = (30, 60, 90, 120, 150)      # (b)(c) 天顶角刻度圈（度）；90° = 地平
A_LIM, SKY_LIM = 72.0, 172.0
TAPE_COLOR, MATRIX_COLOR, BASE_COLOR, SUN_COLOR = "accent_warm", "accent_cool", "cloud", "sample_2"
GRID = LineStyle("ink_faint", linewidth=0.8)
HORIZON = LineStyle("ink_soft", linewidth=1.2, linestyle="--")
PAIR = LineStyle("ink_soft", linewidth=0.6, alpha=0.5)
TEXT14 = TextStyle("ink_soft", fontsize=13, family=CJK_SANS)
TEXT15 = TextStyle("ink", fontsize=15, family=CJK_SANS)


def load(group: str) -> dict[str, np.ndarray]:
    """读一组互证 CSV，只留两侧都可达的行：``tape`` / ``matrix`` 两侧光点 (K, 3)，外加该组自己的列（浮点）。"""
    with open(DATA / FILES[group], newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["reach_matrix"] == "1" and r["reach_tape"] == "1"]
    out = {k: np.array([float(r[k]) for r in rows]) for k in rows[0] if k not in ("i",)}
    out["tape"] = np.array([[float(r[k]) for k in TAPE_COLS[group]] for r in rows])
    out["matrix"] = np.array([[float(r[k]) for k in MATRIX_COLS] for r in rows])
    return out


def h35_from_rule1(h_rule1: np.ndarray) -> np.ndarray:
    """CSV 的 Rule 1 列 = zrot(120°)·H_35（Tape 侧幻日光点）；反转得 H_35 本身（纯坐标换算，不重算光点）。"""
    return h_rule1 @ zrot(-FOLD_DEG).T


def sun_polar(S: np.ndarray, H: np.ndarray) -> np.ndarray:
    """以太阳为心的平面坐标：半径 Δ、方位 τ（τ = 0 朝上、顺时针为正，与 s_centered 同约定）。"""
    out = []
    for s, h in zip(S, H):
        delta, tau = s_centered(s, h)
        t = np.deg2rad(tau)
        out.append([delta * np.sin(t), delta * np.cos(t)])
    return np.array(out)


def sky_polar(H: np.ndarray) -> np.ndarray:
    """以天顶为心的平面坐标：半径 = 天顶角、方位 = 方位角（逆时针，太阳在方位 0° = +x）。绕天顶转 = 整张图转。"""
    zen = np.degrees(np.arccos(np.clip(H[:, 2], -1, 1)))
    az = np.arctan2(H[:, 1], H[:, 0])
    return np.stack([zen * np.cos(az), zen * np.sin(az)], axis=1)


def rings(ax, radii, labels_at_deg: float, lim: float, horizon: float | None = None) -> None:
    th = np.linspace(0, 2 * np.pi, 361)
    for r in radii:
        style = HORIZON if r == horizon else GRID
        ax.plot(r * np.cos(th), r * np.sin(th), zorder=1, **PRESET.line_kwargs(style))
        p = r * np.array([np.cos(np.deg2rad(labels_at_deg)), np.sin(np.deg2rad(labels_at_deg))])
        annotate_2d(ax, f"{r}°", p, preset=PRESET, ha="left", va="bottom", semantic=TEXT14)
    finish(ax, (-lim, lim), (-lim, lim))


def pairs(ax, tape_xy, matrix_xy, *, link: bool) -> None:
    if link:
        for p, q in zip(tape_xy, matrix_xy):
            ax.plot([p[0], q[0]], [p[1], q[1]], zorder=2, **PRESET.line_kwargs(PAIR))
    ax.plot(tape_xy[:, 0], tape_xy[:, 1], "o", ms=11, mfc="none", mec=PRESET.palette[TAPE_COLOR], mew=1.6, zorder=4)
    ax.plot(matrix_xy[:, 0], matrix_xy[:, 1], "o", ms=4.2, color=PRESET.palette[MATRIX_COLOR], zorder=5)


def legend(ax, items, x0: float, y0: float, dy: float) -> None:
    for i, (kind, text) in enumerate(items):
        y = y0 - i * dy
        if kind == "tape":
            ax.plot([x0], [y], "o", ms=11, mfc="none", mec=PRESET.palette[TAPE_COLOR], mew=1.6)
        elif kind == "matrix":
            ax.plot([x0], [y], "o", ms=4.2, color=PRESET.palette[MATRIX_COLOR])
        elif kind == "sun":
            ax.plot([x0], [y], "*", ms=9, color=PRESET.palette[SUN_COLOR])
        elif kind == "base":
            ax.plot([x0], [y], "o", ms=4.0, color=PRESET.palette[BASE_COLOR])
        annotate_2d(ax, text, (x0 + dy * 0.6, y), preset=PRESET, ha="left", va="center", semantic=TEXT15)


def sky_common(ax, d: dict) -> np.ndarray:
    """(b)(c) 共用：刻度圈、天顶、各样本的太阳、H_35 灰点、Rule 1 的 120° 旋转弧；返回 H_35 的平面坐标。"""
    rings(ax, SKY_RINGS, -38.0, SKY_LIM, horizon=90)
    ax.plot([0], [0], "+", ms=10, mew=1.4, color=PRESET.palette["ink"], zorder=6)
    annotate_2d(ax, "天顶", (4, -4), preset=PRESET, ha="left", va="top", semantic=TEXT14)
    annotate_2d(ax, "地平", (90 * np.cos(np.deg2rad(-100)), 90 * np.sin(np.deg2rad(-100))), preset=PRESET,
                ha="right", va="bottom", semantic=TEXT14)
    zen_sun = 90.0 - d["sigma_deg"]
    ax.plot(zen_sun, np.zeros_like(zen_sun), "*", ms=9, color=PRESET.palette[SUN_COLOR], zorder=3)
    h35 = sky_polar(h35_from_rule1(d["tape"]))
    ax.plot(h35[:, 0], h35[:, 1], "o", ms=4.0, color=PRESET.palette[BASE_COLOR], zorder=3)
    # Rule 1：绕天顶转 120°（整张图逆时针转 120°）
    r = 42.0
    th = np.deg2rad(np.linspace(12.0, FOLD_DEG - 6.0, 64))
    kw = PRESET.line_kwargs(LineStyle("ink_soft", linewidth=1.6))
    ax.plot(r * np.cos(th), r * np.sin(th), zorder=2, solid_capstyle="round", **kw)
    tip = r * np.array([np.cos(th[-1]), np.sin(th[-1])])
    draw_arrowhead(ax, tip, np.array([-np.sin(th[-1]), np.cos(th[-1])]), length=6.0, width=4.0, color=kw["color"], z=2)
    annotate_2d(ax, "Rule 1：绕天顶转 120°", (-6.0, r + 5.0), preset=PRESET, ha="center", va="bottom",
                semantic=TEXT14, bbox=dict(boxstyle="round,pad=0.15", fc=PRESET.palette["background"], ec="none", alpha=0.85))
    return h35


def panel_a(ax) -> None:
    d = load("a")
    S = np.stack([d["Sx"], d["Sy"], d["Sz"]], axis=1)
    rings(ax, A_RINGS, 60.0, A_LIM)
    ax.plot([0], [0], "*", ms=16, color=PRESET.palette[SUN_COLOR], zorder=6)
    annotate_2d(ax, "太阳", (3, -3), preset=PRESET, ha="left", va="top", semantic=TEXT14)
    pairs(ax, sun_polar(S, d["tape"]), sun_polar(S, d["matrix"]), link=False)
    legend(ax, [("tape", "Tape：两次平行投影"), ("matrix", r"本系列：$\mathbf{H}=-R\,\Phi(-R^{-1}\mathbf{S})$")],
           -68, -54, 8.0)
    annotate_2d(ax, "各样本以自己的太阳为心：半径 = 到太阳的角距", (-68, 68), preset=PRESET, ha="left", va="top",
                semantic=TEXT14)


def panel_b(ax) -> None:
    d = load("b")
    sky_common(ax, d)
    pairs(ax, sky_polar(d["tape"]), sky_polar(d["matrix"]), link=False)
    legend(ax, [("sun", "太阳（各样本，方位 0°）"), ("base", "3-5 光点（幻日）"), ("tape", "Tape + Rule 1：绕竖直轴转 120°"),
                ("matrix", "本系列真值 3-4-5-7")], -165, -116, 14.0)


def panel_c(ax) -> None:
    d = load("c")
    sky_common(ax, d)
    pairs(ax, sky_polar(d["tape"]), sky_polar(d["matrix"]), link=True)
    legend(ax, [("sun", "太阳（各样本，方位 0°）"), ("base", "3-5 光点"), ("tape", "强行绕竖直轴转 120°"),
                ("matrix", "本系列真值：绕水平 c 轴转 120°")], -165, -116, 14.0)


def main() -> None:
    titles = ["(a) `3-5`：两种语言，同一个点", "(b) 片晶 `3-4-5-7`：绕竖直轴转 120°", "(c) 柱晶 `3-4-5-7`：绕水平轴转 120°"]
    fig, axes = multi_panel(1, 3, WIDTH, HEIGHT, DPI, preset=PRESET, title_frac=0.1,
                            titles=[t.replace("`", "") for t in titles])
    for ax in axes[0]:
        for t in ax.texts:
            t.set_fontfamily(CJK_SANS)
            t.set_fontsize(22)
    panel_a(axes[0][0])
    panel_b(axes[0][1])
    panel_c(axes[0][2])
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
