# 产出 ../img/corridor_1_3.png（图 7「`1-3` 走廊的截面」）：h/a = 1、截顶比例 0.5（截断较浅）与 0.8（顶面只剩两成）两个锥晶，
# 过 c 轴、含面 3 法向的截面并排。截面里画从顶面 1 折入的一族光线：只画**能从柱面 3 出射**的方向带——折入后与 c 轴成
# 90° − θc … θc（θc = arcsin(1/n) 临界角，现场算），太平的在面 3 全反射，太陡的到不了面 3——起点铺满整条顶面线段。
#   截顶比例 0.5：一部分光线落在柱面 3 上（直通，蓝），其余先撞锥面 13（红叉）；
#   截顶比例 0.8：顶面收窄、锥面变长，整条方向带全撞在锥面 13 上，一条也到不了面 3。
# 截面内的光线是示意（截面平面内的二维追迹）；机械结论用三维的可行方向集：`admissible_directions(…, (1, 3), …).area_sr`
# 截顶比例 0.5 时 > 0、0.8 时 = 0（单测钉住；同 `halo_notes/math/tests/test_pyramid_signature_data.py` 的见证测试）。
# 右图下方注明该档 90° 族最短代表的字长（读 `data/raypaths_h1_t0.8.csv`，不手填）。
# 读者要看出：楔角没变（面 1 与面 3 仍成 90°），走廊被锥面挡死，46° 晕只剩多次反射的光路。
from __future__ import annotations

import csv
import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

import _ch9_fig as F
import enumerate_signatures as ES
import fig_pyramid_faces as PF
from lumice_integral.geometry import Pyramid, admissible_directions
from lumice_integral.geometry.core import N_ICE
from lumice_integral.geometry.feasibility import LatLonGrid

NAME = "corridor_1_3"
WIDTH, HEIGHT, DPI = 2400, 1300, 200
H_OVER_A = 1.0
TIPS = (0.5, 0.8)
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}
CRIT = math.degrees(math.asin(1 / N_ICE))          # 49.8°
BAND = (90.0 - CRIT, CRIT)                          # 折入后与 −c 的夹角：能在面 3 透射出去的方向带
N_START, N_DIR = 17, 5
OPEN_COLOR, BLOCK_COLOR = PAL["face_4"], PAL["face_3"]


def crystal(tip: float) -> Pyramid:
    return Pyramid(a=1.0, h=H_OVER_A, tip_ratio=tip)


def corridor_area_sr(tip: float, grid: LatLonGrid | None = None) -> float:
    """三维：光路 `1-3` 的可行方向集面积（sr）。"""
    return float(admissible_directions(crystal(tip), (1, 3), grid or LatLonGrid(90, 180), refine_levels=0).area_sr)


def _edge_faces(p: Pyramid) -> list[tuple[int, float, np.ndarray]]:
    """截面（xz 平面）里每个面对应的半平面 (面号, d, 2D 法向)。"""
    out = []
    for f in p.faces:
        n = np.asarray(p.normal(f), float)
        n2 = np.array([n[0], n[2]])
        if np.linalg.norm(n2) < 1e-9 or abs(n[1]) > 1e-9:
            continue
        out.append((f.number, float(n @ p.face_vertices(f)[0]), n2))
    return out


def trace_fan(tip: float) -> list[tuple[np.ndarray, np.ndarray, int]]:
    """截面内从顶面 1 折入的光线：[(起点, 终点, 撞到的面号)]。起点均布在顶面线段上（两端各缩 4%），方向在 BAND 内均布、朝 +x 偏。"""
    p = crystal(tip)
    top = p.h / 2 + p.a * p.c_over_a * p.tip_ratio
    half_top = p.a * (1 - p.tip_ratio) * math.sqrt(3) / 2
    planes = _edge_faces(p)
    rays = []
    for x0 in np.linspace(-half_top, half_top, N_START)[1:-1] * 0.96:
        for a in np.linspace(*BAND, N_DIR):
            d = np.array([math.sin(math.radians(a)), -math.cos(math.radians(a))])
            o = np.array([x0, top])
            best, face = np.inf, None
            for num, dist, n2 in planes:
                den = n2 @ d
                if den <= 1e-12:
                    continue
                t = (dist - n2 @ o) / den
                if 1e-9 < t < best:
                    best, face = t, num
            rays.append((o, o + best * d, face))
    return rays


