# 图 2：同源绕太阳转动与等角距天空轨迹 → ../img/solar_circle.png。
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from halo_notes.draw.geometry import HexPrism
from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish, render_crystal
from halo_notes.draw.style import PRESETS

import check_parhelion as C
from fig_plate_terrain import P, latitude_minimum, plt

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location('_ch9p1_solar_orbit', ROOT / '09.1-orientation-space/code/_sun_rotation.py')
ORBIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ORBIT)
ANGLES = np.array([30., 60., 90., 120.])
CAMERA = Camera(azimuth=-55, elevation=24, distance=6)
COLORS = {'ink': P.PAL['ink_soft'], 'sun': P.PAL['face_5'],
          'point': P.PAL['arc_roll'], 'guide': P.PAL['reference']}


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
    fig = plt.figure(figsize=(12.8, 4.8))
    fig.text(0.045, 0.92, '绕太阳方向转，角距离不变', fontsize=18, color=ink)
    fig.text(0.045, 0.845, '同一颗晶体原地旋转的四帧 · 3–5 光路', fontsize=11, color=ink)
    data = scene_data()
    rotations, sun, us, points = data
    for i, (rotation, point, angle) in enumerate(zip(rotations, points, ANGLES)):
        ax = fig.add_axes([0.025 + i * 0.245, 0.23, 0.24, 0.54], label=f'attitude-{i}')
        poly = HexPrism(a=0.48, h=1.2).transformed(rotation=rotation)
        preset = PRESETS['ice_filled'].replace(
            geom=PRESETS['ice_filled'].geom.replace(face_number_height=0.23))
        render_crystal(ax, poly, camera=CAMERA, preset=preset, face_numbers=[1, 3])
        arrow(ax, sun, COLORS['sun'])
        arrow(ax, point, COLORS['point'])
        arc = CAMERA.project_xy(angle_arc(sun, point))
        patch = FancyArrowPatch(path=MplPath(arc), arrowstyle='<->',
                                mutation_scale=9, color=ink, lw=1.1, zorder=18)
        patch.set_gid('angular-distance')
        ax.add_patch(patch)
        mid = CAMERA.project_xy(angle_arc(sun, point, radius=1.55))[40]
        ax.text(*mid, 'D', fontsize=11, color=ink, ha='center', va='center',
                bbox=dict(facecolor=P.PAL['background'], edgecolor='none', pad=0.5), zorder=20)
        # 同一个太阳轴上的小旋转箭头，不是独立的天空整圆。
        e = np.cross(sun, CAMERA.view_dir)
        e /= np.linalg.norm(e)
        f = np.cross(sun, e)
        t = np.linspace(-0.4, 4.2, 100)
        spin = 1.65 * sun + 0.23 * (np.cos(t)[:, None] * e + np.sin(t)[:, None] * f)
        spin_arrow = FancyArrowPatch(path=MplPath(CAMERA.project_xy(spin)), arrowstyle='->',
                                     mutation_scale=10, color=COLORS['sun'], lw=1.3, zorder=19)
        spin_arrow.set_gid('solar-axis-rotation')
        ax.add_patch(spin_arrow)
        finish(ax, (-1.15, 2.05), (-1.15, 1.75))
        ax.set_title(f'θ = {angle:g}°', color=ink, fontsize=11, pad=9)
    radius = np.degrees(np.arccos(sun @ points[0]))
    fig.legend(handles=[Line2D([], [], color=COLORS['sun'], lw=2, label='指向太阳 s · 旋转轴'),
                        Line2D([], [], color=COLORS['point'], lw=2, label='指向所见光点 x')],
               loc='lower left', bbox_to_anchor=(0.04, 0.13), ncol=2, fontsize=11)
    fig.text(0.79, 0.16, f'D = {radius:.2f}°', fontsize=14, color=ink, ha='center')
    fig.text(0.045, 0.07, '两箭头都是观察方向；出射光向相反方向传播。每帧的 u = R⁻¹s 相同。',
             fontsize=10.5, color=ink)
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
