# 产出 ../img/two_mirrors_120.png：法线夹角 60° 的两面镜子先后反射 = 绕交线转 120°（正文第 50 行）。
# 纯平面几何，不画晶体（R1-4 作者裁定）：两条镜面线交于一点 O（镜 A 法向 −60°、镜 B 法向 0°，法向夹 60°），一条水平入射的
# 光线先在镜 A、后在镜 B 上反射，每一段都用 `halo_notes.draw.raypath.reflect` 算出来（不手摆）：入射 0° → 60° → 出射 120°
#（两次都是 60° 入射角）。两个反射点处各画一条入射侧法线（虚线），两条法线交于 C，在 C 处标出法线夹角 60°；在出射段上取一点 P
# 用弧箭头从原入射方向（细辐条）转到出射方向标出 120° 偏转；另一条淡色虚线从 P 画出「只转 60°」的方向作对比（显式 sketch，不是光路）。
# 两面镜子登记为一个 Polygon2D「镜楔」（顶点 O、镜 A 远端、镜 B 远端，只画编号 3 / 4 的两条镜边）——光路是它内部的两次
# 内反射（REFLECT_INTERNAL），test_figures 的通用核验据此白盒复核反射定律；镜边沿用 3 / 4 编号只为对应正文「相邻两个侧面」。
# 机械核验：出射 vs 入射方位差 == ±120°（< 1e-9）；两镜法向夹 60°；两个反射矩阵之积 == rotation2d(±120°)；对比线 sketch。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Polygon2D, RayPath2D, SegmentKind, annotate_2d, draw_raypath_2d,
                             draw_rotation_arc, finish, new_figure, reflection2d, render_section, rotation2d)
from halo_notes.draw.geometry import Face
from halo_notes.draw.geometry2d import perp2d
from halo_notes.draw.raypath import EventKind, RayEvent, reflect
from halo_notes.draw.scene2d import Z_REFERENCE, Z_TEXT
from halo_notes.draw.style import LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "two_mirrors_120.png"
WIDTH, HEIGHT, DPI = 2400, 2000, 200

MIRROR_A, MIRROR_B = 3, 4              # 镜边编号（对应正文「相邻两个侧面」）
PATHS = {"镜 A → 镜 B": [MIRROR_A, MIRROR_B]}
PRESET = PRESETS["default"].replace(
    style_map=PRESETS["default"].style_map.replace(
        edge_visible=LineStyle("ink", linewidth=3.0),                       # 镜面线：粗实线
        symmetry_mark=LineStyle("reference", linewidth=2.2)),
    geom=PRESETS["default"].geom.replace(mark_arrow_scale=0.55))
NORMAL_A_DEG, NORMAL_B_DEG = -60.0, 0.0      # 两镜外法向的方位角（相差 60°）
MIRROR_LENGTH = 2.1                          # 镜楔两条镜边的长度（自交点 O 起）
D_IN = np.array([1.0, 0.0])                  # 入射方向：水平向右
HIT_A = 1.25                                 # 第一次反射点到 O 的距离
TAIL, HEAD = 1.7, 2.0                        # 入射段 / 出射段长度
ARC_AT = 1.3                                 # 120° 弧心 P 在出射段上离出射点的距离
COMPARE_LENGTH = 1.2                         # 「只转 60°」对比线长度
NORMAL_DASH = LineStyle("slate", linewidth=1.1, linestyle=(0, (5, 3)), alpha=0.9)
ARC_R_60, ARC_R_120 = 0.42, 0.55


def direction(deg: float) -> np.ndarray:
    return np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])


def azimuth_deg(d: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(d[1], d[0])))


def line_intersection(p: np.ndarray, u: np.ndarray, q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """直线 p + s·u 与 q + t·v 的交点。"""
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]   # noqa: E731（numpy 2 弃用 2D cross）
    return p + cross(q - p, v) / cross(u, v) * u


# 镜楔：O 为交点；镜 A 的边方向 = 其法向顺时针转 90°… 按 Polygon2D 约定（逆时针顶点、外法向 = 边方向顺时针转 90°）反推：
# 边方向 = 法向逆时针转 90°，镜 A 从远端 A 走到 O、镜 B 从 O 走到远端 B
N_A, N_B = direction(NORMAL_A_DEG), direction(NORMAL_B_DEG)
O = np.zeros(2)
A_FAR = O - perp2d(N_A) * MIRROR_LENGTH      # perp2d：逆时针转 90°
B_FAR = O + perp2d(N_B) * MIRROR_LENGTH
WEDGE = Polygon2D(np.array([O, B_FAR, A_FAR]), [Face(MIRROR_B, (0, 1)), Face(9, (1, 2)), Face(MIRROR_A, (2, 0))])
assert np.allclose(WEDGE.normal(WEDGE.face(MIRROR_A)), N_A) and np.allclose(WEDGE.normal(WEDGE.face(MIRROR_B)), N_B)
assert abs(np.degrees(np.arccos(N_A @ N_B)) - 60.0) < 1e-9

