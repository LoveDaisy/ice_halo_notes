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
from halo_notes.draw.scene import Z_EXTERNAL, Z_INTERNAL, draw_segment, finish, render_crystal
from halo_notes.draw.style import PRESETS
from halo_notes.draw.style.candidate import scheme
from halo_notes.draw.style.mapping import FillStyle, LineStyle

import check_parhelion as optics
from fig_plate_terrain import latitude_minimum

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_ch10_prism_ch8_style", ROOT / "08-wedge-times-fold/code/_ch8_plot.py"
)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

# 颜色全部取自 #48 候选方案的语义槽；图 4 与图 6 共享这些入口。
S = scheme()
INK = S.ink
RAY = S.ray_in            # 入射与冰内段：珊瑚红
RAY_OUT = S.ray_out       # 出射段：蓝（系列光线约定）
ANGLE = S.pair["b"]       # 方位差 Δφ：与图 5 同一个紫
COMPONENT = S.pair["a"]   # 非族的中性强调（k 的分量）：墨
ICE = S.crystal_fill
EDGE = S.crystal_edge
GUIDE = S.guide
PAPER = S.paper
PRISM_STYLE = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(
        face_fill=FillStyle("ice", alpha=0.27),
        ray_incident=LineStyle("accent_warm", linewidth=1.8),
        ray_internal=LineStyle("accent_warm", linewidth=1.8),
        ray_exit=LineStyle("accent_cool", linewidth=1.8),
        ray_occluded=LineStyle("accent_warm", linewidth=1.4, alpha=0.75),
    ),
    geom=PRESETS["ice_filled"].geom.replace(end_markers=False, face_number_height=0.24),
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


def ray_head(ax, p, q, color, zorder=9):
    """光线上的方向箭头：纸面上同一种实心小三角，三维图与俯视图共用（不用锥体，免得近端视成圆环）。"""
    d = (np.asarray(q) - np.asarray(p))
    d = d / np.linalg.norm(d)
    tip = 0.42 * np.asarray(p) + 0.58 * np.asarray(q)
    return ax.annotate("", xy=tip, xytext=tip - 0.01 * d,
                       arrowprops=dict(arrowstyle="-|>", color=color, lw=0,
                                       mutation_scale=19, shrinkA=0, shrinkB=0), zorder=zorder)


def draw_ray3d(ax, scene, camera):
    """真实光路的透视投影：外部段按晶体遮挡分段，冰内段整段画出；入射红、出射蓝。"""
    points = scene.path.points
    exit_hidden = LineStyle("accent_cool", linewidth=1.4, alpha=0.6)
    for (p0, p1, kind), semantic in zip(scene.path.segments(),
                                        ("ray_incident", None, "ray_exit")):
        if semantic is None:
            xy = camera.project_xy(np.stack([p0, p1]))
            ax.plot(*xy.T, color=RAY, lw=1.8, alpha=0.85, solid_capstyle="round", zorder=Z_INTERNAL)
            continue
        draw_segment(ax, p0, p1, camera=camera, preset=PRISM_STYLE, semantic=semantic,
                     occluded_semantic="ray_occluded" if semantic == "ray_incident" else exit_hidden,
                     occluder=scene.crystal,
                     z_visible=Z_EXTERNAL, z_hidden=Z_INTERNAL)
    xy = camera.project_xy(points)
    for i, color in ((0, RAY), (2, RAY_OUT)):
        ray_head(ax, xy[i], xy[i + 1], color)
    return xy


