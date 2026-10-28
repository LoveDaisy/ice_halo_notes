# 图 4a：等步长欧拉角与 Haar 样本的 c 轴方向及同桶份额 → ../img/euler_sampling.png。
import numpy as np

from lumice_integral.so3 import haar_rotations
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
                   '两边各取 1,440 个方向，使用相同视角和点大小；下方按同一组 β 桶计数。', size=(11.8, 8.0))
    for i, (points, expected) in enumerate(zip(samples(), expected_fractions())):
        ax = fig.add_axes([0.055 + i*0.49, 0.36, 0.4, 0.44])
        F.globe(ax)
        xy = F.CAMERA.project_xy(points)
        visible = points @ F.CAMERA.view_dir > 0
        ax.scatter(xy[~visible, 0], xy[~visible, 1], s=4, color=F.BLUE, alpha=0.10, zorder=3)
        ax.scatter(xy[visible, 0], xy[visible, 1], s=4, color=F.BLUE, alpha=0.8, zorder=7)
        ax.set_title(('欧拉角等步长', 'Haar 均匀取向')[i], color=F.INK, fontsize=12)
        for sign, label in ((1, 'β = 0°'), (-1, 'β = 180°')):
            ax.text(0, 1.20*sign, label, fontsize=10, color=F.INK, ha='center')
        bx = fig.add_axes([0.09 + i*0.49, 0.135, 0.35, 0.19])
        bx.stairs(bin_fractions(points), EDGES, color=F.BLUE, lw=1.5, fill=True, alpha=0.3, label='本图样本')
        bx.stairs(expected, EDGES, color=F.INK, lw=1.2, linestyle='--', label='解析份额')
        bx.set(xlim=(0, 180), ylim=(0, .12), xlabel='c 轴天顶角 β')
        bx.set_xticks([0, 90, 180], ['0°', '90°', '180°'])
        bx.set_yticks([0, .05, .1], ['0', '5%', '10%'])
        bx.set_ylabel('每 10° 桶内份额')
        bx.legend(fontsize=9, loc='upper center', ncol=2)
    fig.text(0.5, 0.035, '这里只显示 c 轴在球面上的方向，不是整个三维姿态空间；绕 c 轴的自转角未显示。',
             ha='center', color=F.INK, fontsize=10)
    F.save(fig, 'euler_sampling', out)


if __name__ == '__main__':
    F.cli(main)
