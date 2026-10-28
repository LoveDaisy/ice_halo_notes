# 图 2a 候选：柱晶的两个周期自由度构成环面，锁住自转后留下 Parry 圆 → ../img/column_torus.png。
from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb

from lumice_integral.symmetry.attitude import column_attitude

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch8_plot", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

MAJOR, MINOR = 2.05, 0.72
PARRY_THETA = 180.0
VIEW_AZ, VIEW_EL = np.radians([-55.0, 36.0])
RIGHT = np.array([-np.sin(VIEW_AZ), np.cos(VIEW_AZ), 0.0])
EYE = np.array([np.cos(VIEW_EL) * np.cos(VIEW_AZ),
                np.cos(VIEW_EL) * np.sin(VIEW_AZ), np.sin(VIEW_EL)])
UP = np.cross(EYE, RIGHT)
CAMERA = np.stack([RIGHT, UP, EYE])
ROLL_COLOR, PARRY_COLOR = P.PAL["arc_roll"], P.PAL["face_5"]


def torus(psi, theta, offset=0.0):
    """度制的参数环面；θ=180° 放在管顶。只保拓扑，不代表轴角坐标或姿态距离。"""
    p, t = np.broadcast_arrays(np.radians(psi), np.radians(theta) - np.pi / 2)
    r = MINOR + offset
    return np.stack([(MAJOR + r * np.cos(t)) * np.cos(p),
                     (MAJOR + r * np.cos(t)) * np.sin(p), r * np.sin(t)], axis=-1)


def attitude(psi, theta):
    """图上每个参数点对应的实际姿态（体坐标到世界坐标）。"""
    return column_attitude(float(psi), float(theta))


def project(points):
    points = np.asarray(points)
    return (points.reshape(-1, 3) @ CAMERA.T).reshape(points.shape)


def signed_distance(xyz):
    radial = np.hypot(xyz[..., 0], xyz[..., 1])
    return np.hypot(radial - MAJOR, xyz[..., 2]) - MINOR


def surface_pixels(width=1401):
    """沿正射相机射线追踪最近表面；同一命中点着色，网格不会穿透或与表面争深度。"""
    height = int(width * 4.2 / 6)
    x, y = np.meshgrid(np.linspace(-3, 3, width), np.linspace(-2.1, 2.1, height))
    origins = (x[..., None] * RIGHT + y[..., None] * UP + 5 * EYE).reshape(-1, 3)
    distance = np.zeros(len(origins))
    active = np.arange(len(origins))
    hit = np.zeros(len(origins), dtype=bool)
    for _ in range(160):
        if not len(active):
            break
        p = origins[active] - distance[active, None] * EYE
        step = signed_distance(p)
        found = step < 2e-5
        hit[active[found]] = True
        distance[active] += step
        active = active[~found & (distance[active] < 10)]
    xyz = origins[hit] - distance[hit, None] * EYE
    radial = np.hypot(xyz[:, 0], xyz[:, 1])
    psi = np.arctan2(xyz[:, 1], xyz[:, 0])
    tube = np.arctan2(xyz[:, 2], radial - MAJOR)
    normals = np.column_stack([np.cos(tube) * np.cos(psi),
                               np.cos(tube) * np.sin(psi), np.sin(tube)])
    light = np.array([-0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    brightness = 0.82 + 0.18 * np.maximum(normals @ light, 0)
    rgb = brightness[:, None] * np.array(to_rgb(P.PAL["ice"]))

    def periodic_distance(angle, period):
        return np.abs((angle + period / 2) % period - period / 2)

    def ink_band(dist, half_width, color):
        coverage = np.clip((half_width + 0.003 - dist) / 0.006, 0, 1)
        rgb[:] = rgb * (1 - coverage[:, None]) + np.array(to_rgb(color)) * coverage[:, None]

    grid_p = periodic_distance(psi, np.pi / 6) * radial
    grid_t = periodic_distance(tube, np.pi / 4) * MINOR
    ink_band(np.minimum(grid_p, grid_t), 0.003, P.PAL["ice_edge"])
    ink_band(periodic_distance(tube - np.pi / 2, 2 * np.pi) * MINOR, 0.012, PARRY_COLOR)
    ink_band(periodic_distance(psi - np.radians(15), 2 * np.pi) * radial, 0.018, ROLL_COLOR)
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    return image.reshape(height, width, 3), xyz


def surface(ax):
    image, _ = surface_pixels()
    ax.imshow(image, origin="lower", extent=(-3, 3, -2.1, 2.1), interpolation="lanczos")


def main():
    P.apply_style()
    fig = plt.figure(figsize=(10.4, 6.4))
    ax = fig.add_axes([0.025, 0.14, 0.95, 0.75])
    ax.set_aspect("equal")
    surface(ax)
    ink = P.PAL["ink_soft"]

    def leader(psi, theta, xytext, text, *, ha="left"):
        xy = project(torus(psi, theta))[:2]
        ax.annotate(text, xy=xy, xytext=xytext, fontsize=12, color=ink, ha=ha,
                    va="center", linespacing=1.65,
                    arrowprops=dict(arrowstyle="-", color=P.PAL["ice_edge"], lw=0.9,
                                    connectionstyle="angle,angleA=0,angleB=90,rad=5"))

    leader(48, 180, (3.1, 1.35), "Parry\n锁住自转角 θ\n只剩方位 ψ 可以转")
    leader(15, 90, (3.1, -0.8), "绕 c 轴自转 θ\n沿管子的小圈转一周")
    leader(-135, 180, (-3.1, 1.5), "c 轴方位 ψ\n沿环面的大圈转一周", ha="right")
    for points, color in (
        (torus(np.linspace(-105, -85, 12), 180, 0.02), PARRY_COLOR),
        (torus(15, np.linspace(95, 125, 12), 0.02), ROLL_COLOR),
    ):
        q = project(points)
        ax.annotate("", xy=q[-1, :2], xytext=q[-4, :2],
                    arrowprops=dict(arrowstyle="-|>", mutation_scale=16, color=color, lw=1.8))
    ax.set_xlim(-4.7, 5.5)
    ax.set_ylim(-2.25, 2.45)
    ax.axis("off")
    fig.text(0.055, 0.935, "柱晶：两个圆的乘积", fontsize=16, color=ink)
    fig.text(0.055, 0.882, "每一点都是一个姿态；两种转动各自走满一圈，都会回到原处。",
             fontsize=10.5, color=ink)
    fig.text(0.5, 0.12, r"$S^1_{\psi}\;\times\;S^1_{\theta}\;=\;T^2$", ha="center",
             fontsize=18, color=ink)
    fig.text(0.5, 0.05, "参数环面示意 · 不是轴角球中的形状，也不表示姿态之间的距离",
             ha="center", fontsize=9, color=ink)
    out = Path(__file__).resolve().parents[1] / "img/column_torus.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
