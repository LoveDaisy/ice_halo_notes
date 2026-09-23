# 产出 ../img/pyramid_faces.png（图 1「六方锥晶的二十个面及编号」）：参考几何 (h/a, tip_ratio) = (1, 0.5) 的锥晶，三联——
#   左：斜上方看（正交投影），中：斜下方看（方位转 180°、仰角取负），两个视角各自只标**可见**面的编号（`visible_faces` 机械筛选，
#       不手选），两个视角的可见面并集 = 全部 20 面（单测钉住）；编号按四组着色：底面 1/2、柱面 3–8、上锥面 13–18、下锥面 23–28；
#   右：过 c 轴、含面 3 法向的截面（正视），标柱段高 h、截顶比例（锥台在理论锥顶高度的几成处截断，虚线补出被截掉的锥尖）、
#       锥面 13 外法向与 c 轴的夹角——角度现场从几何对象的法向算出，并与 `pyramid_face_angle()` 的闭式值互相核对。
# 读者要看出：面的分组与编号约定；62.0° 是晶格常数比 c/a 定下的几何量，不是可调参数（截面里只有 h 与截顶比例是参数）。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, FancyArrowPatch, Polygon

import _ch9_fig as F
from halo_notes.draw import PRESETS, Camera, frame, render_crystal, visible_faces
from halo_notes.draw.style.geom_style import FaceNumberStyle
from lumice_integral.geometry import Pyramid, pyramid_face_angle

NAME = "pyramid_faces"
WIDTH, HEIGHT, DPI = 2400, 1100, 200
TIER = (1.0, 0.5)                       # 参考几何
VIEWS = {"upper": (20.0, 22.0), "lower": (200.0, -22.0)}   # (方位角, 仰角)：两视角互为对径，可见面互补
PRESET = PRESETS["ice_filled"]
PRESET = PRESET.replace(geom=PRESET.geom.replace(face_number_style=FaceNumberStyle.FLAT, label_hidden_faces=False))
PAL = F.PAL

GROUPS = {                               # 组名 → (面号, 颜色)
    "底面": ((1, 2), PAL["ink_soft"]),
    "柱面": (tuple(range(3, 9)), PAL["face_4"]),
    "上锥面": (tuple(range(13, 19)), PAL["face_3"]),
    "下锥面": (tuple(range(23, 29)), PAL["face_6"]),
}
FACE_COLOR = {f: c for faces, c in GROUPS.values() for f in faces}
SECTION_FACES = (1, 2, 3, 6, 13, 16, 23, 26)   # 过 c 轴、含 +x 的截面切到的面（法向落在 xz 平面内）
FONT = {"family": list(F.CHART_FONTS)}


def crystal() -> Pyramid:
    return Pyramid(a=1.0, h=TIER[0], tip_ratio=TIER[1])


def camera(view: str) -> Camera:
    az, el = VIEWS[view]
    return Camera(azimuth=az, elevation=el, projection="orthographic")


def labelled_faces(view: str, p: Pyramid | None = None) -> tuple[int, ...]:
    """某视角下标了编号的面 = 该视角可见的面（单测：两视角并集 = 全部 20 面）。"""
    p = p or crystal()
    return tuple(sorted(f.number for f in visible_faces(p, camera(view))))


def face_angle_deg(p: Pyramid | None = None) -> float:
    """锥面 13 外法向与 +c 轴的夹角：从几何对象的法向现场算（不是抄 62.0）。"""
    p = p or crystal()
    n = np.asarray(p.normal(p.face(13)), float)
    return float(np.degrees(np.arccos(n[2] / np.linalg.norm(n))))


