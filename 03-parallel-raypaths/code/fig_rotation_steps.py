# 产出 ../img/rotation_steps.png：从标准坐标系到普通柱晶取向的三步旋转——横向三帧，每帧 xyz 坐标轴 + 六方柱晶。
# 帧 1：晶体 c 轴沿 z，绕 z 轴（= 绕自身 c 轴）转 θ（蓝弧）；帧 2：再绕 y 轴转 90°（绿弧，从 z 到 x）晶体横过来，
# 绕 c 轴的蓝弧 θ 跟到近端；帧 3：再绕 z 轴转 α（橙弧，从 x 到 c 轴的水平投影），黑色粗箭头 = 主轴（c 轴），蓝弧 θ 仍在。
# 重制 3.4 旧图 img/legacy/rotation_steps.png。读者要看出正文第 71 行的三步顺序 R = R_z(α)·R_y(π/2)·R_z(θ)，
# 每帧只比上一帧多做一步。三帧共用同一个相机与同一组取景，比例尺一致。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, annotate, draw_axes, draw_axis_arrow, draw_rotation_arc_3d,
                             finish, frame, multi_panel, render_crystal, rotation, solve_camera_distance)

OUT = Path(__file__).resolve().parent.parent / "img" / "rotation_steps.png"
WIDTH, HEIGHT, DPI = 6750, 2250, 200  # = 旧图分辨率，三帧等宽

PATHS: dict = {}   # 本图没有光路
PRESET = PRESETS["default"]
CRYSTAL = HexPrism(a=0.8, h=2.4)    # 柱晶（旧图长宽比目测约 1.5:1，半长约为坐标轴长的 0.45）
# 三步旋转的角度：θ 是绕 c 轴的 roll，取一个大角让弧看起来像"绕一圈"的示意（旧图观感；晶体六重对称，θ mod 60° 才可见）；
# α 是主轴方位角，取旧图观感的 30°。二者都是示意值，可调
THETA_DEG, ALPHA_DEG = 260.0, 30.0
Z, Y, X = np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0])
# 正文公式逐步累积：R₁ = R_z(θ)，R₂ = R_y(90°)·R₁，R₃ = R_z(α)·R₂（test_figures 读取核验）
R1 = rotation(Z, THETA_DEG)
R2 = rotation(Y, 90.0) @ R1
R3 = rotation(Z, ALPHA_DEG) @ R2
ROTATIONS = (R1, R2, R3)

AXIS_LENGTH = 2.6
ROLL_ARC_RADIUS, ROLL_ARC_OFFSET = 0.5, 0.5       # 绕 c 轴的 θ 弧：半径、弧心离晶体端面的距离
TILT_ARC_RADIUS, AZIMUTH_ARC_RADIUS = 2.3, 2.3    # 绕 y 的 π/2 弧、绕 z 的 α 弧（都以原点为心，落在晶体端面之外）
MAIN_AXIS_LENGTH = 2.5                            # 主轴箭头伸到 α 弧之外一点
ROLL_LABEL_OFFSET = (0.28, 0.0)                   # θ 标签放在弧箭头右侧（画面偏移，晶体单位）
AZIMUTH, ELEVATION, FOV_DEG = 72.0, 22.0, 18.0     # 视角沿用 3.3 标准坐标系图（x 轴向左、y 轴向右前）；窄视场贴近旧图的近正交观感


def roll_arc(ax, R: np.ndarray, camera: Camera) -> None:
    """绕当前 c 轴（R 的第三列）的 θ 弧，弧心在晶体近端之外；起点选得让弧的中段朝向观察者（缺口在背面），
    θ 标签写在箭头旁。"""
    c = R[:, 2]
    center = c * (CRYSTAL.h / 2 + ROLL_ARC_OFFSET)
    start = rotation(c, -THETA_DEG / 2) @ camera.view_dir
    _, cone = draw_rotation_arc_3d(ax, c, ROLL_ARC_RADIUS, start, THETA_DEG, center=center, camera=camera,
                                   preset=PRESET, semantic="arc_roll")
    annotate(ax, r"$\theta$", cone.apex, ROLL_LABEL_OFFSET, camera=camera, preset=PRESET, semantic="arc_label")


def main() -> None:
    crystals = [CRYSTAL.transformed(R) for R in ROTATIONS]
    # 三帧共用同一个相机（同一实例）与同一组取景点：坐标轴两端 + 三帧晶体 + 弧与主轴的最远点
    extent = [s * AXIS_LENGTH * e for e in (X, Y, Z) for s in (1, -1)]
    scene_points = [np.array(extent)] + [c.vertices for c in crystals] + [R3[:, 2] * (MAIN_AXIS_LENGTH + 0.4)]
    distance = solve_camera_distance(scene_points, azimuth=AZIMUTH, elevation=ELEVATION, target_fov_deg=FOV_DEG)
    camera = Camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=distance)
    limits = frame(camera, scene_points, WIDTH // 3, HEIGHT, margin=0.06)

    fig, axes = multi_panel(1, 3, WIDTH, HEIGHT, DPI, preset=PRESET, title_frac=0.0)
    for k, (ax, crystal, R) in enumerate(zip(axes[0], crystals, ROTATIONS), start=1):
        render_crystal(ax, crystal, camera=camera, preset=PRESET)
        draw_axes(ax, camera=camera, preset=PRESET, occluder=crystal, length=AXIS_LENGTH)
        if k >= 2:   # 绕 y 轴从 z 到 x 的 π/2（R_y(90°)·z = x）
            draw_rotation_arc_3d(ax, Y, TILT_ARC_RADIUS, Z, 90.0, camera=camera, preset=PRESET,
                                 semantic="arc_tilt", label=r"$\pi/2$")
        if k == 3:   # 绕 z 轴从 x 到 c 轴水平投影的 α，主轴粗箭头沿 c 轴
            draw_rotation_arc_3d(ax, Z, AZIMUTH_ARC_RADIUS, X, ALPHA_DEG, camera=camera, preset=PRESET,
                                 semantic="arc_azimuth", label=r"$\alpha$")
            draw_axis_arrow(ax, (0, 0, 0), R[:, 2], MAIN_AXIS_LENGTH, camera=camera, preset=PRESET,
                            occluder=crystal)
        roll_arc(ax, R, camera)
        finish(ax, *limits)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
