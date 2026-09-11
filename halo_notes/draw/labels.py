"""面编号文字：默认像写在晶体表面上一样贴面、随视角仿射变形（旧图观感），可选在面心水平正放。

贴面用的是仿射近似：取面心处「面内位移 → 画面位移」的雅可比（面内基取自面的
顶点环，见 :func:`projection.face_in_plane_basis`），把整段字形当成一个小平面片
一起变形。文字尺寸远小于面时与真投影无可见差别；文字接近面的尺寸时笔画本身
该有的非线性透视弯曲会被忽略。背面的面透过晶体看到时文字呈镜像，与旧图一致。
"""

from __future__ import annotations

import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

from .geometry import Face, Polyhedron
from .projection import Camera, face_jacobian, face_visible
from .style import FaceNumberStyle, Preset


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


def _text_semantic(poly, face, camera, visible):
    if visible is None:
        visible = face_visible(poly, face, camera)
    return "face_number" if visible else "face_number_hidden"


def draw_face_number_flat(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                          visible: bool | None = None, text: str | None = None):
    """在面心水平正放面编号（可读性优先于随面变形）。"""
    x, y = face_label_anchor(poly, face, camera)
    kw = preset.text_kwargs(_text_semantic(poly, face, camera, visible))
    return ax.text(x, y, text if text is not None else str(face.number),
                   ha="center", va="center", **kw)


def face_text_transform(ax, poly: Polyhedron, face: Face, camera: Camera, *,
                        glyph_height: float, world_height: float):
    """把「以 (0,0) 为中心」的字形坐标贴到面上的 matplotlib 变换（贴纸语义）。

    字形单位 → 缩放到世界单位（字高 = ``world_height``，与晶体同单位）→ 面内仿射
    （:func:`face_jacobian`，世界 → 数据坐标）→ 平移到面心 → ``transData``。
    字高随晶体缩放、随透视近大远小，不按印刷点计。
    """
    J = face_jacobian(poly, face, camera)
    x, y = face_label_anchor(poly, face, camera)
    k = world_height / glyph_height
    return (Affine2D(np.array([[J[0, 0] * k, J[0, 1] * k, x],
                               [J[1, 0] * k, J[1, 1] * k, y],
                               [0.0, 0.0, 1.0]]))
            + ax.transData)


def draw_face_number_warped(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                            visible: bool | None = None, text: str | None = None):
    """面编号贴面：``TextPath`` 字形经面内仿射铺到面上，随视角倾斜 / 缩放。"""
    style = preset.style(_text_semantic(poly, face, camera, visible))
    if style.family:
        prop = FontProperties(weight=style.weight, style=style.style, family=style.family)
    else:
        prop = FontProperties(weight=style.weight, style=style.style)
    path = TextPath((0, 0), text if text is not None else str(face.number),
                    size=style.fontsize, prop=prop)
    bb = path.get_extents()
    centered = Affine2D().translate(-(bb.x0 + bb.x1) / 2, -(bb.y0 + bb.y1) / 2).transform_path(path)
    # 以数字「0」的字高为基准，同一预设下各编号等高（"1" 比 "8" 窄但一样高）
    ref_h = TextPath((0, 0), "0", size=style.fontsize, prop=prop).get_extents().height
    tf = face_text_transform(ax, poly, face, camera, glyph_height=ref_h,
                             world_height=preset.geom.face_number_height)
    patch = PathPatch(centered, transform=tf,
                      facecolor=preset.palette[style.color], alpha=style.alpha, edgecolor="none",
                      linewidth=0)
    ax.add_patch(patch)
    return patch


def draw_face_number(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                     visible: bool | None = None, text: str | None = None):
    """按 ``preset.geom.face_number_style`` 分派到贴面或正放；``visible`` 为 None 时自动判定。"""
    fn = (draw_face_number_warped if preset.geom.face_number_style is FaceNumberStyle.WARPED
          else draw_face_number_flat)
    return fn(ax, poly, face, camera, preset, visible=visible, text=text)
