"""2D 截面图的场景组装：截面 / 幽灵 / 参考六边形、截面光路（实心小三角箭头）、对称操作标注
（旋转弧箭头、翻转轴）、楔形 / 平板介质、多面板网格。

与 3D :mod:`scene` 平行的一套入口，不经过相机——数据坐标就是截面坐标。画图脚本：
``multi_panel`` / ``new_figure`` → ``render_section(ax, section, [paths], preset=...)`` →
``finish(ax, xlim, ylim)``（沿用 :func:`scene.finish`）。
"""

from __future__ import annotations

from typing import Iterable, Literal, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon

from .geometry import unit
from .geometry2d import Polygon2D, perp2d
from .labels import draw_edge_number
from .raypath import RayPath2D, SegmentKind
from .schematic import (CLOSURE_FACES, ENTRY_FACE, EXIT_FACE, jagged_polyline, wavy_polyline,
                        wedge_angle, wedge_apex)
from .style import PRESETS, LineStyle, MarkerStyle, Preset, TextStyle

# 绘制层级：从后往前
Z_FILL, Z_REFERENCE, Z_EDGE, Z_RAY, Z_ARROW, Z_LABEL, Z_TEXT = 1, 2, 3, 4, 5, 6, 7

Variant = Literal["body", "ghost", "reference"]
_VARIANT_STYLES: dict[str, tuple[str, str, bool]] = {
    # variant → (边语义, 编号语义, 是否填充)
    "body": ("edge_visible", "face_number", True),
    "ghost": ("edge_ghost", "face_number_ghost", False),
    "reference": ("edge_reference", "face_number_reference", False),
}


# ---- 截面 -------------------------------------------------------------------

def render_section(ax, poly: Polygon2D, raypaths: Iterable[RayPath2D] | None = None, *,
                   preset: Preset = PRESETS["default"], face_numbers: bool | Iterable[int] = False,
                   variant: Variant = "body", edges: Iterable[int] | None = None,
                   fill: str | None = "face_fill") -> None:
    """画一个截面多边形（填充 + 编号边 + 编号）及其光路。

    ``variant``：``"body"`` 实体（``edge_visible`` / ``face_number`` / 按 ``fill`` 语义填充）、
    ``"ghost"`` 光路展开的幽灵（``edge_ghost`` 点线、``face_number_ghost``、不填充）、
    ``"reference"`` 对称操作的参考幽灵（``edge_reference`` 淡实线、``face_number_reference``、不填充）。
    ``edges``：只画这些编号的边（None = 全部）；``fill``：填充语义名（None = 不填充；仅 body 生效）。
    """
    edge_semantic, number_semantic, fillable = _VARIANT_STYLES[variant]
    wanted_edges = None if edges is None else set(edges)
    if fillable and fill is not None:
        kw = preset.fill_kwargs(fill)
        if kw is not None:
            ax.add_patch(MplPolygon(poly.vertices, closed=True, zorder=Z_FILL, **kw))
    line = preset.line_kwargs(edge_semantic)
    for f in poly.faces:
        if wanted_edges is not None and f.number not in wanted_edges:
            continue
        a, b = poly.face_vertices(f)
        ax.plot([a[0], b[0]], [a[1], b[1]], solid_capstyle="round",
                zorder=Z_REFERENCE if variant == "reference" else Z_EDGE, **line)
    if face_numbers:
        wanted = {f.number for f in poly.faces} if face_numbers is True else set(face_numbers)
        for f in poly.faces:
            if f.number in wanted:
                draw_edge_number(ax, poly, f, preset, semantic=number_semantic).set_zorder(Z_LABEL)
    for path in raypaths or ():
        draw_raypath_2d(ax, path, preset=preset)


# ---- 光路 -------------------------------------------------------------------

def draw_arrowhead(ax, tip: Sequence[float], direction: Sequence[float], *, length: float,
                   width: float, color, alpha: float = 1.0, z: int = Z_ARROW) -> MplPolygon:
    """实心小三角：尖在 ``tip``、指向 ``direction``。返回 3 顶点的 ``Polygon``。"""
    tip = np.asarray(tip, dtype=float)
    d = unit(direction)
    p = perp2d(d)
    base = tip - d * length
    tri = np.array([tip, base + p * (width / 2), base - p * (width / 2)])
    patch = MplPolygon(tri, closed=True, zorder=z, facecolor=color, edgecolor="none", alpha=alpha)
    ax.add_patch(patch)
    return patch


