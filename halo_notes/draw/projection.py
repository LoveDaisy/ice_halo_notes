"""相机、3D→2D 投影与凸多面体的可见性判定。

约定：``Camera`` 用「从原点指向观察者」的单位向量 ``view_dir`` 描述视角，
由方位角 / 仰角给出；投影默认透视（旧图 Mathematica 观感），可切换正交。
深度值越大离观察者越近。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Sequence

import numpy as np

from .geometry import Face, Polyhedron, unit

Projection = Literal["orthographic", "perspective"]


@dataclass
class Camera:
    """视角描述。

    - ``azimuth`` / ``elevation``：观察者相对原点的方位角（xy 平面内从 +x 起，
      逆时针）与仰角，角度制
    - ``projection``：``"perspective"``（默认）或 ``"orthographic"``
    - ``distance``：透视投影时相机到原点的距离（晶体单位，a=1）；正交投影忽略
    - ``up``：世界系里的"上"方向，决定画面竖直方向
    - ``roll``：绕视线的画面旋转（度，逆时针为正）
    """

    azimuth: float = 30.0
    elevation: float = 20.0
    projection: Projection = "perspective"
    distance: float = 8.0
    up: Sequence[float] = (0.0, 0.0, 1.0)
    roll: float = 0.0
    _basis: np.ndarray = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        az, el = np.deg2rad(self.azimuth), np.deg2rad(self.elevation)
        view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        up = unit(self.up)
        if abs(view @ up) > 1 - 1e-9:
            raise ValueError("view direction is parallel to `up`")
        right = unit(np.cross(up, view))  # 画面 x 轴
        cam_up = np.cross(view, right)     # 画面 y 轴
        if self.roll:
            r = np.deg2rad(self.roll)
            right, cam_up = (np.cos(r) * right + np.sin(r) * cam_up,
                             -np.sin(r) * right + np.cos(r) * cam_up)
        self._basis = np.stack([right, cam_up, view])

    @classmethod
    def from_direction(cls, direction: Sequence[float], **kwargs) -> "Camera":
        """由「指向观察者」的方向向量构造。"""
        d = unit(direction)
        el = np.rad2deg(np.arcsin(np.clip(d[2], -1, 1)))
        az = np.rad2deg(np.arctan2(d[1], d[0]))
        return cls(azimuth=az, elevation=el, **kwargs)

    # ---- 基向量 ----------------------------------------------------------
    @property
    def right(self) -> np.ndarray:
        return self._basis[0]

    @property
    def cam_up(self) -> np.ndarray:
        return self._basis[1]

    @property
    def view_dir(self) -> np.ndarray:
        """从原点指向观察者的单位向量。"""
        return self._basis[2]

    @property
    def position(self) -> np.ndarray:
        """透视相机的位置（正交投影下仅用于深度参考）。"""
        return self.view_dir * self.distance

    def to_world(self, right: float, up: float, toward: float) -> np.ndarray:
        """用画面坐标（右 / 上 / 朝观察者）合成一个世界向量，便于按画面观感摆姿态。"""
        return right * self.right + up * self.cam_up + toward * self.view_dir

    # ---- 投影 ------------------------------------------------------------
    def project(self, points: Sequence[float] | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """把 (N,3) 或 (3,) 的点投到画面。返回 ``(xy (N,2), depth (N,))``。

        透视投影把像平面放在原点处，使原点附近的尺度与正交投影一致。
        """
        p = np.asarray(points, dtype=float).reshape(-1, 3)
        cam = p @ self._basis.T  # 列：right, up, view
        depth = cam[:, 2]
        if self.projection == "orthographic":
            xy = cam[:, :2]
        elif self.projection == "perspective":
            z = self.distance - depth  # 相机到点的沿视线距离
            if np.any(z <= 0):
                raise ValueError("point behind the perspective camera")
            xy = cam[:, :2] * (self.distance / z)[:, None]
        else:
            raise ValueError(f"unknown projection {self.projection!r}")
        return xy, depth

    def project_xy(self, points) -> np.ndarray:
        return self.project(points)[0]

    def view_vector(self, points: Sequence[float] | np.ndarray) -> np.ndarray:
        """各点处「指向观察者」的单位向量（正交：常量；透视：指向相机位置）。"""
        p = np.asarray(points, dtype=float).reshape(-1, 3)
        if self.projection == "orthographic":
            return np.broadcast_to(self.view_dir, p.shape).copy()
        v = self.position - p
        return v / np.linalg.norm(v, axis=1, keepdims=True)


# ---- 可见性 ----------------------------------------------------------------

VISIBILITY_EPS = 1e-9


def face_visible(poly: Polyhedron, face: Face, camera: Camera) -> bool:
    """外法向朝向观察者即可见（凸体无自遮挡，无需再查遮挡）；
    恰好侧对视线（掠射）的面按不可见处理。"""
    n = poly.normal(face)
    v = camera.view_vector(poly.centroid(face))[0]
    return bool(n @ v > VISIBILITY_EPS)


def visible_faces(poly: Polyhedron, camera: Camera) -> list[Face]:
    return [f for f in poly.faces if face_visible(poly, f, camera)]


def hidden_faces(poly: Polyhedron, camera: Camera) -> list[Face]:
    return [f for f in poly.faces if not face_visible(poly, f, camera)]


def edge_visible(poly: Polyhedron, edge: tuple[int, int], camera: Camera) -> bool:
    """边可见 ⇔ 至少一个相邻面可见。"""
    return any(face_visible(poly, f, camera) for f in poly.edge_faces(edge))


def face_in_plane_basis(poly: Polyhedron, face: Face) -> tuple[np.ndarray, np.ndarray]:
    """面内一对正交单位向量 ``(u, v)``，取自面自身的顶点环，与相机无关。

    ``u`` 沿顶点环的首条边（``Face`` 约定从外侧看逆时针，所以这是从外侧看的
    "向右"），``v = n × u`` 是从外侧看的"向上"。贴面文字用这组基就像是写在晶体
    表面上：晶体转动文字跟着转，从背面透过晶体看到时呈镜像——与旧图（0.2 里
    背面的 7 / 2 / 6）一致。``HexPrism`` 的柱面首条边是底边，故文字"上"即 c 轴。

    注意：「首条边=地面边」只是 ``HexPrism`` 当前顶点排列的事实，不是
    ``Face``/``Polyhedron`` 的通用契约（后者只保证「外侧看逆时针」）。新增
    非棱柱几何或顶点排列不同的棱柱时，需要重新核实这条假设，否则贴面文字
    可能静默转向错误方向（当前 test_labels.py 只覆盖 ``HexPrism``）。
    """
    pts = poly.face_vertices(face)
    u = unit(pts[1] - pts[0])
    v = np.cross(poly.normal(face), u)
    return u, v


def face_jacobian(poly: Polyhedron, face: Face, camera: Camera, eps: float = 1e-3) -> np.ndarray:
    """面心处「面内位移 → 画面位移」的 2×2 雅可比（列对应 :func:`face_in_plane_basis` 的 u、v）。

    正交投影下正对相机且 ``u`` 水平的面给出单位阵；侧对时列向量被压缩（透视
    变形），从背面看到时行列式为负（镜像），透视投影下还带一层近大远小的整体
    缩放。用于把贴面文字按仿射近似铺到面上。
    """
    c = poly.centroid(face)
    u, v = face_in_plane_basis(poly, face)
    base = camera.project_xy(c)[0]
    du = (camera.project_xy(c + eps * u)[0] - base) / eps
    dv = (camera.project_xy(c + eps * v)[0] - base) / eps
    return np.stack([du, dv], axis=1)


def depth_sorted_faces(poly: Polyhedron, camera: Camera) -> list[Face]:
    """按面质心深度从远到近排序（painter's algorithm 的绘制顺序）。"""
    depths = {f.number: camera.project(poly.centroid(f))[1][0] for f in poly.faces}
    return sorted(poly.faces, key=lambda f: depths[f.number])


def point_on_visible_face(poly: Polyhedron, point: Sequence[float], camera: Camera,
                          eps: float = 1e-6) -> bool | None:
    """判断落在体表面上的点位于可见面还是不可见面。

    返回 ``True`` / ``False``；点不在任何面上时返回 ``None``。
    """
    p = np.asarray(point, dtype=float)
    on = [f for f in poly.faces
          if abs(poly.normal(f) @ (p - poly.face_vertices(f)[0])) < eps]
    if not on:
        return None
    return any(face_visible(poly, f, camera) for f in on)
