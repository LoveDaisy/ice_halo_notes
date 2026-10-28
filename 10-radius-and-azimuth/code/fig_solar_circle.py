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
ANGLES = np.array([0., 60., 120., 180.])
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
    cosine = np.clip(np.asarray(points) @ sun, -1, 1)
    distance = np.arccos(cosine)
    xy = np.column_stack([np.asarray(points) @ east, np.asarray(points) @ up])
    scale = np.divide(np.degrees(distance), np.sin(distance),
                      out=np.full_like(distance, 180/np.pi), where=np.abs(distance) > 1e-12)
    return xy * scale[:, None]


def arrow(ax, vector, color):
    end = CAMERA.project_xy(1.8 * vector)[0]
    ax.annotate('', xy=end, xytext=(0, 0), zorder=15,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=1.5, mutation_scale=12))


def main(out=None):
    P.apply_style()
    ink = COLORS['ink']
    fig = plt.figure(figsize=(12.0, 6.8))
    fig.text(0.045, 0.935, '晶体绕太阳转，光点也沿同一个圆转', fontsize=17, color=ink)
    fig.text(0.045, 0.88, '同一 3–5 光路 · 四帧是同一晶体原地旋转，不是四颗晶体的位置。', fontsize=11, color=ink)
    rotations, sun, us, points = scene_data()
    for i, (rotation, point, angle) in enumerate(zip(rotations, points, ANGLES)):
        ax = fig.add_axes([0.04+(i % 2)*0.235, 0.46-(i // 2)*0.33, 0.225, 0.29])
        poly = HexPrism(a=0.6, h=1.5).transformed(rotation=rotation)
        render_crystal(ax, poly, camera=CAMERA, preset=PRESETS['ice_filled'], face_numbers=[1, 3])
        arrow(ax, sun, COLORS['sun'])
        arrow(ax, point, COLORS['point'])
        finish(ax, (-1.55, 1.95), (-1.45, 1.95))
        ax.set_title(f'{chr(65+i)}    θ = {angle:g}°', color=ink, fontsize=11)
    sky = fig.add_axes([0.57, 0.19, 0.38, 0.59])
    _, _, _, trajectory = scene_data(np.linspace(0, 360, 721))
    curve = sky_xy(trajectory, sun)
    sky.plot(*curve.T, color=COLORS['point'], lw=1.6)
    xy = sky_xy(points, sun)
    sky.scatter(*xy.T, color=COLORS['point'], edgecolor='white', lw=1.5, s=50, zorder=5)
    for i, q in enumerate(xy):
        sky.text(*(q*1.16), chr(65+i), color=ink, fontsize=13, ha='center', va='center')
    sky.scatter(0, 0, s=90, color=COLORS['sun'], edgecolor='white', lw=1.5, zorder=6)
    sky.text(0, -3.8, '太阳', color=ink, ha='center', fontsize=11)
    sky.plot([0, xy[1, 0]], [0, xy[1, 1]], color=COLORS['ink'], ls=(0, (3, 3)), lw=0.8)
    radius = np.linalg.norm(xy[1])
    sky.text(2, 4, f'D = {radius:.2f}°\n始终不变', color=ink, fontsize=11, linespacing=1.6,
             bbox=dict(facecolor=P.PAL['background'], edgecolor='none', pad=3))
    k = 65
    sky.annotate('', xy=curve[k+12], xytext=curve[k],
                 arrowprops=dict(arrowstyle='-|>', color=COLORS['point'], lw=1.6, mutation_scale=12))
    sky.set_aspect('equal')
    sky.set(xlim=(-32, 32), ylim=(-32, 32))
    sky.axis('off')
    sky.set_title('天空：以太阳为中心的等距投影', color=ink, fontsize=11, pad=18)
    # 两种向量通过线段图例及文字区分，不依赖颜色。
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([0], [0], color=COLORS['sun'], lw=2, label='指向太阳 s（固定）'),
                        Line2D([0], [0], color=COLORS['point'], lw=2, label='指向所见光点 x（随晶体转）')],
               loc='lower center', bbox_to_anchor=(0.5, 0.055), ncol=2, fontsize=10)
    fig.text(0.5, 0.025, '箭头表示观察方向，不是光线传播方向；每帧的 u = R⁻¹s 都相同。', ha='center', color=ink, fontsize=10)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/solar_circle.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
