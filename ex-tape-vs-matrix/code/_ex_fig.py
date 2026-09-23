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


# ---- 网格表（图 5）：照搬 ch8 图 3 `fig_phi_class_grid.py` 的视觉语言 ------------------------------------------------
# 调色板、字体、折叠行标签直接从 ch8 脚本取（同一份权威，不另抄一份）；下面几个画法与该脚本 main() 里的写法逐项一致：
# 圆角框（rounding_size=14、实线 soft / 虚线 faint）、讨论中的格子黄底 + accent_warm 描边、组标题粗体 + 小字 + 下划线、
# 行标签右对齐主标签 + 小字注、行间 faint 分隔线。坐标一律像素（y 向下）。
def _load_ch8_grid():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "08-wedge-times-fold" / "code" / "fig_phi_class_grid.py"
    spec = importlib.util.spec_from_file_location("_ch8_fig_phi_class_grid", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CH8_GRID = _load_ch8_grid()
GRID_PAL, GRID_FONTS, GRID_PAD = CH8_GRID.PAL, CH8_GRID.FONTS, CH8_GRID.PAD


def grid_text(ax, x, y, s, size, color="ink", ha="center", va="center", **kw):
    return ax.text(x, y, s, fontsize=size, color=GRID_PAL[color], ha=ha, va=va, fontfamily=list(GRID_FONTS), **kw)


def grid_box(ax, x0, y0, w, h, *, kind: str) -> None:
    """一个格子的圆角框。``kind``：``"solid"``（ch8 成对格）/ ``"dashed"``（ch8 自对偶格）/ ``"star"``（ch8 黄底讨论格）。"""
    star = kind == "star"
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x0 + GRID_PAD, y0 + GRID_PAD), w - 2 * GRID_PAD, h - 2 * GRID_PAD,
                                boxstyle="round,pad=0,rounding_size=14",
                                facecolor=GRID_PAL["highlight"] if star else "none", alpha=0.35 if star else 1.0,
                                edgecolor=GRID_PAL["accent_warm"] if star else GRID_PAL["ink_soft" if kind == "solid" else "ink_faint"],
                                linewidth=1.6 if star else (1.1 if kind == "solid" else 0.9),
                                linestyle="-" if kind != "dashed" else (0, (4, 3)), zorder=1))


def grid_header(ax, x0, w, y_title, title, note, header_h) -> None:
    """列组表头：粗体标题 + 小字 + 下划线（ch8 组标题）。"""
    grid_text(ax, x0 + w / 2, y_title, title, 13.5, weight="bold")
    if note:
        grid_text(ax, x0 + w / 2, y_title + 0.3 * header_h, note, 10.5, "ink_soft")
    ax.plot([x0 + GRID_PAD, x0 + w - GRID_PAD], [y_title + 0.58 * header_h, y_title + 0.58 * header_h],
            color=GRID_PAL["ink_soft"], lw=1.0)


def grid_row_label(ax, x_right, y, main, note, *, main_size: float = 13, bold: bool = False) -> None:
    """行标签：右对齐的主标签 + 下一行小字注（ch8 行标签）。"""
    if note:
        ax.text(x_right, y - 16, main, fontsize=main_size, color=GRID_PAL["ink"], ha="right", va="center",
                fontfamily=list(GRID_FONTS), weight="bold" if bold else "normal")
        grid_text(ax, x_right, y + 16, note, 9.5, "ink_soft", ha="right")
    else:
        grid_text(ax, x_right, y, main, main_size, ha="right", weight="bold" if bold else "normal")


def grid_chip(ax, cx, cy, text: str, color: str, *, dashed: bool = False) -> None:
    """格内的光路标签 chip：实心语义色底 + 白字；``dashed`` 时换成白底 + 语义色虚线描边 + 语义色字（表外之物）。"""
    from matplotlib.patches import FancyBboxPatch
    w, h = 15.0 * len(text) + 28, 34
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=9",
                                facecolor=GRID_PAL["background"] if dashed else GRID_PAL[color],
                                edgecolor=GRID_PAL[color], linewidth=1.6,
                                linestyle=(0, (3, 2)) if dashed else "-", zorder=4))
    grid_text(ax, cx, cy, text, 11.5, color if dashed else "background", weight="bold", zorder=5)