def draw_raypath_2d(ax, path: RayPath2D, *, preset: Preset, semantic: str | LineStyle = "ray2d",
                    internal: str | LineStyle | None = None, exit: str | LineStyle | None = None,
                    arrows: Sequence[tuple[int, float]] | None = None,
                    markers: bool = False) -> None:
    """画一条截面光路：各段折线 + 实心小三角箭头（尖朝传播方向）。

    - ``semantic``：线样式（语义名或 ``LineStyle``）；``internal`` / ``exit`` 给定时晶体内部段 /
      出射段改用它（如 3.1 的淡红内部段、蓝点线出射段），否则整条同色
    - ``arrows``：``[(段下标, 尖在该段上的位置 0–1), …]``；None = 每段在 ``geom.arrow2d_at`` 处各一个
      （旧图 1.2）。三角尺寸 ``geom.arrow2d_length`` × ``geom.arrow2d_width``，颜色随所在段
    - ``markers``：在首尾与各事件点画小圆点（颜色 / 透明度随线，尺寸取 ``ray_marker``）
    """
    geom, sm = preset.geom, preset.style_map
    segments = list(path.segments())
    styles = []
    for p0, p1, kind in segments:
        s = semantic
        if internal is not None and kind is SegmentKind.INTERNAL:
            s = internal
        elif exit is not None and kind is SegmentKind.EXIT:
            s = exit
        styles.append(preset.line_kwargs(s))
    for (p0, p1, _), kw in zip(segments, styles):
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], solid_capstyle="round", zorder=Z_RAY, **kw)
    if arrows is None:
        arrows = [(i, geom.arrow2d_at) for i in range(len(segments))]
    for i, at in arrows:
        p0, p1, _ = segments[i]
        kw = styles[i]
        draw_arrowhead(ax, p0 + (p1 - p0) * at, p1 - p0, length=geom.arrow2d_length,
                       width=geom.arrow2d_width, color=kw["color"], alpha=kw.get("alpha", 1.0))
    if markers:
        idx = {0, len(path.points) - 1, *(ev.point_index for ev in path.events)}
        for i in sorted(idx):
            kw = styles[min(i, len(styles) - 1)]
            marker = MarkerStyle(sm.ray_marker.color, size=sm.ray_marker.size, alpha=kw.get("alpha", 1.0))
            mk = preset.marker_kwargs(marker)
            mk["color"] = kw["color"]
            ax.plot([path.points[i][0]], [path.points[i][1]], zorder=Z_ARROW, **mk)


# ---- 对称操作标注 ----------------------------------------------------------------

def draw_rotation_arc(ax, center: Sequence[float], radius: float, start_deg: float, end_deg: float, *,
                      preset: Preset, spokes: float | None = None, samples: int = 64) -> None:
    """旋转弧箭头：以 ``center`` 为心、从 ``start_deg`` 转到 ``end_deg``（逆时针为正）的圆弧，
    末端带实心三角；``spokes`` 给定时在起止两个方向各画一条该长度的辐条（``symmetry_spoke``）。弧样式 ``symmetry_mark``。
    ``start_deg == end_deg``（$R^c_0$）时只画辐条。"""
    c = np.asarray(center, dtype=float)
    kw = preset.line_kwargs("symmetry_mark")
    geom = preset.geom
    if spokes is not None:
        for deg in {start_deg, end_deg}:
            d = np.array([np.cos(np.deg2rad(deg)), np.sin(np.deg2rad(deg))])
            ax.plot([c[0], c[0] + spokes * d[0]], [c[1], c[1] + spokes * d[1]],
                    solid_capstyle="round", zorder=Z_REFERENCE, **preset.line_kwargs("symmetry_spoke"))
    if np.isclose(start_deg, end_deg):
        return
    th = np.deg2rad(np.linspace(start_deg, end_deg, samples))
    arc = c[None, :] + radius * np.stack([np.cos(th), np.sin(th)], axis=1)
    L, W = geom.arrow2d_length * geom.mark_arrow_scale, geom.arrow2d_width * geom.mark_arrow_scale
    # 弧线在箭头底处止步（不从三角里穿出来）：按每个采样步的弧长算要去掉几个点
    step = radius * abs(th[1] - th[0])
    cut = min(int(np.ceil(L / step)), samples - 2)
    ax.plot(arc[:samples - cut, 0], arc[:samples - cut, 1], solid_capstyle="round",
            zorder=Z_REFERENCE, **kw)
    tangent = np.array([-np.sin(th[-1]), np.cos(th[-1])]) * np.sign(end_deg - start_deg)
    draw_arrowhead(ax, arc[-1], tangent, length=L, width=W, color=kw["color"],
                   alpha=kw.get("alpha", 1.0), z=Z_REFERENCE)


