# 图 5a：世界系绕太阳转动，晶体坐标下太阳方向不变 → ../img/sun_rotation.png。
import numpy as np
from scipy.spatial.transform import Rotation

import _orientation_fig as F
from _sun_rotation import body_sun, solar_orbit

SUN = np.array([0.35, 0.75, 0.56])
INITIAL = Rotation.from_euler('ZYZ', [25, 45, -20], degrees=True).as_matrix()
ANGLES = [0., 100.]


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
                   '上排固定世界坐标看冰晶；下排跟着晶体，把它放回同一个体坐标系。', size=(11.8, 8.2))
    rotations, sun, us = scene_data()
    for i, (R, u) in enumerate(zip(rotations, us)):
        ax = fig.add_axes([0.11+i*0.44, 0.47, 0.32, 0.33])
        F.crystal(ax, R)
        direction(ax, sun, r'$\hat{\mathbf{s}}$')
        ax.set_title(('初始姿态 R', '绕太阳轴转过 100°')[i], color=F.INK, fontsize=12)
        bx = fig.add_axes([0.14+i*0.44, 0.13, 0.27, 0.27])
        F.crystal(bx, np.eye(3))
        direction(bx, u, r'$\mathbf{u}$')
        bx.text(0, -1.38, '同一个体坐标方向', color=F.INK, fontsize=10, ha='center')
    fig.text(0.5, 0.65, '→', color=F.INK, fontsize=27, ha='center')
    fig.text(0.5, 0.27, '=', color=F.INK, fontsize=27, ha='center')
    fig.text(0.045, 0.59, '世界系', color=F.INK, rotation=90, fontsize=11)
    fig.text(0.045, 0.22, '晶体系', color=F.INK, rotation=90, fontsize=11)
    fig.text(0.5, 0.435, r'$\mathbf{u}=R^{-1}\hat{\mathbf{s}}=(\mathrm{Rot}_{\hat{\mathbf{s}}}(\theta)R)^{-1}\hat{\mathbf{s}}$',
             ha='center', color=F.INK, fontsize=16)
    fig.text(0.5, 0.045, '橙箭头只表示指向太阳的方向，不是穿过晶体的光线；两个面板不是晶体的平移。',
             ha='center', color=F.INK, fontsize=9.5)
    F.save(fig, 'sun_rotation', out)


if __name__ == '__main__':
    F.cli(main)
