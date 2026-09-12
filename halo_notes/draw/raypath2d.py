"""2D 截面光路：按边序列反解、展开。

Snell 折射 / 镜面反射 / 追迹 / 白盒复核 / 展开全部**复用** :mod:`raypath` 与 :mod:`unfold`
（它们只用点积与镜像公式，与维数无关）；本模块只补 2D 专属的一小块——入射方向只有一个自由度
（入射角 θ，正负各一侧），采样方式与 3D 的 θ × φ 不同。

- :class:`RayPath2D`：见 :mod:`raypath`（这里再导出一次）
- :func:`solve_raypath_2d`：2D 版 :func:`raypath.solve_raypath`
- :func:`unfold_2d`：2D 版 :func:`unfold.unfold`（级联镜像的幽灵截面）
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .geometry2d import Polygon2D, perp2d
from .raypath import N_ICE, RayPath2D, search_raypath
from .unfold import unfold


def _incident_directions_2d(n: np.ndarray, theta_deg: np.ndarray) -> np.ndarray:
    """朝向边（外法向 ``n``）的入射方向采样：入射角 θ（有符号，正 = 偏向 ``n`` 逆时针一侧），(N, 2)。"""
    u = perp2d(n)
    th = np.deg2rad(np.asarray(theta_deg, dtype=float)).ravel()
    return -np.cos(th)[:, None] * n[None, :] + np.sin(th)[:, None] * u[None, :]


def solve_raypath_2d(section: Polygon2D, faces: Sequence[int], *, n_ice: float = N_ICE,
                     prefer_point: Sequence[float] | None = None,
                     prefer_direction: Sequence[float] | None = None,
                     angle_range: tuple[float, float] = (-88.0, 88.0),
                     theta_step: float = 2.0, n_ring: int = 3,
                     tail: float = 1.6, head: float = 1.6) -> RayPath2D:
    """按边序列反解一条截面光路（首边折入、中间边内反射、末边折出；单边 = 外反射），约定、
    偏好与择优规则同 :func:`raypath.solve_raypath`；搜索空间是入射边上的采样点 × 有符号入射角
    ``angle_range`` 内每 ``theta_step`` 度。找不到解抛 ``ValueError``。"""
    if section.DIM != 2:
        raise TypeError("solve_raypath_2d expects a 2D polygon (Polygon2D / CrossSection)")
    faces = [int(f) for f in faces]
    n = section.normal(section.face(faces[0]))
    thetas = np.arange(angle_range[0], angle_range[1] + 1e-9, theta_step)
    dirs = _incident_directions_2d(n, thetas)
    path = search_raypath(section, faces, dirs, n_ice=n_ice, prefer_point=prefer_point,
                          prefer_direction=prefer_direction, n_ring=n_ring, tail=tail, head=head)
    assert isinstance(path, RayPath2D)
    return path


def unfold_2d(section: Polygon2D, path: RayPath2D) -> list[Polygon2D]:
    """光路每次内反射对应的幽灵截面（级联镜像，编号字形随之镜像）；无内反射时返回空列表。
    与 3D :func:`unfold.unfold` 是同一份实现。"""
    if section.DIM != 2 or path.DIM != 2:
        raise TypeError("unfold_2d expects a 2D polygon and a RayPath2D")
    return unfold(section, path)


__all__ = ["RayPath2D", "solve_raypath_2d", "unfold_2d"]
