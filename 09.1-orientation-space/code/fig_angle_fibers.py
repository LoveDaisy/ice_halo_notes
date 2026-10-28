# 图 5b：底球上的角纤维与最短转动参考点相对局部截面的卷绕 → ../img/angle_fibers.png。
import numpy as np
from matplotlib.patches import Circle

from halo_notes.draw.projection import Camera
from halo_notes.draw.sphere import Sphere
from check_orientation_space import min_rotation_to
import _orientation_fig as F


def reference_loop(count=721, radius_deg=5.):
    phi = np.linspace(0, 2*np.pi, count)
    e = np.radians(radius_deg)
    u = np.column_stack((np.sin(e)*np.cos(phi), np.sin(e)*np.sin(phi),
                         np.full(count, -np.cos(e))))
    sun = np.array([0., 0., 1.])
    shortest = min_rotation_to(u, sun)
    local = np.diag([1., -1., -1.]) @ min_rotation_to(u, -sun)
    relative = shortest @ local.transpose(0, 2, 1)
    # 固定一次整体起点，使 φ=0 时两截面重合；常量左乘不破坏局部光滑性。
    local = relative[0] @ local
    relative = shortest @ local.transpose(0, 2, 1)
    phase = np.unwrap(np.arctan2(relative[:, 1, 0], relative[:, 0, 0]))
    return phi, u, shortest, local, phase


def clock(ax, center, angle, radius=0.19):
    center = np.asarray(center)
    ax.add_patch(Circle(center, radius, facecolor='white', edgecolor=F.BLUE, lw=1.15, zorder=9))
    # 十二点方向在每个小圆中都代表同一个局部光滑起点；正角逆时针。
    zero = center + [0, radius]
    ax.plot([zero[0], zero[0]], [zero[1]-0.025, zero[1]+0.025], color=F.INK, lw=1.0, zorder=10)
    mark = center + radius*np.array([-np.sin(angle), np.cos(angle)])
    ax.plot([center[0], mark[0]], [center[1], mark[1]], color=F.ORANGE, lw=1.2, zorder=11)
    ax.scatter([mark[0]], [mark[1]], s=28, color=F.ORANGE, edgecolor='white', lw=0.5, zorder=12)


def main(out=None):
    fig = F.canvas('每个方向挂一个圆，但参考起点不能处处光滑',
                   '小圆代表绕太阳转动的角 θ；橙点是最短转动选出的 θ = 0 参考姿态。', size=(12.0, 8.0))
    camera = Camera(azimuth=-55, elevation=-27, projection='orthographic')
    ax = fig.add_axes([0.03, 0.26, 0.42, 0.54])
    F.globe(ax, camera)
    for lon, lat, offset in ((-70, 45, (-0.4, 0.25)), (-115, -8, (-0.5, 0.13)),
                              (10, -10, (0.48, 0.14))):
        p = camera.project_xy(Sphere().point(lon, lat))[0]
        c = p + offset
        ax.plot([p[0], c[0]], [p[1], c[1]], color=F.EDGE, lw=0.8, zorder=7)
        ax.scatter([p[0]], [p[1]], s=18, color=F.BLUE, zorder=8)
        # 这里只画纤维集合，不为它凭空指定一个参考点。
        ax.add_patch(Circle(c, 0.13, facecolor='white', edgecolor=F.BLUE, lw=1, zorder=9))
    phi, u, _, _, phase = reference_loop()
    loop = camera.project_xy(u)
    ax.plot(loop[:, 0], loop[:, 1], color=F.ORANGE, lw=2, zorder=10)
    south = camera.project_xy([0, 0, -1])[0]
    ax.scatter(*south, marker='x', color=F.INK, s=35, zorder=11)
    ax.annotate('−ŝ：最短转动没有唯一起点', south,
                xytext=(-1.3, -1.23), color=F.INK, fontsize=10,
                arrowprops=dict(arrowstyle='-', color=F.EDGE, lw=0.8))
    ax.set_title('底空间 S² · 每点对应一根角纤维', fontsize=11, color=F.INK)
    ax.set(xlim=(-1.6, 1.6), ylim=(-1.5, 1.5))
    bx = fig.add_axes([0.52, 0.3, 0.43, 0.49])
    radius = 0.91
    bx.plot(radius*np.cos(phi), radius*np.sin(phi), color=F.EDGE, lw=1.1, zorder=1)
    for j in range(8):
        k = j*(len(phi)-1)//8
        center = radius*np.array([np.cos(phi[k]), np.sin(phi[k])])
        clock(bx, center, phase[k]-phase[0])
    F.arrow(bx, (0.38, 0.82), (0.24, 0.88), F.INK, lw=1)
    bx.text(0, 0.1, '绕 −ŝ 一周', ha='center', color=F.INK, fontsize=12)
    bx.text(0, -0.16, '参考点转两周', ha='center', color=F.INK, fontsize=12)
    bx.text(1.3, 0, '起点', ha='center', va='center', color=F.INK, fontsize=10)
    bx.set(xlim=(-1.4, 1.55), ylim=(-1.3, 1.3), aspect='equal')
    bx.axis('off')
    bx.set_title('把 5° 小圈展开来看（纤维放大示意）', color=F.INK, fontsize=11)
    cx = fig.add_axes([0.59, 0.135, 0.30, 0.12])
    cx.plot(phi/(2*np.pi), (phase-phase[0])/(2*np.pi), color=F.ORANGE, lw=1.8)
    cx.set(xlim=(0, 1), ylim=(0, 2.1), xlabel='沿底球小圈走过的圈数', ylabel='相对转角 / 圈')
    cx.set_xticks([0, .5, 1])
    cx.set_yticks([0, 1, 2])
    cx.tick_params(labelsize=9)
    fig.text(0.25, 0.17, '小圆是角度的示意，\n不是额外的一条空间轨道。',
             ha='center', color=F.INK, fontsize=10, linespacing=1.6)
    fig.text(0.5, 0.035, '每个小圆的上方短刻线，都是同一局部光滑截面的起点；“转两圈”相对于它计数。',
             ha='center', color=F.INK, fontsize=9.5)
    F.save(fig, 'angle_fibers', out)


if __name__ == '__main__':
    F.cli(main)
