# 番外配图共用的二维小工具（图 1 万花筒 / 图 2 同心圆共用；从原 fig_kaleidoscope_and_spheres.py 抽出，不是新外观）。
import numpy as np

from halo_notes.draw import FACE_COLORS, PRESETS
from halo_notes.draw.scene2d import draw_arrowhead
from halo_notes.draw.style import LineStyle, TextStyle
from halo_notes.draw.style.mapping import CJK_SANS

PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(face_number_colors=FACE_COLORS))
TEXT15 = TextStyle("ink", fontsize=15, family=CJK_SANS)
SPOKE = LineStyle("ink_faint", linewidth=0.9)


def direction(deg: float) -> np.ndarray:
    return np.array([np.cos(np.deg2rad(deg)), np.sin(np.deg2rad(deg))])


def azimuth(v) -> float:
    return float(np.degrees(np.arctan2(v[1], v[0])))


def unwrap_to(a1: float, a0: float) -> float:
    """把角 ``a1`` 平移整圈，使它与 ``a0`` 之差落在 (−180°, 180°]。"""
    while a1 - a0 > 180:
        a1 -= 360
    while a1 - a0 <= -180:
        a1 += 360
    return a1


def draw_line(ax, a, b, style: LineStyle, z: float = 4) -> None:
    ax.plot([a[0], b[0]], [a[1], b[1]], solid_capstyle="round", zorder=z, **PRESET.line_kwargs(style))


def draw_circle(ax, r: float, style: LineStyle, center=(0.0, 0.0), z: float = 3) -> None:
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(center[0] + r * np.cos(th), center[1] + r * np.sin(th), zorder=z, **PRESET.line_kwargs(style))


def draw_arrow(ax, a, b, color: str, *, linewidth: float = 1.8, z: float = 6, linestyle="-", head: float = 1.0) -> None:
    """``a`` → ``b`` 的直线箭头（末端实心三角，杆在三角根部截止；``head`` 缩放三角）。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L, W = PRESET.geom.arrow2d_length * head, PRESET.geom.arrow2d_width * head
    u = (b - a) / np.linalg.norm(b - a)
    stem = b - u * L * 0.9
    ax.plot([a[0], stem[0]], [a[1], stem[1]], color=PRESET.palette[color], linewidth=linewidth, linestyle=linestyle,
            solid_capstyle="round", zorder=z)
    draw_arrowhead(ax, b, u, length=L, width=W, color=PRESET.palette[color], z=z)


def draw_arc_arrow(ax, r: float, start_deg: float, end_deg: float, color: str, *, both: bool = False,
                   linewidth: float = 1.5) -> None:
    """以原点为心、从 ``start_deg`` 走到 ``end_deg`` 的弧，末端（``both`` 时两端）带实心三角。"""
    geom = PRESET.geom
    L, W = geom.arrow2d_length, geom.arrow2d_width
    th = np.deg2rad(np.linspace(start_deg, end_deg, 96))
    arc = r * np.stack([np.cos(th), np.sin(th)], axis=1)
    step = r * abs(th[1] - th[0])
    cut = int(np.ceil(L / step))
    lo = cut if both else 0
    ax.plot(arc[lo:len(arc) - cut, 0], arc[lo:len(arc) - cut, 1], color=PRESET.palette[color], linewidth=linewidth,
            solid_capstyle="round", zorder=5)
    sgn = np.sign(end_deg - start_deg)
    ends = [(arc[-1], th[-1], sgn)] + ([(arc[0], th[0], -sgn)] if both else [])
    for tip, t, s in ends:
        tangent = np.array([-np.sin(t), np.cos(t)]) * s
        draw_arrowhead(ax, tip, tangent, length=L, width=W, color=PRESET.palette[color], z=5)


def draw_point(ax, xy, color: str, size: float = 11.0, z: float = 8, alpha: float = 1.0) -> None:
    ax.plot([xy[0]], [xy[1]], "o", ms=size, color=PRESET.palette[color], markeredgecolor=PRESET.palette["background"],
            markeredgewidth=1.4, zorder=z, alpha=alpha)
