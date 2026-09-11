"""六方柱冰晶几何：顶点、面、面编号、外法向，以及刚体变换与射线求交。

面编号沿用系列既有约定（与 Lumice `doc/configuration.md` 一致）：
底面 1（+c，即 +z）、2（-c）；侧面 3–8，面 ``3+i`` 的外法向方位角为 ``i·60°``
（从 +x 起逆时针），因此从 +c 轴俯视时 3→8 逆时针递增，
绕 c 轴转 60° 等价于侧面编号 +1 (mod 6)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

Vec3 = np.ndarray

BASAL_TOP = 1
BASAL_BOTTOM = 2
PRISM_FACES = (3, 4, 5, 6, 7, 8)


@dataclass(frozen=True)
class Face:
    """多面体的一个面：编号 + 从外侧看逆时针排列的顶点索引环。"""

    number: int
    vertex_ids: tuple[int, ...]


def unit(v: Vec3) -> Vec3:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("zero-length vector")
    return v / n


def rotation(axis: Sequence[float], angle_deg: float) -> np.ndarray:
    """绕任意轴的旋转矩阵（Rodrigues 公式），右手系、角度制。"""
    k = unit(np.asarray(axis, dtype=float))
    t = np.deg2rad(angle_deg)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(t) * kx + (1 - np.cos(t)) * kx @ kx


def rotation_between(src: Sequence[float], dst: Sequence[float]) -> np.ndarray:
    """把方向 ``src`` 转到 ``dst`` 的最小旋转矩阵。"""
    a, b = unit(src), unit(dst)
    c = np.cross(a, b)
    s = np.linalg.norm(c)
    if s < 1e-12:
        if a @ b > 0:
            return np.eye(3)
        # 反向：绕任一垂直轴转 180°
        helper = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
        return rotation(np.cross(a, helper), 180.0)
    return rotation(c, np.rad2deg(np.arctan2(s, a @ b)))


class Polyhedron:
    """凸多面体：顶点数组 + 带编号的面。所有几何查询均基于顶点即时计算，
    所以刚体变换只需变换顶点。"""

    def __init__(self, vertices: np.ndarray, faces: Iterable[Face]):
        self.vertices = np.asarray(vertices, dtype=float).reshape(-1, 3)
        self.faces: tuple[Face, ...] = tuple(faces)
        self._by_number = {f.number: f for f in self.faces}
        if len(self._by_number) != len(self.faces):
            raise ValueError("duplicate face numbers")

    # ---- 基本查询 -------------------------------------------------------
    def face(self, number: int) -> Face:
        return self._by_number[number]

    def face_vertices(self, face: Face) -> np.ndarray:
        return self.vertices[list(face.vertex_ids)]

    def centroid(self, face: Face | None = None) -> Vec3:
        """面质心；``face=None`` 时返回整个体的顶点质心。"""
        pts = self.vertices if face is None else self.face_vertices(face)
        return pts.mean(axis=0)

    def normal(self, face: Face) -> Vec3:
        """面的单位外法向（Newell 公式；顶点环从外侧看逆时针）。"""
        pts = self.face_vertices(face)
        nxt = np.roll(pts, -1, axis=0)
        n = np.sum(np.cross(pts, nxt), axis=0)
        return unit(n)

    @property
    def edges(self) -> tuple[tuple[int, int], ...]:
        """去重后的边（顶点索引对，小索引在前）。"""
        seen: dict[tuple[int, int], None] = {}
        for f in self.faces:
            ids = f.vertex_ids
            for a, b in zip(ids, ids[1:] + ids[:1]):
                seen[(min(a, b), max(a, b))] = None
        return tuple(seen)

    def edge_faces(self, edge: tuple[int, int]) -> tuple[Face, ...]:
        """与某条边相邻的面。"""
        a, b = edge
        out = []
        for f in self.faces:
            ids = f.vertex_ids
            pairs = {(min(x, y), max(x, y)) for x, y in zip(ids, ids[1:] + ids[:1])}
            if (min(a, b), max(a, b)) in pairs:
                out.append(f)
        return tuple(out)

    # ---- 变换 ------------------------------------------------------------
    def transformed(self, rotation: np.ndarray | None = None,
                    translation: Sequence[float] | None = None) -> "Polyhedron":
        """返回刚体变换后的副本：先绕原点旋转，再平移。"""
        v = self.vertices
        if rotation is not None:
            v = v @ np.asarray(rotation, dtype=float).T
        if translation is not None:
            v = v + np.asarray(translation, dtype=float)
        return type(self)._copy_with(self, v)

    def _copy_with(self, vertices: np.ndarray) -> "Polyhedron":
        return Polyhedron(vertices, self.faces)

    # ---- 射线求交 --------------------------------------------------------
    def intersect_ray(self, origin: Sequence[float], direction: Sequence[float],
                      eps: float = 1e-9):
        """射线与凸体求交（半空间裁剪）。

        返回 ``(t_in, face_in, t_out, face_out)``；不相交返回 ``None``。
        起点在体内时 ``t_in < 0``、``face_in`` 为起点反向最近穿出的面。
        """
        o = np.asarray(origin, dtype=float)
        d = unit(direction)
        t_in, t_out = -np.inf, np.inf
        f_in = f_out = None
        for f in self.faces:
            n = self.normal(f)
            p0 = self.face_vertices(f)[0]
            denom = n @ d
            num = n @ (p0 - o)  # 到平面的有符号距离（沿 d 的分子）
            if abs(denom) < eps:
                if num < -eps:
                    return None  # 与该面平行且在外侧
                continue
            t = num / denom
            if denom < 0:  # 进入半空间
                if t > t_in:
                    t_in, f_in = t, f
            else:  # 离开半空间
                if t < t_out:
                    t_out, f_out = t, f
        if t_in > t_out or f_in is None or f_out is None:
            return None
        return t_in, f_in, t_out, f_out

    def contains(self, point: Sequence[float], eps: float = 1e-9) -> bool:
        p = np.asarray(point, dtype=float)
        return all(self.normal(f) @ (p - self.face_vertices(f)[0]) <= eps
                   for f in self.faces)


class HexPrism(Polyhedron):
    """六方柱冰晶。``a`` 为六边形边长（= 外接圆半径），``h`` 为柱高。

    片晶 ``h/a`` 小，柱晶 ``h/a`` 大。生成时 c 轴沿 +z、面 3 法向沿 +x，
    体心在原点；其他姿态用 :meth:`transformed` 得到。
    """

    def __init__(self, a: float = 1.0, h: float = 1.0):
        self.a = float(a)
        self.h = float(h)
        # 六边形顶点 k 位于方位角 -30° + 60°k，使面 3+i 的外法向落在 i·60°
        ang = np.deg2rad(-30.0 + 60.0 * np.arange(6))
        ring = np.stack([self.a * np.cos(ang), self.a * np.sin(ang)], axis=1)
        top = np.column_stack([ring, np.full(6, self.h / 2)])
        bottom = np.column_stack([ring, np.full(6, -self.h / 2)])
        vertices = np.vstack([top, bottom])  # 0–5 顶环，6–11 底环

        faces = [
            Face(BASAL_TOP, tuple(range(6))),
            Face(BASAL_BOTTOM, tuple(6 + k for k in range(5, -1, -1))),
        ]
        for i in range(6):
            j = (i + 1) % 6
            # 从外侧看逆时针：底-左、底-右、顶-右、顶-左
            faces.append(Face(3 + i, (6 + i, 6 + j, j, i)))
        super().__init__(vertices, faces)

    @classmethod
    def from_ratio(cls, ratio: float, a: float = 1.0) -> "HexPrism":
        """按高径比 ``h/a`` 构造。"""
        return cls(a=a, h=ratio * a)

    def _copy_with(self, vertices: np.ndarray) -> "HexPrism":
        # 手动搬运字段以绕开 __init__（它会按 a/h 重新生成顶点，覆盖掉变换后的 vertices）；
        # HexPrism.__init__ 新增构造参数时必须同步在这里搬运，否则变换后的实例会悄悄丢字段。
        obj = HexPrism.__new__(HexPrism)
        obj.a, obj.h = self.a, self.h
        Polyhedron.__init__(obj, vertices, self.faces)
        return obj
