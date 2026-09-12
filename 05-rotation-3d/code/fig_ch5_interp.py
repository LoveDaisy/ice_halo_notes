# 产出 ../img/ch5_interp.gif（61 帧、20 ms/帧、循环）与静态三联 ../img/ch5_interp.png（首 / 中 / 末三帧各一行）：
# 同一对起终姿态，三种插值并排——左：旋转矩阵逐元素线性插值（中途不再正交，晶体缩瘪 / 塌陷）；中：经度 λ / 纬度 φ /
# 转角 θ 三参数线性插值（绕远：中途横躺）；右：单位四元数 SLERP（最短路径、匀速、全程刚性）。晶体带贴面编号，透视投影。
# 重制 5.1 旧图 img/legacy/ch5_interp.gif（旧 matlab 已丢失；起终姿态按旧 gif 首末帧反推：首帧倒立、末帧直立，
# 二者相差约 163°——刻意不取 180°，避免 slerp 最短路径歧义）。旧 gif 无坐标轴、无参考球，保持。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, animate, export_frames_png, finish, frame, lerp_euler,
                             lerp_matrix, lon_lat_roll_to_matrix, multi_panel, render_crystal, slerp_matrix,
                             solve_camera_distance)
from halo_notes.draw.style import TextStyle

IMG = Path(__file__).resolve().parent.parent / "img"
OUT_GIF, OUT_PNG = IMG / "ch5_interp.gif", IMG / "ch5_interp.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率（每帧）；静态三联高 3×
N_FRAMES, FPS = 61, 50                # 旧 gif：61 帧、20 ms/帧
STATIC_FRAMES = (0, N_FRAMES // 2, N_FRAMES - 1)

PATHS: dict = {}   # 本图没有光路
PRESET = PRESETS["default"].replace(style_map=PRESETS["default"].style_map.replace(
    panel_title=TextStyle("ink", fontsize=13, weight="bold", family=("DejaVu Sans",))))   # 旧图：粗体无衬线英文标题
TITLES = ("Interpolation on rotation matrix", "Interpolation on Euler angle", "SLERP on unit quaternion")
METHODS = (lerp_matrix, lerp_euler, slerp_matrix)
CRYSTAL = HexPrism(a=1.0, h=2.8)      # 柱晶（旧 gif 观感）
# 起终姿态（经度 λ、纬度 φ、转角 θ，度）：起点 c 轴指向纬度 −80°（倒立、略斜），终点 +80°（直立、略斜）；
# 经度只差 20° 让欧拉角插值的中间帧横躺着侧对观察者（旧 gif 中栏观感）；θ₀=60° 把起终相对旋转角调到约 163°
POSE_START, POSE_END = (-20.0, -80.0, 60.0), (0.0, 80.0, 0.0)
R_START, R_END = lon_lat_roll_to_matrix(*POSE_START), lon_lat_roll_to_matrix(*POSE_END)
AZIMUTH, ELEVATION, FOV_DEG = 80.0, 15.0, 24.0   # 观察者在 +y 侧偏 x 一点：末帧正对面 4 / 5


def pose(method: int, i: int) -> np.ndarray:
    """第 ``method`` 栏第 ``i`` 帧的姿态矩阵（t = i / (N-1)）。"""
    return METHODS[method](R_START, R_END, i / (N_FRAMES - 1))


def all_poses() -> list[np.ndarray]:
    return [pose(m, i) for m in range(3) for i in range(N_FRAMES)]


# 三栏 × 全部帧共用同一相机与取景（相机距离按所有帧的顶点自动取，帧间尺寸 / 比例尺完全一致）
_ALL_VERTICES = [CRYSTAL.transformed(R).vertices for R in all_poses()]
CAMERA = Camera(azimuth=AZIMUTH, elevation=ELEVATION,
                distance=solve_camera_distance(_ALL_VERTICES, azimuth=AZIMUTH, elevation=ELEVATION,
                                               target_fov_deg=FOV_DEG))
LIMITS = frame(CAMERA, _ALL_VERTICES, WIDTH // 3, HEIGHT, margin=0.06)


def build_axes(n_rows: int):
    """``n_rows`` 行 × 3 栏，标题带在上方（旧 gif）。"""
    return multi_panel(n_rows, 3, WIDTH, HEIGHT * n_rows, DPI, preset=PRESET, titles=list(TITLES) * n_rows,
                       title_frac=0.12, title_pos="top")


def render_frame(fig, row, i: int) -> None:
    for m, ax in enumerate(row):
        render_crystal(ax, CRYSTAL.transformed(pose(m, i)), camera=CAMERA, preset=PRESET, face_numbers=True)
        finish(ax, *LIMITS)


def main() -> None:
    animate(render_frame, N_FRAMES, OUT_GIF, fps=FPS, build_axes=build_axes, dpi=DPI)
    print(f"saved {OUT_GIF}")
    export_frames_png(render_frame, STATIC_FRAMES, OUT_PNG, build_axes=build_axes, dpi=DPI)
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
