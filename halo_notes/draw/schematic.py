"""示意图元的几何：楔形介质 / 平板（两条界面线夹着的介质）与界面处"反射 + 折射"的分光树。

- :func:`two_face_medium`：由入射界面段与出射界面段围成的凸四边形（:class:`geometry2d.Polygon2D`），
  界面编号 ``ENTRY_FACE = 1`` / ``EXIT_FACE = 2``，另两条闭合边 3 / 4 只用于把区域封起来
  （渲染时画成参差 / 波浪边表示"无限延伸"，光线不应穿过它们）。楔形与平板只差两条界面是否平行。
- :func:`wedge_angle`：两条界面线的夹角（楔角 θ），由几何算出，不手填
- :func:`split_tree`：光线在介质两个界面处的分裂树——外反射、折射穿透、内反射三支，
  角度全部由 :func:`raypath.trace` / :func:`raypath.reflect` 按定律算出
- :func:`jagged_polyline` / :func:`wavy_polyline`：闭合边的装饰折线（确定性，无随机）
- :func:`concentric_projection`：同心圆（同心天球）作图里一次界面作用——入射 / 反射 / 折射三个光点沿界面法线共线
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .geometry import Face, unit
from .geometry2d import Polygon2D, perp2d
from .raypath import (N_ICE, EventKind, RayEvent, RayPath2D, SegmentKind, reflect, trace)

ENTRY_FACE, EXIT_FACE = 1, 2
CLOSURE_FACES = (3, 4)


def two_face_medium(entry: Sequence[Sequence[float]], exit: Sequence[Sequence[float]]) -> Polygon2D:
    """由入射界面段 ``entry = (A, B)`` 与出射界面段 ``exit = (C, D)`` 围成的凸四边形
    ``A → B → C → D``（自动整理成逆时针）。界面 1 = AB，界面 2 = CD，另两条闭合边编号 3 / 4。"""
    a, b = (np.asarray(p, dtype=float) for p in entry)
    c, d = (np.asarray(p, dtype=float) for p in exit)
    verts = np.array([a, b, c, d])
    area2 = sum(verts[i][0] * verts[(i + 1) % 4][1] - verts[(i + 1) % 4][0] * verts[i][1]
                for i in range(4))
    if abs(area2) < 1e-12:
        raise ValueError("degenerate medium: the four corners are collinear")
    if area2 < 0:  # 顺时针 → 反转顶点，同时保住"1 = AB, 2 = CD"的编号语义
        verts = np.array([b, a, d, c])
    faces = (Face(ENTRY_FACE, (0, 1)), Face(CLOSURE_FACES[0], (1, 2)),
             Face(EXIT_FACE, (2, 3)), Face(CLOSURE_FACES[1], (3, 0)))
    return Polygon2D(verts, faces)


def wedge_angle(medium: Polygon2D) -> float:
    """两条界面的夹角（度）：外法向夹角的补角——平行平板为 0。"""
    n1, n2 = medium.normal(medium.face(ENTRY_FACE)), medium.normal(medium.face(EXIT_FACE))
    return float(180.0 - np.degrees(np.arccos(np.clip(n1 @ n2, -1.0, 1.0))))


def wedge_apex(medium: Polygon2D) -> np.ndarray:
    """两条界面线的交点（楔角顶点）；平行时抛 ``ValueError``。"""
    (a, b), (c, d) = (medium.face_vertices(medium.face(k)) for k in (ENTRY_FACE, EXIT_FACE))
    u, v = b - a, d - c
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < 1e-12:
        raise ValueError("interfaces are parallel: no apex")
    w = c - a
    s = (w[0] * v[1] - w[1] * v[0]) / den
    return a + s * u


@dataclass(frozen=True)
class SplitTree:
    """介质两个界面处的分光树：三支光路都是可核验的 :class:`RayPath2D`。

    - ``transmitted``：折入界面 1、折出界面 2（面序列 ``[1, 2]``）
    - ``reflected_outside``：在界面 1 外反射（面序列 ``[1]``）
    - ``reflected_inside``：折入界面 1 后在界面 2 内反射，画到 ``inside_length`` 长为止
      （面序列 ``[1, 2]``：首事件与 ``transmitted`` 在同一点同一面，属于同一条光线的分支）
    """

    transmitted: RayPath2D
    reflected_outside: RayPath2D
    reflected_inside: RayPath2D

    def branches(self) -> tuple[RayPath2D, ...]:
        return self.transmitted, self.reflected_outside, self.reflected_inside


def split_tree(medium: Polygon2D, origin: Sequence[float], direction: Sequence[float], *,
               n_ice: float = N_ICE, tail: float = 1.6, head: float = 1.6,
               inside_length: float = 1.2) -> SplitTree:
    """从介质外 ``origin`` 沿 ``direction`` 射向界面 1，在两个界面处按反射 / 折射定律分裂。"""
    transmitted = trace(medium, origin, direction, ["refract", "refract"], n_ice=n_ice,
                        tail=tail, head=head)
    if [ev.face_number for ev in transmitted.events] != [ENTRY_FACE, EXIT_FACE]:
        raise ValueError("the ray does not go in through interface 1 and out through interface 2")
    reflected_outside = trace(medium, origin, direction, ["reflect"], n_ice=n_ice,
                              tail=tail, head=head)
    p_in, p_out = transmitted.points[1], transmitted.points[2]
    d_inside = unit(p_out - p_in)
    n2 = medium.normal(medium.face(EXIT_FACE))
    d_back = reflect(d_inside, -n2)
    reflected_inside = RayPath2D(
        np.array([p_in, p_out, p_out + d_back * inside_length]),
        (SegmentKind.INTERNAL, SegmentKind.INTERNAL),
        (RayEvent(0, ENTRY_FACE, EventKind.REFRACT_IN), RayEvent(1, EXIT_FACE, EventKind.REFLECT_INTERNAL)))
    return SplitTree(transmitted, reflected_outside, reflected_inside)


# ---- 闭合边的装饰折线 -----------------------------------------------------------

def jagged_polyline(p: Sequence[float], q: Sequence[float], *, n: int = 12, amplitude: float = 0.12,
                    seed: int = 0) -> np.ndarray:
    """``p → q`` 之间的参差折线（"介质向外无限延伸"的断口示意），确定性伪随机。"""
    p, q = np.asarray(p, dtype=float), np.asarray(q, dtype=float)
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, n + 1)
    off = rng.uniform(-1.0, 1.0, n + 1) * amplitude
    off[0] = off[-1] = 0.0
    d = q - p
    return p[None, :] + t[:, None] * d[None, :] + off[:, None] * perp2d(unit(d))[None, :]


def wavy_polyline(p: Sequence[float], q: Sequence[float], *, waves: float = 2.5,
                  amplitude: float = 0.15, samples: int = 80) -> np.ndarray:
    """``p → q`` 之间的正弦波浪线（平板两端的断口示意）。"""
    p, q = np.asarray(p, dtype=float), np.asarray(q, dtype=float)
    t = np.linspace(0.0, 1.0, samples)
    off = np.sin(2 * np.pi * waves * t) * amplitude
    d = q - p
    return p[None, :] + t[:, None] * d[None, :] + off[:, None] * perp2d(unit(d))[None, :]


# ---- 同心圆（同心天球）作图 --------------------------------------------------------

@dataclass(frozen=True)
class ConcentricProjection:
    """同心圆作图里一次界面作用的三个光点（向量长度 = 所在介质的折射率）与界面单位法向。

    - ``incident``：入射光点 $\mathbf S$（在半径 = 入射侧折射率的圆 / 球上）
    - ``reflected``：反射光点 $\mathbf S'$（同一个圆上，$\mathbf S$ 关于界面的镜像）
    - ``refracted``：折射光点 $\mathbf R$（在半径 ``radius_out`` 的圆 / 球上）
    - ``normal``：界面单位法向；三点都在过 $\mathbf S$、平行于它的直线上
    """

    incident: np.ndarray
    reflected: np.ndarray
    refracted: np.ndarray
    normal: np.ndarray


def concentric_projection(incident: Sequence[float], normal: Sequence[float], radius_out: float) -> ConcentricProjection:
    """同心圆（同心天球）作图 [TM2006 Fig. 4.5]：光点 = 光线方向 × 所在介质折射率（``incident`` 的长度就是入射侧折射率）。
    反射光点是入射光点关于界面的镜像；折射光点是入射光点**沿界面法线**平行投影到半径 ``radius_out`` 的圆 / 球上的交点——
    切向分量守恒就是 Snell 定律 $n_1\sin\theta_1=n_2\sin\theta_2$。直线与圆的两个交点取法向分量与入射同号的那个
    （光线穿过界面、法向分量不换向；另一根是反射侧的解）。二维、三维通用；全反射（切向分量 > ``radius_out``）抛 ``ValueError``。"""
    s = np.asarray(incident, dtype=float)
    n = unit(normal)
    s_n = float(s @ n)
    tangential = s - s_n * n
    t2 = float(tangential @ tangential)
    if t2 > radius_out ** 2:
        raise ValueError(f"total internal reflection: |tangential|={np.sqrt(t2):.6g} > radius_out={radius_out:g}")
    sign = 1.0 if s_n >= 0 else -1.0
    refracted = tangential + sign * np.sqrt(radius_out ** 2 - t2) * n
    return ConcentricProjection(incident=s, reflected=s - 2.0 * s_n * n, refracted=refracted, normal=n)


__all__ = ["CLOSURE_FACES", "ENTRY_FACE", "EXIT_FACE", "ConcentricProjection", "SplitTree", "concentric_projection",
           "jagged_polyline", "split_tree", "two_face_medium", "wavy_polyline", "wedge_angle", "wedge_apex"]
