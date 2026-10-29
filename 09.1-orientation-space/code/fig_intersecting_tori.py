# 图 3 扩展候选：开窗的两张参数环面与两条原始交圈 → ../img/intersecting_tori.png。
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D

import fig_column_torus as T
import fig_parry_neighborhood as N

P = T.P
# 两个母圆的旋转曲面，仅实现集合关联，不是 SO(3) 的欧氏嵌入。
LOWITZ, COLUMN = 0, 1
MAJOR = np.array([T.MAJOR, 1.7])
MINOR = T.MINOR
CROSS_R = MAJOR.mean()
CROSS_Z = np.sqrt(MINOR**2 - (CROSS_R - MAJOR[0])**2)
CROSS_ANGLE = np.arccos((CROSS_R - MAJOR) / MINOR)
AZ, EL = T.VIEW_AZ, T.VIEW_EL
FRONT = np.array([np.cos(AZ), np.sin(AZ), 0.0])
CAMERA = T.CAMERA
RIGHT, UP, EYE = CAMERA.right, CAMERA.cam_up, CAMERA.view_dir
EXTENT = T.EXTENT
# 开窗只移除面片，不加封口面；两条交圈的任何点都不落入切口。
WINDOW_R, WINDOW_Z = 2.25, 0.84
COLUMN_INNER = 1.42
LEADERS = (
    (LOWITZ, AZ + np.radians(55), CROSS_ANGLE[LOWITZ], (3.5, 1.35),
     '另一原始圈\n经晶体对称对应 Parry', 'left'),
    (LOWITZ, AZ, -CROSS_ANGLE[LOWITZ], (3.5, -1.55),
     'Parry 原始圈\nt = −90°', 'left'),
    (LOWITZ, AZ - np.radians(105), 0, (-3.75, 1.3),
     '片晶圈 · t = 0°\n在 Lowitz 上，\n不与橙圈相交', 'right'),
    (COLUMN, AZ - np.radians(45), 0, (-3.55, -1.15),
     '柱晶环面的一部分\n上下已弯回去', 'right'),
)


def surface(kind, phi, angle):
    """显示环面的弧度参数；angle 是母圆角，非物理摆角。"""
    p, a = np.broadcast_arrays(phi, angle)
    r = MAJOR[kind] + MINOR * np.cos(a)
    return np.stack([r * np.cos(p), r * np.sin(p), MINOR * np.sin(a)], axis=-1)


def parameters(kind, xyz):
    xyz = np.asarray(xyz)
    r = np.hypot(xyz[..., 0], xyz[..., 1])
    return np.arctan2(xyz[..., 1], xyz[..., 0]), np.arctan2(xyz[..., 2], r - MAJOR[kind])


def physical_angle(kind, angle):
    """圆周的光滑重参数化：显示交线 ±CROSS_ANGLE 对应物理角 ±90°。"""
    k = np.tan(CROSS_ANGLE[kind] / 2)
    return 2 * np.arctan2(np.sin(angle / 2) / k, np.cos(angle / 2))


def display_angle(kind, physical):
    """physical_angle 的圆周逆映射；输入、输出均为弧度。"""
    k = np.tan(CROSS_ANGLE[kind] / 2)
    return 2 * np.arctan2(k * np.sin(np.asarray(physical) / 2),
                          np.cos(np.asarray(physical) / 2))


def attitude(kind, phi, angle):
    p, b = np.degrees([phi, physical_angle(kind, angle)])
    if kind == LOWITZ:
        return N.lowitz_attitude(p, b)
    theta = 90.0 - b
    # 两交圈逐点配对；柱晶的方位坐标在下圈相差 180°，不能直接当同一个 ψ。
    return T.attitude(p + theta, theta)


def torus_distance(kind, xyz):
    r = np.hypot(xyz[..., 0], xyz[..., 1])
    return np.hypot(r - MAJOR[kind], xyz[..., 2]) - MINOR


def cut_distance(kind, xyz):
    """正值表示被切掉的区域；都是 1-Lipschitz 距离的 min/max。"""
    r = np.hypot(xyz[..., 0], xyz[..., 1])
    if kind == COLUMN:
        return COLUMN_INNER - r
    return np.minimum.reduce([xyz @ FRONT, r - WINDOW_R, WINDOW_Z - np.abs(xyz[..., 2])])


def distance_bound(kind, xyz, cutter=cut_distance):
    # 到保留薄面的保守距离下界，不会把切口画成额外的实体封口面。
    return np.maximum(np.abs(torus_distance(kind, xyz)), cutter(kind, xyz))


def trace(origins, directions, kind, cutter=cut_distance, *, tolerance=2e-5, max_steps=420):
    """按单位方向追踪；返回自相机点起的欧氏射线距离，非 Camera.depth。"""
    distance = np.zeros(len(origins))
    active = np.arange(len(origins))
    depths = np.full(len(origins), np.inf)
    for _ in range(max_steps):
        if not len(active):
            break
        xyz = origins[active] + distance[active, None] * directions[active]
        step = distance_bound(kind, xyz, cutter)
        found = step < tolerance
        depths[active[found]] = distance[active[found]]
        distance[active] += step
        active = active[~found & (distance[active] < 2 * CAMERA.distance)]
    return depths


