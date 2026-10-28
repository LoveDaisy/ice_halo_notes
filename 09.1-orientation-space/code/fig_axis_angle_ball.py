# 图 1a：轴角球边界的对径点代表同一旋转 → ../img/axis_angle_ball.png。
import numpy as np
from scipy.spatial.transform import Rotation

import _orientation_fig as F

AXIS = np.array([1., 0., 0.])


def boundary_rotations():
    return Rotation.from_rotvec(np.pi * np.array([AXIS, -AXIS])).as_matrix()


def main(out=None):
    fig = F.canvas('球面上相对的两点，其实是同一个姿态',
                   '球心是不转；离球心越远，转角越大；球面对应 180°。')
    ax = fig.add_axes([0.025, 0.17, 0.47, 0.65])
    F.globe(ax)
    ends = F.CAMERA.project_xy(np.array([-AXIS, AXIS]))
    ax.plot(ends[:, 0], ends[:, 1], '--', color=F.ORANGE, lw=1.7, zorder=9)
    ax.scatter(ends[:, 0], ends[:, 1], s=70, color=F.ORANGE,
               edgecolor='white', zorder=10)
    ax.scatter([0], [0], s=32, color=F.INK, zorder=10)
    ax.text(-0.02, -0.18, '0° · 不转', ha='center', color=F.INK, fontsize=11)
    for p, label, shift in zip(ends, ('−πa', '+πa'), (-0.16, 0.16)):
        ax.text(p[0] + shift, p[1] + np.sign(shift)*0.1, label,
                ha='right' if shift < 0 else 'left', color=F.INK, fontsize=13)
    ax.annotate('对径认同', xy=ends[0]*0.55, xytext=(-0.85, -1.12),
                ha='center', color=F.INK, fontsize=11,
                arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=0.8))
    for i, R in enumerate(boundary_rotations()):
        bx = fig.add_axes([0.52 + 0.23*i, 0.28, 0.22, 0.41])
        F.crystal(bx, R)
        bx.set_title(('绕 +a 转 180°', '绕 −a 转 180°')[i], fontsize=11, color=F.INK)
    fig.text(0.745, 0.49, '=', fontsize=24, color=F.INK, ha='center')
    fig.text(0.75, 0.22, '同一晶体，面号与朝向完全重合', ha='center', color=F.INK, fontsize=11)
    fig.text(0.5, 0.07, '球内每一点代表一个旋转；只有边界上的对径点需要粘合。',
             ha='center', color=F.INK, fontsize=10)
    F.save(fig, 'axis_angle_ball', out)


if __name__ == '__main__':
    F.cli(main)
