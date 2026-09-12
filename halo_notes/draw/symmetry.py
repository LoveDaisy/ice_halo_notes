"""截面的对称操作：绕中心旋转 ``k·60°``、关于过面心 / 过顶点的轴翻转。

两者都返回新的 :class:`geometry2d.Polygon2D`，**边编号不变、几何位置变**——旋转后原来编号 k 的边
落到编号 k+1 的位置（1.3 旧图"编号随晶体转"）、翻转后被轴穿过的面 / 顶点不动，其余成对互换；
编号字形随 ``frame`` 转动 / 镜像，由 :func:`labels.draw_edge_number` 自动体现。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .geometry import unit
from .geometry2d import Polygon2D, reflection2d

AxisKind = Literal["face", "vertex"]


@dataclass(frozen=True)
class FlipAxis:
    """翻转轴：``face(k)`` 过边 k 的中点与中心（$F^f_k$）；``vertex(k, k+1)`` 过边 k、k+1 的公共
    顶点与中心（$F^d_{k,k+1}$）。"""

    kind: AxisKind
    numbers: tuple[int, ...]

    @classmethod
    def face(cls, k: int) -> "FlipAxis":
        return cls("face", (int(k),))

    @classmethod
    def vertex(cls, k: int, j: int) -> "FlipAxis":
        return cls("vertex", (int(k), int(j)))

    @property
    def label(self) -> str:
        """LaTeX 标题：``$F^f_k$`` / ``$F^d_{k,j}$``。"""
        if self.kind == "face":
            return f"$F^f_{{{self.numbers[0]}}}$"
        return f"$F^d_{{{self.numbers[0]},{self.numbers[1]}}}$"

    def direction(self, section: Polygon2D) -> np.ndarray:
        """轴的单位方向（从中心指向面心 / 顶点）。"""
        c = section.centroid()
        if self.kind == "face":
            return unit(section.midpoint(section.face(self.numbers[0])) - c)
        return unit(section.vertex_between(*self.numbers) - c)


def rotate(section: Polygon2D, k: int) -> Polygon2D:
    """绕中心逆时针转 ``k·60°``（$R^c_k$）。"""
    return section.rotated(60.0 * k)


def flip(section: Polygon2D, axis: FlipAxis) -> Polygon2D:
    """关于过中心的轴 ``axis`` 镜像（行列式 −1：编号字形随之镜像）。"""
    c = section.centroid()
    m = reflection2d(axis.direction(section))
    return section.transformed(m, c - m @ c)


def face_permutation(section: Polygon2D, moved: Polygon2D) -> dict[int, int]:
    """对称操作前后边号的对应：``{原位置上的边号: 现在落在该位置的边号}``——用原截面每条边的外法向
    在 ``moved`` 里找法向相同的边。两者中心须重合。"""
    out: dict[int, int] = {}
    for f in section.faces:
        n = section.normal(f)
        match = [g.number for g in moved.faces if np.allclose(moved.normal(g), n, atol=1e-9)]
        if len(match) != 1:
            raise ValueError(f"no unique edge of the moved polygon faces the way edge {f.number} did")
        out[f.number] = match[0]
    return out


__all__ = ["FlipAxis", "face_permutation", "flip", "rotate"]
