# 产出 ../img/ch5_interp.gif（61 帧、20 ms/帧、循环）与静态三联 ../img/ch5_interp.png（首 / 中 / 末三帧各一行）：
# 同一对起终姿态，三种插值并排——左：旋转矩阵逐元素线性插值（中途不再正交，晶体缩瘪 / 塌陷）；中：经度 λ / 纬度 φ /
# 转角 θ 三参数线性插值（绕远：中途横躺 + 多余旋转）；右：单位四元数 SLERP（最短路径、匀速、全程刚性）。晶体带贴面
# 编号，透视投影。
# 场景（chore-figures-followup E，2026-09-12 改）：六棱柱上下底面翻个个儿——终点直立（面 1 朝上），
# 起点是终点绕世界水平轴（+x）翻 180°（面 1 朝下），让三种插值的动态差别最大化：
# - 矩阵线性插值：R_START + R_END 恰好正交抵消成奇异矩阵 diag(1,0,0)，中途晶体压扁成一条线；
# - 欧拉角插值：不能从矩阵反解 (λ,φ,θ)（±90° 纬度万向锁，反解给出的 λ/θ 是任意值，抹掉本该有的「多余
#   旋转」），改为显式给一组精确表示 R_START/R_END 的三元组（纬度 −90→+90 过程中经度、转角也都有大幅
#   变化），插值路径总旋转量 ≈ 255°，明显超过最短路径的 180°；
# - slerp：R_START/R_END 相对旋转角恰为 180°（四元数点积为 0），测地线唯一，匀速绕翻转轴转过 180°。
# 旧 gif（img/legacy/ch5_interp.gif，旧 matlab 已丢失）无坐标轴、无参考球，保持。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, animate, export_frames_png, finish, frame, lerp_euler,
                             lerp_matrix, lon_lat_roll_to_matrix, multi_panel, render_crystal, rotation, slerp_matrix,
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
CRYSTAL = HexPrism(a=1.0, h=2.8)      # 柱晶（旧 gif 观感）
# 终点：直立，面 1（c 轴）朝上；起点：终点绕世界 +x 轴翻 180°，面 1 朝下——两者相对旋转角恰为 180°。
R_END = lon_lat_roll_to_matrix(0.0, 90.0, 0.0)
R_START = rotation((1.0, 0.0, 0.0), 180.0) @ R_END
# 欧拉角插值专用三元组（经度 λ、纬度 φ、转角 θ，度）：精确表示 R_START / R_END（φ=±90° 处经度/转角
# 不唯一——这里显式选出一组带非零 λ/θ 变化的解，让插值路径出现「多余旋转」，而不是被动落到反解给出的
# λ=0 默认解）。核验：``lon_lat_roll_to_matrix(*EULER_POSE_START)`` 与 ``R_START`` 逐元素相差 < 1e-9（单测覆盖）。
EULER_POSE_START, EULER_POSE_END = (180.0, -90.0, 0.0), (0.0, 90.0, 0.0)
AZIMUTH, ELEVATION, FOV_DEG = 80.0, 15.0, 24.0   # 观察者在 +y 侧偏 x 一点：末帧正对面 4 / 5


def pose(method: int, i: int) -> np.ndarray:
    """第 ``method`` 栏第 ``i`` 帧的姿态矩阵（t = i / (N-1)）。"""
    t = i / (N_FRAMES - 1)
    if method == 0:
        return lerp_matrix(R_START, R_END, t)
    if method == 1:
        return lerp_euler(EULER_POSE_START, EULER_POSE_END, t)
    return slerp_matrix(R_START, R_END, t)


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