def draw_ray2d(ax, xy, gid):
    """平面投影上的同一条光路：入射 + 冰内段一条红线，出射段蓝线，箭头同 ``ray_head``。"""
    line, = ax.plot(*xy[:3].T, color=RAY, lw=1.8, zorder=4)
    line.set_gid(gid)
    out, = ax.plot(*xy[2:].T, color=RAY_OUT, lw=1.8, zorder=4)
    out.set_gid(f"{gid}-exit")
    for i, color in enumerate((RAY, RAY, RAY_OUT)):
        ray_head(ax, xy[i], xy[i + 1], color, zorder=5)


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
    render_crystal(ax, scene.crystal, camera=CAMERA, preset=PRISM_STYLE, face_numbers=False)
    c_line = np.array([[0, 0, -1.6], [0, 0, 1.85]])
    cp = CAMERA.project_xy(c_line)
    ax.plot(*cp.T, color=EDGE, lw=0.8, ls=(0, (3, 3)), zorder=2)
    arrow(ax, cp[-1] - [0, 0.3], cp[-1], color=EDGE)
    ax.text(*(cp[-1] + [0.12, 0.01]), "竖直棱", color=INK, fontsize=12)
    xy = draw_ray3d(ax, scene, CAMERA)
    ax.text(*(xy[0] + [-0.06, 0.12]), "入射", color=INK, ha="right", fontsize=12)
    ax.text(*(xy[-1] + [0.08, -0.03]), "出射", color=INK, fontsize=12, va="center")
    finish(ax, (-2.25, 2.3), (-1.8, 2.05))


def horizontal_deviation(scene):
    directions = scene.directions[:, :2]
    directions = directions / np.linalg.norm(directions, axis=1, keepdims=True)
    return float(np.degrees(np.arctan2(
        abs(np.linalg.det(directions[[0, -1]])), directions[0] @ directions[-1],
    )))


def wedge_edges(scene):
    """水平截面上入射面 3 与出射面 5 的两条边（纸面坐标）：构成 60° 楔的就是这两面。"""
    top = scene.crystal.face_vertices(scene.crystal.face(1))
    edges = []
    for number in (3, 5):
        face = scene.crystal.face(number)
        normal = scene.crystal.normal(face)
        offset = scene.crystal.face_vertices(face)[0] @ normal
        on_face = np.abs(top @ normal - offset) < 1e-9
        edges.append(top[on_face][:, :2] @ SECTION_BASIS.T)
    return edges


def line_intersection(a, b):
    (p, q), (r, s) = a, b
    d1, d2 = q - p, s - r
    t = np.linalg.solve(np.column_stack([d1, -d2]), r - p)[0]
    return p + t * d1


