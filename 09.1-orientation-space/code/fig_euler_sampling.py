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
    fig = F.canvas(size=(11.8, 5.9))
    for i, points in enumerate(samples()):
        ax = fig.add_axes([0.03 + i*0.5, 0.02, 0.44, 0.88])
        F.globe(ax)
        xy = F.CAMERA.project_xy(points)
        visible = Sphere().facing(points, F.CAMERA)
        # 点是「画在球面上」的小圆片：随球面倾斜同样缩小（面积 ∝ 法向与视线夹角的余弦），
        # 否则球缘的投影压缩会让均匀分布看起来在边缘更密。
        view = F.CAMERA.view_vector(points)
        tilt = np.clip(np.sum(points * view, axis=1), 0, 1)
        ax.scatter(xy[~visible, 0], xy[~visible, 1], s=2, color=F.NEUTRAL, alpha=0.08,
                   lw=0, zorder=3)
        ax.scatter(xy[visible, 0], xy[visible, 1], s=9*tilt[visible], color=F.NEUTRAL,
                   alpha=0.85, lw=0, zorder=7)
        ax.set_title(('欧拉角等步长', 'Haar 均匀取向')[i], color=F.INK, fontsize=14, pad=2)
        for sign, label in ((1, 'β = 0°'), (-1, 'β = 180°')):
            p = F.CAMERA.project_xy([0, 0, sign])[0]
            ax.annotate(label, p, xytext=(.62, 1.12*sign), ha='left', va='center',
                        fontsize=12, color=F.INK,
                        arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=.7, shrinkB=2))
    F.save(fig, 'euler_sampling', out)


if __name__ == '__main__':
    F.cli(main)
