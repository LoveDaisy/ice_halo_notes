# 产出 ../img/conjugate_rot90.png：把侧面镜的法向转到 c 轴方向的那个 90° 旋转（正文第 123–125 行）。两栏 3D、同一相机：
# 左 = 直立六棱柱（c 轴沿 z）+ 一面侧面镜（面 3 高亮）+ 坐标轴；右 = 同一晶体绕 y 轴转 90° 后横躺（$R_y(90°)$：面 3 的法向
# +x → −z，占了「底面镜」的位置），3D 弧箭头标出 90°，淡画原直立晶体的幽灵轮廓。
# 读者要看出：存在一个 90° 旋转把侧面镜转到底面镜的位置（所以特征值把 #2 和 #11 并成一类），但这个旋转不是晶体的对称操作——
# 横躺的六棱柱与原来的自己（幽灵）不重合。机械核验见 test_figures：右栏顶点 == R_y(90°)·左栏顶点；R_y(90°)·n_3 = ±e_z；
# 转后面法向集合 ≠ 转前；弧的轴 = y、张角 = 90°。
# 返工 R1（2026-09-13 作者裁定）：原「变体 b」（加半透明镜面平面）已删，只保留面高亮这一版。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, draw_axes, draw_rotation_arc_3d, finish, frame, multi_panel,
                             render_crystal, rotation, solve_camera_distance)
from halo_notes.draw.style import TextStyle
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.math import reflection_group as rg

OUT = Path(__file__).resolve().parent.parent / "img" / "conjugate_rot90.png"
WIDTH, HEIGHT, DPI = 4000, 2000, 200

PATHS: dict = {}   # 本图没有光路
PRESET = PRESETS["default"].replace(style_map=PRESETS["default"].style_map.replace(
    panel_title=TextStyle("ink", fontsize=22, family=CJK_SANS)))
TITLES = ("直立六棱柱 + 侧面镜（面 3）", "绕 $y$ 轴转 90°：侧面镜转到底面镜的位置，晶体却横躺了")
CRYSTAL = HexPrism(a=0.8, h=2.4)    # 柱晶（同 3.4）
MIRROR_FACE = 3
Y, Z = np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])
R = rotation(Y, 90.0)                # 把面 3 法向 +x 转到 −z、c 轴 z 转到 +x
TURNED = CRYSTAL.transformed(R)
AXIS_LENGTH, ARC_RADIUS = 2.4, 1.9
AZIMUTH, ELEVATION, FOV_DEG = 40.0, 24.0, 20.0

# 机械自检：R n_3 = ±e_z；转后晶体不与自身重合（面法向集合变了）——这正是"不是对称操作"
N3 = CRYSTAL.normal(CRYSTAL.face(MIRROR_FACE))
assert np.allclose(np.abs(R @ N3), Z) and np.allclose(N3, rg.NORMALS[MIRROR_FACE])
_before = {tuple(np.round(CRYSTAL.normal(f), 6)) for f in CRYSTAL.faces}
_after = {tuple(np.round(TURNED.normal(f), 6)) for f in TURNED.faces}
assert _before != _after


def main() -> None:
    extent = np.array([s * AXIS_LENGTH * e for e in np.eye(3) for s in (1, -1)])
    scene_points = [extent, CRYSTAL.vertices, TURNED.vertices]
    distance = solve_camera_distance(scene_points, azimuth=AZIMUTH, elevation=ELEVATION, target_fov_deg=FOV_DEG)
    camera = Camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=distance)
    limits = frame(camera, scene_points, WIDTH // 2, HEIGHT, margin=0.06)
    fig, axes = multi_panel(1, 2, WIDTH, HEIGHT, DPI, preset=PRESET, titles=list(TITLES), title_frac=0.1)
    ax_left, ax_right = axes[0]
    # 左：直立晶体，面 3 高亮
    render_crystal(ax_left, CRYSTAL, camera=camera, preset=PRESET, face_numbers=[MIRROR_FACE], highlight=[MIRROR_FACE])
    draw_axes(ax_left, camera=camera, preset=PRESET, occluder=CRYSTAL, length=AXIS_LENGTH)
    # 右：幽灵 = 原直立晶体；实体 = 转 90° 后的晶体，面 3 仍高亮；弧从 z 转到 x
    render_crystal(ax_right, CRYSTAL, camera=camera, preset=PRESET, ghost=True)
    render_crystal(ax_right, TURNED, camera=camera, preset=PRESET, face_numbers=[MIRROR_FACE], highlight=[MIRROR_FACE])
    draw_axes(ax_right, camera=camera, preset=PRESET, occluder=TURNED, length=AXIS_LENGTH)
    draw_rotation_arc_3d(ax_right, Y, ARC_RADIUS, Z, 90.0, camera=camera, preset=PRESET, semantic="arc_tilt",
                         label=r"$90^\circ$")
    for ax in (ax_left, ax_right):
        finish(ax, *limits)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
