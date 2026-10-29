# 图 2a 候选：柱晶的两个周期自由度构成环面，锁住自转后留下 Parry 圆 → ../img/column_torus.png。
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from halo_notes.draw.projection import Camera

from halo_notes.draw.style.candidate import scheme
from lumice_integral.symmetry.attitude import column_attitude

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch8_plot", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

MAJOR, MINOR = 2.5, 1.0
PARRY_THETA = 180.0
CAMERA = Camera(azimuth=-55, elevation=19, distance=24, projection="perspective")
VIEW_AZ, VIEW_EL = np.radians([CAMERA.azimuth, CAMERA.elevation])
RIGHT, UP, EYE = CAMERA.right, CAMERA.cam_up, CAMERA.view_dir
EXTENT = (-3.8, 3.8, -2.3, 2.3)
# 此簇唯一的镜头、图框与语义色；图 2a/2b 使用完全相同的构图。
FIGSIZE = (11.6, 5.6)
AX_RECT = [0.0, 0.12, 1.0, 0.88]
XLIM, YLIM = (-5.7, 5.7), (-2.3, 2.3)
S = scheme()
# 篇内语义：柱晶蓝、Parry 深蓝、片晶红；「固定一个自由度后剩下的那个转动方向」用紫。
TOKENS = dict(plate=S.family['plate'], parry=S.family['parry'], motion=S.pair['b'],
              ink=S.ink)
PARRY_COLOR, ROLL_COLOR = TOKENS['parry'], TOKENS['motion']


def torus(psi, theta, offset=0.0):
    """度制的参数环面；θ=180° 放在管顶。只保拓扑，不代表轴角坐标或姿态距离。"""
    p, t = np.broadcast_arrays(np.radians(psi), np.radians(theta) - np.pi / 2)
    r = MINOR + offset
    return np.stack([(MAJOR + r * np.cos(t)) * np.cos(p),
                     (MAJOR + r * np.cos(t)) * np.sin(p), r * np.sin(t)], axis=-1)


def attitude(psi, theta):
    """图上每个参数点对应的实际姿态（体坐标到世界坐标）。"""
    return column_attitude(float(psi), float(theta))


def project(points, camera=CAMERA):
    """保留 (..., 3) 输出 API：透视 xy，加 Camera 的朝观察者深度（非射线距离）。"""
    points = np.asarray(points)
    xy, depth = camera.project(points.reshape(-1, 3))
    return np.column_stack([xy, depth]).reshape(points.shape)


def camera_rays(xy, camera=CAMERA):
    """Camera 像平面（过原点）的逆投影；所有射线同源于 camera.position。"""
    if camera.projection != "perspective":
        raise ValueError("环面渲染必须使用 perspective Camera")
    xy = np.asarray(xy).reshape(-1, 2)
    origins = np.broadcast_to(camera.position, (len(xy), 3))
    directions = xy[:, :1] * camera.right + xy[:, 1:] * camera.cam_up - origins
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    return origins, directions


def pixel_rays(width, extent=EXTENT, camera=CAMERA):
    """像素中心取样，与 imshow 的像素边界 extent 精确互逆。"""
    left, right, bottom, top = extent
    height = round(width * (top - bottom) / (right - left))
    x = left + (np.arange(width) + 0.5) * (right - left) / width
    y = bottom + (np.arange(height) + 0.5) * (top - bottom) / height
    xx, yy = np.meshgrid(x, y)
    origins, directions = camera_rays(np.column_stack([xx.ravel(), yy.ravel()]), camera)
    return height, origins, directions


def trace(origins, directions, *, tolerance=2e-5, max_steps=420):
    distance = np.zeros(len(origins))
    active = np.arange(len(origins))
    depths = np.full(len(origins), np.inf)
    for _ in range(max_steps):
        if not len(active):
            break
        points = origins[active] + distance[active, None] * directions[active]
        step = np.abs(signed_distance(points))
        found = step < tolerance
        depths[active[found]] = distance[active[found]]
        distance[active] += step
        active = active[~found & (distance[active] < 2 * CAMERA.distance)]
    return depths


def line_visibility(points):
    points = np.asarray(points).reshape(-1, 3)
    origins, directions = camera_rays(project(points)[:, :2])
    nearest = trace(origins, directions, tolerance=1e-8, max_steps=12000)
    return np.linalg.norm(points - origins, axis=1) <= nearest + 0.002


def signed_distance(xyz):
    radial = np.hypot(xyz[..., 0], xyz[..., 1])
    return np.hypot(radial - MAJOR, xyz[..., 2]) - MINOR


def outline_mask(depth, jump=0.25):
    """轮廓 = 命中/未命中交界或射线深度跳变处的命中像素（相邻两像素内）。

    只认深度跳变：两张环面的连续交接（图 3 的 Parry 交线）不画成轮廓。
    """
    hit = np.isfinite(depth)
    filled = np.where(hit, depth, np.inf)
    edge = np.zeros_like(hit)
    with np.errstate(invalid='ignore'):
        for axis in (0, 1):
            for shift in (1, -1, 2, -2):
                other = np.roll(filled, shift, axis=axis)
                edge |= hit & ((other - filled) > jump)
    return edge