def draw_section(ax, scene):
    section = scene.crystal.face_vertices(scene.crystal.face(1))[:, :2] @ SECTION_BASIS.T
    ax.add_patch(Polygon(section, facecolor=ICE, edgecolor=EDGE, lw=1.1, alpha=0.55))
    # 构成 60° 楔的两面：加粗画出，各自延长到相交处标出楔角。
    edges = wedge_edges(scene)
    apex = line_intersection(*edges)
    for edge in edges:
        line, = ax.plot(*edge.T, color=EDGE, lw=3.0, solid_capstyle="butt", zorder=3)
        line.set_gid("wedge-face")
        near = edge[np.argmin(np.linalg.norm(edge - apex, axis=1))]
        ax.plot(*np.vstack([near, apex]).T, color=EDGE, lw=0.9, ls=(0, (3, 3)), zorder=3)
    legs = [e.mean(axis=0) - apex for e in edges]
    angles = sorted(np.arctan2(v[1], v[0]) for v in legs)
    if angles[1] - angles[0] > np.pi:
        angles = [angles[1], angles[0] + 2 * np.pi]
    t = np.linspace(*angles, 40)
    ax.plot(*(apex[:, None] + 0.32 * np.vstack([np.cos(t), np.sin(t)])), color=EDGE, lw=0.9)
    mid = np.mean(angles)
    ax.text(*(apex + 0.55 * np.array([np.cos(mid), np.sin(mid)])), "60°", color=INK,
            fontsize=12, ha="center", va="center")
    path_xy = scene.path.points[:, :2] @ SECTION_BASIS.T
    draw_ray2d(ax, path_xy, "projected-ray")
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
    line, = ax.plot(*arc.T, color=ANGLE, lw=1.6, zorder=7)
    line.set_gid("horizontal-deviation-arc")
    ax.annotate("", xy=arc[-1], xytext=arc[-5],
                arrowprops=dict(arrowstyle="->", color=ANGLE, lw=1.6), zorder=7)
    tip = vertex + 1.1 * radius * np.array([np.cos(angles[30]), np.sin(angles[30])])
    ax.text(tip[0] + 0.1, tip[1], f"Δφ = {horizontal_deviation(scene):.2f}°",
            color=INK, fontsize=13, ha="left", va="center")
    finish(ax, (-2.0, 2.9), (-1.42, 1.15))


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
        ax.text(*(0.5 * (start + corner) + [0, 0.3]), label, ha="center",
                fontsize=12, color=INK)
        ax.text(*(0.5 * (start + corner) + [0, 0.03]), r"$k_\perp$", ha="center", va="bottom",
                fontsize=13, color=INK)
        ax.text(*(0.5 * (corner + tip) + [0.09, 0]), r"$k_z$", color=INK,
                fontsize=13, va="center")
    ax.plot([-0.1, 2.9], [kvec[0, 2]] * 2, color=EDGE, lw=0.8, ls=(0, (3, 3)))
    ax.text(2.95, kvec[0, 2], r"$k_z$", fontsize=13, color=INK, va="center")
    ax.text(3.2, kvec[0, 2], "相同", fontsize=12, color=INK, va="center")
    finish(ax, (-0.15, 3.6), (-0.95, 0.55))


def make_figure():
    scenes = build_comparison()
    P.apply_style()
    fig = plt.figure(figsize=(12.4, 8.2))
    for index, (left, scene, title) in enumerate(zip(
        (0.035, 0.525), scenes, ("正穿 · h = 0°", f"斜穿 · h = {SUN_HEIGHT:g}°"),
    )):
        fig.text(left + 0.02, 0.965, title, fontsize=14, color=INK, va="top")
        ax = fig.add_axes([left, 0.575, 0.44, 0.37], label=f"prism-3d-{index}")
        draw_prism(ax, scene)
        fig.text(left + 0.02, 0.57, "从上往下看", fontsize=13, color=INK, va="top")
        ax2 = fig.add_axes([left, 0.29, 0.44, 0.28], label=f"horizontal-section-{index}")
        draw_section(ax2, scene)
        k = scene.wavevectors
        n_eff = np.linalg.norm(k[1, :2]) / np.linalg.norm(k[0, :2])
        fig.text(left + 0.43, 0.33, f"水平截面的 n′ = {n_eff:.3f}", fontsize=13, color=INK,
                 ha="right", va="center")

    fig.add_artist(Line2D([0.055, 0.945], [0.235, 0.235], transform=fig.transFigure,
                         color=GUIDE, lw=0.7))
    fig.text(0.055, 0.215, f"斜穿（h = {SUN_HEIGHT:g}°）时入射面两侧的 k", fontsize=13,
             color=INK, va="top")
    comp = fig.add_axes([0.055, 0.02, 0.44, 0.17], label="wavevector-components")
    draw_components(comp, scenes[1])
    fig.text(0.6, 0.15, r"$\mathbf{k} = n\,\hat{\mathbf{d}}$", fontsize=15, color=INK)
    fig.text(0.6, 0.075, r"$n'=\dfrac{|k_{\perp,\,\mathrm{ice}}|}{|k_{\perp,\,\mathrm{air}}|}"
             r"=\dfrac{\sqrt{n^2-\sin^2h}}{\cos h}$", fontsize=17, color=INK)
    return fig, scenes


def main(output=None):
    fig, _ = make_figure()
    save(fig, "bravais_prism", output)


if __name__ == "__main__":
    cli(main)
