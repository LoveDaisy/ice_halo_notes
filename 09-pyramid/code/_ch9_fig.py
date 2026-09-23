# ch9 十一张正文插图（task-draw-ch9-figs）共用的画图侧工具，与仿真侧 `_ch9_sim.py` 分工：
#   - `_ch9_sim.py` 管「怎么渲染 / 怎么从渲染取数」（过滤器、曝光、径向剖面、峰判据），本文件**不改它、只 import 它**；
#   - 本文件管「怎么把数画成图」：曲线图外观（沿用 ch8 `_ch8_plot.py` 的一份实现，不复制）、族配色、天空图重投影 / 裁窗、
#     多曲线按能量加总、片晶弧计数判据。函数随各 fig 脚本按最小必要增量加入，不预设接口。
# 仿真参数（太阳高度、光线数、h/a……）不进图面，留在各脚本头注释与 provenance（ch8 惯例）。
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

CODE_DIR = Path(__file__).resolve().parent
CHAPTER = CODE_DIR.parent
IMG = CHAPTER / "img"
DATA = CHAPTER / "data"
CH8_CODE = CHAPTER.parent / "08-wedge-times-fold" / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


def _load_ch8_plot():
    """按文件路径加载 ch8 的 `_ch8_plot.py`（曲线图外观的唯一实现，ch9 直接复用）。不把 ch8 code/ 放进 sys.path：两章都有
    `enumerate_signatures.py` / `analyze_energy.py`，同名模块会互相遮蔽。"""
    spec = importlib.util.spec_from_file_location("_ch8_plot", CH8_CODE / "_ch8_plot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P8 = _load_ch8_plot()

PAL = P8.PAL
CHART_FONTS = P8.CHART_FONTS
apply_style = P8.apply_style
deg = P8.deg


def out_png(name: str) -> Path:
    """``img/<name>.png``（一图一脚本：脚本 ``fig_<name>.py`` → 本路径）。"""
    IMG.mkdir(parents=True, exist_ok=True)
    return IMG / f"{name}.png"


# PNG 元数据里 matplotlib 默认写入版本号 / 时间戳之类的 Software 字段：统一清空，几何 / 图表类产物才能逐字节复现
PNG_META = {"Software": None}
