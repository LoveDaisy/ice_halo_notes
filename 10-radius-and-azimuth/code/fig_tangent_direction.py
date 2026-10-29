# 图 6：柱晶正穿 / 斜穿的真光路与等角距天空上的切弧 → ../img/tangent_direction.png。
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.patches import Polygon
import numpy as np

from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish, render_crystal

from fig_bravais_prism import (
    COMPONENT, EDGE, GUIDE, ICE, INK, P, PAPER, PRISM_STYLE, S,
    PrismScene, arrow, cli, draw_ray2d, draw_ray3d, minimum_sun_direction, optics, save,
    traced_scene,
)

COLUMN = S.family["column"]   # 切弧属柱晶族：聚焦轨迹与光点都用柱晶蓝
SUN = S.sun

from fig_solar_circle import sky_xy as sky_projection

SUN_HEIGHT = 25.0
OBLIQUITIES = (0.0, 40.0, 55.0)
CAMERA = Camera(azimuth=-38, elevation=18, distance=10, projection="perspective")


@dataclass(frozen=True)
class TangentScene:
    sun: np.ndarray
    upper: PrismScene
    lower: PrismScene
    radius: float
    circle: np.ndarray
    examples: tuple[PrismScene, ...]
    obliquities: np.ndarray
    radii: np.ndarray
    fold_beta: np.ndarray
    folds: tuple[np.ndarray, np.ndarray]


@lru_cache(maxsize=512)
def minimum_pose(beta, height=SUN_HEIGHT, branch=-1):
    """固定水平 c 轴，绕轴取横截面的最小偏折；branch=-1 为上支。"""
    sun = optics.unit_from(height, 0.0)
    body_sun = minimum_sun_direction(beta)
    body_c = np.array([0.0, 0.0, 1.0])
    body_transverse = body_sun.copy()
    body_transverse[2] = 0.0
    body_transverse /= np.linalg.norm(body_transverse)
    # s·c=sin β；c 水平，故 c_x=sin β/cos h。不是把竖直片晶旋转后仍称柱晶。
    cx = body_sun[2] / sun[0]
    if abs(cx) >= 1:
        raise ValueError("此斜穿角不在水平柱晶的可取带内")
    c_axis = np.array([cx, branch * np.sqrt(1 - cx * cx), 0.0])
    transverse = sun - (sun @ c_axis) * c_axis
    transverse /= np.linalg.norm(transverse)
    world_frame = np.column_stack([transverse, np.cross(c_axis, transverse), c_axis])
    body_frame = np.column_stack([body_transverse, np.cross(body_c, body_transverse), body_c])
    return world_frame @ body_frame.T


def sky_point(rotation, sun):
    """固定 c 轴时出射点在 c·x=c·s 的小圆上，横截面偏折极小令自转导数为零。

    test_tangent_revision 再检查另一自由度导数非零、核方向的法向二阶项非零、
    映射的有向面积跨过该姿态变号，才将这条曲线称为折叠聚焦轨迹。
    """
    return rotation @ optics.light_point(rotation.T @ sun)[0]


def distance_circle(sun, radius):
    angles = np.linspace(0, 2 * np.pi, 721)
    east = np.array([0.0, 1.0, 0.0])
    up = np.cross(sun, east)
    r = np.radians(radius)
    return np.cos(r) * sun + np.sin(r) * (
        np.cos(angles)[:, None] * east + np.sin(angles)[:, None] * up
    )


def build_scene(height=SUN_HEIGHT):
    sun = optics.unit_from(height, 0.0)
    examples = tuple(traced_scene(minimum_sun_direction(beta), minimum_pose(beta, height))
                     for beta in OBLIQUITIES)
    lower = traced_scene(minimum_sun_direction(0.0), minimum_pose(0.0, height, 1))
    radii = np.array([np.degrees(np.arctan2(np.linalg.norm(np.cross(sun, scene.light_point)),
                                          sun @ scene.light_point)) for scene in examples])
    # 每一点都重新取该水平 c 轴下的横截面最小偏折；不是连接三幅示意姿态。
    # 只画 |β|≤55° 的正透射局部，避免把掠射末端当作可见亮像的边界。
    beta = np.linspace(-55.0, 55.0, 221)
    folds = tuple(np.array([sky_point(minimum_pose(float(b), height, branch), sun) for b in beta])
                  for branch in (-1, 1))
    return TangentScene(sun, examples[0], lower, radii[0], distance_circle(sun, radii[0]),
                        examples, np.array(OBLIQUITIES), radii, beta, folds)


def draw_attitude(ax, scene):
    render_crystal(ax, scene.crystal, camera=CAMERA, preset=PRISM_STYLE, face_numbers=False)
    draw_ray3d(ax, scene, CAMERA)
    c_axis = scene.rotation[:, 2]
    ends = CAMERA.project_xy(np.array([-1.8, 1.8])[:, None] * c_axis)
    ax.plot(*ends.T, color=EDGE, lw=0.9, ls=(0, (3, 3)), zorder=8)
    arrow(ax, ends[0], ends[-1], color=EDGE, lw=0.9, zorder=8)
    label_at = ends[np.argmax(ends[:, 0])]
    ax.text(*(label_at + [0.12, 0.06]), "c 轴", fontsize=12, color=INK)
    # 横截面始终垂直于 c，斜穿光路不必共面；不用虚构竖直光路平面托住它。
    body_vertices = (scene.crystal.vertices @ scene.rotation)[:6].copy()
    body_vertices[:, 2] = 0.0
    section = body_vertices @ scene.rotation.T
    cross_section = CAMERA.project_xy(np.vstack([section, section[0]]))
    line, = ax.plot(*cross_section.T, color=COMPONENT, lw=0.9, alpha=0.55, zorder=7)
    line.set_gid("transverse-section")
    finish(ax, (-2.4, 2.6), (-1.65, 1.65))


