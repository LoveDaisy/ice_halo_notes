# 图 1：轴角球的一条直径与逐点对应的晶体姿态 → ../img/axis_angle_ball.png。
import numpy as np
from matplotlib.patches import ConnectionPatch
from matplotlib.lines import Line2D
from scipy.spatial.transform import Rotation

from halo_notes.draw.projection import Camera
import _orientation_fig as F

AXIS = np.array([1., 0., 0.])
ANGLES = np.array([-180., -90., 0., 90., 180.])
BALL_CAMERA = Camera(azimuth=-90, elevation=22, distance=5)


def signed_angle(degrees):
    degrees = np.asarray(degrees)
    return np.where(degrees <= 180, degrees, degrees - 360)


def orientations(degrees):
    return Rotation.from_rotvec(np.radians(np.asarray(degrees))[..., None] * AXIS).as_matrix()


def boundary_rotations():
    return orientations([180, -180])


def main(out=None):
    fig = F.canvas('球里的点，与冰晶的姿态一一对应',
                   '固定转轴 a，只看一条直径；球面两端虽然分开，代表的却是同一个姿态。', size=(12.2, 8.8))
    ax = fig.add_axes([0.19, 0.43, 0.62, 0.42])
    F.globe(ax, BALL_CAMERA)
    points = BALL_CAMERA.project_xy(ANGLES[:, None] / 180 * AXIS)
    ax.plot(points[:, 0], points[:, 1], color=F.BLUE, lw=1.8, zorder=8)
    ax.scatter(points[:, 0], points[:, 1], s=35, color=F.BLUE,
               edgecolor=F.PAPER, linewidth=1, zorder=10)
    for xy, angle in zip(points, ANGLES):
        ax.text(xy[0], xy[1]+.12, f'{angle:g}°', ha='center', color=F.INK, fontsize=11)
    ax.text(0, -.2, '球心 · 不转', ha='center', color=F.INK, fontsize=10)
    ax.annotate('', points[0], points[-1],
                arrowprops=dict(arrowstyle='<->', color=F.ORANGE, lw=1.5,
                                linestyle='--', connectionstyle='arc3,rad=.85'), zorder=11)
    ax.text(0, 1.18, '+180° ≡ −180°', color=F.INK, ha='center', fontsize=12)
    F.arrow(ax, (.16, -.08), (.75, -.08), F.BLUE, lw=1.2, zorder=11)
    F.arrow(ax, (-.78, -.08), (-.2, -.08), F.BLUE, lw=1.2, zorder=11)
    ax.set(xlim=(-1.38, 1.38), ylim=(-1.22, 1.4))
    lower = []
    for i, (angle, rotation) in enumerate(zip(ANGLES, orientations(ANGLES))):
        bx = fig.add_axes([.035+i*.192, .15, .17, .23])
        F.crystal(bx, rotation)
        bx.text(0, -1.28, f'{angle:g}°', ha='center', color=F.INK, fontsize=11)
        fig.add_artist(ConnectionPatch(points[i], (0, 1.15), coordsA='data', coordsB='data',
                                       axesA=ax, axesB=bx, color=F.EDGE, lw=.8,
                                       zorder=1, clip_on=False))
        lower.append(bx)
    # 用排版连线认同两端，而不是在三维场景里画一条不存在的轨迹。
    fig.add_artist(Line2D([.12, .12, .888, .888], [.15, .12, .12, .15],
                          transform=fig.transFigure, color=F.ORANGE,
                          lw=1.2, linestyle='--', zorder=20))
    fig.text(.5, .096, '两端的晶体完全重合（包括面号）', ha='center', color=F.INK, fontsize=11,
             bbox=dict(facecolor=F.PAPER, edgecolor='none', pad=4))
    fig.text(.5, .04, '实际继续转：0° → 90° → 180° → 270° → 360°；球中坐标：0° → 90° → ±180° → −90° → 0°。',
             ha='center', color=F.INK, fontsize=10)
    F.save(fig, 'axis_angle_ball', out)


if __name__ == '__main__':
    F.cli(main)
