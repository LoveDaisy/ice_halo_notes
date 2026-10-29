# 图 4：同一竖直楔的正穿 / 斜穿、水平偏折与单界面分量 → ../img/bravais_prism.png。
from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import numpy as np

from halo_notes.draw.geometry import HexPrism, Polyhedron
from halo_notes.draw.projection import Camera
from halo_notes.draw.raypath import RayPath, search_raypath
from halo_notes.draw.scene import finish, render_crystal
from halo_notes.draw.style import PRESETS
from halo_notes.draw.style.mapping import FillStyle, LineStyle

import check_parhelion as optics
from fig_plate_terrain import latitude_minimum

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch10_prism_ch8_style", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

# 几何、光线和分量各司其职；不复制系列调色板。两图共享这些语义入口。
INK = P.PAL["ink_soft"]
RAY = P.PAL["accent_warm"]
COMPONENT = P.PAL["arc_roll"]
ICE = P.PAL["ice"]
EDGE = P.PAL["ice_edge"]
GUIDE = P.PAL["reference"]
PAPER = P.PAL["background"]
PRISM_STYLE = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(
        face_fill=FillStyle("ice", alpha=0.27),
        ray_incident=LineStyle("accent_warm", linewidth=1.8),
        ray_internal=LineStyle("accent_warm", linewidth=1.8),
        ray_exit=LineStyle("accent_warm", linewidth=1.8),
        ray_occluded=LineStyle("accent_warm", linewidth=1.4, alpha=0.75),
    ),
    geom=PRESETS["ice_filled"].geom.replace(
        cone_length=0.18, cone_radius=0.055, cone_rings=1,
        end_markers=False, face_number_height=0.24,
    ),
)
CAMERA = Camera(azimuth=40, elevation=22, distance=9, projection="perspective")
SUN_HEIGHT = 40.0
# 水平截面的纸面旋转：与立体图同向阅读，仍为等比例二维投影。
SECTION_BASIS = np.array([CAMERA.right[:2], [-CAMERA.right[1], CAMERA.right[0]]])


@dataclass(frozen=True)
class PrismScene:
    crystal: Polyhedron
    path: RayPath
    rotation: np.ndarray
    sun: np.ndarray

    @property
    def directions(self):
        segments = np.diff(self.path.points, axis=0)
        return segments / np.linalg.norm(segments, axis=1, keepdims=True)

    @property
    def wavevectors(self):
        """k = n d；d 是单位传播方向，不把冰内 d_z 误当守恒量。"""
        return self.directions * np.array([1.0, optics.N, 1.0])[:, None]

    @property
    def light_point(self):
        # 天空光点是出射传播的反向，不是从晶体指向下游的射线。
        return -self.directions[-1]


def minimum_sun_direction(height):
    """只选取景方向；定义域与 D 的唯一实现仍是 check_parhelion / LI。"""
    return latitude_minimum(height)[0]


def traced_scene(body_sun, rotation=None, *, height=2.8):
    """在有限六棱柱内寻找 3-5 真光路；方向固定，不允许求解器换光源。"""
    rotation = np.eye(3) if rotation is None else np.asarray(rotation)
    crystal = HexPrism(a=0.9, h=height)
    # 全部候选入射点在晶体 z=0 的截面上；图 6 的整条光路因此位于过原点的竖直面。
    face = crystal.face_vertices(crystal.face(3))
    midpoint = crystal.centroid(crystal.face(3))
    edge = face[1] - face[0]
    edge = edge / np.linalg.norm(edge)
    points = midpoint + np.linspace(-0.30, 0.30, 13)[:, None] * edge
    path = search_raypath(
        crystal, optics.PATH, np.atleast_2d(-body_sun),
        entry_points=points, n_ice=optics.N, tail=1.3, head=1.3,
    )
    return PrismScene(crystal.transformed(rotation=rotation),
                      path.transformed(rotation=rotation), rotation, rotation @ body_sun)


def build_scene(height=SUN_HEIGHT):
    return traced_scene(minimum_sun_direction(height))