def draw_section(ax, scene):
    body_points = scene.path.points @ scene.rotation
    body_vertices = scene.crystal.vertices @ scene.rotation
    section = body_vertices[:6, :2]
    ax.add_patch(Polygon(section, facecolor=ICE, edgecolor=EDGE, lw=1.0))
    draw_ray2d(ax, body_points[:, :2], "transverse-ray")
    finish(ax, (-1.7, 1.7), (-1.6, 1.6))


def make_figure():
    data = build_scene()
    P.apply_style()
    fig = plt.figure(figsize=(12.8, 8.0))
    halo = [patheffects.withStroke(linewidth=3, foreground=PAPER)]
    fig.text(0.08, 0.965, "三维光路", fontsize=13, color=INK, va="top")
    fig.text(0.35, 0.965, "垂直 c 轴看", fontsize=13, color=INK, va="top")
    fig.text(0.57, 0.965, f"以太阳为中心的天空（h = {SUN_HEIGHT:g}°）· 半径 = 角距 D",
             fontsize=13, color=INK, va="top")

    for index, (scene, beta, radius, tag) in enumerate(zip(data.examples, data.obliquities,
                                                         data.radii, "ABC")):
        y = 0.68 - index * 0.315
        ax = fig.add_axes([0.025, y, 0.28, 0.255], label=f"prism-{tag}")
        draw_attitude(ax, scene)
        section = fig.add_axes([0.325, y + 0.015, 0.17, 0.23], label=f"section-{tag}")
        draw_section(section, scene)
        kind = "正穿" if beta == 0 else "斜穿"
        n_eff = optics.bravais(beta)[0]
        fig.text(0.05, y - 0.01, f"{tag}  {kind}  β = {beta:g}°", fontsize=13, color=INK)
        fig.text(0.325, y - 0.01, f"n′ = {n_eff:.3f}   D = {radius:.2f}°", fontsize=12, color=INK)

    sky = fig.add_axes([0.53, 0.03, 0.46, 0.88], label="sky-directions")
    for index, radius in enumerate(data.radii):
        xy = sky_projection(distance_circle(data.sun, radius), data.sun)
        ring, = sky.plot(*xy.T, color=EDGE if index == 0 else GUIDE, lw=1.0,
                         ls=(0, (4, 3)), zorder=0)
        ring.set_gid("angular-distance-circle" if index == 0 else f"distance-circle-{index}")
        # 圈的读数放在右下象限：那里没有切弧与地平线，标签不压线。
        angle = np.radians(-10 - 10 * index)
        sky.text((radius + 0.6) * np.cos(angle), (radius + 0.6) * np.sin(angle),
                 f"{radius:.2f}°", color=INK, fontsize=12, ha="left", va="top",
                 path_effects=halo)
    for branch, points in zip(("upper", "lower"), data.folds):
        line, = sky.plot(*sky_projection(points, data.sun).T, color=COLUMN, lw=2.0)
        line.set_gid(f"{branch}-fold")
    horizon = optics.unit_from(0, np.linspace(-65, 65, 301))
    line, = sky.plot(*sky_projection(horizon, data.sun).T, color=EDGE, lw=0.8,
                    ls=(0, (2, 3)), zorder=0)
    line.set_gid("horizon")
    sky.text(-41, -21.5, "地平线", color=INK, fontsize=12, va="bottom")
    sky.scatter(0, 0, s=90, color=SUN, edgecolor=PAPER, linewidth=1, zorder=5)
    sky.text(2.2, 0, "太阳", color=INK, fontsize=13, va="center")
    for tag, scene in zip("ABC", data.examples):
        xy = sky_projection(scene.light_point, data.sun)
        point, = sky.plot(*xy, marker="o", markersize=8, linestyle="none", color=COLUMN,
                          markeredgecolor=PAPER, markeredgewidth=1.2, zorder=6)
        point.set_gid(f"example-{tag}")
        offset = {"A": (1.6, 2.2), "B": (-1.2, 2.6), "C": (-4.2, 1.4)}[tag]
        sky.text(*(xy + offset), tag, fontsize=14, color=INK, path_effects=halo)
    lower_xy = sky_projection(data.lower.light_point, data.sun)
    point, = sky.plot(*lower_xy, marker="o", markersize=7, linestyle="none", color=COLUMN,
                      markeredgecolor=PAPER, markeredgewidth=1.1, zorder=6)
    point.set_gid("lower-tangent")
    lower_height = np.degrees(np.arcsin(data.lower.light_point[2]))
    # 切点正上方、22° 圈以内没有别的线：标签放在那里，不用引线。
    sky.text(lower_xy[0], lower_xy[1] + 2.0, f"下切点\n高度 {lower_height:.2f}°", fontsize=12,
             color=INK, ha="center", va="bottom", linespacing=1.4, path_effects=halo)
    sky.text(-7, 40, "上切弧", fontsize=13, color=INK)
    sky.text(-7, -39, "下切弧", fontsize=13, color=INK)
    finish(sky, (-44, 44), (-44, 44))
    return fig, data


def main(output=None):
    fig, _ = make_figure()
    save(fig, "tangent_direction", output)


if __name__ == "__main__":
    cli(main)
