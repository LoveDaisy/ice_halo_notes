# 3.5 / 3.6 共用：特里克尔弧参数方程、太阳高度角、球面 + 弧的基础画法。fig_tricker_arc_plot.py 与
# fig_tricker_arc_cone_plot.py 各自 import 本模块，不各写一份曲线。
import numpy as np

import halo_notes.draw as draw
from halo_notes.draw.style import LineStyle

# 太阳高度角 Σ：取自旧 Mathematica 脚本 code/plot_figures.nb（`With[{s = 10 Degree}, …]`）
SUN_ELEVATION_DEG = 10.0
# 视角同旧 nb：ViewPoint az=-150°, el=12°，ViewAngle 8°（窄视场，近正交观感）
AZIMUTH, ELEVATION, FOV_DEG = -150.0, 12.0, 8.0
GRID_STEP_DEG = 10.0          # 旧 nb：Mesh 间隔 Pi/18
N_CURVE = 721                 # 曲线采样点数（α 从 0 到 2π）
SPHERE = draw.Sphere()
# 旧图观感：细黑网格、只画朝向观察者的半球（球面不透明）
PRESET = draw.PRESETS["default"].replace(style_map=draw.PRESETS["default"].style_map.replace(
    sphere_grid=LineStyle("ink", linewidth=0.45, alpha=0.85)))


def tricker_arc(alpha_rad, sigma_deg: float = SUN_ELEVATION_DEG) -> np.ndarray:
    """正文第 104–110 行的参数方程 r̂'(α)：入射方向取太阳方向 (cos Σ, 0, sin Σ)，经整体变换 T = R M R⁻¹。
    返回 (N, 3) 单位向量。"""
    a = np.asarray(alpha_rad, float)
    s = np.deg2rad(sigma_deg)
    c, k = np.cos(s), np.sin(s)
    r3 = np.sqrt(3.0) / 2
    return np.stack([-0.25 * (3 + np.cos(2 * a)) * c - r3 * np.sin(a) * k,
                     -0.25 * np.sin(2 * a) * c + r3 * np.cos(a) * k,
                     r3 * np.sin(a) * c - 0.5 * k], axis=-1)


def anthelic_point(sigma_deg: float = SUN_ELEVATION_DEG) -> np.ndarray:
    """反日点 ŝ_a = (−cos Σ, 0, sin Σ)（正文第 117 行起：r̂' − ŝ_a = A(α)·(½ sin α, −½ cos α, √3/2)）。"""
    s = np.deg2rad(sigma_deg)
    return np.array([-np.cos(s), 0.0, np.sin(s)])


ALPHA = np.linspace(0.0, 2 * np.pi, N_CURVE)
CURVE = tricker_arc(ALPHA)


def make_camera() -> draw.Camera:
    extent = np.array([[s * 1.0 if i == k else 0.0 for i in range(3)] for k in range(3) for s in (1, -1)])
    d = draw.solve_camera_distance([extent], azimuth=AZIMUTH, elevation=ELEVATION, target_fov_deg=FOV_DEG)
    return draw.Camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=d)


def draw_sphere_and_arc(ax, camera: draw.Camera) -> None:
    """白底球面（只画可见半球的经纬网格）+ 整条特里克尔弧（旧图不分前后，一笔画）。"""
    draw.graticule(ax, SPHERE, camera=camera, preset=PRESET, lat_step=GRID_STEP_DEG, lon_step=GRID_STEP_DEG,
                   hidden_semantic=None)
    draw.render_curve(ax, SPHERE, CURVE, camera=camera, preset=PRESET, split=False)


def limits(camera: draw.Camera, width_px: int, height_px: int, extra_points=()):
    """取景：单位球的六个极点 + 额外点（3.6 的锥面网格），四周留 10% 空白。"""
    extent = np.array([[s * 1.0 if i == k else 0.0 for i in range(3)] for k in range(3) for s in (1, -1)])
    return draw.frame(camera, [extent, *extra_points], width_px, height_px, margin=0.1)
