# 产出 ../img/plate_vs_column.png（番外图 4「片晶与柱晶」）：`3-4-5-7` 的折叠 M（晶体系里绕 c 轴转 120°）经姿态 R 共轭到天空，
# RMR⁻¹ 是绕 Rc 的 120° 旋转。两栏三维、同一相机：左片晶（R = plate_attitude，c 轴竖直）、右柱晶（R = column_attitude，
# c 轴水平）。每栏画晶体本身、晶体 c 轴（= RMR⁻¹ 的旋转轴 Rc，粗箭头）、天顶方向 k（细箭头）、绕 Rc 的 120° 旋转弧，以及一圈
# 淡虚线的水平面作参照。左栏 Rc 与 k 重合 ⇒ 绕竖直轴转 120°，TK1999 的 Rule 1 认得；右栏 Rc 水平 ⇒ 绕一根水平轴翻 120°，Rule 1 不认。
# 读者要看出：Rule 1 只认绕竖直轴的旋转；片晶恰好把 M 的轴摆成竖直、柱晶把它摆成水平——片晶那一步是巧合，不是结构。
# 取值：片晶方位 φ = 20°、柱晶 ψ = −20° / 自转 θ = 0°，只为让晶体面在画面里不退化，不承载数值结论。旋转轴与转角由矩阵 RMR⁻¹
# 反解（不手摆）；M 由 fold_matrix 按面序列 3-4-5-7 算出。图上不出现任何精度数字。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
from lumice_integral.geometry import fold_matrix

from halo_notes.draw import (PRESETS, Camera, HexPrism, draw_axis_arrow, draw_rotation_arc_3d, finish, frame, multi_panel,
                             render_crystal, solve_camera_distance)
from halo_notes.draw.geometry import unit
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from lumice_integral.symmetry.attitude import column_attitude
from lumice_integral.symmetry.reflection_group import Rz

OUT = Path(__file__).resolve().parent.parent / "img" / "plate_vs_column.png"
WIDTH, HEIGHT, DPI = 3600, 1800, 200

PATHS: dict = {}   # 本图没有光路：画的是姿态与旋转轴
PRESET = PRESETS["default"].replace(style_map=PRESETS["default"].style_map.replace(
    panel_title=TextStyle("ink", fontsize=22, family=CJK_SANS)))
M_3457 = fold_matrix(HexPrism.from_ratio(1.0), [3, 4, 5, 7])     # 晶体系里的折叠：绕 c 轴转 120°（与晶体高径比无关）
K = np.array([0.0, 0.0, 1.0])                                   # 天顶
C = np.array([0.0, 0.0, 1.0])                                   # 晶体系 c 轴
PLATE_PHI, COLUMN_PSI, COLUMN_THETA = 20.0, -20.0, 0.0   # ψ 离「垂直视线」偏 35°：c 轴基本横着，120° 弧又能看成椭圆
# 栏：(名字, 晶体, 姿态 R, Rc 箭头长, 弧心沿 Rc 的距离, 弧半径, 标题, 格内说明)
ARC_PHASE_COLUMN = 132.0   # 柱晶栏：把 120° 弧绕 Rc 转开这么多，免得弧与 Rc 箭杆在投影里压在一起（R1 作者意见）
PANELS = [
    ("plate", HexPrism(a=1.25, h=0.45), Rz(PLATE_PHI), 1.75, 1.0, 0.85, 0.0, "片晶：$RMR^{-1}$ 绕竖直轴转 $120^\\circ$",
     "旋转轴 $R\\mathbf{c}$ 竖直，与天顶 $\\mathbf{k}$ 重合\n$\\Rightarrow$ 绕天顶转 $120°$，Rule 1 认得"),
    ("column", HexPrism(a=0.5, h=2.5), column_attitude(COLUMN_PSI, COLUMN_THETA), 2.75, 1.55, 0.8, ARC_PHASE_COLUMN,
     "柱晶：$RMR^{-1}$ 绕水平轴转 $120^\\circ$", "旋转轴 $R\\mathbf{c}$ 水平，与天顶 $\\mathbf{k}$ 垂直\n$\\Rightarrow$ 绕水平轴翻 $120°$，Rule 1 不认"),
]
K_LEN = 2.5
HORIZON_R = 1.9
AZIMUTH, ELEVATION, FOV_DEG = 35.0, 18.0, 22.0
HORIZON = LineStyle("ink_faint", linewidth=1.1, linestyle="--")
TEXT16 = TextStyle("ink", fontsize=16, family=CJK_SANS)


def axis_angle(A: np.ndarray) -> tuple[np.ndarray, float]:
    """正交矩阵 A（det = +1、转角 ∈ (0°, 180°)）的旋转轴（单位向量）与右手转角（度）。"""
    angle = float(np.degrees(np.arccos(np.clip((np.trace(A) - 1.0) / 2.0, -1.0, 1.0))))
    w = np.array([A[2, 1] - A[1, 2], A[0, 2] - A[2, 0], A[1, 0] - A[0, 1]])
    return unit(w), angle


