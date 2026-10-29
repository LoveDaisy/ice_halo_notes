# 图 2：同源绕太阳转动与等角距天空轨迹 → ../img/solar_circle.png。
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from halo_notes.draw.geometry import HexPrism
from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish, render_crystal
from halo_notes.draw.style.figure import figure_scheme
from halo_notes.draw.style.presets import crystal_preset

import check_parhelion as C
from fig_plate_terrain import P, latitude_minimum, plt

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location('_ch9p1_solar_orbit', ROOT / '09.1-orientation-space/code/_sun_rotation.py')
ORBIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ORBIT)
ANGLES = np.array([30., 60., 90., 120.])
CAMERA = Camera(azimuth=-55, elevation=24, distance=6)
SCHEME = figure_scheme()
COLORS = {'ink': SCHEME.ink, 'sun': SCHEME.sun, 'point': SCHEME.point, 'guide': SCHEME.guide}


def scene_data(angles=ANGLES):
    sun = C.unit_from(20., 0.)
    u, _ = latitude_minimum(20.)
    initial = Rotation.align_vectors([sun], [u])[0].as_matrix()
    rotations, sun = ORBIT.solar_orbit(initial, sun, angles)
    us = ORBIT.body_sun(rotations, sun)
    points = np.einsum('nij,nj->ni', rotations, C.light_point(us))
    return rotations, sun, us, points


def sky_xy(points, sun):
    """太阳中心等距投影：径向距离就是天球角距离，不是空间透视图。"""
    east = np.cross([0., 0., 1.], sun)
    east /= np.linalg.norm(east)
    up = np.cross(sun, east)
    points = np.asarray(points, dtype=float)
    cosine = np.clip(points @ sun, -1, 1)
    xy = np.stack([points @ east, points @ up], axis=-1)
    sine = np.linalg.norm(xy, axis=-1)
    distance = np.degrees(np.arctan2(sine, cosine))
    scale = np.divide(distance, sine, out=np.ones_like(distance), where=sine > 1e-12)
    return xy * scale[..., None]


def arrow(ax, vector, color):
    end = CAMERA.project_xy(1.8 * vector)[0]
    ax.annotate('', xy=end, xytext=(0, 0), zorder=15,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=1.5, mutation_scale=12))


def angle_arc(sun, point, radius=1.35):
    """两条观察方向张成的大圆小弧；不拿屏幕夹角冒充天球角距。"""
    angle = np.arccos(np.clip(sun @ point, -1, 1))
    tangent = point - (point @ sun) * sun
    tangent /= np.linalg.norm(tangent)
    t = np.linspace(0, angle, 81)
    return radius * (np.cos(t)[:, None] * sun + np.sin(t)[:, None] * tangent)


def make_figure():
    from matplotlib.lines import Line2D
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import FancyArrowPatch

    P.apply_style()
    ink = COLORS['ink']
    fig = plt.figure(figsize=(12.8, 3.7))
    data = scene_data()
    rotations, sun, us, points = data
    preset = crystal_preset()
    radius = np.degrees(np.arccos(sun @ points[0]))
    for i, (rotation, point, angle) in enumerate(zip(rotations, points, ANGLES)):
        ax = fig.add_axes([0.01 + i * 0.245, 0.13, 0.245, 0.80], label=f'attitude-{i}')
        poly = HexPrism(a=0.48, h=1.2).transformed(rotation=rotation)
        render_crystal(ax, poly, camera=CAMERA, preset=preset)
        # x 的箭头尖绕 s 扫出的圆：四帧共用同一个圆锥，当前 x 只是圆上一点。
        e = np.cross(sun, CAMERA.view_dir)
        e /= np.linalg.norm(e)
        f = np.cross(sun, e)
        tip = 1.8 * point
        axial = (tip @ sun) * sun
        ring_r = np.linalg.norm(tip - axial)
        t = np.linspace(0, 2 * np.pi, 241)
        ring = axial + ring_r * (np.cos(t)[:, None] * e + np.sin(t)[:, None] * f)
        ring_xy = CAMERA.project_xy(ring)
        ring_line, = ax.plot(*ring_xy.T, color=COLORS['point'], lw=0.9, ls=(0, (2.5, 2.5)),
                             alpha=0.75, zorder=14)
        ring_line.set_gid('point-cone-rim')
        arrow(ax, sun, COLORS['sun'])
        arrow(ax, point, COLORS['point'])
        arc = CAMERA.project_xy(angle_arc(sun, point))
        patch = FancyArrowPatch(path=MplPath(arc), arrowstyle='<->',
                                mutation_scale=10, color=ink, lw=1.2, zorder=18)
        patch.set_gid('angular-distance')
        ax.add_patch(patch)
        mid = CAMERA.project_xy(angle_arc(sun, point, radius=1.1))[40]
        ax.text(*mid, '$D$', fontsize=14, color=ink, ha='center', va='center', zorder=20)
        # 同一个太阳轴上的小旋转箭头，不是独立的天空整圆。
        t = np.linspace(-0.4, 4.2, 100)
        spin = 1.65 * sun + 0.23 * (np.cos(t)[:, None] * e + np.sin(t)[:, None] * f)
        spin_arrow = FancyArrowPatch(path=MplPath(CAMERA.project_xy(spin)), arrowstyle='->',
                                     mutation_scale=11, color=COLORS['sun'], lw=1.4, zorder=19)
        spin_arrow.set_gid('solar-axis-rotation')
        ax.add_patch(spin_arrow)
        finish(ax, (-1.15, 2.05), (-1.0, 1.45))
        ax.set_title(f'转过 {angle - ANGLES[0]:g}°', color=ink, fontsize=13, pad=0)
    fig.legend(handles=[Line2D([], [], color=COLORS['sun'], lw=2.2, label='太阳方向 s（转轴）'),
                        Line2D([], [], color=COLORS['point'], lw=2.2, label='光点方向 x'),
                        Line2D([], [], color=COLORS['point'], lw=1.0, ls=(0, (2.5, 2.5)),
                               label=f'x 绕 s 扫出的圆 · 角距 D = {radius:.2f}°')],
               loc='lower center', bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=12,
               handlelength=2.2, columnspacing=2.4)
    return fig, data


def main(out=None):
    fig, _ = make_figure()
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/solar_circle.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
