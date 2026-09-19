# 产出 ../img/direction_scan.png（图 4「方向扫描与走廊投影求交」）：
#   左：光路 `3-4-5-7`（与图 1 同一条走廊，这里看三维）在六方柱里展开成的光走廊——真实晶体 + 两个幽灵，走廊的四个面（3、幽灵 4、
#       幽灵 5、幽灵 7）高亮，一条固定方向 d 的直线（蓝）穿过全部四个面；
#   右：把这四个面沿 d 正交投影到与 d 垂直的平面上，四个多边形（按面号取色）的公共交集涂色——直线本身投影成交集里的一个点。
# 交集由 lumice_integral.geometry.feasibility.corridor_intersection（枚举器判可行性用的同一份实现）算出，不是画出来「看着像」。
# 读者要看出：「找一条穿过所有面的直线」= 「固定一个方向，看各面的投影有没有公共内点」；有交集 ⇒ 这个方向可行，交集的面积就是
# 这个方向附近能通过的「窗口」大小；扫遍所有方向得到的可行方向集就是 Φ 的定义域。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from lumice_integral.geometry.feasibility import corridor_intersection, corridor_polygons, perp_bases
from matplotlib.patches import Polygon as MplPolygon

from halo_notes.draw import (PRESETS, Camera, Corridor, HexPrism, draw_raypath, finish, frame, render_corridor,
                             rotation_from_frames, solve_raypath)
from halo_notes.draw.geometry import unit
from dataclasses import replace

from halo_notes.draw.style import FACE_COLORS, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

OUT = Path(__file__).resolve().parent.parent / "img" / "direction_scan.png"
WIDTH, HEIGHT, DPI = 2400, 1200, 200
LEFT_W = 0.6                                    # 左栏占画幅宽度比例
CAMERA = Camera(azimuth=53, elevation=38, distance=14)   # 俯视偏斜：三个六边形像图 1 那样铺在水平面上，走廊横穿画面
PATHS = {"3-4-5-7": [3, 4, 5, 7]}
PRESET = PRESETS["default"]
PRESET = PRESET.replace(geom=replace(PRESET.geom, cone_length=0.26, cone_radius=0.095))   # 晶体只有 a=1、h=0.8，锥体按比例收小
FONTS = ("Helvetica Neue", *CJK_SANS)
LABEL = TextStyle("ink", fontsize=15, family=FONTS)
LABEL_SOFT = TextStyle("ink_soft", fontsize=12.5, family=FONTS)


def direction(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def main() -> None:
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PRESET.palette["background"])
    ax3 = fig.add_axes([0, 0, LEFT_W, 1])
    ax2 = fig.add_axes([LEFT_W, 0, 1 - LEFT_W, 1])
    for ax in (ax3, ax2):
        ax.set_axis_off()

    # ---- 左：三维走廊 ----
    prism = HexPrism(1.0, 0.8)
    faces = PATHS["3-4-5-7"]
    # c 轴保持竖直（不摆姿态）：走廊全是侧面事件，幽灵沿水平面铺开，与图 1 的俯视图是同一布局
    crystal = prism
    path = solve_raypath(crystal, faces, prefer_direction=direction(160, 12),
                         prefer_point=crystal.centroid(crystal.face(3)) + np.array([0, 0, 0.1]),
                         tail=PRESET.geom.incident_tail, head=PRESET.geom.exit_head)
    corridor = Corridor(crystal, path)
    chain = render_corridor(ax3, crystal, path, camera=CAMERA, preset=PRESET, ghost_crystal=False)   # 真实晶体实体、幽灵线框，读者分得清哪个是真的
    assert len(chain) == 3
    draw_raypath(ax3, corridor.straight, chain[-1], camera=CAMERA, preset=PRESET, semantic="ray_unfolded")
    xlim, ylim = frame(CAMERA, [c.vertices for c in chain] + [corridor.straight.points], WIDTH * LEFT_W, HEIGHT, margin=0.1)
    finish(ax3, xlim, ylim)
    d = unit(corridor.straight.points[2] - corridor.straight.points[1])          # 展开直线的内部方向 = 固定的扫描方向
    tip = CAMERA.project_xy(corridor.straight.points[-1])[0]
    ax3.text(tip[0], tip[1] + 0.25, "固定一个方向 d", ha="center", va="bottom", **PRESET.text_kwargs(LABEL))

    # ---- 右：沿 d 投影四个走廊面，求公共交集 ----
    polys, _ = corridor_polygons(crystal, faces)
    assert len(polys) == len(faces)
    u, w = perp_bases(d[None, :])
    proj = [np.column_stack([p @ u[0], p @ w[0]]) for p in polys]
    inter = corridor_intersection(polys, d[None, :])
    cut = inter.points[0, :inter.count[0]]
    area = float(inter.area()[0])
    assert cut.shape[0] >= 3 and area > 0, (cut.shape, area)
    # 直线本身投影成一个点：取入射点
    p0 = corridor.straight.points[1]
    dot = np.array([p0 @ u[0], p0 @ w[0]])
    # 该点必须落在交集内部（凸多边形：对每条逆时针边都在左侧）
    q = np.roll(cut, -1, axis=0)
    assert np.all((q[:, 0] - cut[:, 0]) * (dot[1] - cut[:, 1]) - (q[:, 1] - cut[:, 1]) * (dot[0] - cut[:, 0]) > 0)

    for face_number, poly in zip(faces, proj):
        color = PRESET.palette[FACE_COLORS[face_number]]
        ax2.add_patch(MplPolygon(poly, closed=True, facecolor=color, alpha=0.12, edgecolor="none", zorder=2))
        ax2.add_patch(MplPolygon(poly, closed=True, facecolor="none", edgecolor=color, linewidth=1.6, zorder=3))
        c = poly.mean(axis=0)
        ax2.text(c[0], c[1], str(face_number), ha="center", va="center", zorder=6,
                 **PRESET.text_kwargs(TextStyle(FACE_COLORS[face_number], fontsize=14, family=FONTS)))
    ax2.add_patch(MplPolygon(cut, closed=True, facecolor=PRESET.palette["highlight"], alpha=0.9, edgecolor=PRESET.palette["ink"],
                             linewidth=1.2, zorder=4))
    ax2.plot([dot[0]], [dot[1]], "o", ms=5, color=PRESET.palette["accent_cool"], zorder=7)
    all_pts = np.vstack(proj)
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    cx, cy = (lo + hi) / 2
    span = (hi - lo).max() * 1.7
    aspect = (WIDTH * (1 - LEFT_W)) / HEIGHT
    wspan, hspan = (span * aspect, span) if aspect >= 1 else (span, span / aspect)
    finish(ax2, (cx - wspan / 2, cx + wspan / 2), (cy - hspan / 2, cy + hspan / 2))
    ax2.text(cx, cy + hspan * 0.42, "沿 d 看过去：四个面的投影", ha="center", va="top", **PRESET.text_kwargs(LABEL))
    ax2.annotate("公共交集：确实有\n这条直线就落在里面", xy=dot, xytext=(cx - wspan * 0.42, cy - hspan * 0.40),
                 ha="left", va="bottom", **PRESET.text_kwargs(LABEL_SOFT),
                 arrowprops=dict(arrowstyle="-", color=PRESET.palette["ink"], lw=0.8, shrinkA=0, shrinkB=4))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}  (intersection area {area:.3f}, direction {np.round(d, 3)})")


if __name__ == "__main__":
    main()