def arrow(ax, start, end, *, color=COMPONENT, lw=1.5, **kwargs):
    return ax.annotate("", xy=end, xytext=start,
                       arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                       mutation_scale=12, shrinkA=0, shrinkB=0), **kwargs)


def save(fig, name, output=None):
    output = Path(output) if output else Path(__file__).resolve().parents[1] / f"img/{name}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(output)


def cli(main):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    main(parser.parse_args().output)


def build_comparison():
    """同一有限晶体的两条真实光路；两例各自在给定高度上取最小偏向。"""
    return build_scene(0.0), build_scene(SUN_HEIGHT)


def draw_prism(ax, scene):
    render_crystal(ax, scene.crystal, [scene.path], camera=CAMERA,
                   preset=PRISM_STYLE, face_numbers=False)
    c_line = np.array([[0, 0, -1.6], [0, 0, 1.85]])
    cp = CAMERA.project_xy(c_line)
    ax.plot(*cp.T, color=EDGE, lw=0.8, ls=(0, (3, 3)), zorder=2)
    arrow(ax, cp[-1] - [0, 0.3], cp[-1], color=EDGE)
    ax.text(*(cp[-1] + [0.12, 0.01]), "竖直棱", color=INK, fontsize=10)
    xy = CAMERA.project_xy(scene.path.points)
    ax.text(*(xy[0] + [-0.04, 0.18]), "入射", color=INK, ha="right", fontsize=10)
    ax.text(*(xy[-1] + [0.06, -0.03]), "出射", color=INK, fontsize=10)
    finish(ax, (-2.25, 2.3), (-1.8, 2.05))


def horizontal_deviation(scene):
    directions = scene.directions[:, :2]
    directions = directions / np.linalg.norm(directions, axis=1, keepdims=True)
    return float(np.degrees(np.arctan2(
        abs(np.linalg.det(directions[[0, -1]])), directions[0] @ directions[-1],
    )))


def draw_section(ax, scene):
    section = scene.crystal.face_vertices(scene.crystal.face(1))[:, :2] @ SECTION_BASIS.T
    ax.add_patch(Polygon(section, facecolor=ICE, edgecolor=EDGE, lw=1.1))
    path_xy = scene.path.points[:, :2] @ SECTION_BASIS.T
    line, = ax.plot(*path_xy.T, color=RAY, lw=1.8, zorder=4)
    line.set_gid("projected-ray")
    for p, q in zip(path_xy[:-1], path_xy[1:]):
        arrow(ax, 0.7 * p + 0.3 * q, 0.4 * p + 0.6 * q, color=RAY, zorder=5)
    for event in scene.path.events:
        point = path_xy[event.point_index]
        ax.scatter(*point, color=RAY, s=19, edgecolors=PAPER, linewidths=0.5, zorder=6)
    # 将入射方向平移到出射点，弧线量的是实际水平偏折，不是两面夹角。
    vertex = path_xy[2]
    d_in = path_xy[1] - path_xy[0]
    d_out = path_xy[3] - path_xy[2]
    a0 = np.arctan2(d_in[1], d_in[0])
    da = np.arctan2(np.linalg.det(np.array([d_in, d_out])), d_in @ d_out)
    angles = a0 + np.linspace(0, da, 61)
    radius = 0.72
    arc = vertex + radius * np.column_stack([np.cos(angles), np.sin(angles)])
    ax.plot(*np.vstack([vertex, vertex + 1.15 * d_in / np.linalg.norm(d_in)]).T,
            color=EDGE, lw=0.9, ls=(0, (3, 3)))
    line, = ax.plot(*arc.T, color=COMPONENT, lw=1.5, zorder=7)
    line.set_gid("horizontal-deviation-arc")
    ax.annotate("", xy=arc[-1], xytext=arc[-5],
                arrowprops=dict(arrowstyle="->", color=COMPONENT, lw=1.5), zorder=7)
    ax.text(0.0, 0.48, "同一个 60° 楔", color=INK, ha="center", fontsize=11)
    ax.text(1.35, -0.70, f"Δφ = {horizontal_deviation(scene):.2f}°",
            color=INK, fontsize=12, ha="center")
    ax.text(1.64, -0.43, "入射方向延长", color=INK, fontsize=8.5, ha="center")
    finish(ax, (-2.15, 2.5), (-1.03, 1.02))


