# 产出 ../img/crystal_pose.jpg：冰晶取向——左右两栏「片晶取向」「柱晶取向」。每栏：单位球经纬网格（细灰线，背面更淡）+
# 赤道（前半实线、后半虚线）+ 球心处一枚晶体 + 从晶体中心沿 c 轴伸出的红色粗箭头（主轴）+ 球面上的姿态点云
#（大量晶体主轴方向的样本）。左：片晶主轴竖直，点云聚在北极附近一小簇（天顶角高斯）；右：柱晶主轴水平，
# 点云沿赤道成一条带（天顶角 ≈ 90° 高斯 + 方位角均匀）。
# 重制 6.1 旧图 img/legacy/crystal_pose.jpg（旧 Mathematica 出两栏 + psd 合成标题；psd 的手工图层只有两栏图 + 两个中文标题，
# 现全部改由代码画）。读者要看出：主轴箭头方向 = 点云的分布中心；片晶「立着」柱晶「躺着」；点云散布 = 姿态的随机抖动。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, Sphere, draw_axis_arrow, finish, frame, graticule,
                             multi_panel, render_crystal, render_great_circle, render_point_cloud, rotation,
                             solve_camera_distance)
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

OUT = Path(__file__).resolve().parent.parent / "img" / "crystal_pose.jpg"
WIDTH, HEIGHT, DPI = 2700, 1350, 200  # = 旧图分辨率

PATHS: dict = {}   # 本图没有光路
PRESET = PRESETS["default"].replace(style_map=PRESETS["default"].style_map.replace(
    panel_title=TextStyle("ink", fontsize=20, family=CJK_SANS),      # 中文标题，字体沿用前序图的 CJK 回退序列
    axis_main=LineStyle("accent_warm", linewidth=3.0)))               # 旧图：主轴是红色粗箭头（与坐标轴同色）
TITLES = ("片晶取向", "柱晶取向")
SPHERE = Sphere()
CRYSTAL_SCALE = 0.4                      # 晶体相对单位球的尺寸（旧图观感）
PLATE, COLUMN = HexPrism(a=1.0, h=0.5), HexPrism(a=0.5, h=2.0)   # 片晶 h/a=0.5，柱晶 h/a=4
# 两栏的主轴方向（c 轴）：片晶竖直、柱晶水平（方位角 5°：与视线成 65°，箭头朝观察者左前方、近端六边形微露，旧图观感）
PLATE_AXIS = np.array([0.0, 0.0, 1.0])
COLUMN_AXIS = np.array([np.cos(np.deg2rad(5.0)), np.sin(np.deg2rad(5.0)), 0.0])
# 姿态点云：天顶角（与 +z 的夹角）取高斯、方位角均匀——片晶天顶角均值 0°（聚在北极），柱晶均值 90°（沿赤道成带）；
# std 与样本数按旧图观感取，待 owner 裁定
N_SAMPLES, SEED = 4000, 20260912
PLATE_ZENITH_STD_DEG, COLUMN_ZENITH_STD_DEG = 4.0, 3.0
AXIS_ARROW_LENGTH, AXIS_CONE_SCALE = 0.62, 0.3   # 锥体尺寸按晶体单位（a=1）定义，这里世界单位是球半径，要缩小
AZIMUTH, ELEVATION, FOV_DEG = 70.0, 22.0, 20.0


def crystal_rotation(axis: np.ndarray) -> np.ndarray:
    """把标准姿态（c 轴沿 +z）的晶体转到 c 轴沿 ``axis``：竖直不转，水平的先绕 y 放倒再绕 z 到方位角。"""
    if np.allclose(axis, [0, 0, 1]):
        return np.eye(3)
    az = np.degrees(np.arctan2(axis[1], axis[0]))
    return rotation((0, 0, 1), az) @ rotation((0, 1, 0), 90.0)


def pose_cloud(zenith_mean_deg: float, zenith_std_deg: float, rng: np.random.Generator) -> np.ndarray:
    """(N,3) 单位方向：天顶角 ~ N(mean, std)（度）、方位角在 [0, 2π) 均匀。"""
    zen = np.deg2rad(rng.normal(zenith_mean_deg, zenith_std_deg, N_SAMPLES))
    phi = rng.uniform(0.0, 2 * np.pi, N_SAMPLES)
    return np.stack([np.sin(zen) * np.cos(phi), np.sin(zen) * np.sin(phi), np.cos(zen)], axis=1)


def zenith_deg(directions: np.ndarray) -> np.ndarray:
    """各方向的天顶角（与 +z 的夹角，度）。"""
    return np.degrees(np.arccos(np.clip(directions[:, 2], -1, 1)))


RNG = np.random.default_rng(SEED)
PANELS = (
    ("plate", PLATE, PLATE_AXIS, pose_cloud(0.0, PLATE_ZENITH_STD_DEG, RNG)),
    ("column", COLUMN, COLUMN_AXIS, pose_cloud(90.0, COLUMN_ZENITH_STD_DEG, RNG)),
)
CLOUDS = {name: cloud for name, _, _, cloud in PANELS}
AXES = {name: axis for name, _, axis, _ in PANELS}


def main() -> None:
    extent = np.array([[s * 1.0 if i == k else 0.0 for i in range(3)] for k in range(3) for s in (1, -1)])
    distance = solve_camera_distance([extent], azimuth=AZIMUTH, elevation=ELEVATION, target_fov_deg=FOV_DEG)
    camera = Camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=distance)
    limits = frame(camera, [extent], WIDTH // 2, HEIGHT, margin=0.06)
    fig, axes = multi_panel(1, 2, WIDTH, HEIGHT, DPI, preset=PRESET, titles=list(TITLES), title_frac=0.1)
    for ax, (name, prism, axis, cloud) in zip(axes[0], PANELS):
        graticule(ax, SPHERE, camera=camera, preset=PRESET)
        render_great_circle(ax, SPHERE, camera=camera, preset=PRESET)
        crystal = prism.transformed(crystal_rotation(axis)).transformed(CRYSTAL_SCALE * np.eye(3))
        render_crystal(ax, crystal, camera=camera, preset=PRESET)
        draw_axis_arrow(ax, (0, 0, 0), axis, AXIS_ARROW_LENGTH, camera=camera, preset=PRESET, occluder=crystal,
                        cone_scale=AXIS_CONE_SCALE)
        render_point_cloud(ax, SPHERE, cloud, camera=camera, preset=PRESET)
        finish(ax, *limits)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
