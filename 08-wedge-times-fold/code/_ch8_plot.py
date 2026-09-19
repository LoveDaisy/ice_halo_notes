# ch8 两张曲线图（图 6 方位剖面、图 7 截面敏感性）共用的外观，只在此实现一份：
# 中文标签、格子称呼与正文一致（正文不出现 A60-10 这类类编号）、颜色从系列配色板取、CJK 字体回退序列、去掉上/右边框。
# 仿真参数（太阳高度、h/a、光线数……）不进图面，留在各脚本顶部注释与 provenance。
from __future__ import annotations

from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from halo_notes.draw.style import DEFAULT_LIGHT  # noqa: E402
from halo_notes.draw.style.mapping import CJK_SANS  # noqa: E402

PAL = DEFAULT_LIGHT

# 曲线图字体：拉丁字体在前、中文字体兜底——matplotlib 逐字形回退，数字 / ° / 减号取 Helvetica Neue（Hiragino 的 ° 是全角宽度、
# 且缺 U+2212），汉字取 Hiragino。CJK_SANS 是整段中文标注用的序列，这里只借它的中文字体名。
CHART_FONTS = ("Helvetica Neue", *CJK_SANS)

# 格子 / 曲线的正文称呼（图例、面板标题都用这个，不用类编号）
CELL_LABEL = {
    "A60-10": "60° 楔 + 120° 折叠这一格",
    "A0-02": "幻日环那一格",
    "all": "全部光路",
}
CELL_COLOR = {
    "A60-10": PAL["face_4"],      # 蓝
    "A0-02": PAL["face_5"],       # 橙
    "all": PAL["slate"],          # 灰
}
# 参数扫描（图 7 的四档 d）用的有序四色：蓝 → 绿 → 橙 → 红，全部取自侧面固定配色
SEQ_COLORS: tuple[str, ...] = (PAL["face_4"], PAL["face_6"], PAL["face_5"], PAL["face_3"])

AZ_LABEL = "方位角（从太阳算起）"
ENERGY_LABEL = "幻日环条带内的能量（对数）"
GUIDE_COLOR = PAL["ink_faint"]
TEXT_COLOR = PAL["ink_soft"]

RC = {
    "font.family": list(CHART_FONTS),
    "font.size": 11,
    "axes.titlesize": 12.5,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": PAL["ink_soft"],
    "axes.labelcolor": PAL["ink_soft"],
    "xtick.color": PAL["ink_soft"],
    "ytick.color": PAL["ink_soft"],
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "legend.fontsize": 10,
    "figure.facecolor": PAL["background"],
    "savefig.facecolor": PAL["background"],
}


def apply_style() -> None:
    plt.rcParams.update(RC)


def deg(x: float, digits: int = 0) -> str:
    return f"{x:.{digits}f}°"


def _plain(v: float) -> str:
    """对数轴刻度用普通小数（0.01 / 0.1 / 1）而不是 10 的幂：能量是任意单位，读者只需看数量级差。"""
    return f"{v:g}"


def profile_axes(ax, *, az_range: Sequence[float], ylabel: bool = True) -> None:
    """方位剖面的公共坐标轴：对数纵轴、x 刻度每 10°、带 ° 的刻度标签、淡横向网格。"""
    ax.set_yscale("log")
    ax.set_xlim(*az_range)
    lo, hi = az_range
    ticks = np.arange(np.ceil(lo / 10) * 10, hi + 1e-9, 10)
    ax.set_xticks(ticks)
    ax.set_xticklabels([deg(t) for t in ticks])
    ax.grid(axis="y", color=GUIDE_COLOR, lw=0.6, alpha=0.7)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _plain(v)))
    ax.set_xlabel(AZ_LABEL)
    if ylabel:
        ax.set_ylabel(ENERGY_LABEL)
    ax.tick_params(axis="y", which="minor", left=False)


def mark_azimuth(ax, az: float, text: str, *, color: str = TEXT_COLOR, y: float = 0.03, va: str = "bottom", ha: str = "left",
                 pad_deg: float = 0.6) -> None:
    """竖直参考线 + 小字标注（默认贴底，文字在线的 ``ha`` 一侧；``y`` 是轴高度比例）。"""
    ax.axvline(az, color=color, lw=0.8, ls=(0, (4, 3)), alpha=0.9, zorder=1)
    dx = pad_deg if ha == "left" else -pad_deg
    ax.text(az + dx, y, text, transform=ax.get_xaxis_transform(), ha=ha, va=va, fontsize=9.5, color=color)


def section_polygon(face_distance: Sequence[float]) -> np.ndarray:
    """截面多边形 = 六个半平面 {p·n_k ≤ d_k} 的交（法向 n_k 每 60° 一个，从 +x 起），Sutherland–Hodgman 逐半平面裁一个大方框。"""
    poly = [np.array(v, float) for v in ((-9, -9), (9, -9), (9, 9), (-9, 9))]
    for k, dk in enumerate(face_distance):
        n = np.array([np.cos(np.radians(60 * k)), np.sin(np.radians(60 * k))])
        out: list[np.ndarray] = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            sp, sq = p @ n - dk, q @ n - dk
            if sp <= 0:
                out.append(p)
            if (sp <= 0) != (sq <= 0):
                out.append(p + (q - p) * (sp / (sp - sq)))
        poly = out
    return np.array(poly)
