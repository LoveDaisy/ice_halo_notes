# 图 3 / 图 2b 共用的两张参数环面几何：母圆、物理姿态映射、透视射线求交与着色（不单独出图）。
from __future__ import annotations

import numpy as np
from matplotlib.colors import to_rgb

import fig_column_torus as T
from halo_notes.draw.style.figure import figure_scheme
import check_orientation_space as C

P = T.P
S = figure_scheme()
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


def lowitz_attitude(phi, t):
    """度制 Lowitz 姿态：方位 φ 下绕长对角线摆 t，Rz(φ) Ry(t)。"""
    return C.Rz(float(phi)) @ C.Ry(float(t))


def attitude(kind, phi, angle):
    p, b = np.degrees([phi, physical_angle(kind, angle)])
    if kind == LOWITZ:
        return lowitz_attitude(p, b)
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
        # 两张环面的表面处理由候选方案给出；实体身份还由引线/图例明确标识。
        finish = S.surfaces['lowitz' if kind == LOWITZ else 'column']
        base = np.array(to_rgb(finish.base))
        brightness = finish.ambient + (1 - finish.ambient) * np.maximum(normal @ light, 0)
        color = base * brightness[:, None]

        def ink(dist, half_width, value):
            nonlocal color
            coverage = np.clip((half_width + 0.003 - dist) / 0.006, 0, 1)
            color = color * (1 - coverage[:, None]) + np.array(to_rgb(value)) * coverage[:, None]

        radial = np.hypot(points[:, 0], points[:, 1])
        mesh = np.minimum(periodic_distance(phi, np.pi / 6) * radial,
                          periodic_distance(angle, np.pi / 6) * MINOR)
        ink(mesh, finish.mesh_width, finish.mesh)
        # 强调线在真实命中面上着色，绝不透过遮挡把背面线叠在前面。
        for sign in (-1, 1):
            ink(periodic_distance(angle - sign * CROSS_ANGLE[kind], 2 * np.pi) * MINOR,
                0.019, S.family['parry'])
        if kind == LOWITZ:
            ink(periodic_distance(angle, 2 * np.pi) * MINOR, 0.018, S.family['plate'])
        rgb[selected] = color
    image = np.ones((len(origins), 3))
    image[hit] = rgb
    image = image.reshape(height, width, 3)
    kind_map = np.full(len(origins), -1)
    kind_map[hit] = kinds
    edges = T.outline_mask(nearest.reshape(height, width))
    for kind in (LOWITZ, COLUMN):
        selected = edges & (kind_map.reshape(height, width) == kind)
        image[selected] = to_rgb(S.surfaces['lowitz' if kind == LOWITZ else 'column'].outline)
    return image, xyz, kinds
