# 图 5：同一天球上的夹角与水平投影夹角 → ../img/parhelion_rulers.png。
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import numpy as np

from halo_notes.draw.projection import Camera

import check_parhelion as C
from fig_plate_terrain import P, plt

COLORS = {'distance': P.PAL['arc_roll'], 'azimuth': P.PAL['face_5'],
          'ink': P.PAL['ink_soft'], 'guide': P.PAL['reference'],
          'edge': P.PAL['ice_edge'], 'sphere': P.PAL['ice'],
          'paper': P.PAL['background']}
CAMERA = Camera(azimuth=0, elevation=18, distance=5, projection='perspective')
SUN_HEIGHT = 40.0


@dataclass(frozen=True)
class RulerGeometry:
    height: float
    directions: np.ndarray
    projections: np.ndarray
    great_circle: np.ndarray
    horizontal_arc: np.ndarray
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
    projections = directions.copy()
    projections[:, 2] = 0.0
    distance = C.spherical_distance(height, delta)
    angle = np.radians(distance)
    t = np.linspace(0.0, 1.0, 181)
    great_circle = (np.sin((1 - t) * angle)[:, None] * directions[0]
                    + np.sin(t * angle)[:, None] * directions[1]) / np.sin(angle)
    horizontal_arc = C.unit_from(0.0, np.linspace(-delta / 2, delta / 2, len(t)))
    return RulerGeometry(float(height), directions, projections, great_circle,
                         horizontal_arc, float(distance), float(delta))


def plot3(ax, points, *, gid=None, **kwargs):
    line, = ax.plot(*CAMERA.project_xy(points).T, **kwargs)
    if gid:
        line.set_gid(gid)
    return line


def angle_arrows(ax, points, color):
    """弧本身来自几何；短箭头仅沿弧两端的切向，不另拟圆弧。"""
    for start, end in ((points[9], points[0]), (points[-10], points[-1])):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1.4,
                                    mutation_scale=11, shrinkA=0, shrinkB=0))


def sphere_outline():
    # 真透视轮廓：单位球切点满足 x·camera.position=1。
    t = np.linspace(0, 2 * np.pi, 361)
    center = CAMERA.view_dir / CAMERA.distance
    radius = np.sqrt(1 - 1 / CAMERA.distance**2)
    return center + radius * (np.cos(t)[:, None] * CAMERA.right
                              + np.sin(t)[:, None] * CAMERA.cam_up)