def section_polygon(p: Pyramid) -> np.ndarray:
    """y = 0 截面（xz 平面）：全部 20 个半平面 n·x ≤ d 限制在 y = 0 上，逐个裁一个大方框（凸多边形，逆时针）。"""
    poly = [np.array(v, float) for v in ((-9, -9), (9, -9), (9, 9), (-9, 9))]
    for f in p.faces:
        n = np.asarray(p.normal(f), float)
        d = float(n @ p.face_vertices(f)[0])
        n2 = np.array([n[0], n[2]])
        if np.linalg.norm(n2) < 1e-12:
            continue
        out: list[np.ndarray] = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            sa, sb = a @ n2 - d, b @ n2 - d
            if sa <= 1e-12:
                out.append(a)
            if (sa <= 1e-12) != (sb <= 1e-12):
                out.append(a + (b - a) * (sa / (sa - sb)))
        poly = out
    return np.array(poly)


def draw_view(ax, p: Pyramid, view: str) -> None:
    cam = camera(view)
    render_crystal(ax, p, camera=cam, preset=PRESET, face_numbers=False)
    for num in labelled_faces(view, p):
        xy = cam.project_xy(p.face_vertices(p.face(num))).mean(axis=0)
        ax.text(xy[0], xy[1], str(num), ha="center", va="center", fontsize=15, fontweight="bold",
                color=FACE_COLOR[num], zorder=20, **FONT)
    xlim, ylim = frame(cam, [p.vertices], 1, 1.25, margin=0.06)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_axis_off()


