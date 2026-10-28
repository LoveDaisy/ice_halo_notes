# 图 6：水平柱晶的真实光路与太阳正上 / 正下的几何切点 → ../img/tangent_direction.png。
from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import numpy as np

from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish, render_crystal

from fig_bravais_prism import (
    COMPONENT, EDGE, GUIDE, ICE, INK, P, PAPER, PRISM_STYLE, RAY,
    PrismScene, arrow, cli, minimum_sun_direction, optics, save, traced_scene,
)

SUN_HEIGHT = 20.0
CAMERA = Camera(azimuth=-38, elevation=18, distance=10, projection="perspective")


@dataclass(frozen=True)
class TangentScene:
    sun: np.ndarray
    upper: PrismScene
    lower: PrismScene
    radius: float
    circle: np.ndarray


def build_scene(height=SUN_HEIGHT):
    """将最小偏向的真实截面转到过太阳的竖直面；两个不同姿态给出上下切点。"""
    sun = optics.unit_from(height, 0.0)
    body_sun = minimum_sun_direction(0.0)
    body_c = np.array([0.0, 0.0, 1.0])
    body_frame = np.column_stack([body_sun, np.cross(body_c, body_sun), body_c])
    cases = []
    for sign in (1, -1):
        c_axis = np.array([0.0, float(sign), 0.0])
        world_frame = np.column_stack([sun, np.cross(c_axis, sun), c_axis])
        rotation = world_frame @ body_frame.T
        cases.append(traced_scene(body_sun, rotation))
    cases.sort(key=lambda scene: scene.light_point[2])
    lower, upper = cases
    # 几何等角距圈，不包含光强信息；半径取实际追迹落点，不写死 22°。
    radius = float(np.degrees(np.arccos(np.clip(upper.light_point @ sun, -1, 1))))
    east = np.array([0.0, 1.0, 0.0])
    north = np.cross(sun, east)
    angles = np.linspace(0, 2 * np.pi, 721)
    r = np.radians(radius)
    circle = np.cos(r) * sun + np.sin(r) * (
        np.cos(angles)[:, None] * east + np.sin(angles)[:, None] * north
    )
    return TangentScene(sun, upper, lower, radius, circle)


def draw_attitude(ax, scene):
    # 光路面 y=0，法向平行 c；薄填充在晶体背后，不充当物理界面。
    plane = np.array([[-2, 0, -1.5], [2, 0, -1.5], [2, 0, 1.5], [-2, 0, 1.5]])
    ax.add_patch(Polygon(CAMERA.project_xy(plane), facecolor=ICE,
                         edgecolor=GUIDE, alpha=0.22, lw=0.8, zorder=0))
    render_crystal(ax, scene.crystal, [scene.path], camera=CAMERA,
                   preset=PRISM_STYLE, face_numbers=False)
    c_axis = scene.rotation[:, 2]
    ends = CAMERA.project_xy(np.array([-1.8, 1.8])[:, None] * c_axis)
    ax.plot(*ends.T, color=EDGE, lw=1.0, ls=(0, (3, 3)), zorder=8)
    arrow(ax, ends[0], ends[-1], color=EDGE, lw=1.0, zorder=8)
    label_at = ends[np.argmax(ends[:, 0])]
    ax.text(*(label_at + [0.32, 0.04]), "c 轴", fontsize=10, color=INK)
    # 实际截面多边形（沿 c 轴的中面）与光线共面，用于辨认竖直光路面。
    body_vertices = (scene.crystal.vertices @ scene.rotation)[:6].copy()
    body_vertices[:, 2] = 0.0
    section = body_vertices @ scene.rotation.T
    cross_section = CAMERA.project_xy(np.vstack([section, section[0]]))
    line, = ax.plot(*cross_section.T, color=COMPONENT, lw=1.2, zorder=7)
    line.set_gid("vertical-cross-section")
    xy = CAMERA.project_xy(scene.path.points)
    source_label_y = 1.35 if xy[0, 1] > 0 else -1.4
    ax.annotate("来自太阳", xy=xy[0], xytext=(2.32, source_label_y), ha="right",
                fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=EDGE, lw=0.7))
    ax.annotate("出射传播", xy=xy[-1], xytext=(-2.25, -1.25), ha="left",
                fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=EDGE, lw=0.7))
    finish(ax, (-2.4, 2.5), (-1.7, 1.65))


