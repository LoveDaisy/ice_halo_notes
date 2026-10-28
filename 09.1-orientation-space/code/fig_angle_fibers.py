# 图 5b 局部辅助候选：最短转动选起点，在反向点没有唯一极限 → ../img/angle_fibers.png。
from matplotlib.lines import Line2D
from matplotlib.patches import ConnectionPatch
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


def approach_frames(azimuth):
    """三个沿路姿态及其单侧极限；反向点不调用最短转动求解器。"""
    u, matrices = approach(azimuth, [95., 60., 25.])
    return np.vstack((u, -SUN)), np.concatenate((matrices, [limiting_reference(azimuth)]))


def main(out=None):
    fig = F.canvas('同一个方向，不同的参考姿态',
                   '沿 A、B 两路靠近反向点：每一步都用“把 u 转到太阳方向的最短转动”选参考姿态。',
                   size=(13, 10.5))
    ax = fig.add_axes([.30, .32, .40, .47])
    F.globe(ax, CAMERA)
    ax.set_title('u 球 · 太阳在晶体中的方向', color=F.INK, fontsize=12, pad=15)
    ax.set(xlim=(-1.22, 1.22), ylim=(-1.25, 1.25))
    fig.text(.5, .84, '选太阳方向 ŝ 为北极，反向 −ŝ 就是南极。',
             ha='center', color=F.INK, fontsize=10.5)
    handles = []
    for i, (azimuth, color, style) in enumerate(zip(APPROACH_AZIMUTHS, (F.BLUE, F.ORANGE), ('-', '--'))):
        route = 'AB'[i]
        u, _ = approach(azimuth, np.linspace(100, .1, 401))
        xy = CAMERA.project_xy(np.vstack((u, -SUN)))
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=2, ls=style, zorder=9)
        F.arrow(ax, xy[205], xy[230], color, zorder=10)
        handles.append(Line2D([], [], color=color, lw=2, ls=style, label=f'路线 {route}'))
        points, matrices = approach_frames(azimuth)
        projected = CAMERA.project_xy(points)
        for j, (point, R, bottom) in enumerate(zip(projected, matrices, (.65, .46, .27, .08))):
            bx = fig.add_axes([.035 if i == 0 else .765, bottom, .20, .16])
            F.crystal(bx, R)
            bx.set_gid(f'{route}{j+1}')
            end = F.CAMERA.project_xy(1.65*SUN)[0]
            F.arrow(bx, (0, 0), end, F.INK, zorder=13)
            bx.text(end[0]+.10, end[1], 'ŝ', color=F.INK, fontsize=10)
            # 同一条带标签的体轴随真实旋转移动，避免外形对称掩盖不同姿态。
            tip = F.CAMERA.project_xy(1.2*R[:, 0])[0]
            F.arrow(bx, (0, 0), tip, color, zorder=14)
            bx.annotate('e₁', tip, xytext=(-12 if i == 0 else 10, -4),
                        textcoords='offset points', ha='right' if i == 0 else 'left',
                        color=F.INK, fontsize=10, zorder=20,
                        bbox=dict(facecolor=F.PAPER, edgecolor='none', pad=.6))
            title = f'{route}{j+1}' if j < 3 else f'沿 {route} 的极限'
            bx.set_title(title, color=F.INK, fontsize=11, pad=3)
            bx.set(xlim=(-1.65, 1.65), ylim=(-1.5, 1.95))
            connector = ConnectionPatch(
                xyA=(1.35 if i == 0 else -1.35, 0), xyB=point,
                coordsA='data', coordsB='data', axesA=bx, axesB=ax,
                color=F.EDGE, lw=.7, alpha=.65, zorder=1)
            fig.add_artist(connector)
            if j < 3:
                ax.scatter(*point, s=38, color=color, edgecolor=F.PAPER, linewidth=1, zorder=11)
                ax.annotate(f'{route}{j+1}', point, xytext=(-10 if i == 0 else 10, 5),
                            textcoords='offset points', ha='right' if i == 0 else 'left',
                            color=F.INK, fontsize=10, zorder=12)
    south = CAMERA.project_xy(-SUN)[0]
    ax.scatter(*south, marker='x', s=45, color=F.INK, zorder=12)
    ax.annotate('同一个方向  u = −ŝ', south, xytext=(0, -1.25),
                color=F.INK, fontsize=11, ha='center', va='top',
                arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=.8))
    fig.legend(handles=handles, loc='center', bbox_to_anchor=(.5, .29),
               ncol=2, frameon=False, labelcolor=F.INK)
    fig.text(.5, .225, '两路的极限：同一 u，不同参考姿态',
             ha='center', color=F.INK, fontsize=12)
    fig.text(.5, .17, '≠', ha='center', color=F.INK, fontsize=25)
    fig.text(.5, .115, '带标记的姿态相差绕太阳轴的 90°；\n反向点没有唯一的“最短转动”起点。',
             ha='center', color=F.INK, fontsize=10.5, linespacing=1.7)
    fig.text(.5, .067, '两列使用同一世界坐标和镜头；彩色箭头标记同一条体轴 e₁。',
             ha='center', color=F.INK, fontsize=9.5)
    fig.text(.5, .035, '局部辅助示意：只展示最短转动选法的坏点，不是任意参考选法都无法全局光滑的证明。',
             ha='center', color=F.INK, fontsize=9.5)
    F.save(fig, 'angle_fibers', out)


if __name__ == '__main__':
    F.cli(main)