def draw_flip_axis(ax, point: Sequence[float], direction: Sequence[float], half_length: float, *,
                   preset: Preset, arrow_at: float | None = None, arrow_half: float = 0.3) -> None:
    """翻转轴：过 ``point`` 沿 ``direction`` 的点划线（±``half_length``；样式 ``flip_axis``）；
    ``arrow_at`` 给定时在 ``point + direction·arrow_at`` 处画一支与轴垂直的双向箭头
    （半长 ``arrow_half``；样式 ``symmetry_mark``）。"""
    p = np.asarray(point, dtype=float)
    d = unit(direction)
    a, b = p - d * half_length, p + d * half_length
    ax.plot([a[0], b[0]], [a[1], b[1]], zorder=Z_REFERENCE, **preset.line_kwargs("flip_axis"))
    if arrow_at is None:
        return
    kw = preset.line_kwargs("symmetry_mark")
    geom = preset.geom
    m = p + d * arrow_at
    n = perp2d(d)
    L, W = geom.arrow2d_length * 1.1, geom.arrow2d_width * 1.5   # 双向箭头的两个头：比光线箭头略大、要留出可见的杆
    if arrow_half <= L:
        raise ValueError(f"arrow_half={arrow_half} leaves no shaft for arrowheads of length {L:.3g}")
    inner = arrow_half - L
    ax.plot([m[0] - n[0] * inner, m[0] + n[0] * inner], [m[1] - n[1] * inner, m[1] + n[1] * inner],
            solid_capstyle="round", zorder=Z_REFERENCE, **kw)
    for sgn in (+1, -1):
        draw_arrowhead(ax, m + n * sgn * arrow_half, n * sgn, length=L, width=W,
                       color=kw["color"], alpha=kw.get("alpha", 1.0), z=Z_REFERENCE)


# ---- 楔形 / 平板介质 ----------------------------------------------------------------

def render_medium(ax, medium: Polygon2D, *, preset: Preset, closure: Literal["jagged", "wavy"],
                  fill: str = "medium_fill", edge: str = "medium_edge", amplitude: float = 0.12) -> None:
    """画两条界面夹着的介质：区域填充（闭合边换成参差 / 波浪装饰线）+ 两条界面实线。
    界面线经 :func:`render_section` 画出（本图渲染的实体由此登记）。"""
    outline: list[np.ndarray] = []
    for f in medium.faces:
        a, b = medium.face_vertices(f)
        if f.number in CLOSURE_FACES:
            seg = (jagged_polyline(a, b, amplitude=amplitude, seed=f.number) if closure == "jagged"
                   else wavy_polyline(a, b, amplitude=amplitude))
        else:
            seg = np.array([a, b])
        outline.append(seg[:-1])
    ring = np.vstack(outline)
    kw = preset.fill_kwargs(fill)
    ax.add_patch(MplPolygon(ring, closed=True, zorder=Z_FILL, **kw))
    if closure == "jagged":  # 3.1 旧图：断口也描一圈黑边
        ekw = preset.line_kwargs(edge)
        ax.add_patch(MplPolygon(ring, closed=True, zorder=Z_EDGE, facecolor="none",
                                edgecolor=ekw["color"], linewidth=ekw["linewidth"], alpha=ekw["alpha"]))
    render_section(ax, medium, preset=preset.replace(
        style_map=preset.style_map.replace(edge_visible=preset.style(edge))),
        edges=(ENTRY_FACE, EXIT_FACE), fill=None)