def conjugated(R: np.ndarray) -> np.ndarray:
    """天空里的那个旋转 $RMR^{-1}$（R 正交，$R^{-1}=R^T$）。"""
    return R @ M_3457 @ R.T


def horizon_points(n: int = 181) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, n)
    return np.stack([HORIZON_R * np.cos(t), HORIZON_R * np.sin(t), np.zeros(n)], axis=1)


def perpendicular(v: np.ndarray) -> np.ndarray:
    """与 v 垂直、尽量朝上（没有朝上分量时朝 +x 方向转）的单位向量：弧的起点方向。"""
    up = K - (K @ v) * v
    return unit(up) if np.linalg.norm(up) > 1e-9 else unit(np.cross(v, np.array([1.0, 0.0, 0.0]))) * -1


def rotate_about(v: np.ndarray, axis: np.ndarray, deg: float) -> np.ndarray:
    """把 v 绕 axis 右手转 deg（Rodrigues）——只用来挪弧的起点相位，不改弧的轴与转角。"""
    t = np.deg2rad(deg)
    k = unit(axis)
    return v * np.cos(t) + np.cross(k, v) * np.sin(t) + k * (k @ v) * (1.0 - np.cos(t))


def draw_panel(ax, crystal, R, c_len, arc_at, arc_r, arc_phase, note, camera) -> None:
    body = crystal.transformed(R)
    axis, angle = axis_angle(conjugated(R))
    xy = camera.project_xy(horizon_points())
    ax.plot(xy[:, 0], xy[:, 1], zorder=1, **PRESET.line_kwargs(HORIZON))
    hx, hy = camera.project_xy(np.array([np.cos(np.deg2rad(160)), np.sin(np.deg2rad(160)), 0.0]) * HORIZON_R)[0]
    ax.text(hx, hy + 0.08, "水平面", ha="center", va="bottom", **PRESET.text_kwargs(TextStyle("ink_soft", fontsize=15,
                                                                                      family=CJK_SANS)))
    render_crystal(ax, body, camera=camera, preset=PRESET)
    draw_axis_arrow(ax, np.zeros(3), K, K_LEN, camera=camera, preset=PRESET, semantic="axis_main", occluder=body,
                    label=r"$\mathbf{k}$")
    kx, ky = camera.project_xy(K * (K_LEN + PRESET.geom.axis_label_pad))[0]
    ax.text(kx + 0.18, ky, "天顶", ha="left", va="center", **PRESET.text_kwargs(TEXT16))
    draw_axis_arrow(ax, np.zeros(3), R @ C, c_len, camera=camera, preset=PRESET, semantic="arc_roll", occluder=body)
    cx, cy = camera.project_xy(R @ C * (c_len + 0.1))[0]                # 标签放在箭头尖左边：片晶里 Rc 与 k 共线
    ax.text(cx - 0.2, cy, r"$R\mathbf{c}$", ha="right", va="center", **PRESET.text_kwargs("axis_label"))
    start = rotate_about(perpendicular(axis), axis, arc_phase)
    draw_rotation_arc_3d(ax, axis, arc_r, start, angle, camera=camera, preset=PRESET,
                         semantic="arc_roll", center=axis * arc_at, label=r"$120^\circ$")
    ax.text(0.03, 0.97, note, transform=ax.transAxes, ha="left", va="top", linespacing=1.6,
            **PRESET.text_kwargs(TEXT16))


def main() -> None:
    bodies = [crystal.transformed(R) for _, crystal, R, *_ in PANELS]
    extent = [horizon_points(), K[None, :] * (K_LEN + 0.35)] + [(p[2] @ C)[None, :] * (p[3] + 0.35) for p in PANELS]
    scene = extent + [b.vertices for b in bodies]
    distance = solve_camera_distance(scene, azimuth=AZIMUTH, elevation=ELEVATION, target_fov_deg=FOV_DEG)
    camera = Camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=distance)
    fig, axes = multi_panel(1, 2, WIDTH, HEIGHT, DPI, preset=PRESET, titles=[p[7] for p in PANELS], title_frac=0.1)
    limits = frame(camera, scene, WIDTH // 2, int(HEIGHT * 0.9), margin=0.1)
    ylo, yhi = limits[1]
    limits = (limits[0], (ylo, yhi + (yhi - ylo) * 0.12))       # 顶上给格内说明留地方
    for ax, (_, crystal, R, c_len, arc_at, arc_r, arc_phase, _, note) in zip(axes[0], PANELS):
        draw_panel(ax, crystal, R, c_len, arc_at, arc_r, arc_phase, note, camera)
        finish(ax, *limits)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
