"""场景组装：把几何、投影、光路、文字与风格预设拼成 matplotlib 图。

画图脚本只需：建 figure → `render_crystal(ax, crystal, raypaths, camera=..., preset=...)`
→（可选）`draw_axes` → `finish(ax)`。``camera`` 没有隐式默认值，必须显式传入。
"""

from __future__ import annotations

from typing import Iterable, Literal, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

from .geometry import Polyhedron, unit
from .labels import draw_face_number
from .projection import (Camera, depth_sorted_faces, edge_visible, face_visible,
                         point_on_visible_face)
from .raypath import Cone, RayPath, SegmentKind
from .style import PRESETS, HiddenEdgeMode, Preset

# 绘制层级：从后往前。光线锥体的遮挡衬底压在光线 / 晶体线之上、锥体轮廓之下
Z_HIDDEN_FILL, Z_HIDDEN_EDGE, Z_HIDDEN_LABEL, Z_INTERNAL = 1, 2, 3, 4
Z_VISIBLE_FILL, Z_VISIBLE_EDGE, Z_VISIBLE_LABEL, Z_EXTERNAL = 5, 6, 7, 8
Z_CONE_FILL, Z_CONE_OUTLINE = 9, 10
Z_TEXT = 11

ConeFillMode = Literal["wire", "solid", "occlude"]