# 光路：逐段反射
Q1 = O - perp2d(N_A) * HIT_A                     # 镜 A 上的反射点
D1 = reflect(D_IN, -N_A)                         # 内反射：入射侧法向 = −外法向
Q2 = line_intersection(Q1, D1, O, perp2d(N_B))   # 沿 D1 打到镜 B
D_OUT = reflect(D1, -N_B)
assert WEDGE.face_margin(WEDGE.face(MIRROR_A), Q1) > 0.1 and WEDGE.face_margin(WEDGE.face(MIRROR_B), Q2) > 0.1
PATH = RayPath2D(np.array([Q1 - D_IN * TAIL, Q1, Q2, Q2 + D_OUT * HEAD]),
                 (SegmentKind.INTERNAL, SegmentKind.INTERNAL, SegmentKind.INTERNAL),
                 (RayEvent(1, MIRROR_A, EventKind.REFLECT_INTERNAL), RayEvent(2, MIRROR_B, EventKind.REFLECT_INTERNAL)))
ROTATION_DEG = (azimuth_deg(D_OUT) - azimuth_deg(D_IN) + 180.0) % 360.0 - 180.0   # 有符号转角
assert abs(abs(ROTATION_DEG) - 120.0) < 1e-9, ROTATION_DEG
# 两个反射矩阵之积 == 绕交点转 2α = 120°（reflection2d 取镜面线方向）
assert np.allclose(reflection2d(perp2d(N_B)) @ reflection2d(perp2d(N_A)), rotation2d(ROTATION_DEG))
# 对比线：只转 60°（从出射段上的 P 出发、入射方向转 ±60°），显式 sketch
P_ARC = Q2 + D_OUT * ARC_AT
D_COMPARE = rotation2d(np.sign(ROTATION_DEG) * 60.0) @ D_IN
COMPARE = RayPath2D(np.array([P_ARC, P_ARC + D_COMPARE * COMPARE_LENGTH]), (SegmentKind.INTERNAL,), sketch=True)
# 两条入射侧法线的交点 C
C = line_intersection(Q1, -N_A, Q2, -N_B)


def main() -> None:
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    render_section(ax, WEDGE, preset=PRESET, edges=(MIRROR_A, MIRROR_B), fill=None)
    for q, text, off in ((A_FAR, "镜 A", (0.12, 0.0)), (B_FAR, "镜 B", (0.12, 0.0))):
        annotate_2d(ax, text, q + off, preset=PRESET, ha="left", va="center")
    # 反射点处的入射侧法线（虚线到交点 C）+ 60° 角标
    for q, n in ((Q1, N_A), (Q2, N_B)):
        ax.plot([q[0], C[0]], [q[1], C[1]], zorder=Z_REFERENCE, **PRESET.line_kwargs(NORMAL_DASH))
        ax.plot([q[0]], [q[1]], zorder=Z_TEXT, **PRESET.marker_kwargs(PRESET.style_map.ray_marker))
    a0, a1 = azimuth_deg(Q1 - C), azimuth_deg(Q2 - C)
    th = np.radians(np.linspace(a0, a1, 32))
    ax.plot(C[0] + ARC_R_60 * np.cos(th), C[1] + ARC_R_60 * np.sin(th), zorder=Z_TEXT, **PRESET.line_kwargs("angle_mark"))
    mid = direction((a0 + a1) / 2)
    annotate_2d(ax, "60°", C + mid * (ARC_R_60 + 0.16), preset=PRESET, ha="center", va="center")
    annotate_2d(ax, "两镜法线夹角 α = 60°", C + (-0.05, -0.62), preset=PRESET, ha="center", va="top")
    # 光路 + 120° 偏转弧（心在出射段上的 P，从原入射方向转到出射方向；两条细辐条分别是这两个方向）
    draw_raypath_2d(ax, PATH, preset=PRESET, arrows=[(0, 0.55), (1, 0.55), (2, 0.35)], markers=False)
    draw_rotation_arc(ax, P_ARC, ARC_R_120, azimuth_deg(D_IN), azimuth_deg(D_OUT), preset=PRESET, spokes=ARC_R_120 + 0.25)
    mid = direction(azimuth_deg(D_IN) + ROTATION_DEG * 0.28)     # 标签放在弧的前 1/3（避开 60° 处的对比线）
    annotate_2d(ax, "2α = 120°", P_ARC + mid * (ARC_R_120 + 0.2), preset=PRESET, ha="left", va="center")
    annotate_2d(ax, "原方向", P_ARC + (ARC_R_120 + 0.3, 0.0), preset=PRESET, ha="left", va="center")
    draw_raypath_2d(ax, COMPARE, preset=PRESET, semantic="ray2d_discarded", arrows=[(0, 0.7)])
    annotate_2d(ax, "只转 60°？\n（对比方向，不是光路）", COMPARE.end + (0.1, 0.0), preset=PRESET, ha="left", va="center")
    annotate_2d(ax, "入射", PATH.points[0] + (0.0, 0.12), preset=PRESET, ha="left", va="bottom")
    annotate_2d(ax, "出射", PATH.points[-1] + (-0.1, 0.0), preset=PRESET, ha="right", va="center")
    pts = np.vstack([WEDGE.vertices, PATH.points, COMPARE.points, [C]])
    lo, hi = pts.min(axis=0) - 0.5, pts.max(axis=0) + np.array([1.6, 0.5])   # 右侧留出对比线的两行文字
    finish(ax, (lo[0], hi[0]), (lo[1], hi[1]))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
