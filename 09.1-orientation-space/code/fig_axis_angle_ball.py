# 图 1：轴角球的一条直径与逐点对应的晶体姿态 → ../img/axis_angle_ball.png。
import numpy as np
from matplotlib import patheffects
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


def signed_label(angle):
    return '0°' if angle == 0 else f"{'+' if angle > 0 else '−'}{abs(angle):g}°"


def exit_point(start, end, radius):
    """从球内一点 start 沿直线走向 end，穿出半径 radius 的轮廓圆的位置（球的纸面坐标）。"""
    d = end - start
    a, b, c = d @ d, 2 * start @ d, start @ start - radius**2
    t = (-b + np.sqrt(b * b - 4 * a * c)) / (2 * a)
    return start + t * d


def crystal_axis(ax, camera=F.CAMERA, length=1.25):
    """晶体上的固定转轴 a：穿过晶体中心的点划线，正端带箭头。"""
    ends = camera.project_xy(np.array([-length, length])[:, None] * AXIS)
    ax.plot(*ends.T, color=F.NEUTRAL, lw=1.1, ls=(0, (6, 2, 1, 2)), zorder=30)
    F.arrow(ax, ends[1] - 0.12 * (ends[1] - ends[0]), ends[1], F.NEUTRAL, lw=1.1, zorder=31)
    return ends[1]


def main(out=None):
    fig = F.canvas(size=(12.2, 7.6))
    ink, mark = F.INK, F.NEUTRAL
    ax = fig.add_axes([0.2, 0.42, 0.6, 0.56])
    F.globe(ax, BALL_CAMERA)
    points = BALL_CAMERA.project_xy(ANGLES[:, None] / 180 * AXIS)
    ax.plot(points[:, 0], points[:, 1], color=mark, lw=1.8, zorder=8)
    ax.scatter(points[1:-1, 0], points[1:-1, 1], s=36, color=mark,
               edgecolor=F.PAPER, linewidth=1, zorder=10)
    # ±180° 两端是同一个姿态：两端画成同一个空心记号，而不是一条「走过去」的弧。
    ax.scatter(points[[0, -1], 0], points[[0, -1], 1], s=70, facecolor=F.PAPER,
               edgecolor=mark, linewidth=1.8, zorder=11)
    halo = [patheffects.withStroke(linewidth=3, foreground=F.PAPER)]
    for xy, angle in zip(points[1:-1], ANGLES[1:-1]):
        ax.text(xy[0], xy[1] + .1, signed_label(angle), ha='center', va='bottom', color=ink,
                fontsize=13, path_effects=halo, zorder=12)
    ax.text(points[0, 0] - .1, points[0, 1], '−180°', ha='right', va='center', color=ink, fontsize=13)
    ax.text(points[-1, 0] + .1, points[-1, 1], '+180°', ha='left', va='center', color=ink, fontsize=13)
    ax.set(xlim=(-1.6, 1.6), ylim=(-1.12, 1.12))
    ax.apply_aspect()
    radius = BALL_CAMERA.distance / np.sqrt(BALL_CAMERA.distance**2 - 1)
    for i, (angle, rotation) in enumerate(zip(ANGLES, orientations(ANGLES))):
        bx = fig.add_axes([.035+i*.192, .09, .17, .25])
        F.crystal(bx, rotation)
        tip = crystal_axis(bx)
        if i == 2:
            bx.text(tip[0] + .08, tip[1], 'a', color=ink, fontsize=15, style='italic',
                    va='center')
        bx.text(0, -1.32, signed_label(angle), ha='center', color=ink, fontsize=13)
        # 连线在球内淡画、出球后实画：读者看见的是「这一点对应下面这颗晶体」，不是一条穿球的线。
        target = ax.transData.inverted().transform(bx.transData.transform((0, 1.2)))
        leave = exit_point(points[i], target, radius)
        ax.plot(*np.column_stack([points[i], leave]), color=F.EDGE, lw=.8, alpha=.5, zorder=2)
        fig.add_artist(ConnectionPatch(leave, (0, 1.2), coordsA='data', coordsB='data',
                                       axesA=ax, axesB=bx, color=F.EDGE, lw=.8,
                                       zorder=1, clip_on=False))
    # 用排版连线认同两端，而不是在三维场景里画一条不存在的轨迹。
    fig.add_artist(Line2D([.12, .12, .888, .888], [.075, .045, .045, .075],
                          transform=fig.transFigure, color=mark,
                          lw=1.1, linestyle=(0, (4, 3)), zorder=20))
    fig.text(.5, .045, '同一个姿态', ha='center', va='center', color=ink, fontsize=13,
             bbox=dict(facecolor=F.PAPER, edgecolor='none', pad=4), zorder=21)
    F.save(fig, 'axis_angle_ball', out)


if __name__ == '__main__':
    F.cli(main)
