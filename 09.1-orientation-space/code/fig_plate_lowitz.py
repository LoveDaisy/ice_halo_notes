# 图 2b：片晶的对径粘合圆与 Lowitz 环面上的同一圈 → ../img/plate_lowitz.png。
import numpy as np
from matplotlib.lines import Line2D

from lumice_integral.symmetry.attitude import Ry
from lumice_integral.symmetry.reflection_group import Rz
import _orientation_fig as F
import fig_column_torus as T


def attitude(phi, swing):
    return Rz(float(phi)) @ Ry(float(swing))


def parameter_point(phi, swing):
    # 只平移显示角度：t=0 的片晶圈放在管顶，物理姿态仍为 Rz(φ)Ry(t)。
    return T.torus(phi, np.asarray(swing) + 180)


def main(out=None):
    fig = F.canvas('片晶是 Lowitz 环面上的一圈',
                   '把摆角锁在 t = 0°：c 轴朝上，只剩绕竖直方向转动的自由度。', size=(12.2, 6.9))
    ax = fig.add_axes([0.025, 0.25, 0.33, 0.52])
    F.globe(ax)
    ends = F.CAMERA.project_xy([[0, 0, -1], [0, 0, 1]])
    ax.plot(ends[:, 0], ends[:, 1], color=F.BLUE, lw=2.5, zorder=9)
    ax.scatter(ends[:, 0], ends[:, 1], s=50, color=F.BLUE, edgecolor='white', zorder=10)
    ax.text(0.12, 0.82, '+π', color=F.INK, fontsize=11)
    ax.text(0.12, -0.92, '−π', color=F.INK, fontsize=11)
    ax.text(-0.15, 0, '0', color=F.INK, va='center')
    ax.set_title('轴角球里的片晶', fontsize=12, color=F.INK)
    ax.annotate('', xy=ends[0], xytext=ends[1],
                arrowprops=dict(arrowstyle='<->', connectionstyle='arc3,rad=0.8',
                                color=F.EDGE, lw=1, linestyle='--'), zorder=10)
    fig.text(0.19, 0.24, '直径两端粘合，首尾接成一个圆', ha='center', color=F.INK, fontsize=10)
    bx = fig.add_axes([0.39, 0.23, 0.58, 0.59])
    image, _ = T.surface_pixels(ring_color=F.BLUE, meridian_color=F.ORANGE)
    bx.imshow(image, origin='lower', extent=(-3, 3, -2.1, 2.1), interpolation='lanczos')
    for phi, t, text, target in ((48, 0, '片晶圈\nt = 0°', (3.1, 1.15)),
                                (15, -80, '摆角 t\n绕长对角线摆动', (3.1, -0.8)),
                                (-125, 0, '长对角线方位 φ', (-3.0, 1.6))):
        xy = T.project(parameter_point(phi, t))[:2]
        bx.annotate(text, xy, xytext=target, color=F.INK, fontsize=10.5,
                    ha='right' if target[0] < 0 else 'left', va='center',
                    arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=0.8))
    for ps, ts, color in ((np.linspace(-105, -85, 15), 0, F.BLUE),
                           (15, np.linspace(-85, -55, 15), F.ORANGE)):
        xy = T.project(parameter_point(ps, ts))
        F.arrow(bx, xy[-5, :2], xy[-1, :2], color)
    bx.set(xlim=(-3.7, 4.9), ylim=(-2.1, 2.3), aspect='equal')
    bx.axis('off')
    fig.legend(handles=[Line2D([], [], color=F.BLUE, lw=2, label='蓝线：片晶圆'),
                        Line2D([], [], color=F.ORANGE, lw=2, label='橙线：固定方位下的摆动')],
               loc='lower center', bbox_to_anchor=(0.52, 0.12), ncol=2, labelcolor=F.INK)
    fig.text(0.5, 0.06, '左：带面号、c 轴朝上的片晶分支。右：全摆幅参数环面示意，不是轴角球中的嵌入。',
             ha='center', color=F.INK, fontsize=9.5)
    F.save(fig, 'plate_lowitz', out)


if __name__ == '__main__':
    F.cli(main)