def draw_wedge_angle(ax, medium: Polygon2D, *, preset: Preset, radius: float, text: str = r"$\theta$",
                     label_offset: float = 0.3, samples: int = 48) -> float:
    """在楔角顶点处标注两界面的夹角：双向箭头弧 + 文字（样式 ``angle_mark`` / ``annotation``；文字放在
    弧中点再往外 ``label_offset``）。弧张角就是 :func:`schematic.wedge_angle` 算出的几何值，返回该角（度）。"""
    apex = wedge_apex(medium)
    theta = wedge_angle(medium)
    # 两条界面从顶点出发的方向：指向介质内部（各取该界面上离顶点较远的端点）
    dirs = []
    for k in (ENTRY_FACE, EXIT_FACE):
        pts = medium.face_vertices(medium.face(k))
        far = max(pts, key=lambda q: np.linalg.norm(q - apex))
        dirs.append(unit(far - apex))
    a0, a1 = (np.degrees(np.arctan2(d[1], d[0])) for d in dirs)
    if (a1 - a0) % 360 > 180:
        a0, a1 = a1, a0
    a1 = a0 + (a1 - a0) % 360
    assert np.isclose(a1 - a0, theta, atol=1e-9)
    th = np.deg2rad(np.linspace(a0, a1, samples))
    arc = apex[None, :] + radius * np.stack([np.cos(th), np.sin(th)], axis=1)
    kw = preset.line_kwargs("angle_mark")
    geom = preset.geom
    L, W = geom.arrow2d_length, geom.arrow2d_width
    cut = max(1, int(samples * (L / (radius * np.deg2rad(theta)))))
    ax.plot(arc[cut:-cut, 0], arc[cut:-cut, 1], solid_capstyle="round", zorder=Z_TEXT, **kw)
    for tip, tangent in ((arc[0], -np.array([-np.sin(th[0]), np.cos(th[0])])),
                         (arc[-1], np.array([-np.sin(th[-1]), np.cos(th[-1])]))):
        draw_arrowhead(ax, tip, tangent, length=L, width=W, color=kw["color"], z=Z_TEXT)
    mid = np.deg2rad((a0 + a1) / 2)
    label_at = apex + (radius + label_offset) * np.array([np.cos(mid), np.sin(mid)])
    ax.text(label_at[0], label_at[1], text, ha="center", va="center", zorder=Z_TEXT,
            **preset.text_kwargs("annotation"))
    return theta


# ---- 文字 / 版面 ----------------------------------------------------------------

def annotate_2d(ax, text: str, xy: Sequence[float], *, preset: Preset, ha: str = "left",
                va: str = "center", semantic: str | TextStyle = "annotation",
                leader_to: Sequence[Sequence[float]] | None = None, **text_kw):
    """在数据坐标 ``xy`` 写注释；``leader_to`` 给定时从文字位置向每个目标点画一条引线（``leader`` 样式）。"""
    x, y = xy
    if leader_to:
        kw = preset.line_kwargs("leader")
        for target in leader_to:
            ax.plot([x, target[0]], [y, target[1]], zorder=Z_TEXT, solid_capstyle="round", **kw)
    return ax.text(x, y, text, ha=ha, va=va, zorder=Z_TEXT, **preset.text_kwargs(semantic), **text_kw)


def multi_panel(rows: int, cols: int, width_px: int, height_px: int, dpi: int = 200, *,
                preset: Preset = PRESETS["default"], titles: Sequence[str] | None = None,
                title_frac: float = 0.14, pad: float = 0.01, title_pos: Literal["bottom", "top"] = "bottom"):
    """``rows × cols`` 网格：每格一个 axes（等比例、无坐标框），下方（``title_pos="top"`` 时上方）留
    ``title_frac`` 高的标题带。``titles`` 按行优先给每格的（LaTeX）标题，样式 ``panel_title``，数学字体
    Computer Modern。返回 ``(fig, axes)``，``axes`` 是 ``rows × cols`` 的嵌套列表。调用方对每个 ax 用同一组
    ``xlim`` / ``ylim`` :func:`scene.finish`，即共用比例尺。"""
    fig = plt.figure(figsize=((width_px + 0.5) / dpi, (height_px + 0.5) / dpi), dpi=dpi)
    fig.patch.set_facecolor(preset.palette["background"])
    cell_w, cell_h = 1.0 / cols, 1.0 / rows
    axes = []
    k = 0
    for r in range(rows):
        row = []
        for c in range(cols):
            x0 = c * cell_w + pad
            y0 = 1.0 - (r + 1) * cell_h + (cell_h * title_frac if title_pos == "bottom" else pad)
            ax = fig.add_axes([x0, y0, cell_w - 2 * pad, cell_h * (1 - title_frac) - pad])
            ax.set_axis_off()
            if titles is not None and k < len(titles):
                ty = -title_frac / (1 - title_frac) / 2
                if title_pos == "top":
                    ty = 1.0 - ty
                ax.text(0.5, ty, titles[k], transform=ax.transAxes,
                        ha="center", va="center", math_fontfamily="cm",
                        **preset.text_kwargs("panel_title"))
            row.append(ax)
            k += 1
        axes.append(row)
    return fig, axes


__all__ = ["annotate_2d", "draw_arrowhead", "draw_flip_axis", "draw_raypath_2d", "draw_rotation_arc",
           "draw_wedge_angle", "multi_panel", "render_medium", "render_section"]