def project(xyz):
    return T.project(xyz, CAMERA)


def periodic_distance(angle, period):
    return np.abs((angle + period / 2) % period - period / 2)


def surface_pixels(width=1601, cutter=cut_distance):
    height, origins, directions = T.pixel_rays(width, EXTENT, CAMERA)
    depths = np.stack([trace(origins, directions, kind, cutter) for kind in (LOWITZ, COLUMN)])
    nearest, kinds = depths.min(axis=0), depths.argmin(axis=0)
    hit = np.isfinite(nearest)
    xyz, kinds = origins[hit] + nearest[hit, None] * directions[hit], kinds[hit]
    rgb = np.empty((len(xyz), 3))
    light = np.array([-0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    for kind in (LOWITZ, COLUMN):
        selected = kinds == kind
        points = xyz[selected]
        phi, angle = parameters(kind, points)
        normal = np.column_stack([np.cos(angle) * np.cos(phi), np.cos(angle) * np.sin(phi), np.sin(angle)])
        # 同一冰蓝材质，柱晶用较深明度；实体身份还由引线/图例明确标识。
        base = np.array(to_rgb(P.PAL['ice']))
        if kind == COLUMN:
            base = 0.60 * base + 0.40 * np.array(to_rgb(P.PAL['arc_roll']))
        brightness = 0.82 + 0.18 * np.maximum(normal @ light, 0)
        color = base * brightness[:, None]

        def ink(dist, half_width, value):
            nonlocal color
            coverage = np.clip((half_width + 0.003 - dist) / 0.006, 0, 1)
            color = color * (1 - coverage[:, None]) + np.array(to_rgb(value)) * coverage[:, None]

        radial = np.hypot(points[:, 0], points[:, 1])
        mesh = np.minimum(periodic_distance(phi, np.pi / 6) * radial,
                          periodic_distance(angle, np.pi / 6) * MINOR)
        ink(mesh, 0.004, P.PAL['ice_edge'])
        # 强调线在真实命中面上着色，绝不透过遮挡把背面线叠在前面。
        for sign in (-1, 1):
            ink(periodic_distance(angle - sign * CROSS_ANGLE[kind], 2 * np.pi) * MINOR,
                0.019, P.PAL['face_5'])
        if kind == LOWITZ:
            ink(periodic_distance(angle, 2 * np.pi) * MINOR, 0.018, P.PAL['arc_roll'])
        rgb[selected] = color
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    return image.reshape(height, width, 3), xyz, kinds


def main(out=None):
    P.apply_style()
    ink = P.PAL['ink_soft']
    fig = plt.figure(figsize=(11.6, 8.3))
    fig.text(0.055, 0.945, '两张环面，交于 Parry 族的两圈', fontsize=17, color=ink)
    fig.text(0.055, 0.901, '把前侧打开，露出相交处；每条橙圈同时属于柱晶与 Lowitz。', fontsize=11, color=ink)
    ax = fig.add_axes([0.025, 0.235, 0.95, 0.635])
    image, _, _ = surface_pixels()
    ax.imshow(image, origin='lower', extent=EXTENT, interpolation='lanczos')
    ax.set_aspect('equal')

    def leader(point, target, text, ha='left'):
        ax.annotate(text, xy=project(point)[:2], xytext=target, ha=ha, va='center',
                    fontsize=10.5, color=ink, linespacing=1.7,
                    arrowprops=dict(arrowstyle='-', color=P.PAL['ice_edge'], lw=0.9,
                                    connectionstyle='angle,angleA=0,angleB=90,rad=4'))

    for kind, phi, angle, target, text, align in LEADERS:
        leader(surface(kind, phi, angle), target, text, align)
    ax.set_xlim(-5.5, 5.2)
    ax.set_ylim(-2.5, 2.5)
    ax.axis('off')
    handles = [Line2D([], [], color=P.PAL['ice_edge'], lw=8, alpha=0.35, label='浅面：Lowitz 环面'),
               Line2D([], [], color=P.PAL['arc_roll'], lw=8, alpha=0.45, label='深面：柱晶环面'),
               Line2D([], [], color=P.PAL['face_5'], lw=2.5, label='橙线：Parry 族的两条交圈')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.245),
               ncol=3, frameon=False, fontsize=10, labelcolor=ink, handlelength=1.6)
    fig.text(0.5, 0.205, '开窗只是揭去遮挡的面片；片晶圈被揭去的前半段仍属于原来的环面。',
             ha='center', fontsize=9.5, color=ink)
    fig.text(0.5, 0.145, '完整 Lowitz：t = ±90° 各交一圈；roll 锁 0 的半环只保留 t = −90°。',
             ha='center', fontsize=10, color=ink)
    fig.text(0.5, 0.1, '两条原始交圈不同，但按 D₆ 晶体对称认同后属于同一 Parry 族。',
             ha='center', fontsize=10, color=ink)
    fig.text(0.5, 0.045, '集合关系示意 · 非整个 SO(3) 在三维欧氏空间的嵌入；高度、半径、网格间距均无物理刻度',
             ha='center', fontsize=9, color=ink)
    out = Path(out) if out is not None else Path(__file__).resolve().parents[1] / 'img/intersecting_tori.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
