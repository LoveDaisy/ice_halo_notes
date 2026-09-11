"""光路与锥体箭头。

- :class:`RayPath`：折线光路，每段带语义（入射 / 内部 / 出射）
- :func:`trace`：在凸晶体内按给定事件序列（折射 / 反射）做几何光学追迹，
  得到物理上自洽的折线，画图脚本只需声明"进哪个面、在哪反射、从哪出"
- :class:`Cone`：3D 圆锥体（顶点 + 轴向 + 长度 + 半径），投影后给出可见的
  轮廓母线与纬线圆弧，视角一变形状随之变化
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Sequence

import numpy as np

from .geometry import Polyhedron, unit
from .projection import Camera

N_ICE = 1.31  # 冰的折射率（可见光中段）


class SegmentKind(str, Enum):
    INCIDENT = "incident"
    INTERNAL = "internal"
    EXIT = "exit"


class EventKind(str, Enum):
    REFRACT_IN = "refract_in"
    REFLECT_INTERNAL = "reflect_internal"
    REFRACT_OUT = "refract_out"
    REFLECT_EXTERNAL = "reflect_external"


@dataclass(frozen=True)
class RayEvent:
    point_index: int      # 在 RayPath.points 里的下标
    face_number: int
    kind: EventKind


@dataclass(frozen=True)
class RayPath:
    points: np.ndarray                 # (N, 3)
    kinds: tuple[SegmentKind, ...]     # N-1 段
    events: tuple[RayEvent, ...] = ()

    def __post_init__(self) -> None:
        pts = np.asarray(self.points, dtype=float).reshape(-1, 3)
        object.__setattr__(self, "points", pts)
        if len(self.kinds) != len(pts) - 1:
            raise ValueError("kinds must have len(points)-1 entries")

    def segments(self) -> Iterator[tuple[np.ndarray, np.ndarray, SegmentKind]]:
        for i, k in enumerate(self.kinds):
            yield self.points[i], self.points[i + 1], k

    @property
    def start(self) -> np.ndarray:
        return self.points[0]

    @property
    def end(self) -> np.ndarray:
        return self.points[-1]

    def transformed(self, rotation: np.ndarray | None = None,
                    translation: Sequence[float] | None = None) -> "RayPath":
        p = self.points
        if rotation is not None:
            p = p @ np.asarray(rotation, dtype=float).T
        if translation is not None:
            p = p + np.asarray(translation, dtype=float)
        return RayPath(p, self.kinds, self.events)


# ---- 几何光学 --------------------------------------------------------------

def reflect(d: np.ndarray, n: np.ndarray) -> np.ndarray:
    """镜面反射。``n`` 为入射侧法向（与 ``d`` 夹角 > 90°）。"""
    return d - 2 * (n @ d) * n


def refract(d: np.ndarray, n: np.ndarray, n1: float, n2: float) -> np.ndarray:
    """Snell 折射（矢量形式）。``n`` 指向入射介质一侧；全反射时抛 ``ValueError``。"""
    eta = n1 / n2
    cos_i = -(n @ d)
    sin2_t = eta * eta * (1 - cos_i * cos_i)
    if sin2_t > 1:
        raise ValueError("total internal reflection: refraction impossible here")
    return eta * d + (eta * cos_i - np.sqrt(1 - sin2_t)) * n


def trace(crystal: Polyhedron, origin: Sequence[float], direction: Sequence[float],
          events: Sequence[str], *, n_ice: float = N_ICE,
          tail: float = 1.6, head: float = 1.6) -> RayPath:
    """从晶体外一点沿 ``direction`` 追迹，逐次表面相遇按 ``events`` 决定折射还是反射。

    ``events`` 每项取 ``"refract"`` 或 ``"reflect"``：第一次相遇发生在外表面
    （``reflect`` = 外反射，路径就此结束；``refract`` = 进入晶体），之后的相遇
    发生在内表面（``reflect`` = 内反射；``refract`` = 出射，路径结束）。
    ``tail`` / ``head`` 是入射段 / 出射段在晶体外画出的长度。
    """
    o = np.asarray(origin, dtype=float)
    d = unit(direction)
    hit = crystal.intersect_ray(o, d)
    if hit is None or hit[0] <= 0:
        raise ValueError("ray does not hit the crystal from outside")
    t_in, f_in, _, _ = hit
    p = o + t_in * d
    points = [p - d * tail, p]
    kinds = [SegmentKind.INCIDENT]
    ev: list[RayEvent] = []

    if not events:
        raise ValueError("events must not be empty")
    first, rest = events[0], list(events[1:])
    n = crystal.normal(f_in)  # 外法向 = 入射侧法向
    if first == "reflect":
        d = reflect(d, n)
        ev.append(RayEvent(1, f_in.number, EventKind.REFLECT_EXTERNAL))
        points.append(p + d * head)
        kinds.append(SegmentKind.EXIT)
        return RayPath(np.array(points), tuple(kinds), tuple(ev))
    if first != "refract":
        raise ValueError(f"unknown event {first!r}")
    d = refract(d, n, 1.0, n_ice)
    ev.append(RayEvent(1, f_in.number, EventKind.REFRACT_IN))

    for e in rest:
        hit = crystal.intersect_ray(p + d * 1e-9, d)
        if hit is None:
            raise RuntimeError("internal ray lost the crystal (numerical trouble)")
        _, _, t_out, f_out = hit
        p = p + d * (t_out + 1e-9)
        n_out = crystal.normal(f_out)
        points.append(p)
        kinds.append(SegmentKind.INTERNAL)
        idx = len(points) - 1
        if e == "reflect":
            d = reflect(d, -n_out)
            ev.append(RayEvent(idx, f_out.number, EventKind.REFLECT_INTERNAL))
        elif e == "refract":
            d = refract(d, -n_out, n_ice, 1.0)
            ev.append(RayEvent(idx, f_out.number, EventKind.REFRACT_OUT))
            points.append(p + d * head)
            kinds.append(SegmentKind.EXIT)
            return RayPath(np.array(points), tuple(kinds), tuple(ev))
        else:
            raise ValueError(f"unknown event {e!r}")
    raise ValueError("event sequence ended while the ray is still inside the crystal")


def aim(crystal: Polyhedron, face_number: int, direction: Sequence[float], *,
        offset: Sequence[float] = (0.0, 0.0, 0.0), back: float = 3.0) -> np.ndarray:
    """给 :func:`trace` 选起点：让沿 ``direction`` 的射线正好打在某面质心（+ ``offset``）上。"""
    target = crystal.centroid(crystal.face(face_number)) + np.asarray(offset, dtype=float)
    return target - unit(direction) * back


# ---- 锥体箭头 --------------------------------------------------------------

@dataclass(frozen=True)
class Cone:
    """圆锥体：``apex`` 为顶点，``axis`` 指向底面，``length`` 高，``radius`` 底面半径。"""

    apex: np.ndarray
    axis: np.ndarray
    length: float
    radius: float
    rings: int = 3
    samples: int = 72

    def __post_init__(self) -> None:
        object.__setattr__(self, "apex", np.asarray(self.apex, dtype=float))
        object.__setattr__(self, "axis", unit(self.axis))
        if self.rings < 1:
            raise ValueError("rings must be >= 1")

    @classmethod
    def along(cls, apex: Sequence[float], direction: Sequence[float], *,
              length: float, radius: float, **kw) -> "Cone":
        return cls(np.asarray(apex, float), unit(direction), length, radius, **kw)

    # ---- 3D 采样 ---------------------------------------------------------
    def _frame(self) -> tuple[np.ndarray, np.ndarray]:
        """与轴垂直的两个正交单位向量。"""
        a = self.axis
        helper = np.array([0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = unit(np.cross(a, helper))
        w = np.cross(a, u)
        return u, w

    def ring_points(self, t: float) -> np.ndarray:
        """底面方向距顶点 ``t·length`` 处的纬线圆（(samples+1, 3)，首尾闭合）。"""
        u, w = self._frame()
        th = np.linspace(0, 2 * np.pi, self.samples + 1)
        c = self.apex + self.axis * (t * self.length)
        r = self.radius * t
        return c + r * (np.cos(th)[:, None] * u + np.sin(th)[:, None] * w)

    def surface_normals(self, t: float) -> np.ndarray:
        """与 :meth:`ring_points` 同序的锥面外法向。"""
        u, w = self._frame()
        th = np.linspace(0, 2 * np.pi, self.samples + 1)
        radial = np.cos(th)[:, None] * u + np.sin(th)[:, None] * w
        alpha = np.arctan2(self.radius, self.length)
        return np.cos(alpha) * radial - np.sin(alpha) * self.axis

    @property
    def base_center(self) -> np.ndarray:
        return self.apex + self.axis * self.length

    # ---- 投影 ------------------------------------------------------------
    def wireframe(self, camera: Camera) -> list[np.ndarray]:
        """可见的线：两条轮廓母线 + 各圈纬线的可见弧。返回 2D 折线列表。"""
        pieces: list[np.ndarray] = []
        normals = self.surface_normals(1.0)
        rim = self.ring_points(1.0)
        vis = np.einsum("ij,ij->i", normals, camera.view_vector(rim)) > 0
        base_faces_viewer = (self.axis @ camera.view_vector(self.base_center)[0]) > 0

        # 轮廓母线：锥面可见/不可见分界处的两条母线
        for i in range(self.samples):
            if vis[i] != vis[i + 1]:
                # 线性插值找分界角
                a = normals[i] @ camera.view_vector(rim[i])[0]
                b = normals[i + 1] @ camera.view_vector(rim[i + 1])[0]
                s = a / (a - b) if a != b else 0.5
                p = rim[i] + s * (rim[i + 1] - rim[i])
                pieces.append(camera.project_xy(np.stack([self.apex, p])))

        # 纬线圆弧
        for k in range(1, self.rings + 1):
            t = k / self.rings
            ring = self.ring_points(t)
            if k == self.rings and base_faces_viewer:
                pieces.append(camera.project_xy(ring))  # 底面圆整圈可见
                continue
            pieces.extend(self._visible_runs(ring, vis, camera))
        return pieces

    @staticmethod
    def _visible_runs(ring: np.ndarray, vis: np.ndarray, camera: Camera) -> list[np.ndarray]:
        """把一圈点按可见掩码切成若干连续弧（考虑首尾相接）。"""
        n = len(ring) - 1  # 最后一点与第一点重合
        v = vis[:n]
        if v.all():
            return [camera.project_xy(ring)]
        if not v.any():
            return []
        start = int(np.argmin(v))  # 从一个不可见点开始转一圈，运行段不会跨首尾
        idx = [(start + i) % n for i in range(n + 1)]
        runs, cur = [], []
        for i in idx:
            if v[i]:
                cur.append(i)
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        return [camera.project_xy(ring[r]) for r in runs if len(r) > 1]

    def outline(self, camera: Camera) -> np.ndarray:
        """投影轮廓（顶点 + 底面圆的 2D 凸包），用于画实心箭头。"""
        pts = camera.project_xy(np.vstack([self.apex[None, :], self.ring_points(1.0)]))
        return convex_hull_2d(pts)


def convex_hull_2d(points: np.ndarray) -> np.ndarray:
    """Andrew 单调链凸包，返回逆时针顶点（不闭合）。"""
    pts = sorted(map(tuple, np.asarray(points, dtype=float)))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])