def draw_section(ax, p: Pyramid) -> None:
    poly = section_polygon(p)
    ax.add_patch(Polygon(poly, closed=True, facecolor=PAL["ice"], edgecolor=PAL["ice_edge"], lw=1.4, zorder=2))
    half = p.a * np.sqrt(3) / 2                    # 截面半宽 = 柱面到 c 轴的距离
    z_ring = p.h / 2
    H = p.a * p.c_over_a                            # 理论锥顶高出棱柱环的高度（在截面里沿锥面母线外推）
    apex = z_ring + H
    z_top = z_ring + H * p.tip_ratio
    ink, soft, faint = PAL["ink_soft"], PAL["slate"], PAL["ink_faint"]
    # 被截掉的锥尖（上下对称，虚线）
    for s in (1, -1):
        ax.plot([-half * (1 - p.tip_ratio), 0, half * (1 - p.tip_ratio)], [s * z_top, s * apex, s * z_top],
                color=soft, lw=1.0, ls=(0, (4, 3)), zorder=1)
    # c 轴
    ax.annotate("", xy=(0, apex + 0.35), xytext=(0, -apex - 0.1),
                arrowprops=dict(arrowstyle="-|>", color=ink, lw=1.0, mutation_scale=12), zorder=3)
    ax.text(0.08, apex + 0.3, "c 轴", ha="left", va="center", fontsize=11, color=ink, **FONT)
    # 截面边上的面号
    labels = {1: (0.3, z_top), 2: (0.3, -z_top),      # 底面编号让开 c 轴
              3: (half, 0), 6: (-half, 0),
              13: ((half + half * (1 - p.tip_ratio)) / 2, (z_ring + z_top) / 2),
              16: (-(half + half * (1 - p.tip_ratio)) / 2, (z_ring + z_top) / 2),
              23: ((half + half * (1 - p.tip_ratio)) / 2, -(z_ring + z_top) / 2),
              26: (-(half + half * (1 - p.tip_ratio)) / 2, -(z_ring + z_top) / 2)}
    for num, (x, z) in labels.items():
        r = np.array([x, z])
        n = np.asarray(p.normal(p.face(num)), float)
        inward = -np.array([n[0], n[2]]) / np.linalg.norm([n[0], n[2]])
        q = r + inward * 0.2
        ax.text(q[0], q[1], str(num), ha="center", va="center", fontsize=12, fontweight="bold",
                color=FACE_COLOR[num], zorder=6, **FONT)
    # 柱段高 h（右侧尺寸线）
    xd = half + 0.35
    ax.annotate("", xy=(xd, z_ring), xytext=(xd, -z_ring), arrowprops=dict(arrowstyle="<|-|>", color=ink, lw=0.9,
                                                                            mutation_scale=9, shrinkA=0, shrinkB=0))
    for z in (z_ring, -z_ring):
        ax.plot([half + 0.05, xd + 0.08], [z, z], color=faint, lw=0.8)
    ax.text(xd + 0.1, 0, "柱段高 h", ha="left", va="center", fontsize=11, color=ink, **FONT)
    # 截顶比例（左侧：锥台高 / 理论锥高）
    xl = -half - 0.35
    for z in (z_ring, z_top, apex):
        ax.plot([xl - 0.08, -half * (1 - (z - z_ring) / H) - 0.05], [z, z], color=faint, lw=0.8)
    ax.annotate("", xy=(xl, z_top), xytext=(xl, z_ring), arrowprops=dict(arrowstyle="<|-|>", color=ink, lw=0.9,
                                                                        mutation_scale=9, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(xl - 0.22, apex), xytext=(xl - 0.22, z_ring), arrowprops=dict(arrowstyle="<|-|>", color=soft, lw=0.9,
                                                                                      mutation_scale=9, shrinkA=0, shrinkB=0))
    ax.text(xl - 0.3, (z_ring + apex) / 2 + 0.25, f"截顶比例\n= 实线段 / 到锥尖\n= {p.tip_ratio:g}", ha="right", va="center",
            fontsize=10.5, color=ink, linespacing=1.4, **FONT)
    # 锥面 13 外法向与 c 轴的夹角
    ang = face_angle_deg(p)
    n = np.asarray(p.normal(p.face(13)), float)
    n2 = np.array([n[0], n[2]]) / np.linalg.norm([n[0], n[2]])
    foot = np.array(labels[13]) + np.array([0.0, 0.0])
    tip = foot + n2 * 0.9
    ax.add_patch(FancyArrowPatch(foot, tip, arrowstyle="-|>", mutation_scale=12, color=PAL["face_3"], lw=1.4, zorder=7))
    ax.plot([foot[0], foot[0]], [foot[1], foot[1] + 0.95], color=PAL["face_3"], lw=1.0, ls=(0, (3, 2)), zorder=7)
    ax.add_patch(Arc(foot, 0.9, 0.9, theta1=90 - ang, theta2=90, color=PAL["face_3"], lw=1.1, zorder=7))
    mid = np.radians(90 - ang / 2)
    ax.text(foot[0] + 0.55 * np.cos(mid) + 0.02, foot[1] + 0.55 * np.sin(mid) + 0.03, F.deg(ang, 1), ha="left", va="bottom",
            fontsize=12, color=PAL["face_3"], zorder=8, **FONT)
    ax.text(tip[0] + 0.05, tip[1] - 0.02, "锥面法向", ha="left", va="center", fontsize=10.5, color=PAL["face_3"], **FONT)
    ax.set_xlim(-2.9, 2.5)
    ax.set_ylim(-apex - 0.25, apex + 0.55)
    ax.set_aspect("equal")
    ax.set_axis_off()


def main() -> None:
    p = crystal()
    assert abs(face_angle_deg(p) - pyramid_face_angle(p.c_over_a)) < 1e-9
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    boxes = [(0.00, 0.13, 0.30, 0.85), (0.30, 0.13, 0.30, 0.85), (0.60, 0.10, 0.40, 0.88)]
    titles = ["从斜上方看", "从斜下方看（绕 c 轴转过 180°）", "过 c 轴的截面"]
    axes = [fig.add_axes(b) for b in boxes]
    draw_view(axes[0], p, "upper")
    draw_view(axes[1], p, "lower")
    draw_section(axes[2], p)
    for ax, t, b in zip(axes, titles, boxes):
        fig.text(b[0] + b[2] / 2, 0.075, t, ha="center", va="center", fontsize=12, color=PAL["ink"], **FONT)
    # 分组图例（颜色 = 编号颜色）
    x = 0.08
    for name, (faces, color) in GROUPS.items():
        lo, hi = faces[0], faces[-1]
        rng = f"{lo}/{hi}" if len(faces) == 2 else f"{lo}–{hi}"
        fig.text(x, 0.02, f"■ {name} {rng}", ha="left", va="center", fontsize=11, color=color, **FONT)
        x += 0.14
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
