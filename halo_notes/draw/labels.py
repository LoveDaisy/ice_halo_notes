"""面编号文字：贴在面投影多边形的质心、水平正放（可读性优先于随面变形）。"""

from __future__ import annotations

import numpy as np

from .geometry import Face, Polyhedron
from .projection import Camera, face_visible
from .style import Preset


def face_label_anchor(poly: Polyhedron, face: Face, camera: Camera) -> np.ndarray:
    """面质心的投影点 (2,)。"""
    return camera.project_xy(poly.centroid(face))[0]


def point_in_polygon(pt, polygon: np.ndarray) -> bool:
    """射线法判断 2D 点是否在多边形内。"""
    x, y = pt
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def draw_face_number(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                     visible: bool | None = None, text: str | None = None):
    """在面心画面编号；``visible`` 为 None 时自动判定，决定用哪套文字样式。"""
    if visible is None:
        visible = face_visible(poly, face, camera)
    x, y = face_label_anchor(poly, face, camera)
    kw = preset.text_kwargs("face_number" if visible else "face_number_hidden")
    return ax.text(x, y, text if text is not None else str(face.number),
                   ha="center", va="center", **kw)
