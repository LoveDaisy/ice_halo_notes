# 图 4：真实 3-5 光路的竖直守恒与 Bravais 水平截面 → ../img/bravais_prism.png。
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


def make_figure():
    scene = build_scene()
    P.apply_style()
    fig = plt.figure(figsize=(12.4, 7.7))
    fig.text(0.045, 0.94, "斜着穿过，水平偏得更多", fontsize=18, color=INK)
    fig.text(0.045, 0.89, "同一条 3 → 5 光路：沿竖直棱守恒，偏折发生在水平截面内", fontsize=11, color=INK)
    fig.text(0.06, 0.825, "竖直棱镜中的真实光路", fontsize=12.5, color=INK)
    fig.text(0.56, 0.825, "同一光路的水平投影", fontsize=12.5, color=INK)

    ax = fig.add_axes([0.035, 0.345, 0.46, 0.46], label="prism-3d")
    render_crystal(ax, scene.crystal, [scene.path], camera=CAMERA,
                   preset=PRISM_STYLE, face_numbers=False)
    c_line = np.array([[0, 0, -1.6], [0, 0, 1.95]])
    cp = CAMERA.project_xy(c_line)
    ax.plot(*cp.T, color=EDGE, lw=0.9, ls=(0, (3, 3)), zorder=2)
    arrow(ax, cp[-1] - [0, 0.3], cp[-1], color=EDGE)
    ax.text(*(cp[-1] + [0.10, 0.04]), "c 轴（竖直）", color=INK, fontsize=10)
    xy = CAMERA.project_xy(scene.path.points)
    ax.text(*(xy[0] + [-0.06, 0.16]), "入射", color=INK, ha="right", fontsize=10)
    ax.text(*(xy[-1] + [0.07, -0.02]), "出射", color=INK, fontsize=10)
    # 在冰内真实传播段上作 k 的分解三角；向量的长度不是光程。
    anchor = scene.path.points[1] * 0.65 + scene.path.points[2] * 0.35
    k = scene.wavevectors[1] * 0.75
    horizontal = k.copy()
    horizontal[2] = 0
    tri = CAMERA.project_xy([anchor, anchor + horizontal, anchor + k])
    arrow(ax, tri[0], tri[1], zorder=10)
    arrow(ax, tri[1], tri[2], zorder=10)
    ax.text(*(tri[1] + [0.08, 0.05]), r"$k_{\perp}$", color=INK, fontsize=11)
    ax.text(*(0.5 * (tri[1] + tri[2]) + [0.12, 0]), r"$k_z$", color=INK, fontsize=11)
    finish(ax, (-2.2, 2.3), (-2.0, 2.3))

    # 分量比较是 2D 示意，纵轴为真实 k_z，而非透视图上的屏幕长度。
    comp = fig.add_axes([0.055, 0.15, 0.43, 0.145], label="wavevector-components")
    kvec = scene.wavevectors
    bases = np.array([0.0, 1.7, 3.4])
    labels = ("空气 · 入射", "冰内", "空气 · 出射")
    for base, k, label in zip(bases, kvec, labels):
        tip = np.array([base + np.linalg.norm(k[:2]), k[2]])
        line, = comp.plot([base, tip[0]], [0, tip[1]], color=RAY, lw=1.6)
        line.set_gid("wavevector")
        arrow(comp, (base, 0), tip, color=RAY)
        arrow(comp, (base, 0), (tip[0], 0), color=COMPONENT, lw=1.1)
        arrow(comp, (tip[0], 0), tip, color=COMPONENT, lw=1.1)
        comp.text(base + 0.48, 0.17, label, ha="center", fontsize=9.5, color=INK)
    comp.axhline(kvec[0, 2], color=EDGE, lw=0.8, ls=(0, (3, 3)))
    comp.text(0.85, -1.02, r"$k_z=-\sin h$", ha="center", fontsize=10.5, color=INK)
    comp.text(3.1, -1.02, "空气 → 冰 → 空气，一路相同", ha="center", fontsize=10, color=INK)
    finish(comp, (-0.15, 4.9), (-1.12, 0.4))
    fig.text(0.06, 0.315, "分量比较：k = n × 单位传播方向", fontsize=10.5, color=INK)

    ax2 = fig.add_axes([0.54, 0.37, 0.43, 0.41], label="horizontal-section")
    section = scene.crystal.face_vertices(scene.crystal.face(1))[:, :2] @ SECTION_BASIS.T
    ax2.add_patch(Polygon(section, facecolor=ICE, edgecolor=EDGE, lw=1.3))
    path_xy = scene.path.points[:, :2] @ SECTION_BASIS.T
    line, = ax2.plot(*path_xy.T, color=RAY, lw=1.8, zorder=4)
    line.set_gid("projected-ray")
    for p, q in zip(path_xy[:-1], path_xy[1:]):
        arrow(ax2, 0.65 * p + 0.35 * q, 0.4 * p + 0.6 * q, color=RAY, zorder=5)
    for event in scene.path.events:
        point = path_xy[event.point_index]
        normal = scene.crystal.normal(scene.crystal.face(event.face_number))[:2] @ SECTION_BASIS.T
        endpoints = point + np.array([-0.35, 0.55])[:, None] * normal
        ax2.plot(*endpoints.T, color=EDGE, lw=0.9, ls=(0, (3, 3)))
        ax2.scatter(*point, color=RAY, s=18, zorder=6)
        ax2.text(*(point + normal * 0.72), f"面 {event.face_number}",
                 fontsize=10, color=INK, ha="center", va="bottom")
    ax2.text(0, 0.38, "60° 楔", color=INK, ha="center", fontsize=12)
    ax2.text(0, 0.14, "虚线为界面法线", color=INK, ha="center", fontsize=9)
    finish(ax2, (-1.85, 1.85), (-1.3, 1.3))
    n_eff, dphi = optics.bravais(SUN_HEIGHT)
    fig.text(0.57, 0.30, r"$n'=\dfrac{\sqrt{n^2-\sin^2h}}{\cos h}>n$", fontsize=17, color=INK)
    fig.text(0.57, 0.235, f"h = {SUN_HEIGHT:g}°：n = {optics.N:g} → n′ = {n_eff:.3f}",
             fontsize=11, color=INK)
    fig.text(0.57, 0.185, f"水平偏折 Δφ = {dphi:.2f}°；不是天空角距离 D", fontsize=10.5, color=INK)
    fig.legend(handles=[Line2D([], [], color=RAY, lw=1.8, label="光的传播方向"),
                        Line2D([], [], color=COMPONENT, lw=1.5, label="分解后的分量")],
               loc="lower left", bbox_to_anchor=(0.045, 0.065), ncol=2, labelcolor=INK)
    fig.text(0.045, 0.035, "天空光点看向出射传播的反方向：入、出空气中的 k_z 相同，所以光点与太阳同高。",
             fontsize=10.5, color=INK)
    return fig, scene


def main(output=None):
    fig, _ = make_figure()
    save(fig, "bravais_prism", output)


if __name__ == "__main__":
    cli(main)
