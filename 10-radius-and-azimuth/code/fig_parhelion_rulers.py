# 图 5：同一天球上的夹角与水平投影夹角 → ../img/parhelion_rulers.png。
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import numpy as np

from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import _plot_runs
from halo_notes.draw.sphere import Sphere

import check_parhelion as C
from fig_plate_terrain import P, plt

COLORS = {'distance': P.PAL['arc_roll'], 'azimuth': P.PAL['face_5'],
          'ink': P.PAL['ink_soft'], 'guide': P.PAL['reference'],
          'edge': P.PAL['ice_edge'], 'sphere': P.PAL['ice'],
          'paper': P.PAL['background']}
CAMERA = Camera(azimuth=-32, elevation=22, distance=5, projection='perspective')
SUN_HEIGHT = 40.0
ANGLE_RADIUS = 0.36


@dataclass(frozen=True)
class RulerGeometry:
    height: float
    directions: np.ndarray
    projections: np.ndarray
    great_circle: np.ndarray
    horizontal_arc: np.ndarray
    meridians: np.ndarray
    latitude: np.ndarray
    equator: np.ndarray
    distance: float
    azimuth: float


def curve_data(heights=None):
    if heights is None:
        heights = np.r_[np.linspace(0, C.critical_height() - 0.001, 801),
                        C.critical_height(), 62., 65.]
    heights = np.asarray(heights, dtype=float)
    azimuth = np.full(heights.shape, np.nan)
    distance = np.full(heights.shape, np.nan)
    for index, h in np.ndenumerate(heights):
        _, delta = C.bravais(h)
        if h < C.critical_height() and delta is not None:
            azimuth[index] = delta
            distance[index] = C.spherical_distance(h, delta)
    return heights, distance, azimuth


def ruler_geometry(height=SUN_HEIGHT):
    """同高的两个天空方向；大圆由向量球面插值，不把纬线弧当作 D。"""
    _, delta = C.bravais(height)
    if height < 0 or height >= C.critical_height() or delta is None:
        raise ValueError('height must lie below the grazing critical height')
    directions = C.unit_from(height, np.array([-delta / 2, delta / 2]))
    # 沿经线落到赤道的是单位方位方向，不是长度 cos(h) 的垂足。
    projections = directions.copy()
    projections[:, 2] = 0.0
    projections /= np.linalg.norm(projections, axis=1, keepdims=True)
    distance = C.spherical_distance(height, delta)
    angle = np.radians(distance)
    t = np.linspace(0.0, 1.0, 181)
    great_circle = (np.sin((1 - t) * angle)[:, None] * directions[0]
                    + np.sin(t * angle)[:, None] * directions[1]) / np.sin(angle)
    horizontal_arc = C.unit_from(0.0, np.linspace(-delta / 2, delta / 2, len(t)))
    meridian_heights = np.unique(np.r_[np.linspace(0, 90, 181), height])[::-1]
    meridians = np.stack([C.unit_from(meridian_heights, np.full_like(meridian_heights, az))
                          for az in (-delta / 2, delta / 2)])
    azimuths = np.linspace(0, 360, 721)
    return RulerGeometry(float(height), directions, projections, great_circle,
                         horizontal_arc, meridians, C.unit_from(height, azimuths),
                         C.unit_from(0, azimuths), float(distance), float(delta))


def plot3(ax, points, *, gid=None, **kwargs):
    line, = ax.plot(*CAMERA.project_xy(points).T, **kwargs)
    if gid:
        line.set_gid(gid)
    return line


def angle_arrows(ax, points, color, *, gid=None):
    """弧本身来自几何；短箭头仅沿弧两端的切向，不另拟圆弧。"""
    for i, (start, end) in enumerate(((points[9], points[0]), (points[-10], points[-1]))):
        tip = ax.annotate('', xy=end, xytext=start,
                          arrowprops=dict(arrowstyle='-|>', color=color, lw=1.4,
                                          mutation_scale=11, shrinkA=0, shrinkB=0),
                          zorder=7)
        if gid:
            tip.set_gid(f'{gid}-{i}')


