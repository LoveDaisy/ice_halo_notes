"""2D 截面几何：凸多边形（编号边 + 外法向）与六方柱的正六边形截面。

- :class:`Polygon2D`：凸多边形，继承 :class:`geometry.Polyhedron`（``DIM = 2``）——半空间裁剪
  求交、包含判定、面距离、镜像、刚体变换全部共用 3D 实现；边的外法向与"点在边内"判定按 2D 另写。
  多边形的"面"就是它的边（``faces`` / ``face()`` 等方法名沿用 3D 协议，光路追迹、展开、
  白盒复核才能不分维数直接跑）。另带一个 2×2 的 ``frame``：编号字形的朝向基——旋转 / 翻转 /
  镜像时跟着变换（旋转时字形转动、翻转时字形镜像），把"编号随晶体一起动"的语义锚在多边形自身。
- :class:`CrossSection`：六方柱沿 c 轴的截面。**边的编号不手写**，从 :class:`geometry.HexPrism`
  的侧面 3–8 抽出：每条边取该侧面的顶环两顶点，顶点顺序按"2D 外法向 == 3D 外法向的 xy 分量"
  定；视向是从面 1（+c）一侧沿 −c 看，即 x 向右、y 向上，于是 3 右、4 右上、5 左上、6 左、
  7 左下、8 右下（逆时针）——与旧图 1.2 一致。
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from .geometry import BASAL_TOP, PRISM_FACES, Face, HexPrism, Polyhedron, unit

Vec2 = np.ndarray


def rotation2d(angle_deg: float) -> np.ndarray:
    """平面旋转矩阵（逆时针为正，角度制）。"""
    t = np.deg2rad(angle_deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s], [s, c]])


def reflection2d(direction: Sequence[float]) -> np.ndarray:
    """关于过原点、方向为 ``direction`` 的直线的镜像矩阵（行列式 −1）。"""
    d = unit(np.asarray(direction, dtype=float))
    return 2.0 * np.outer(d, d) - np.eye(2)


def perp2d(v: Sequence[float]) -> np.ndarray:
    """把 2D 向量逆时针转 90°。"""
    v = np.asarray(v, dtype=float)
    return np.array([-v[1], v[0]])


class Polygon2D(Polyhedron):
    """凸多边形：顶点 (N,2) + 编号边。每条边是一个两顶点的 :class:`Face`，顶点顺序 ``(i, j)``
    使多边形逆时针（外法向 = 边方向顺时针转 90°），与 3D「从外侧看逆时针」约定同构。

    ``frame``：编号字形的朝向基（2×2，列 = 字形的"右"与"上"在多边形坐标系里的方向），
    初始为单位阵；``transformed`` / ``mirrored`` 同步变换它。
    """

    DIM = 2

    def __init__(self, vertices: np.ndarray, faces: Iterable[Face],
                 frame: np.ndarray | None = None):
        super().__init__(vertices, faces)
        for f in self.faces:
            if len(f.vertex_ids) != 2:
                raise ValueError(f"edge {f.number} must have exactly two vertices")
        self.frame = np.eye(2) if frame is None else np.asarray(frame, dtype=float).reshape(2, 2)

    # ---- 2D 专属查询 ------------------------------------------------------
    def normal(self, face: Face) -> Vec2:
        """边的单位外法向：边方向顺时针转 90°（多边形逆时针）。"""
        cached = self._normals.get(face.number)
        if cached is not None:
            return cached
        a, b = self.face_vertices(face)
        n = -perp2d(unit(b - a))
        self._normals[face.number] = n
        return n

    def face_margin(self, face: Face, point: Sequence[float]) -> float:
        """点到边两端点的最小有符号距离（沿边方向量）：正 = 在边段内部，负 = 在延长线上。
        不检查点是否在边所在直线上（配合 :meth:`face_distance`）。"""
        q = np.asarray(point, dtype=float)
        a, b = self.face_vertices(face)
        t = unit(b - a)
        s = float((q - a) @ t)
        return min(s, float(np.linalg.norm(b - a)) - s)

    def midpoint(self, face: Face) -> Vec2:
        return self.face_vertices(face).mean(axis=0)

    def vertex_between(self, number_a: int, number_b: int) -> Vec2:
        """两条相邻编号边的公共顶点。"""
        ids = set(self.face(number_a).vertex_ids) & set(self.face(number_b).vertex_ids)
        if len(ids) != 1:
            raise ValueError(f"edges {number_a} and {number_b} are not adjacent")
        return self.vertices[ids.pop()]

    # ---- 变换（同步 frame） -------------------------------------------------
    def transformed(self, rotation: np.ndarray | None = None,
                    translation: Sequence[float] | None = None) -> "Polygon2D":
        """仿射变换后的副本：``rotation`` 可以是旋转，也可以是镜像（行列式 −1，如 :func:`symmetry.flip`）
        ——镜像会把逆时针顶点环翻成顺时针，各边的顶点顺序同步反转以保住外法向；``frame`` 同步变换。"""
        v = self.vertices
        faces = self.faces
        if rotation is not None:
            r = np.asarray(rotation, dtype=float)
            v = v @ r.T
            if np.linalg.det(r) < 0:
                faces = tuple(Face(f.number, tuple(reversed(f.vertex_ids))) for f in self.faces)
        if translation is not None:
            v = v + np.asarray(translation, dtype=float)
        out = self._copy_with(v, faces)
        if rotation is not None:
            out.frame = r @ self.frame
        return out

    def rotated(self, angle_deg: float) -> "Polygon2D":
        """绕自身中心逆时针转 ``angle_deg``（编号字形随之转动）。"""
        c = self.centroid()
        r = rotation2d(angle_deg)
        return self.transformed(r, c - r @ c)

    def mirrored(self, face: Face) -> "Polygon2D":
        """关于边 ``face`` 所在直线镜像（光路展开的幽灵截面）；编号字形同步镜像。"""
        out = super().mirrored(face)
        a, b = self.face_vertices(face)
        out.frame = reflection2d(b - a) @ self.frame
        return out

    def _copy_with(self, vertices: np.ndarray,
                   faces: Iterable[Face] | None = None) -> "Polygon2D":
        return Polygon2D(vertices, self.faces if faces is None else faces, self.frame)


class CrossSection(Polygon2D):
    """六方柱沿 c 轴的正六边形截面，边编号 3–8 由 :class:`HexPrism` 的侧面推导。

    ``a`` 为边长（= 外接圆半径）；也可直接给一个 ``prism``（取它当前姿态下顶环的 xy 投影——
    只对 c 轴仍沿 z 的棱柱有意义）。
    """

    def __init__(self, a: float = 1.0, prism: HexPrism | None = None):
        prism = HexPrism(a, 1.0) if prism is None else prism
        self.a = float(prism.a)
        top_ids = set(prism.face(BASAL_TOP).vertex_ids)
        # 顶环顶点在 prism.vertices 里的下标就是 0..5；截面顶点按该下标原样搬运（面里的顶点 id 不用重映射）
        vertices = prism.vertices[sorted(top_ids), :2]
        index = {vid: k for k, vid in enumerate(sorted(top_ids))}
        edges = []
        for number in PRISM_FACES:
            face = prism.face(number)
            i, j = [index[v] for v in face.vertex_ids if v in top_ids]
            n3 = prism.normal(face)[:2]
            # 顶点顺序由"2D 外法向 == 3D 外法向的 xy 分量"裁定，不假设 HexPrism 顶环的排列方向
            if (-perp2d(vertices[j] - vertices[i])) @ n3 < 0:
                i, j = j, i
            edges.append(Face(number, (i, j)))
        super().__init__(vertices, edges)

    def _copy_with(self, vertices: np.ndarray,
                   faces: Iterable[Face] | None = None) -> "CrossSection":
        obj = CrossSection.__new__(CrossSection)
        obj.a = self.a
        Polygon2D.__init__(obj, vertices, self.faces if faces is None else faces, self.frame)
        return obj
