# 产出 ../img/corridor_1_3.png（图 7「`1-3` 走廊的截面」）：h/a = 1、截顶比例 0.5（截断较浅）与 0.8（顶面只剩两成）两个锥晶，
# 过 c 轴、含面 3 法向的截面并排。每个截面只画**一条**代表光线（返工 R1：光线太密不好看）：以「能从柱面 3 折出的方向带」
# （折入后与 c 轴成 90° − θc … θc，θc = arcsin(1/n) 临界角，现场算）正中的角度、从顶面 1 靠左处折入——两档同一相对起点、同一方向：
#   截顶比例 0.5：落在柱面 3 上并折出（蓝）；截顶比例 0.8：顶面收窄、锥面变长，同一条光线先撞上锥面 13（红叉）。
# 整条方向带 × 整条顶面线段的二维扇形（`trace_fan`）不再画出，只留作单测：0.5 时有光落到面 3、0.8 时全撞 13。
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
REP_START = -0.8
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


def _first_hit(planes, o: np.ndarray, d: np.ndarray) -> tuple[np.ndarray, int]:
    """截面内从 o 沿 d 走，第一次碰到的半平面边界：``(交点, 面号)``。"""
    best, face = np.inf, None
    for num, dist, n2 in planes:
        den = n2 @ d
        if den <= 1e-12:
            continue
        t = (dist - n2 @ o) / den
        if 1e-9 < t < best:
            best, face = t, num
    return o + best * d, face


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
            rays.append((o, *_first_hit(planes, o, d)))
    return rays


def representative_ray(tip: float) -> tuple[np.ndarray, np.ndarray, int]:
    """图面上唯一画出的那条光线：从顶面 1 上 REP_START（相对顶面半宽，负 = 远离面 3 的一侧）处、以方向带正中的角度折入
    （两档同一相对起点、同一方向——楔角没变，只是晶体变了）。"""
    p = crystal(tip)
    top = p.h / 2 + p.a * p.c_over_a * p.tip_ratio
    half_top = p.a * (1 - p.tip_ratio) * math.sqrt(3) / 2
    a = math.radians(sum(BAND) / 2)
    o, d = np.array([REP_START * half_top, top]), np.array([math.sin(a), -math.cos(a)])
    return (o, *_first_hit(_edge_faces(p), o, d))


def first_length_90(tip: float) -> int:
    """该档（h/a = 1）90° 族最短代表的字长（`raypaths_<tier>.csv`）。"""
    path = F.DATA / f"raypaths_{ES.tier_label((H_OVER_A, tip))}.csv"
    with path.open() as fp:
        return min(int(r["length"]) for r in csv.DictReader(fp) if r["family"] and float(r["family"]) == 90.0)


def draw_panel(ax, tip: float) -> None:
    p = crystal(tip)
    poly = F.section_polygon(p)
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
        ax.text(*xy, str(num), ha=ha, va="center", fontsize=13, fontweight="bold", color=F.FACE_COLOR[num], **FONT)
    o, e, face = representative_ray(tip)
    color = OPEN_COLOR if face == 3 else BLOCK_COLOR
    ax.annotate("", xy=e, xytext=o, arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0, mutation_scale=14,
                                                    shrinkA=0, shrinkB=0), zorder=5)
    if face == 3:                                  # 从面 3 折出去（Snell，截面内）
        n2 = np.array([1.0, 0.0])
        d = (e - o) / np.linalg.norm(e - o)
        ci = float(d @ n2)
        st = N_ICE * math.sqrt(max(0.0, 1 - ci ** 2))
        out = np.array([math.sqrt(1 - st ** 2), math.copysign(st, d[1])])
        ax.annotate("", xy=e + 0.4 * out, xytext=e, arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0, mutation_scale=14,
                                                                     shrinkA=0, shrinkB=0), zorder=5)
    else:
        ax.plot(e[0], e[1], marker="x", ms=11, mew=2.4, color=color, zorder=6)
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
    fig.text(0.5, 0.025, f"两边是同一条光线：从顶面 1 靠左处折入，与 c 轴成 {sum(BAND) / 2:.0f}°（能从柱面 3 折出的方向带 "
             f"{BAND[0]:.1f}°–{BAND[1]:.1f}° 的正中）", ha="center", va="center", fontsize=10.5, color=PAL["ink_soft"], **FONT)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
