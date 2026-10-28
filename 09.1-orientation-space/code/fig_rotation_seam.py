# 图 1b：固定轴转动连续，主值轴角坐标在 180° 跳边 → ../img/rotation_seam.png。
import numpy as np
from scipy.spatial.transform import Rotation

import _orientation_fig as F

ANGLES = np.array([0., 90., 170., 190., 270., 360.])
AXIS = np.array([1., 0., 0.])


def signed_angle(degrees):
    degrees = np.asarray(degrees)
    return np.where(degrees <= 180, degrees, degrees - 360)


def orientations(degrees):
    return Rotation.from_rotvec(np.radians(np.asarray(degrees))[..., None] * AXIS).as_matrix()


def main(out=None):
    fig = F.canvas('跳的是坐标，不是冰晶',
                   '绕同一根固定轴一直转：越过 180° 时，坐标换到球的另一侧。', size=(12.2, 7.3))
    for i, (a, R) in enumerate(zip(ANGLES, orientations(ANGLES))):
        ax = fig.add_axes([0.035 + i*0.159, 0.51, 0.15, 0.28])
        F.crystal(ax, R)
        ax.set_title(f'{a:g}°', fontsize=12, color=F.INK)
    fig.text(0.5, 0.49, '170° → 190°：只转了 20°', ha='center', fontsize=11, color=F.INK)
    ax = fig.add_axes([0.115, 0.16, 0.79, 0.26])
    for lo, hi, color in ((0, 180, F.BLUE), (180, 360, F.ORANGE)):
        a = np.linspace(lo, hi, 201)
        y = a if lo == 0 else a-360
        ax.plot(a, y, color=color, lw=1.8)
    ax.scatter(ANGLES, signed_angle(ANGLES), color=[F.BLUE]*3+[F.ORANGE]*3,
               s=38, edgecolor='white', zorder=5)
    ax.scatter([180, 180], [180, -180], facecolors='white', edgecolors=F.INK, s=36, zorder=6)
    ax.annotate('', (180, -165), (180, 165),
                arrowprops=dict(arrowstyle='<->', color=F.EDGE, lw=1.1, linestyle='--'))
    ax.text(188, 0, '边界两端\n是同一姿态', color=F.INK, va='center', fontsize=10)
    ax.axhline(0, color=F.EDGE, lw=0.6, zorder=0)
    ax.set(xlim=(-3, 363), ylim=(-210, 210), xlabel='实际转过的角度', ylabel='沿固定轴的坐标')
    ax.set_xticks([0, 90, 180, 270, 360], ['0°', '90°', '180°', '270°', '360°'])
    ax.set_yticks([-180, 0, 180], ['−πa', '0', '+πa'])
    ax.text(78, 125, '球心 → 正侧边界', color=F.INK, fontsize=10, rotation=0)
    ax.text(263, -170, '负侧边界 → 球心', color=F.INK, fontsize=10)
    fig.text(0.5, 0.035, '蓝段与橙段是同一次连续转动的前半圈和后半圈；360° 回到球心。',
             ha='center', fontsize=10, color=F.INK)
    F.save(fig, 'rotation_seam', out)


if __name__ == '__main__':
    F.cli(main)
