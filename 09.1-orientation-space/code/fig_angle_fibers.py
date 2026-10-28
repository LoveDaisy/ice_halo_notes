# 图 5b 局部辅助候选：最短转动选起点，在反向点没有唯一极限 → ../img/angle_fibers.png。
import numpy as np
from scipy.spatial.transform import Rotation

from halo_notes.draw.projection import Camera
from check_orientation_space import min_rotation_to
import _orientation_fig as F

SUN = np.array([0., 0., 1.])
APPROACH_AZIMUTHS = (0., 45.)
CAMERA = Camera(azimuth=22.5, elevation=-24, distance=5)


def reference_loop(count=721, radius_deg=5.):
    phi = np.linspace(0, 2*np.pi, count)
    e = np.radians(radius_deg)
    u = np.column_stack((np.sin(e)*np.cos(phi), np.sin(e)*np.sin(phi),
                         np.full(count, -np.cos(e))))
    shortest = min_rotation_to(u, SUN)
    local = np.diag([1., -1., -1.]) @ min_rotation_to(u, -SUN)
    relative = shortest @ local.transpose(0, 2, 1)
    local = relative[0] @ local
    relative = shortest @ local.transpose(0, 2, 1)
    phase = np.unwrap(np.arctan2(relative[:, 1, 0], relative[:, 0, 0]))
    return phi, u, shortest, local, phase


def approach(azimuth, distances):
    """在晶体系沿指定经线趋近 −s；返回实际最短参考姿态。"""
    a, e = np.radians(azimuth), np.radians(np.asarray(distances))
    u = np.column_stack((np.sin(e)*np.cos(a), np.sin(e)*np.sin(a), -np.cos(e)))
    return u, min_rotation_to(u, SUN)


def limiting_reference(azimuth):
    # u×s 的极限方向；不在反向点调用没有唯一解的 min_rotation_to。
    a = np.radians(azimuth)
    axis = np.array([np.sin(a), -np.cos(a), 0.])
    return Rotation.from_rotvec(np.pi*axis).as_matrix()


def main(out=None):
    fig = F.canvas('到了反向点，哪一个姿态算“零度”？',
                   '试着用“把 u 转到太阳方向的最短转动”选参考姿态：从不同方向靠近，答案不同。', size=(12.2, 7.8))
    ax = fig.add_axes([.035, .22, .42, .57])
    F.globe(ax, CAMERA)
    for i, (azimuth, color, style) in enumerate(zip(APPROACH_AZIMUTHS, (F.BLUE, F.ORANGE), ('-', '--'))):
        u, _ = approach(azimuth, np.linspace(100, .1, 401))
        xy = CAMERA.project_xy(u)
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=2, ls=style, zorder=9)
        F.arrow(ax, xy[260], xy[290], color, zorder=10)
        ax.text(xy[60, 0]+(-.12 if i == 0 else .12), xy[60, 1], 'A' if i == 0 else 'B',
                ha='right' if i == 0 else 'left', color=F.INK, fontsize=13)
    south = CAMERA.project_xy(-SUN)[0]
    ax.scatter(*south, marker='x', s=45, color=F.INK, zorder=11)
    ax.annotate('同一个方向  u = −ŝ', south, xytext=(0, -1.27),
                color=F.INK, fontsize=11, ha='center',
                arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=.8))
    ax.set_title('u 球 · 两条不同的靠近路线', color=F.INK, fontsize=11)
    ax.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.4))
    for i, (azimuth, color) in enumerate(zip(APPROACH_AZIMUTHS, (F.BLUE, F.ORANGE))):
        bx = fig.add_axes([.50+i*.245, .30, .225, .36])
        R = limiting_reference(azimuth)
        F.crystal(bx, R)
        end = F.CAMERA.project_xy(1.65*SUN)[0]
        F.arrow(bx, (0, 0), end, F.ORANGE, zorder=13)
        bx.text(end[0]+.08, end[1], 'ŝ', color=F.INK, fontsize=12)
        # 用同一条有标签的体轴分辨姿态，不靠六棱柱的外形对称性。
        tip = F.CAMERA.project_xy(1.2*R[:, 0])[0]
        F.arrow(bx, (0, 0), tip, color, zorder=14)
        bx.text(tip[0], tip[1]-.17, '体轴 e₁', ha='center', color=F.INK, fontsize=10)
        bx.set_title(('沿 A 的极限', '沿 B 的极限')[i], color=F.INK, fontsize=12)
        bx.set(xlim=(-1.6, 1.6), ylim=(-1.5, 1.9))
    fig.text(.735, .47, '≠', color=F.INK, fontsize=25, ha='center')
    fig.text(.74, .235, '太阳在晶体中的方向相同，\n带标记的晶体姿态却相差绕太阳轴的 90°。',
             ha='center', color=F.INK, fontsize=11, linespacing=1.8)
    fig.text(.5, .12, '固定一个 u，所有这些姿态仍可绕太阳轴转一圈——这一圈就是角纤维；难的是给它选一个起点。',
             ha='center', color=F.INK, fontsize=10.5)
    fig.text(.5, .055, '局部辅助示意：只展示“最短转动”选法的坏点。任何选法都无法全局光滑，是正文与附录的进一步结论。',
             ha='center', color=F.INK, fontsize=9.5)
    F.save(fig, 'angle_fibers', out)


if __name__ == '__main__':
    F.cli(main)
