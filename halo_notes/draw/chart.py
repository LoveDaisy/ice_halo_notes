# 系列曲线图共用的外观（≥2 章消费才上提；自 ch8 `_ch8_plot.py` 升格，task-figure-style-codify）：
# 中文标签的字体回退序列、曲线图 rcParams、`apply_style()`、度数格式化；颜色从系列配色板取。
# ch8 私有的格子称呼、剖面坐标轴等仍留在 `08-wedge-times-fold/code/_ch8_plot.py`。
# 仿真参数（太阳高度、h/a、光线数……）不进图面，留在各脚本顶部注释与 provenance。
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from halo_notes.draw.style import DEFAULT_LIGHT  # noqa: E402
from halo_notes.draw.style.mapping import CJK_SANS  # noqa: E402

# 曲线图字体：拉丁字体在前、中文字体兜底——matplotlib 逐字形回退，数字 / ° / 减号取 Helvetica Neue（Hiragino 的 ° 是全角宽度、
# 且缺 U+2212），汉字取 Hiragino。CJK_SANS 是整段中文标注用的序列，这里只借它的中文字体名。
CHART_FONTS = ("Helvetica Neue", *CJK_SANS)

# 消费方沿用的配色板别名（ch8 `P.PAL` / ch9 `F.PAL`）：权威仍在 style.palette.DEFAULT_LIGHT
PAL = DEFAULT_LIGHT

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