def make_figure():
    data = build_scene()
    P.apply_style()
    fig = plt.figure(figsize=(12.5, 8.1))
    fig.text(0.045, 0.94, "切点为什么在太阳的正上、正下？", fontsize=18, color=INK)
    fig.text(0.045, 0.89, "c 轴水平且垂直于太阳方位 → 光路面竖直 → 光点与太阳同方位", fontsize=11, color=INK)
    fig.text(0.055, 0.825, "两个真实姿态，各自达到最小偏向", fontsize=12, color=INK)
    fig.text(0.55, 0.825, "天空方向 · 太阳高度 20°", fontsize=12, color=INK)

    top = fig.add_axes([0.025, 0.49, 0.45, 0.31], label="upper-prism")
    bottom = fig.add_axes([0.025, 0.155, 0.45, 0.31], label="lower-prism")
    draw_attitude(top, data.upper)
    draw_attitude(bottom, data.lower)
    top.text(0.035, 0.97, "上切点的姿态", transform=top.transAxes, fontsize=10.5, color=INK, va="top")
    bottom.text(0.035, 0.97, "下切点的姿态", transform=bottom.transAxes, fontsize=10.5, color=INK, va="top")

    sky = fig.add_axes([0.55, 0.22, 0.40, 0.55], label="sky-directions")
    az, el = optics.az_el(data.circle)
    ring, = sky.plot(az, el, color=EDGE, lw=1.1, ls=(0, (4, 3)))
    ring.set_gid("angular-distance-circle")
    sky.axvline(0, color=GUIDE, lw=0.9, zorder=0)
    sky.axhline(0, color=EDGE, lw=0.8, zorder=0)
    sky.text(-32, 1.4, "地平线", fontsize=9.5, color=INK)
    sky.fill_between([-35, 35], -12, 0, color=GUIDE, alpha=0.22, zorder=-1)
    sky.scatter(0, SUN_HEIGHT, marker="*", s=150, color=RAY, edgecolor=PAPER,
                linewidth=0.7, zorder=5)
    sky.text(3, SUN_HEIGHT, "太阳 20°", color=INK, fontsize=10.5, va="center")
    for scene, name, marker, offset in (
        (data.upper, "上切点", "^", (6, 5)),
        (data.lower, "下切点（地平线下）", "v", (6, -6)),
    ):
        a, e = optics.az_el(scene.light_point)
        point, = sky.plot([a], [e], marker=marker, markersize=8, linestyle="none",
                          markerfacecolor=COMPONENT if e >= 0 else PAPER,
                          markeredgecolor=COMPONENT, markeredgewidth=1.4, zorder=6)
        point.set_gid("upper-tangent" if e > SUN_HEIGHT else "lower-tangent")
        sky.annotate(f"{name}\n{e:.2f}°", xy=(a, e), xytext=(a + offset[0], e + offset[1]),
                     fontsize=10, color=INK, va="center",
                     arrowprops=dict(arrowstyle="-", color=EDGE, lw=0.8))
    sky.text(-31, 49, f"等角距圈 D = {data.radius:.2f}°", fontsize=10.5, color=INK)
    sky.text(-31, 45, "（22° 晕的内缘）", fontsize=10, color=INK)
    sky.set(xlim=(-35, 35), ylim=(-12, 55), xlabel="方位差 Δφ", ylabel="高度角")
    sky.set_aspect("equal")
    sky.set_xticks([-30, -15, 0, 15, 30], ["−30°", "−15°", "0°", "15°", "30°"])
    sky.set_yticks([0, 20, 40], ["0°", "20°", "40°"])
    sky.tick_params(labelsize=10)

    fig.legend(handles=[Line2D([], [], color=RAY, lw=1.8, label="光的传播方向"),
                        Line2D([], [], color=COMPONENT, lw=1.2, label="竖直截面 / 几何切点")],
               loc="lower left", bbox_to_anchor=(0.045, 0.105), ncol=2, labelcolor=INK)
    fig.text(0.045, 0.075, "天空光点", fontsize=11, color=INK)
    fig.text(0.12, 0.075, r"$\mathbf{x}=-\hat{\mathbf{d}}_{\rm out}$", fontsize=12, color=INK)
    fig.text(0.22, 0.075, "看向出射传播的反方向。", fontsize=11, color=INK)
    fig.text(0.045, 0.035, "这里只标几何切点与角距圈，不画亮弧；下切点在此太阳高度下位于地平线下，不代表可见天象。",
             fontsize=10.5, color=INK)
    return fig, data


def main(output=None):
    fig, _ = make_figure()
    save(fig, "tangent_direction", output)


if __name__ == "__main__":
    cli(main)