def sky_panel(ax, data):
    ink = COLORS['ink']
    rim = CAMERA.project_xy(sphere_outline())
    ax.add_patch(Polygon(rim, facecolor=COLORS['sphere'], alpha=0.20,
                         edgecolor='none', zorder=-10))
    ax.plot(*rim.T, color=COLORS['edge'], lw=0.9, zorder=-2)
    az = np.linspace(0, 360, 721)
    horizon = C.unit_from(0, az)
    ax.add_patch(Polygon(CAMERA.project_xy(horizon), facecolor=COLORS['sphere'],
                         alpha=0.35, edgecolor='none', zorder=-5))
    plot3(ax, horizon, color=COLORS['edge'], lw=0.8, zorder=-1)
    latitude = C.unit_from(data.height, az)
    plot3(ax, latitude, color=COLORS['guide'], lw=0.85, ls=(0, (2, 3)), zorder=0)
    plot3(ax, [[0, 0, -1], [0, 0, 1.15]], color=COLORS['guide'], lw=0.8, zorder=-1)
    north = CAMERA.project_xy([0, 0, 1.15])[0]
    ax.text(*north, '天顶', ha='center', va='bottom', color=ink, fontsize=10)

    for i, (direction, foot) in enumerate(zip(data.directions, data.projections)):
        plot3(ax, [[0, 0, 0], direction], gid=f'direction-{i}',
              color=COLORS['distance'], lw=1.45, zorder=3)
        plot3(ax, [[0, 0, 0], foot], gid=f'projection-{i}',
              color=COLORS['azimuth'], lw=1.45, ls=(0, (5, 2)), zorder=3)
        plot3(ax, [direction, foot], gid=f'drop-{i}', color=COLORS['edge'],
              lw=0.9, ls=(0, (3, 3)), zorder=2)
        xy = CAMERA.project_xy(direction)[0]
        fp = CAMERA.project_xy(foot)[0]
        ax.scatter(*xy, marker='*' if i == 0 else 'o', s=140 if i == 0 else 48,
                   facecolor=COLORS['distance'], edgecolor=COLORS['paper'],
                   linewidth=1, zorder=8)
        ax.scatter(*fp, s=30, facecolor=COLORS['paper'],
                   edgecolor=COLORS['azimuth'], linewidth=1.4, zorder=8)
        dx = -0.14 if i == 0 else 0.14
        ax.text(xy[0] + dx, xy[1] + 0.045, '太阳' if i == 0 else '幻日',
                ha='right' if i == 0 else 'left', color=ink, fontsize=12)
    plot3(ax, data.great_circle, gid='sky-great-circle',
          color=COLORS['distance'], lw=2.1, zorder=5)
    arc = data.great_circle * 0.58
    plot3(ax, arc, gid='central-distance-arc', color=COLORS['distance'], lw=1.6, zorder=5)
    angle_arrows(ax, CAMERA.project_xy(arc), COLORS['distance'])
    dmid = CAMERA.project_xy(arc[len(arc)//2])[0]
    ax.annotate(f'D = {data.distance:.2f}°', xy=dmid, xytext=(0.48, 0.21),
                color=ink, fontsize=11.5, ha='left',
                arrowprops=dict(arrowstyle='-', color=COLORS['distance'], lw=0.8))
    delta_arc = data.horizontal_arc * 0.50
    plot3(ax, delta_arc, gid='horizontal-angle-arc', color=COLORS['azimuth'],
          lw=1.5, ls=(0, (5, 2)), zorder=5)
    angle_arrows(ax, CAMERA.project_xy(delta_arc), COLORS['azimuth'])
    amid = CAMERA.project_xy(delta_arc[len(delta_arc)//2])[0]
    ax.annotate('Δφ', xy=amid, xytext=(0.40, -0.40), color=ink, fontsize=13,
                arrowprops=dict(arrowstyle='-', color=COLORS['azimuth'], lw=0.8))
    ax.scatter(0, 0, s=18, color=ink, zorder=8)
    ax.text(-0.07, 0.015, 'O', ha='right', va='bottom', color=ink, fontsize=11)
    ax.text(-0.90, -0.30, '水平面', color=ink, fontsize=10)
    ax.text(0, -1.17, 'D 沿两方向张成的大圆量，不沿同高纬线量。',
            ha='center', color=ink, fontsize=10.5)
    ax.set(xlim=(-1.28, 1.30), ylim=(-1.28, 1.27), aspect='equal')
    ax.axis('off')


def horizontal_panel(ax, data):
    ink = COLORS['ink']
    # 俯视坐标的纵轴对准两方向的角平分线，只换纸面基，不改变夹角。
    def top_view(points):
        points = np.asarray(points)
        return np.stack([points[..., 1], points[..., 0]], axis=-1)

    phi = np.linspace(-55, 55, 181)
    arc = C.unit_from(0, phi) * np.cos(np.radians(data.height))
    ax.plot(*top_view(arc).T, color=COLORS['guide'], lw=0.9)
    for i, foot in enumerate(data.projections):
        end = top_view(foot)
        line, = ax.plot([0, end[0]], [0, end[1]], color=COLORS['azimuth'],
                        lw=1.7, ls=(0, (5, 2)))
        line.set_gid(f'top-view-projection-{i}')
        ax.scatter(*end, s=45, facecolor=COLORS['paper'], edgecolor=COLORS['azimuth'],
                   linewidth=1.5, zorder=5)
        ax.text(end[0] + (-0.04 if i == 0 else 0.04), end[1] + 0.05,
                '太阳的投影' if i == 0 else '幻日的投影',
                ha='right' if i == 0 else 'left', color=ink, fontsize=10.5)
    angle = top_view(data.horizontal_arc * 0.46)
    line, = ax.plot(*angle.T, color=COLORS['azimuth'], lw=1.8, ls=(0, (5, 2)))
    line.set_gid('top-view-azimuth-arc')
    angle_arrows(ax, angle, COLORS['azimuth'])
    ax.text(0, 0.91, f'Δφ = {data.azimuth:.2f}°', ha='center', color=ink, fontsize=12)
    ax.scatter(0, 0, s=20, color=ink, zorder=5)
    ax.text(0, -0.07, 'O', ha='center', va='top', color=ink, fontsize=11)
    ax.set(xlim=(-0.73, 0.73), ylim=(-0.16, 0.92), aspect='equal')
    ax.axis('off')


def make_figure(height=SUN_HEIGHT):
    P.apply_style()
    data = ruler_geometry(height)
    ink = COLORS['ink']
    fig = plt.figure(figsize=(12.2, 7.7))
    fig.text(0.045, 0.94, '看天球，还是看水平投影？', fontsize=18, color=ink)
    fig.text(0.045, 0.887, f'同一对方向：太阳与幻日都在高度 h = {height:g}°，却有两种不同的夹角。',
             fontsize=11.5, color=ink)
    fig.text(0.055, 0.825, '天球夹角 D', fontsize=13, color=ink)
    fig.text(0.68, 0.825, '水平方位差 Δφ', fontsize=13, color=ink)
    ax = fig.add_axes([0.025, 0.205, 0.58, 0.60], label='celestial-sphere')
    sky_panel(ax, data)
    top = fig.add_axes([0.655, 0.465, 0.31, 0.31], label='horizontal-view')
    horizontal_panel(top, data)
    fig.text(0.675, 0.425, '投影压低了方向，但保留方位。', color=ink, fontsize=10.5)
    fig.text(0.675, 0.377, '两个方向的高度相同：', color=ink, fontsize=10.5)
    fig.text(0.675, 0.325, r'$\cos D=\sin^2h+\cos^2h\cos\Delta\varphi$',
             color=ink, fontsize=14)
    fig.text(0.675, 0.265, 'h = 0°：两把尺子重合', color=ink, fontsize=11)
    fig.text(0.675, 0.222, 'h > 0°：天球夹角小于方位差', color=ink, fontsize=11)
    fig.legend(handles=[Line2D([], [], color=COLORS['distance'], lw=1.8, label='天球夹角 D'),
                        Line2D([], [], color=COLORS['azimuth'], lw=1.8, ls=(0, (5, 2)),
                               label='水平投影夹角 Δφ')],
               loc='lower left', bbox_to_anchor=(0.042, 0.125), ncol=2,
               labelcolor=ink, handlelength=3)
    heights, ds, deltas = curve_data([0, 40, 60])
    fig.text(0.055, 0.10, '幻日最近处', fontsize=10.5, color=ink)
    for x, h, d, delta in zip((0.25, 0.49, 0.73), heights, ds, deltas):
        fig.text(x, 0.10, f'h = {h:g}°', fontsize=10.5, color=ink)
        fig.text(x, 0.066, f'D {d:.2f}°  /  Δφ {delta:.2f}°', fontsize=10.5, color=ink)
    fig.text(0.055, 0.024, f'太阳升高，两把尺逐渐分开；达到临界高度（约 {C.critical_height():.2f}°）后不再有正透射光路。',
             fontsize=10, color=ink)
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