def new_figure(width_px: int, height_px: int, dpi: int = 200, preset: Preset | None = None):
    """按目标像素尺寸建 figure + 单个铺满的 axes。"""
    # +0.5 px 抵消 figsize×dpi 的浮点截断（否则 1956/200×200 会落成 1955）
    fig = plt.figure(figsize=((width_px + 0.5) / dpi, (height_px + 0.5) / dpi), dpi=dpi)
    if preset is not None:
        fig.patch.set_facecolor(preset.palette["background"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    return fig, ax


def finish(ax, xlim: Sequence[float], ylim: Sequence[float]) -> None:
    """等比例、无坐标框、固定视野。"""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_axis_off()


# ---- 晶体 --------------------------------------------------------------------

def render_crystal(ax, crystal: Polyhedron, raypaths: Iterable[RayPath] | None = None, *,
                   camera: Camera, preset: Preset = PRESETS["default"],
                   face_numbers: bool | Iterable[int] = False,
                   highlight: Iterable[int] = (), ghost: bool = False) -> None:
    """画一个晶体（面填充 + 可见/不可见边 + 面编号）及其光路。

    ``highlight``：要高亮的面号，按该面在**这个**晶体上的可见性选
    ``face_highlight`` / ``face_highlight_hidden``（不查其他晶体的遮挡）。
    ``ghost``：按展开幽灵晶体画——不填充（高亮面除外）、全部边用 ``edge_ghost``
    样式画出（透明线框，不受 ``hidden_edges`` 开关影响）。两个参数正交。
    """
    raypaths = list(raypaths or [])
    sm, geom = preset.style_map, preset.geom
    highlight = set(highlight)
    visible = {f.number: face_visible(crystal, f, camera) for f in crystal.faces}

    # 面填充：painter 顺序，远的先画。优先级：高亮 > 幽灵（不填） > 预设默认填充
    for f in depth_sorted_faces(crystal, camera):
        vis = visible[f.number]
        if f.number in highlight:
            fill = preset.fill_kwargs(sm.face_highlight if vis else sm.face_highlight_hidden)
        elif ghost:
            fill = None
        else:
            fill = preset.fill_kwargs(sm.face_fill if vis else sm.face_fill_hidden)
        if fill is None:
            continue
        xy = camera.project_xy(crystal.face_vertices(f))
        ax.add_patch(Polygon(xy, closed=True, zorder=Z_VISIBLE_FILL if vis else Z_HIDDEN_FILL,
                             **fill))

    # 边
    for e in crystal.edges:
        vis = edge_visible(crystal, e, camera)
        if ghost:
            semantic = "edge_ghost"
        elif vis:
            semantic = "edge_visible"
        elif geom.hidden_edges is HiddenEdgeMode.HIDE:
            continue
        else:
            semantic = "edge_hidden"
        xy = camera.project_xy(crystal.vertices[list(e)])
        ax.plot(xy[:, 0], xy[:, 1], zorder=Z_VISIBLE_EDGE if vis else Z_HIDDEN_EDGE,
                solid_capstyle="round", **preset.line_kwargs(semantic))

    # 面编号
    if face_numbers:
        wanted = {f.number for f in crystal.faces} if face_numbers is True else set(face_numbers)
        for f in crystal.faces:
            if f.number not in wanted:
                continue
            if not visible[f.number] and not geom.label_hidden_faces:
                continue
            t = draw_face_number(ax, crystal, f, camera, preset, visible=visible[f.number])
            t.set_zorder(Z_VISIBLE_LABEL if visible[f.number] else Z_HIDDEN_LABEL)

    for path in raypaths:
        draw_raypath(ax, path, crystal, camera=camera, preset=preset)


# ---- 光路 --------------------------------------------------------------------

def _occluded_mask(points: np.ndarray, occluder: Polyhedron | None, camera: Camera) -> np.ndarray:
    """各点是否被遮挡体挡住：从该点朝观察者发射线，前方仍有遮挡体材料
    （点在体内，或射线稍后穿入）即被挡。"""
    if occluder is None:
        return np.zeros(len(points), dtype=bool)
    vv = camera.view_vector(points)
    out = np.zeros(len(points), dtype=bool)
    for i, (p, v) in enumerate(zip(points, vv)):
        hit = occluder.intersect_ray(p, v)
        out[i] = hit is not None and hit[2] > 1e-7
    return out


def _plot_runs(ax, pts3d: np.ndarray, mask: np.ndarray, camera: Camera,
               kw_true: dict, kw_false: dict, z_true: int, z_false: int) -> None:
    """按掩码把折线切成连续段，两种样式分别画。"""
    xy = camera.project_xy(pts3d)
    n = len(pts3d)
    i = 0
    while i < n - 1:
        j = i
        while j < n - 1 and mask[j + 1] == mask[i]:
            j += 1
        seg = xy[i:j + 1] if j > i else xy[i:i + 2]
        kw, z = (kw_true, z_true) if mask[i] else (kw_false, z_false)
        ax.plot(seg[:, 0], seg[:, 1], zorder=z, solid_capstyle="round", **kw)
        i = max(j, i + 1)


def draw_segment(ax, p0, p1, *, camera: Camera, preset: Preset, semantic: str,
                 occluded_semantic: str, occluder: Polyhedron | None, z_visible: int,
                 z_hidden: int, samples: int = 64) -> None:
    """画一条 3D 线段，被 ``occluder`` 挡住的部分换 ``occluded_semantic`` 样式。"""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ts = np.linspace(0, 1, samples)
    pts = p0[None, :] + ts[:, None] * (p1 - p0)[None, :]
    mask = _occluded_mask(pts, occluder, camera)
    _plot_runs(ax, pts, mask, camera, preset.line_kwargs(occluded_semantic),
               preset.line_kwargs(semantic), z_hidden, z_visible)


def draw_cone(ax, cone: Cone, *, camera: Camera, line_kwargs: dict, z: int,
              fill_mode: ConeFillMode = "wire", fill_kwargs: dict | None = None,
              z_fill: int | None = None) -> None:
    """画锥体箭头，三种填充语义：

    - ``"wire"``：只画线框（轮廓母线 + 纬线弧）
    - ``"solid"``：单色实心三角（取 ``line_kwargs`` 的颜色），不画纬线——坐标轴箭头
    - ``"occlude"``：先在 ``z_fill`` 用 ``fill_kwargs``（背景色）铺实心衬底遮住穿过锥体
      内部的线，再在 ``z`` 叠线框——光线箭头
    """
    if fill_mode == "solid":
        ax.add_patch(Polygon(cone.outline(camera), closed=True, zorder=z,
                             facecolor=line_kwargs["color"], edgecolor=line_kwargs["color"],
                             alpha=line_kwargs.get("alpha", 1.0)))
        return
    if fill_mode == "occlude":
        if fill_kwargs is None or z_fill is None:
            raise ValueError("fill_mode='occlude' requires fill_kwargs and z_fill")
        ax.add_patch(Polygon(cone.outline(camera), closed=True, zorder=z_fill, **fill_kwargs))
    elif fill_mode != "wire":
        raise ValueError(f"unknown fill_mode {fill_mode!r}")
    for piece in cone.wireframe(camera):
        ax.plot(piece[:, 0], piece[:, 1], zorder=z, solid_capstyle="round", **line_kwargs)


def draw_raypath(ax, path: RayPath, crystal: Polyhedron | None = None, *,
                 camera: Camera, preset: Preset) -> None:
    """画光路：入射 / 出射段（含遮挡处理与锥体箭头）、内部段、事件点与端点。"""
    sm, geom = preset.style_map, preset.geom
    for p0, p1, kind in path.segments():
        if kind is SegmentKind.INTERNAL:
            xy = camera.project_xy(np.stack([p0, p1]))
            ax.plot(xy[:, 0], xy[:, 1], zorder=Z_INTERNAL, solid_capstyle="round",
                    **preset.line_kwargs("ray_internal"))
            continue
        semantic = "ray_incident" if kind is SegmentKind.INCIDENT else "ray_exit"
        draw_segment(ax, p0, p1, camera=camera, preset=preset, semantic=semantic,
                     occluded_semantic="ray_occluded", occluder=crystal,
                     z_visible=Z_EXTERNAL, z_hidden=Z_INTERNAL)
        # 锥体箭头：顶点在上游、底面朝传播方向
        d = unit(p1 - p0)
        at = geom.incident_cone_at if kind is SegmentKind.INCIDENT else geom.exit_cone_at
        apex = p0 + (p1 - p0) * at
        cone = Cone.along(apex, d, length=geom.cone_length, radius=geom.cone_radius,
                          rings=geom.cone_rings, samples=geom.cone_samples)
        draw_cone(ax, cone, camera=camera, line_kwargs=preset.line_kwargs(semantic),
                  z=Z_CONE_OUTLINE, fill_mode="occlude", z_fill=Z_CONE_FILL,
                  fill_kwargs=dict(facecolor=preset.palette["background"], edgecolor="none"))

    # 小圆点：首尾 + 事件点
    dots: list[tuple[np.ndarray, bool]] = []
    if geom.end_markers:
        dots += [(path.start, True), (path.end, True)]
    if geom.event_markers and crystal is not None:
        for ev in path.events:
            p = path.points[ev.point_index]
            on_vis = point_on_visible_face(crystal, p, camera)
            dots.append((p, on_vis is not False))
    for p, vis in dots:
        x, y = camera.project_xy(p)[0]
        ax.plot([x], [y], zorder=Z_EXTERNAL if vis else Z_INTERNAL,
                **preset.marker_kwargs("ray_marker" if vis else "ray_marker_hidden"))


# ---- 文字注释 ----------------------------------------------------------------

def annotate(ax, text: str, anchor3d: Sequence[float], offset2d: Sequence[float] = (0.0, 0.0), *,
             camera: Camera, preset: Preset, ha: str = "left", va: str = "center",
             arrow: bool = False):
    """在 3D 锚点的投影处加 2D 偏移（与投影同量纲，即晶体单位）写一段注释文字，
    样式走 ``annotation`` 语义。``arrow=True`` 时从文字到锚点画一条同色细连线。
    返回 ``Text`` 对象。"""
    x, y = camera.project_xy(anchor3d)[0]
    tx, ty = x + offset2d[0], y + offset2d[1]
    kw = preset.text_kwargs("annotation")
    if arrow:
        ax.plot([tx, x], [ty, y], zorder=Z_TEXT, linewidth=0.8, color=kw["color"],
                alpha=kw["alpha"], solid_capstyle="round")
    return ax.text(tx, ty, text, ha=ha, va=va, zorder=Z_TEXT, **kw)


# ---- 坐标轴 ------------------------------------------------------------------

def draw_axes(ax, *, camera: Camera, preset: Preset,
              length: float | Sequence[float] | None = None,
              labels: Sequence[str] = ("x", "y", "z"), origin: Sequence[float] = (0, 0, 0),
              occluder: Polyhedron | None = None, negative: bool = True) -> None:
    """画世界坐标系 xyz 三根轴（小号实心箭头，与光线的线框锥体区分 + 斜体标签）。

    ``length`` 可以是一个数或三根轴各一个；``negative=True`` 时负半轴也画一段
    （无箭头）；穿过 ``occluder`` 内部的部分换 ``axis_occluded`` 样式。
    """
    geom = preset.geom
    L = np.broadcast_to(np.asarray(geom.axis_length if length is None else length, float), (3,))
    o = np.asarray(origin, float)
    kw = preset.line_kwargs("axis")
    for k, lab in enumerate(labels):
        d = np.zeros(3)
        d[k] = 1.0
        tip = o + d * L[k]
        start = o - d * L[k] if negative else o
        draw_segment(ax, start, tip - d * geom.cone_length * geom.axis_cone_scale,
                     camera=camera, preset=preset,
                     semantic="axis", occluded_semantic="axis_occluded", occluder=occluder,
                     z_visible=Z_EXTERNAL, z_hidden=Z_INTERNAL)
        # 轴箭头是标准箭头：锥尖在轴端、锥底朝原点（旧图 3.3 约定）；
        # 与光线端点「沿传播方向张开」的喇叭锥（Cone.along(apex, d)）方向相反
        k_scale = geom.axis_cone_scale
        cone = Cone.along(tip, -d, length=geom.cone_length * k_scale,
                          radius=geom.cone_radius * k_scale, samples=geom.cone_samples)
        draw_cone(ax, cone, camera=camera, line_kwargs=kw, z=Z_EXTERNAL, fill_mode="solid")
        x, y = camera.project_xy(tip + d * geom.axis_label_pad)[0]
        ax.text(x, y, f"${lab}$", ha="center", va="center", zorder=Z_TEXT,
                **preset.text_kwargs("axis_label"))
