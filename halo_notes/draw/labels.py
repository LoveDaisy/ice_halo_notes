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


def _text_semantic(poly, face, camera, visible, semantic=None):
    if semantic is not None:
        return semantic
    if visible is None:
        visible = face_visible(poly, face, camera)
    return "face_number" if visible else "face_number_hidden"


def draw_face_number_flat(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                          visible: bool | None = None, text: str | None = None,
                          semantic: str | None = None):
    """在面心水平正放面编号（可读性优先于随面变形）。"""
    x, y = face_label_anchor(poly, face, camera)
    kw = preset.text_kwargs(_text_semantic(poly, face, camera, visible, semantic))
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


def glyph_path(text: str, style) -> tuple:
    """``TextStyle`` 字体下的字形路径（以 (0,0) 为中心）与参考字高（数字「0」的高，同一预设下各
    编号等高："1" 比 "8" 窄但一样高）。贴面 / 贴边编号共用。"""
    if style.family:
        prop = FontProperties(weight=style.weight, style=style.style, family=style.family)
    else:
        prop = FontProperties(weight=style.weight, style=style.style)
    path = TextPath((0, 0), text, size=style.fontsize, prop=prop)
    bb = path.get_extents()
    centered = Affine2D().translate(-(bb.x0 + bb.x1) / 2, -(bb.y0 + bb.y1) / 2).transform_path(path)
    ref_h = TextPath((0, 0), "0", size=style.fontsize, prop=prop).get_extents().height
    return centered, ref_h


def draw_face_number_warped(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                            visible: bool | None = None, text: str | None = None,
                            semantic: str | None = None):
    """面编号贴面：``TextPath`` 字形经面内仿射铺到面上，随视角倾斜 / 缩放。"""
    style = preset.style(_text_semantic(poly, face, camera, visible, semantic))
    centered, ref_h = glyph_path(text if text is not None else str(face.number), style)
    tf = face_text_transform(ax, poly, face, camera, glyph_height=ref_h,
                             world_height=preset.geom.face_number_height)
    patch = PathPatch(centered, transform=tf,
                      facecolor=preset.palette[style.color], alpha=style.alpha, edgecolor="none",
                      linewidth=0)
    ax.add_patch(patch)
    return patch


def draw_face_number(ax, poly: Polyhedron, face: Face, camera: Camera, preset: Preset,
                     visible: bool | None = None, text: str | None = None,
                     semantic: str | None = None):
    """按 ``preset.geom.face_number_style`` 分派到贴面或正放；``visible`` 为 None 时自动判定；
    ``semantic`` 给定时直接用该文字语义（如幽灵晶体的 ``face_number_ghost``），不再按可见性选。"""
    fn = (draw_face_number_warped if preset.geom.face_number_style is FaceNumberStyle.WARPED
          else draw_face_number_flat)
    return fn(ax, poly, face, camera, preset, visible=visible, text=text, semantic=semantic)


# ---- 2D 截面的边编号 ---------------------------------------------------------

def edge_label_anchor(poly, edge: Face, preset: Preset) -> np.ndarray:
    """边编号的中心：边中点沿内法向退 ``geom.edge_number_inset``。"""
    return poly.midpoint(edge) - poly.normal(edge) * preset.geom.edge_number_inset


def draw_edge_number(ax, poly, edge: Face, preset: Preset, *, semantic: str = "face_number",
                     text: str | None = None):
    """截面边编号：字形按多边形自身的 ``frame``（编号朝向基）铺放——晶体转了字形跟着转，翻转 /
    镜像后字形镜像，与 3D 贴面文字同一套"贴纸"语义。字高 ``geom.edge_number_height``（世界单位）。
    颜色：``style_map.face_number_colors`` 里有该边号时按面号取色，否则用 ``semantic`` 的颜色；
    字号 / 透明度始终取 ``semantic``。"""
    style = preset.style(semantic)
    centered, ref_h = glyph_path(text if text is not None else str(edge.number), style)
    k = preset.geom.edge_number_height / ref_h
    F = poly.frame
    x, y = edge_label_anchor(poly, edge, preset)
    tf = Affine2D(np.array([[F[0, 0] * k, F[0, 1] * k, x],
                            [F[1, 0] * k, F[1, 1] * k, y],
                            [0.0, 0.0, 1.0]])) + ax.transData
    colors = preset.style_map.face_number_colors
    color_name = colors[edge.number] if colors and edge.number in colors else style.color
    patch = PathPatch(centered, transform=tf, facecolor=preset.palette[color_name],
                      alpha=style.alpha, edgecolor="none", linewidth=0)
    ax.add_patch(patch)
    return patch