def draw_components(ax, scene):
    """入射面两侧 k 的分量大小图；横向取模，不冒充同一空间内的光线路径。"""
    kvec = scene.wavevectors[:2]
    for base, k, label in zip((0.0, 1.55), kvec, ("空气", "冰内")):
        start = np.array([base, 0.0])
        corner = start + [np.linalg.norm(k[:2]), 0.0]
        tip = corner + [0.0, k[2]]
        line, = ax.plot(*np.vstack([start, tip]).T, color=RAY, lw=1.6)
        line.set_gid("wavevector")
        arrow(ax, start, tip, color=RAY)
        arrow(ax, start, corner, color=COMPONENT, lw=1.2)
        arrow(ax, corner, tip, color=COMPONENT, lw=1.2)
        ax.text(*(0.5 * (start + corner) + [0, 0.13]), label, ha="center",
                fontsize=10.5, color=INK)
        ax.text(*(0.5 * (corner + tip) + [0.09, 0]), r"$k_z$", color=INK,
                fontsize=11, va="center")
    ax.plot([-0.1, 2.9], [kvec[0, 2]] * 2, color=EDGE, lw=0.8, ls=(0, (3, 3)))
    ax.text(1.3, -0.93, "同一入射界面：竖直分量不变，水平分量增大", ha="center",
            fontsize=10, color=INK)
    finish(ax, (-0.15, 3.05), (-1.03, 0.38))


def make_figure():
    scenes = build_comparison()
    P.apply_style()
    fig = plt.figure(figsize=(12.4, 9.2))
    fig.text(0.045, 0.95, "同一个楔，斜穿时水平偏折更大", fontsize=18, color=INK)
    fig.text(0.045, 0.905, "正穿指光线垂直棱轴；两例都取各自的最小偏向光路。", fontsize=11, color=INK)
    for index, (left, scene, title) in enumerate(zip(
        (0.035, 0.525), scenes, ("正穿 · h = 0°", f"斜穿 · h = {SUN_HEIGHT:g}°"),
    )):
        fig.text(left + 0.02, 0.855, title, fontsize=13, color=INK)
        ax = fig.add_axes([left, 0.525, 0.44, 0.31], label=f"prism-3d-{index}")
        draw_prism(ax, scene)
        fig.text(left + 0.02, 0.49, "从上往下看", fontsize=11, color=INK)
        ax2 = fig.add_axes([left, 0.285, 0.44, 0.19], label=f"horizontal-section-{index}")
        draw_section(ax2, scene)
        k = scene.wavevectors
        n_eff = np.linalg.norm(k[1, :2]) / np.linalg.norm(k[0, :2])
        fig.text(left + 0.15, 0.26, f"水平截面的 n′ = {n_eff:.3f}", fontsize=12, color=INK)

    fig.add_artist(Line2D([0.055, 0.945], [0.225, 0.225], transform=fig.transFigure,
                         color=GUIDE, lw=0.7))
    fig.text(0.055, 0.195, "斜穿时，为什么 n′ 变大？", fontsize=12, color=INK)
    comp = fig.add_axes([0.055, 0.025, 0.40, 0.155], label="wavevector-components")
    draw_components(comp, scenes[1])
    fig.text(0.54, 0.16, "k = n × 单位传播方向", fontsize=11, color=INK)
    fig.text(0.54, 0.105, r"$n'=\dfrac{|k_{\perp,\,\mathrm{ice}}|}{|k_{\perp,\,\mathrm{air}}|}"
             r"=\dfrac{\sqrt{n^2-\sin^2h}}{\cos h}$", fontsize=16, color=INK)
    fig.legend(handles=[Line2D([], [], color=RAY, lw=1.8, label="光线 / k"),
                        Line2D([], [], color=COMPONENT, lw=1.5, label="角度 / 分量")],
               loc="lower left", bbox_to_anchor=(0.525, 0.035), ncol=2, labelcolor=INK)
    return fig, scenes


def main(output=None):
    fig, _ = make_figure()
    save(fig, "bravais_prism", output)


if __name__ == "__main__":
    cli(main)
