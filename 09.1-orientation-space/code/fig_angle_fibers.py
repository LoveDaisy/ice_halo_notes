# 图 5b：最短转动选起点，在反向点没有唯一极限 → ../img/angle_fibers.png。
from matplotlib import patheffects
from matplotlib.patches import Circle
import numpy as np
from scipy.spatial.transform import Rotation

from halo_notes.draw.projection import Camera
from halo_notes.draw.scene import finish
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


ROUTES = 'AB'
DISTANCES = (95., 60., 25., 0.)


def route_style(i):
    """路线 A / B 是非族的二元对照：墨实线 vs 紫虚线。"""
    return F.PAIR['ab'[i]], ('-' if i == 0 else F.PAIR_DASH)


def sphere_panel(fig, rect):
    ax = fig.add_axes(rect)
    F.globe(ax, CAMERA)
    ax.set(xlim=(-1.2, 1.2), ylim=(-1.32, 1.3))
    halo = [patheffects.withStroke(linewidth=3, foreground=F.PAPER)]
    for i, azimuth in enumerate(APPROACH_AZIMUTHS):
        color, style = route_style(i)
        u, _ = approach(azimuth, np.linspace(100, .1, 401))
        xy = CAMERA.project_xy(np.vstack((u, -SUN)))
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=2.2, ls=style, zorder=9)
        F.arrow(ax, xy[205], xy[230], color, zorder=10)
        points, _ = approach_frames(azimuth)
        for j, point in enumerate(CAMERA.project_xy(points[:3])):
            ax.scatter(*point, s=44, color=color, edgecolor=F.PAPER, linewidth=1, zorder=11)
            ax.annotate(f'{ROUTES[i]}{j+1}', point, xytext=(-9 if i == 0 else 9, 4),
                        textcoords='offset points', ha='right' if i == 0 else 'left',
                        color=F.INK, fontsize=13, zorder=12, path_effects=halo)
    north, south = CAMERA.project_xy([SUN, -SUN])
    ax.scatter(*north, s=60, color=F.SUN, edgecolor=F.PAPER, linewidth=1, zorder=12)
    ax.text(north[0]+.06, north[1]+.06, r'$\hat{\mathbf{s}}$', color=F.INK, fontsize=15,
            va='bottom', zorder=12)
    ax.scatter(*south, marker='x', s=55, color=F.INK, linewidth=1.6, zorder=12)
    ax.text(south[0], south[1]-.1, r'$\mathbf{u}=-\hat{\mathbf{s}}$', color=F.INK, fontsize=14,
            ha='center', va='top', zorder=12)
    return ax


def crystal_panel(fig, rect, R, color, gid, labels):
    bx = fig.add_axes(rect)
    F.crystal(bx, R, face_numbers=())
    bx.set_gid(gid)
    sun_tip = F.CAMERA.project_xy(1.55*SUN)[0]
    F.arrow(bx, (0, 0), sun_tip, F.SUN, lw=1.8, zorder=13)
    # 同一条带标签的体轴随真实旋转移动，避免外形对称掩盖不同姿态。
    tip = F.CAMERA.project_xy(1.2*R[:, 0])[0]
    F.arrow(bx, (0, 0), tip, color, lw=2.2, zorder=14).set_gid('body-axis-e1')
    if labels:
        halo = [patheffects.withStroke(linewidth=3, foreground=F.PAPER)]
        right = tip[0] >= 0
        bx.text(tip[0] + (.1 if right else -.1), tip[1], 'e₁', color=F.INK, fontsize=13,
                ha='left' if right else 'right', va='center', zorder=20, path_effects=halo)
        bx.text(sun_tip[0] + (-.12 if right else .12), sun_tip[1]-.05, r'$\hat{\mathbf{s}}$',
                color=F.INK, fontsize=14, ha='right' if right else 'left', va='top')
    bx.set(xlim=(-1.4, 1.4), ylim=(-1.75, 1.6))
    return bx


def top_view_xy(vectors):
    """沿 ŝ（世界 z）俯视的平面坐标；屏幕横轴取晶体镜头的 right，纵轴朝镜头前方，与晶体面板同向。"""
    right = F.CAMERA.right
    forward = -F.CAMERA.view_dir
    forward = forward - forward[2]*SUN
    forward /= np.linalg.norm(forward)
    vectors = np.atleast_2d(vectors)
    return np.column_stack((vectors @ right, vectors @ forward))


def top_view(fig, rect, limits):
    """两路极限沿 ŝ 俯视：e₁ 都躺在水平面里，夹角就是两极限绕太阳轴相差的角。"""
    cx = fig.add_axes(rect)
    cx.add_patch(Circle((0, 0), 1, facecolor='none', edgecolor=F.EDGE, lw=1.0))
    cx.scatter(0, 0, s=50, color=F.SUN, edgecolor=F.PAPER, zorder=5)
    angles = []
    for i, R in enumerate(limits):
        color, style = route_style(i)
        e = top_view_xy(R[:, 0])[0]
        e /= np.linalg.norm(e)
        angles.append(np.degrees(np.arctan2(e[1], e[0])))
        cx.plot([0, .92*e[0]], [0, .92*e[1]], color=color, lw=2.2, ls=style)
        F.arrow(cx, .8*e, .98*e, color, lw=2.2)
        cx.text(*(1.2*e), ROUTES[i], color=F.INK, fontsize=13, ha='center', va='center')
    lo, hi = sorted(angles)
    if hi - lo > 180:
        lo, hi = hi, lo + 360
    t = np.radians(np.linspace(lo, hi, 60))
    cx.plot(.42*np.cos(t), .42*np.sin(t), color=F.INK, lw=1.0)
    mid = np.radians((lo+hi)/2)
    cx.text(.66*np.cos(mid), .66*np.sin(mid), f'{hi-lo:.0f}°', color=F.INK, fontsize=13,
            ha='center', va='center')
    cx.text(0, -1.5, '沿 ŝ 俯视两极限', color=F.INK, fontsize=13, ha='center', va='top')
    cx.set_gid('limit-top-view')
    finish(cx, (-1.45, 1.45), (-1.45, 1.45))
    return cx


def main(out=None):
    fig = F.canvas(size=(13, 6.2))
    sphere_panel(fig, [.0, .03, .34, .94])
    limits = []
    for i, azimuth in enumerate(APPROACH_AZIMUTHS):
        color, _ = route_style(i)
        _, matrices = approach_frames(azimuth)
        limits.append(matrices[-1])
        bottom = .51 - i*.49
        for j, R in enumerate(matrices):
            rect = [.335 + j*.122, bottom, .122, .47]
            bx = crystal_panel(fig, rect, R, color, f'{ROUTES[i]}{j+1}', labels=(j == 0))
            title = f'{ROUTES[i]}{j+1}' if j < 3 else f'{ROUTES[i]} 的极限'
            bx.text(0, -1.62, title, color=F.INK, fontsize=13, ha='center', va='bottom')
    top_view(fig, [.835, .3, .155, .4], limits)
    F.save(fig, 'angle_fibers', out)


if __name__ == '__main__':
    F.cli(main)
