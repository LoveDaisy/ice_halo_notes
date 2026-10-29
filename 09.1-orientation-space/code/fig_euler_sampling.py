# 图 4a：同样本数的 c 轴方向点云，不重复图 4b 的密度曲线 → ../img/euler_sampling.png。
import numpy as np

from lumice_integral.so3 import haar_rotations
from halo_notes.draw.sphere import Sphere
import _orientation_fig as F

SEED = 20261028
EDGES = np.linspace(0, 180, 19)


def samples():
    alpha, beta = np.meshgrid(np.linspace(0, 2*np.pi, 40, endpoint=False),
                              (np.arange(36)+0.5)*np.pi/36)
    euler = np.column_stack((np.sin(beta).ravel()*np.cos(alpha).ravel(),
                            np.sin(beta).ravel()*np.sin(alpha).ravel(), np.cos(beta).ravel()))
    haar = haar_rotations(len(euler), np.random.default_rng(SEED))[:, :, 2]
    return euler, haar


def bin_fractions(directions):
    beta = np.degrees(np.arccos(np.clip(directions[:, 2], -1, 1)))
    return np.histogram(beta, EDGES)[0] / len(directions)


def expected_fractions():
    edges = np.radians(EDGES)
    return np.diff(edges)/np.pi, -np.diff(np.cos(edges))/2


def main(out=None):
    fig = F.canvas('坐标上等间距，不等于姿态上均匀',
                   '两边各取 1,440 个方向；相同视角、相同点大小，背面的点淡画。', size=(11.8, 6.8))
    for i, points in enumerate(samples()):
        ax = fig.add_axes([0.055 + i*0.49, 0.16, 0.4, 0.62])
        F.globe(ax)
        xy = F.CAMERA.project_xy(points)
        visible = Sphere().facing(points, F.CAMERA)
        ax.scatter(xy[~visible, 0], xy[~visible, 1], s=5, color=F.BLUE, alpha=0.10, zorder=3)
        ax.scatter(xy[visible, 0], xy[visible, 1], s=5, color=F.BLUE, alpha=0.8, zorder=7)
        ax.set_title(('欧拉角等步长', 'Haar 均匀取向')[i], color=F.INK, fontsize=12)
        for sign, label in ((1, 'β = 0°'), (-1, 'β = 180°')):
            p = F.CAMERA.project_xy([0, 0, sign])[0]
            ax.annotate(label, p, xytext=(.55, 1.18*sign), ha='center',
                        fontsize=10, color=F.INK,
                        arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=.7))
    fig.text(0.5, 0.07, '这里只显示 c 轴在球面上的方向，不是整个三维姿态空间；绕 c 轴的自转角未显示。',
             ha='center', color=F.INK, fontsize=10)
    F.save(fig, 'euler_sampling', out)


if __name__ == '__main__':
    F.cli(main)
