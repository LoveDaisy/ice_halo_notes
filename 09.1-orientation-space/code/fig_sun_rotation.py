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


def direction(ax, vector, label):
    end = F.CAMERA.project_xy(1.95*np.asarray(vector))[0]
    F.arrow(ax, [0, 0], end, F.ORANGE, zorder=13)
    ax.text(end[0]+0.07, end[1]+0.08, label, color=F.INK, fontsize=12, zorder=14)
    ax.set(xlim=(-1.55, 2.05), ylim=(-1.5, 1.9))


def main(out=None):
    fig = F.canvas('绕着太阳转，晶体眼里的太阳却没动',
                   '同一晶体原地转动的连续五帧；每一列，上下对应同一个时刻。', size=(12.8, 8.2))
    rotations, sun, us = scene_data()
    for i, (angle, R, u) in enumerate(zip(ANGLES, rotations, us)):
        left = .075+i*.181
        ax = fig.add_axes([left, 0.5, 0.175, 0.28])
        F.crystal(ax, R)
        direction(ax, sun, r'$\hat{\mathbf{s}}$')
        ax.set_title(f'θ = {angle:g}°', color=F.INK, fontsize=12)
        bx = fig.add_axes([left, 0.14, 0.175, 0.28])
        F.crystal(bx, np.eye(3))
        direction(bx, u, r'$\mathbf{u}$')
        fig.text(left+.0875, .447, '↓', ha='center', color=F.EDGE, fontsize=20)
        if i < len(ANGLES)-1:
            fig.text(left+.177, .63, '→', ha='center', color=F.INK, fontsize=15)
            fig.text(left+.177, .26, '=', ha='center', color=F.INK, fontsize=16)
    fig.text(0.035, 0.64, '世界系', color=F.INK, rotation=90, fontsize=12, va='center')
    fig.text(0.035, 0.28, '晶体系', color=F.INK, rotation=90, fontsize=12, va='center')
    fig.text(0.48, 0.085, r'$\mathbf{u}=R^{-1}\hat{\mathbf{s}}$',
             ha='right', color=F.INK, fontsize=14)
    fig.text(0.5, 0.085, '每一帧都相同', ha='left', color=F.INK, fontsize=12)
    fig.text(0.5, 0.035, '橙箭头只表示指向太阳的方向，不是光路；上排太阳方向固定，下排随晶体坐标一起观察。',
             ha='center', color=F.INK, fontsize=10)
    F.save(fig, 'sun_rotation', out)


if __name__ == '__main__':
    F.cli(main)