def first_length_90(tip: float) -> int:
    """该档（h/a = 1）90° 族最短代表的字长（`raypaths_<tier>.csv`）。"""
    path = F.DATA / f"raypaths_{ES.tier_label((H_OVER_A, tip))}.csv"
    with path.open() as fp:
        return min(int(r["length"]) for r in csv.DictReader(fp) if r["family"] and float(r["family"]) == 90.0)


def draw_panel(ax, tip: float) -> None:
    p = crystal(tip)
    poly = PF.section_polygon(p)
    ax.add_patch(Polygon(poly, closed=True, facecolor=PAL["ice"], edgecolor=PAL["ice_edge"], lw=1.4, zorder=1))
    half = p.a * math.sqrt(3) / 2
    z_ring = p.h / 2
    top = z_ring + p.a * p.c_over_a * p.tip_ratio
    half_top = p.a * (1 - p.tip_ratio) * math.sqrt(3) / 2
    # 面 1 与面 3 加粗
    ax.plot([-half_top, half_top], [top, top], color=PAL["ink_soft"], lw=3.2, solid_capstyle="butt", zorder=3)
    ax.plot([half, half], [-z_ring, z_ring], color=PAL["ink_soft"], lw=3.2, solid_capstyle="butt", zorder=3)
    for num, xy, ha in ((1, (0, top + 0.12), "center"), (3, (half + 0.1, 0), "left"),
                        (13, ((half + half_top) / 2 + 0.12, (z_ring + top) / 2 + 0.05), "left")):
        ax.text(*xy, str(num), ha=ha, va="center", fontsize=13, fontweight="bold", color=PF.FACE_COLOR[num], **FONT)
    for o, e, face in trace_fan(tip):
        if face == 3:
            ax.plot([o[0], e[0]], [o[1], e[1]], color=OPEN_COLOR, lw=0.9, alpha=0.75, zorder=4)
        else:
            ax.plot([o[0], e[0]], [o[1], e[1]], color=BLOCK_COLOR, lw=0.7, alpha=0.45, zorder=4)
            ax.plot(e[0], e[1], marker="x", ms=4, mew=1.0, color=BLOCK_COLOR, zorder=5)
    ax.set_xlim(-1.6, 1.9)
    tallest = crystal(max(TIPS))                   # 两图同一比例尺、同一视野：按较高的那个晶体取景
    zt = tallest.h / 2 + tallest.a * tallest.c_over_a * tallest.tip_ratio
    ax.set_ylim(-zt - 0.1, zt + 0.3)
    ax.set_aspect("equal")
    ax.set_axis_off()


def main() -> None:
    open_area, closed_area = (corridor_area_sr(t) for t in TIPS)
    assert open_area > 0 and closed_area == 0, (open_area, closed_area)
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    boxes = [(0.02, 0.2, 0.46, 0.78), (0.52, 0.2, 0.46, 0.78)]
    n_long = first_length_90(TIPS[1])
    titles = [(f"截顶比例 {TIPS[0]:g}", "一部分光从顶面 1 直接走到柱面 3"),
              (f"截顶比例 {TIPS[1]:g}（顶面只剩两成）", f"整条方向带都撞上锥面 13；46° 晕要等到字长 {n_long} 的光路")]
    for b, tip, (t1, t2) in zip(boxes, TIPS, titles):
        ax = fig.add_axes(b)
        draw_panel(ax, tip)
        fig.text(b[0] + b[2] / 2, 0.135, t1, ha="center", va="center", fontsize=13, color=PAL["ink"], **FONT)
        fig.text(b[0] + b[2] / 2, 0.085, t2, ha="center", va="center", fontsize=11, color=PAL["ink_soft"], **FONT)
    fig.text(0.5, 0.025, f"截面内只画能从柱面 3 折出的方向（折入后与 c 轴成 {BAND[0]:.1f}°–{BAND[1]:.1f}°）；"
             "蓝：落在面 3 上，红叉：先撞到锥面 13", ha="center", va="center", fontsize=10.5, color=PAL["ink_soft"], **FONT)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