def surface_pixels(width=1401, finish="column", *, ring_color=PARRY_COLOR,
                   meridian_color=ROLL_COLOR, rings=None, meridian_phi=15.0):
    """发散透视射线的最近命中；网格与语义圈只在命中表面着色。

    finish 取候选方案里的曲面处理（"column" 柱晶环面 / "lowitz" Lowitz 环面）；
    rings 为 (母圆弧度角, 颜色)；省略时保留图 2a 管顶 Parry 圈。
    """
    height, origins, directions = pixel_rays(width)
    distance = trace(origins, directions)
    hit = np.isfinite(distance)
    xyz = origins[hit] + distance[hit, None] * directions[hit]
    radial = np.hypot(xyz[:, 0], xyz[:, 1])
    psi = np.arctan2(xyz[:, 1], xyz[:, 0])
    tube = np.arctan2(xyz[:, 2], radial - MAJOR)
    normals = np.column_stack([np.cos(tube) * np.cos(psi),
                               np.cos(tube) * np.sin(psi), np.sin(tube)])
    light = np.array([-0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    surface = S.surfaces[finish]
    brightness = surface.ambient + (1 - surface.ambient) * np.maximum(normals @ light, 0)
    rgb = brightness[:, None] * np.array(to_rgb(surface.base))

    def periodic_distance(angle, period):
        return np.abs((angle + period / 2) % period - period / 2)

    def ink_band(dist, half_width, color):
        coverage = np.clip((half_width + 0.003 - dist) / 0.006, 0, 1)
        rgb[:] = rgb * (1 - coverage[:, None]) + np.array(to_rgb(color)) * coverage[:, None]

    grid_p = periodic_distance(psi, 2 * np.pi / 12) * radial
    grid_t = periodic_distance(tube, 2 * np.pi / 8) * MINOR
    ink_band(np.minimum(grid_p, grid_t), surface.mesh_width, surface.mesh)
    for angle, color in ([(np.pi / 2, ring_color)] if rings is None else rings):
        ink_band(periodic_distance(tube - angle, 2 * np.pi) * MINOR, 0.018, color)
    if meridian_color is not None:
        ink_band(periodic_distance(psi - np.radians(meridian_phi), 2 * np.pi) * radial,
                 0.018, meridian_color)
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    image = image.reshape(height, width, 3)
    image[outline_mask(distance.reshape(height, width))] = to_rgb(surface.outline)
    return image, xyz


def surface(ax, finish="column"):
    image, _ = surface_pixels(finish=finish)
    ax.imshow(image, origin="lower", extent=EXTENT, interpolation="lanczos")


def figure_axes():
    P.apply_style()
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_axes(AX_RECT)
    ax.set(xlim=XLIM, ylim=YLIM, aspect="equal")
    ax.axis("off")
    return fig, ax


def motion_arrow(ax, points, color):
    """沿曲面上一段可见曲线画带箭头的弧（不取弦）；整段须未被遮挡。"""
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.path import Path as MplPath

    points = np.asarray(points)
    if not line_visibility(points).all():
        raise ValueError("箭头落在环面背面")
    q = project(points)[:, :2]
    ax.add_patch(FancyArrowPatch(path=MplPath(q), arrowstyle="-|>", mutation_scale=16,
                                 color=color, lw=1.8, zorder=6))


THETA_PHI = 0.0   # 自转方向那条小圈所在的方位：偏离正对镜头，免得被画成一根竖棍


def main(out=None):
    fig, ax = figure_axes()
    image, _ = surface_pixels(meridian_phi=THETA_PHI)
    ax.imshow(image, origin="lower", extent=EXTENT, interpolation="lanczos")
    ink = TOKENS["ink"]

    def leader(psi, theta, xytext, text, color, *, ha="left"):
        xy = project(torus(psi, theta))[:2]
        ax.annotate(text, xy=xy, xytext=xytext, fontsize=13, color=color, ha=ha,
                    va="center", linespacing=1.5,
                    arrowprops=dict(arrowstyle="-", color=ink, lw=0.7, shrinkA=3,
                                    connectionstyle="angle,angleA=0,angleB=90,rad=5"))

    leader(48, 180, (3.9, 1.45), "Parry 圈\n锁住自转角 θ\n只剩方位 ψ 可转", PARRY_COLOR)
    leader(THETA_PHI, 40, (3.9, -1.0), "绕 c 轴自转 θ\n沿管子的小圈转一周", ROLL_COLOR)
    leader(-135, 180, (-3.9, 1.55), "c 轴方位 ψ\n沿环面的大圈转一周", ink, ha="right")
    motion_arrow(ax, torus(np.linspace(-120, -75, 30), 180), PARRY_COLOR)
    motion_arrow(ax, torus(THETA_PHI, np.linspace(45, 135, 40)), ROLL_COLOR)
    fig.text(0.06, 0.08, r"$S^1_{\psi}\times S^1_{\theta}=T^2$", fontsize=18, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / "img/column_torus.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    main(parser.parse_args().output)
