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
FIGSIZE = (11.6, 7.2)
AX_RECT = [0.025, 0.24, 0.95, 0.58]
XLIM, YLIM = (-5.7, 5.7), (-2.4, 2.4)
ROLL_COLOR, PARRY_COLOR = P.PAL["arc_roll"], P.PAL["face_5"]
TOKENS = dict(plate=ROLL_COLOR, parry=PARRY_COLOR, motion=P.PAL["ink_soft"],
              mesh=P.PAL["ice_edge"], ink=P.PAL["ink_soft"])
# 待作者选择的表面处理；不改变参数、相机或强调圈的语义。
SURFACES = {
    "original": (P.PAL["ice"], 0.82, P.PAL["ice_edge"], 12, 8),
    "chalk": ("#E7E3DB", 0.88, "#C6C0B5", 6, 4),
    "mineral": ("#BFD0CA", 0.90, "#A4B6AF", 6, 4),
}


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


def surface_pixels(width=1401, style="original", *, ring_color=PARRY_COLOR,
                   meridian_color=ROLL_COLOR, rings=None, meridian_phi=15.0):
    """发散透视射线的最近命中；网格与语义圈只在命中表面着色。

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
    base, ambient, grid_color, n_psi, n_theta = SURFACES[style]
    brightness = ambient + (1 - ambient) * np.maximum(normals @ light, 0)
    rgb = brightness[:, None] * np.array(to_rgb(base))

    def periodic_distance(angle, period):
        return np.abs((angle + period / 2) % period - period / 2)

    def ink_band(dist, half_width, color):
        coverage = np.clip((half_width + 0.003 - dist) / 0.006, 0, 1)
        rgb[:] = rgb * (1 - coverage[:, None]) + np.array(to_rgb(color)) * coverage[:, None]

    grid_p = periodic_distance(psi, 2 * np.pi / n_psi) * radial
    grid_t = periodic_distance(tube, 2 * np.pi / n_theta) * MINOR
    ink_band(np.minimum(grid_p, grid_t), 0.003, grid_color)
    for angle, color in ([(np.pi / 2, ring_color)] if rings is None else rings):
        ink_band(periodic_distance(tube - angle, 2 * np.pi) * MINOR, 0.018, color)
    if meridian_color is not None:
        ink_band(periodic_distance(psi - np.radians(meridian_phi), 2 * np.pi) * radial,
                 0.018, meridian_color)
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    return image.reshape(height, width, 3), xyz


def surface(ax, style="original"):
    image, _ = surface_pixels(style=style)
    ax.imshow(image, origin="lower", extent=EXTENT, interpolation="lanczos")


def figure_axes(title, subtitle):
    P.apply_style()
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_axes(AX_RECT)
    ax.set(xlim=XLIM, ylim=YLIM, aspect="equal")
    ax.axis("off")
    fig.text(0.055, 0.935, title, fontsize=17, color=TOKENS['ink'])
    fig.text(0.055, 0.882, subtitle, fontsize=10.5, color=TOKENS['ink'])
    return fig, ax


def motion_arrow(ax, points, color):
    """箭头只落在同一透视射线下未被遮挡的一小段。"""
    points = np.asarray(points)
    if not line_visibility(points).all():
        raise ValueError("箭头落在环面背面")
    q = project(points)
    ax.annotate("", xy=q[-1, :2], xytext=q[0, :2],
                arrowprops=dict(arrowstyle="-|>", mutation_scale=16, color=color, lw=1.8))


def main(style="original", out=None):
    if style != "original" and out is None:
        raise ValueError("候选变体必须显式指定输出路径，不能覆盖原图")
    fig, ax = figure_axes("柱晶：两个圆的乘积",
                          "每一点都是一个姿态；两种转动各自走满一圈，都会回到原处。")
    surface(ax, style)
    ink = TOKENS["ink"]

    def leader(psi, theta, xytext, text, *, ha="left"):
        xy = project(torus(psi, theta))[:2]
        ax.annotate(text, xy=xy, xytext=xytext, fontsize=12, color=ink, ha=ha,
                    va="center", linespacing=1.65,
                    arrowprops=dict(arrowstyle="-", color=P.PAL["ice_edge"], lw=0.9,
                                    connectionstyle="angle,angleA=0,angleB=90,rad=5"))

    leader(48, 180, (3.85, 1.35), "Parry\n锁住自转角 θ\n只剩方位 ψ 可以转")
    leader(15, 90, (3.85, -0.85), "绕 c 轴自转 θ\n沿管子的小圈转一周")
    leader(-135, 180, (-3.85, 1.5), "c 轴方位 ψ\n沿环面的大圈转一周", ha="right")
    motion_arrow(ax, torus(np.linspace(-105, -85, 12), 180), PARRY_COLOR)
    motion_arrow(ax, torus(15, np.linspace(95, 125, 12)), ROLL_COLOR)
    fig.legend(handles=[Line2D([], [], color=PARRY_COLOR, lw=2, label='Parry 定角圈'),
                        Line2D([], [], color=ROLL_COLOR, lw=2, label='固定方位下的自转')],
               loc='lower center', bbox_to_anchor=(0.5, 0.205), ncol=2, labelcolor=ink)
    fig.text(0.5, 0.13, r"$S^1_{\psi}\;\times\;S^1_{\theta}\;=\;T^2$", ha="center",
             fontsize=18, color=ink)
    fig.text(0.5, 0.075, "这里只强调一条 Parry 圈；另一条原始交圈未高亮，并非同一原始点集。",
             ha="center", fontsize=9.5, color=ink)
    fig.text(0.5, 0.035, "参数环面示意 · 不是轴角球中的形状，也不表示姿态之间的距离",
             ha="center", fontsize=9, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / "img/column_torus.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", choices=SURFACES, default="original")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    main(args.style, args.output)
