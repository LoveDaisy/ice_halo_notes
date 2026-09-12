"""球面族图元：单位球经纬网格、球面点云、球面曲线、大圆（赤道）、以任意点为顶的圆锥面
（3.5 / 3.6 特里克尔弧、6.1 姿态点云）。

与 :mod:`scene` 同款"纯函数 + 显式传参"：:class:`Sphere` 只是几何数据容器，渲染入口都是模块级
``render_*(ax, sphere, …, camera=…, preset=…)``；所有元素经同一个 :class:`projection.Camera` 投影。
球面上一点"朝向观察者"的判据与 :func:`projection.face_visible` 同一约定——该点的球面外法向与
:meth:`Camera.view_vector` 点积为正。折线按可见性切段一律走 :func:`scene._plot_runs`（单一实现，
本模块不再写第二份切段循环）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import Polygon

from .geometry import perp_basis, unit
from .projection import Camera
from .scene import Z_EXTERNAL, Z_HIDDEN_EDGE, Z_INTERNAL, Z_VISIBLE_EDGE, _plot_runs
from .style import Preset

# 绘制层级：网格最底、锥面在网格之上、曲线 / 点云 / 大圆压在最上（与 scene 的层级常量并列）
Z_GRID_HIDDEN, Z_GRID = Z_HIDDEN_EDGE, Z_VISIBLE_EDGE
Z_CONE = Z_VISIBLE_EDGE + 0.5
Z_ON_SPHERE_HIDDEN, Z_ON_SPHERE = Z_INTERNAL, Z_EXTERNAL


@dataclass(frozen=True)
class Sphere:
    """球心 + 半径。``point(lon, lat)`` 把经纬度（度；经度从 +x 起逆时针、纬度从赤道向 +z）映到球面。"""

    center: Sequence[float] = (0.0, 0.0, 0.0)
    radius: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "center", np.asarray(self.center, dtype=float))

    def point(self, lon_deg, lat_deg) -> np.ndarray:
        lon, lat = np.deg2rad(np.asarray(lon_deg, float)), np.deg2rad(np.asarray(lat_deg, float))
        lon, lat = np.broadcast_arrays(lon, lat)
        d = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)
        return self.center + self.radius * d.reshape(-1, 3)

    def on_surface(self, directions) -> np.ndarray:
        """把 (N,3) 方向（任意长度）落到球面上：``center + radius · dir/|dir|``。"""
        d = np.asarray(directions, float).reshape(-1, 3)
        return self.center + self.radius * d / np.linalg.norm(d, axis=1, keepdims=True)

    def facing(self, points, camera: Camera) -> np.ndarray:
        """各点（在球面上）是否朝向观察者：外法向 (p - center) 与该点处指向观察者的向量点积 > 0。
        透视投影下靠近轮廓的一圈会被判为背面（相机看不到切点以外），与凸多面体的 ``face_visible`` 同理。"""
        p = np.asarray(points, float).reshape(-1, 3)
        n = p - self.center
        return np.einsum("ij,ij->i", n, camera.view_vector(p)) > 0


def _hidden_kwargs(preset: Preset, hidden_semantic: str | None) -> dict | None:
    """背面段的线样式；``None`` = 不画（:func:`scene._plot_runs` 的 ``kw_false=None``）。"""
    return None if hidden_semantic is None else preset.line_kwargs(hidden_semantic)


# ---- 网格 / 大圆 -----------------------------------------------------------------

def graticule(ax, sphere: Sphere, *, camera: Camera, preset: Preset, lat_step: float | None = None,
              lon_step: float | None = None, semantic: str = "sphere_grid",
              hidden_semantic: str | None = "sphere_grid_hidden",
              samples: int | None = None) -> list[np.ndarray]:
    """经纬网格：纬线圈（``±lat_step, ±2·lat_step, …``，不含两极与赤道之外的特殊处理——赤道本身也是一条
    纬线）与经线（从 0 起每 ``lon_step`` 一条、极到极的半圆）。步长默认取 ``geom.sphere_grid_step_deg``。
    朝向观察者的段用 ``semantic``、背面段用 ``hidden_semantic``（``None`` = 只画可见半球，3.5 旧图观感）。
    返回每条线的 3D 采样点列表。"""
    geom = preset.geom
    lat_step = geom.sphere_grid_step_deg if lat_step is None else lat_step
    lon_step = geom.sphere_grid_step_deg if lon_step is None else lon_step
    n = geom.sphere_samples if samples is None else samples
    lines: list[np.ndarray] = []
    for lat in np.arange(-90.0 + lat_step, 90.0 - 1e-9, lat_step):
        lines.append(sphere.point(np.linspace(0.0, 360.0, n), lat))
    for lon in np.arange(0.0, 360.0 - 1e-9, lon_step):
        lines.append(sphere.point(lon, np.linspace(-90.0, 90.0, n)))
    hidden = _hidden_kwargs(preset, hidden_semantic)
    for pts in lines:
        _plot_runs(ax, pts, sphere.facing(pts, camera), camera, preset.line_kwargs(semantic), hidden,
                   Z_GRID, Z_GRID_HIDDEN)
    return lines


def render_great_circle(ax, sphere: Sphere, *, camera: Camera, preset: Preset,
                        normal: Sequence[float] = (0.0, 0.0, 1.0), semantic: str = "equator",
                        hidden_semantic: str | None = "equator_hidden",
                        samples: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """大圆强调线（默认赤道）：过球心、垂直于 ``normal`` 的圆，前半 ``semantic``（实线）、后半
    ``hidden_semantic``（6.1 旧图的虚线）。返回 ``(采样点, 朝向掩码)``。"""
    n = preset.geom.sphere_samples if samples is None else samples
    u, w = perp_basis(normal)
    t = np.linspace(0.0, 2 * np.pi, n)
    pts = sphere.center + sphere.radius * (np.cos(t)[:, None] * u + np.sin(t)[:, None] * w)
    mask = sphere.facing(pts, camera)
    _plot_runs(ax, pts, mask, camera, preset.line_kwargs(semantic), _hidden_kwargs(preset, hidden_semantic),
               Z_ON_SPHERE, Z_ON_SPHERE_HIDDEN)
    return pts, mask


# ---- 点云 / 曲线 -----------------------------------------------------------------

def render_point_cloud(ax, sphere: Sphere, directions, *, camera: Camera, preset: Preset,
                       semantic: str = "pose_cloud",
                       hidden_semantic: str | None = "pose_cloud_hidden") -> np.ndarray:
    """球面点云：``directions`` (N,3) 各方向落到球面上的散点，朝向观察者的用 ``semantic`` marker、
    背面的用 ``hidden_semantic``（``None`` = 不画）。返回朝向掩码（True = 可见）。"""
    pts = sphere.on_surface(directions)
    mask = sphere.facing(pts, camera)
    for sel, sem, z in ((mask, semantic, Z_ON_SPHERE), (~mask, hidden_semantic, Z_ON_SPHERE_HIDDEN)):
        if sem is None or not sel.any():
            continue
        xy = camera.project_xy(pts[sel])
        ax.plot(xy[:, 0], xy[:, 1], zorder=z, **preset.marker_kwargs(sem))
    return mask


def render_curve(ax, sphere: Sphere, points, *, camera: Camera, preset: Preset,
                 semantic: str = "sphere_curve", hidden_semantic: str | None = "sphere_curve_hidden",
                 split: bool = True) -> np.ndarray | None:
    """球面上的 3D 折线（特里克尔弧这类参数曲线）。``split=True`` 时按朝向切段（背面段
    ``hidden_semantic``，``None`` = 不画）并返回朝向掩码；``split=False`` 时整条按 ``semantic`` 一笔画出、
    不做可见性判定（3.5 / 3.6 旧图：整条弧都画），返回 ``None``。"""
    pts = np.asarray(points, float).reshape(-1, 3)
    if not split:
        xy = camera.project_xy(pts)
        ax.plot(xy[:, 0], xy[:, 1], zorder=Z_ON_SPHERE, solid_capstyle="round",
                **preset.line_kwargs(semantic))
        return None
    mask = sphere.facing(pts, camera)
    _plot_runs(ax, pts, mask, camera, preset.line_kwargs(semantic), _hidden_kwargs(preset, hidden_semantic),
               Z_ON_SPHERE, Z_ON_SPHERE_HIDDEN)
    return mask


# ---- 锥面 -----------------------------------------------------------------------

def cone_surface_points(apex, axis, half_angle_deg: float, lengths: Sequence[float], *,
                        phi_range: Sequence[float] = (0.0, 360.0), phi_from: Sequence[float] | None = None,
                        n_phi: int = 48, n_r: int = 8) -> np.ndarray:
    """圆锥面网格点 (n_r+1, n_phi+1, 3)：顶点 ``apex``、轴 ``axis``、半顶角 ``half_angle_deg``，
    母线从顶点起分 ``n_r`` 段延伸到斜长 ``lengths[i]``（每条母线可以不等长，长度按 ``phi`` 顺序给
    ``n_phi+1`` 个或只给 1 个）。``phi`` 是绕轴的方位角（度），``phi=0`` 指向 ``phi_from``（去掉沿轴分量；
    ``None`` 时取 :func:`geometry.perp_basis` 的第一个基向量），右手绕 ``axis`` 增大。"""
    a = np.asarray(apex, float)
    k = unit(axis)
    if phi_from is None:
        u, w = perp_basis(k)
    else:
        f = np.asarray(phi_from, float)
        u = unit(f - (f @ k) * k)
        w = np.cross(k, u)
    phi = np.deg2rad(np.linspace(phi_range[0], phi_range[1], n_phi + 1))
    half = np.deg2rad(half_angle_deg)
    gen = (np.cos(half) * k[None, :]
           + np.sin(half) * (np.cos(phi)[:, None] * u[None, :] + np.sin(phi)[:, None] * w[None, :]))
    L = np.broadcast_to(np.asarray(lengths, float), (n_phi + 1,))
    r = np.linspace(0.0, 1.0, n_r + 1)
    return a[None, None, :] + (r[:, None, None] * L[None, :, None]) * gen[None, :, :]


def render_cone(ax, apex, axis, half_angle_deg: float, *, camera: Camera, preset: Preset,
                length_up: float, length_down: float = 0.0,
                phi_range: Sequence[float] = (0.0, 360.0), phi_from: Sequence[float] | None = None,
                n_phi: int = 48, n_r: int = 8, fill_semantic: str | None = "cone_surface",
                edge_semantic: str = "cone_edge", clip_inside: Sphere | None = None) -> list[np.ndarray]:
    """（双叶）圆锥面：顶点 ``apex``、轴 ``axis``、半顶角 ``half_angle_deg``，沿 ``+axis`` 一叶母线斜长
    ``length_up``、沿 ``-axis`` 一叶 ``length_down``（0 = 不画）。网格单元按深度从远到近逐格画成
    "淡填充 + 网格线"的四边形（painter 顺序），``phi_range`` 可只画一个扇区（3.6 旧图）。
    ``clip_inside`` 给定时，中心落在该球内部的单元不画——把球当作不透明体，锥面只露出球外的部分
    （3.6 旧图 Mathematica 的真实遮挡观感；2D 分层画不出真正的相互遮挡，这是显式的近似）。
    返回各叶的网格点数组列表（供核验：网格点相对顶点的方向与轴夹角恒为半顶角）。"""
    leaves: list[np.ndarray] = []
    fill = preset.fill_kwargs(fill_semantic)
    edge = preset.line_kwargs(edge_semantic)
    # 下叶 = 半顶角取 180° − half 的同轴锥面（而不是把轴反向），两叶共用同一个 phi 参考方向，扇区不会镜像
    for half, L in ((half_angle_deg, length_up), (180.0 - half_angle_deg, length_down)):
        if L <= 0:
            continue
        leaves.append(cone_surface_points(apex, axis, half, [L], phi_range=phi_range, phi_from=phi_from,
                                          n_phi=n_phi, n_r=n_r))
    cells = []
    for grid in leaves:
        for i in range(grid.shape[0] - 1):
            for j in range(grid.shape[1] - 1):
                quad = np.stack([grid[i, j], grid[i, j + 1], grid[i + 1, j + 1], grid[i + 1, j]])
                c = quad.mean(axis=0)
                if clip_inside is not None and np.linalg.norm(c - clip_inside.center) < clip_inside.radius:
                    continue
                cells.append((camera.project(c)[1][0], quad))
    cells.sort(key=lambda c: c[0])   # 深度小 = 远，先画
    for _, quad in cells:
        xy = camera.project_xy(quad)
        # 填充与网格线各带自己的透明度（Polygon 的 alpha 会同时压住二者，所以把 alpha 揉进 RGBA）
        ax.add_patch(Polygon(xy, closed=True, zorder=Z_CONE,
                             facecolor="none" if fill is None else to_rgba(fill["facecolor"], fill["alpha"]),
                             edgecolor=to_rgba(edge["color"], edge["alpha"]), linewidth=edge["linewidth"]))
    return leaves


__all__ = ["Sphere", "cone_surface_points", "graticule", "render_cone", "render_curve",
           "render_great_circle", "render_point_cloud"]
