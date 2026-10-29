# 图 5a：世界系绕太阳转动，晶体坐标下太阳方向不变 → ../img/sun_rotation.png。
import numpy as np
from scipy.spatial.transform import Rotation

import _orientation_fig as F
from _sun_rotation import body_sun, solar_orbit

SUN = np.array([0.35, 0.75, 0.56])
INITIAL = Rotation.from_euler('ZYZ', [25, 45, -20], degrees=True).as_matrix()
ANGLES = [0., 45., 90., 135., 180.]


def scene_data(angles=ANGLES):
    rotations, sun = solar_orbit(INITIAL, SUN, angles)
    return rotations, sun, body_sun(rotations, sun)


def direction(ax, vector, label, spin=False):
    end = F.CAMERA.project_xy(1.95*np.asarray(vector))[0]
    F.arrow(ax, [0, 0], end, F.SUN, zorder=13)
    ax.text(end[0]+0.07, end[1]+0.08, label, color=F.INK, fontsize=14, zorder=14)
    if spin:
        spin_mark(ax, vector)
    ax.set(xlim=(-1.55, 2.05), ylim=(-1.5, 1.9))


def spin_mark(ax, axis, at=1.3, radius=0.3):
    """绕 ŝ 的旋转箭头：画在太阳轴上的一小段圆弧（与 ch10 图 2 同一画法）。"""
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.path import Path as MplPath

    axis = np.asarray(axis, dtype=float)
    e = np.cross(axis, F.CAMERA.view_dir)
    e /= np.linalg.norm(e)
    f = np.cross(axis, e)
    t = np.linspace(-0.4, 4.2, 100)
    arc = at * axis + radius * (np.cos(t)[:, None] * e + np.sin(t)[:, None] * f)
    patch = FancyArrowPatch(path=MplPath(F.CAMERA.project_xy(arc)), arrowstyle='->',
                            mutation_scale=11, color=F.SUN, lw=1.4, zorder=15)
    patch.set_gid('solar-axis-rotation')
    ax.add_patch(patch)


def main(out=None):
    fig = F.canvas(size=(12.8, 6.6))
    rotations, sun, us = scene_data()
    for i, (angle, R, u) in enumerate(zip(ANGLES, rotations, us)):
        left = .075+i*.181
        ax = fig.add_axes([left, 0.5, 0.175, 0.42])
        # 上排面 3 只在第一帧朝向镜头且近乎侧立，标了反而压边；编号只留在下排表明晶体系不变。
        F.crystal(ax, R, face_numbers=())
        direction(ax, sun, r'$\hat{\mathbf{s}}$', spin=True)
        ax.set_title(f'转过 {angle:g}°', color=F.INK, fontsize=13, pad=0)
        bx = fig.add_axes([left, 0.03, 0.175, 0.42])
        F.crystal(bx, np.eye(3), face_numbers=(3,))
        fig.text(left+.0875, .47, '↓', ha='center', va='center', color=F.EDGE, fontsize=20)
        direction(bx, u, r'$\mathbf{u}$')
        if i < len(ANGLES)-1:
            fig.text(left+.177, .7, '→', ha='center', va='center', color=F.INK, fontsize=16)
            fig.text(left+.177, .23, '=', ha='center', va='center', color=F.INK, fontsize=18)
    fig.text(0.035, 0.7, '世界系', color=F.INK, rotation=90, fontsize=13, va='center')
    fig.text(0.035, 0.23, '晶体系', color=F.INK, rotation=90, fontsize=13, va='center')
    F.save(fig, 'sun_rotation', out)


if __name__ == '__main__':
    F.cli(main)