def sphere_outline():
    # 真透视轮廓：单位球切点满足 x·camera.position=1。
    t = np.linspace(0, 2 * np.pi, 361)
    center = CAMERA.view_dir / CAMERA.distance
    radius = np.sqrt(1 - 1 / CAMERA.distance**2)
    return center + radius * (np.cos(t)[:, None] * CAMERA.right
                              + np.sin(t)[:, None] * CAMERA.cam_up)


def surface_guide(ax, points, *, dotted=False):
    """共用球面朝向与切段机制；背面减淡，纬线另用点线区分。"""
    visible = dict(color=COLORS['edge'], lw=0.9,
                   ls=(0, (1.5, 3)) if dotted else '-')
    hidden = dict(color=COLORS['guide'], lw=0.75, ls=(0, (1.5, 3)))
    _plot_runs(ax, points, Sphere().facing(points, CAMERA), CAMERA,
               visible, hidden, 1, -1)


def sky_panel(ax, data):
    ink = COLORS['ink']
    rim = CAMERA.project_xy(sphere_outline())
    ax.add_patch(Polygon(rim, facecolor=COLORS['sphere'], alpha=0.20,
                         edgecolor='none', zorder=-10))
    ax.plot(*rim.T, color=COLORS['edge'], lw=0.9, zorder=-2)
    ax.add_patch(Polygon(CAMERA.project_xy(data.equator), facecolor=COLORS['sphere'],
                         alpha=0.35, edgecolor='none', zorder=-5))
    surface_guide(ax, data.equator)
    surface_guide(ax, data.latitude, dotted=True)
    plot3(ax, [[0, 0, -1], [0, 0, 1]], color=COLORS['guide'], lw=0.7, zorder=-1)
    north = CAMERA.project_xy([0, 0, 1])[0]
    ax.scatter(*north, s=22, color=ink, zorder=8)
    ax.annotate('天顶', xy=north, xytext=(-9, 10), textcoords='offset points',
                ha='right', va='bottom', color=ink, fontsize=11)

    for i, (direction, foot, meridian) in enumerate(zip(
            data.directions, data.projections, data.meridians)):
        plot3(ax, meridian, gid=f'meridian-{i}', color=COLORS['edge'], lw=1.25, zorder=3)
        plot3(ax, [np.zeros(3), foot], gid=f'equatorial-radius-{i}',
              color=COLORS['azimuth'], lw=1.45, ls=(0, (5, 2)), zorder=5)
        xy = CAMERA.project_xy(direction)[0]
        fp = CAMERA.project_xy(foot)[0]
        ax.scatter(*xy, marker='*' if i == 0 else 'o', s=155 if i == 0 else 55,
                   facecolor=COLORS['distance'], edgecolor=COLORS['paper'],
                   linewidth=1, zorder=8)
        ax.scatter(*fp, s=40, facecolor=COLORS['paper'],
                   edgecolor=COLORS['azimuth'], linewidth=1.5, zorder=8)
        ax.annotate('太阳' if i == 0 else '幻日', xy=xy,
                    xytext=(-12, -5) if i == 0 else (12, 0), textcoords='offset points',
                    ha='right' if i == 0 else 'left', va='center', color=ink, fontsize=12)
        ax.annotate('太阳的方位' if i == 0 else '幻日的方位', xy=fp,
                    xytext=(-12, -16) if i == 0 else (15, -4), textcoords='offset points',
                    ha='right' if i == 0 else 'left', va='top', color=ink, fontsize=10.5)

    plot3(ax, data.great_circle, gid='sky-great-circle',
          color=COLORS['distance'], lw=0.9, alpha=0.55, zorder=4)
    for i, direction in enumerate(data.directions):
        plot3(ax, np.array([np.zeros(3), direction]), gid=f'central-radius-{i}',
              color=COLORS['distance'], lw=1.4, zorder=5)
    # 同一大圆在两半径张成的平面内缩小，弧两端仍各落在一条半径上。
    central_arc = ANGLE_RADIUS * data.great_circle
    plot3(ax, central_arc, gid='central-angle-arc',
          color=COLORS['distance'], lw=2.2, zorder=6)
    angle_arrows(ax, CAMERA.project_xy(central_arc), COLORS['distance'],
                 gid='central-angle-tip')
    origin = CAMERA.project_xy(np.zeros(3))[0]
    ax.scatter(*origin, s=25, color=ink, zorder=8)
    ax.annotate('O', xy=origin, xytext=(-9, -8), textcoords='offset points',
                ha='right', va='top', color=ink, fontsize=12)
    dmid = CAMERA.project_xy(central_arc[len(central_arc)//2])[0]
    ax.annotate(f'D = {data.distance:.2f}°', xy=dmid, xytext=(-0.12, 0.25),
                color=ink, fontsize=12, ha='right',
                arrowprops=dict(arrowstyle='-', color=COLORS['distance'], lw=0.8))
    plot3(ax, data.horizontal_arc, gid='equatorial-azimuth-arc',
          color=COLORS['azimuth'], lw=0.9, ls=(0, (5, 2)), alpha=0.65, zorder=4)
    azimuth_arc = 0.56 * data.horizontal_arc
    plot3(ax, azimuth_arc, gid='equatorial-angle-arc',
          color=COLORS['azimuth'], lw=2.2, ls=(0, (5, 2)), zorder=6)
    angle_arrows(ax, CAMERA.project_xy(azimuth_arc), COLORS['azimuth'],
                 gid='equatorial-angle-tip')
    amid = CAMERA.project_xy(azimuth_arc[len(azimuth_arc)//2])[0]
    ax.annotate(f'Δφ = {data.azimuth:.2f}°', xy=amid, xytext=(0.45, -0.78),
                color=ink, fontsize=12, ha='center',
                arrowprops=dict(arrowstyle='-', color=COLORS['azimuth'], lw=0.8))
    lat_label = CAMERA.project_xy(C.unit_from(data.height, -80))[0]
    ax.annotate('同高度纬线（小圆）', xy=lat_label, xytext=(-0.70, 0.09),
                color=ink, fontsize=10.5, ha='center',
                arrowprops=dict(arrowstyle='-', color=COLORS['edge'], lw=0.7))
    equator_label = CAMERA.project_xy(C.unit_from(0, -80))[0]
    ax.annotate('赤道（水平大圆）', xy=equator_label, xytext=(-0.50, -0.56),
                color=ink, fontsize=10.5, ha='center',
                arrowprops=dict(arrowstyle='-', color=COLORS['edge'], lw=0.7))
    ax.set(xlim=(-1.23, 1.43), ylim=(-1.10, 1.13), aspect='equal')
    ax.axis('off')


def make_figure(height=SUN_HEIGHT):
    P.apply_style()
    data = ruler_geometry(height)
    ink = COLORS['ink']
    fig = plt.figure(figsize=(9.4, 8.0))
    fig.text(0.055, 0.94, '同一个天球，两把角度尺', fontsize=18, color=ink)
    fig.text(0.055, 0.885, f'太阳与幻日同高 h = {height:g}°；两条经线从天顶经过它们，落到赤道。',
             fontsize=11.5, color=ink)
    ax = fig.add_axes([0.025, 0.17, 0.95, 0.67], label='celestial-sphere')
    sky_panel(ax, data)
    fig.legend(handles=[Line2D([], [], color=COLORS['distance'], lw=2, label='球心夹角 · 角距 D'),
                        Line2D([], [], color=COLORS['azimuth'], lw=2, ls=(0, (5, 2)),
                               label='球心夹角 · 方位差 Δφ')],
               loc='lower center', bbox_to_anchor=(0.5, 0.095), ncol=2,
               labelcolor=ink, handlelength=3)
    fig.text(0.5, 0.055, '角度按球心量，不按纸面弧长量；同高纬线不是量 D 的那条大圆。',
             ha='center', fontsize=10.5, color=ink)
    return fig, data


def main(out=None):
    fig, _ = make_figure()
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/parhelion_rulers.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
