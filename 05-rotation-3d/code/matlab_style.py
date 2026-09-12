# 本章三张 MATLAB 重制图（fig_hist01 / fig_hist02 / fig_numerical_err）共用的外观：MATLAB 默认配色、字号（旧脚本
# set(gca,'fontsize',13)、xlabel 16、title 18 粗体）、四边框 + 朝内刻度、1500×1125 画布。直方图 + 解析 pdf 的画法只在此实现一份。
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator  # noqa: E402

MATLAB_BLUE = "#0072BD"     # MATLAB 默认第 1 色（bar 加 alpha 0.5 后即旧图的浅蓝）
MATLAB_ORANGE = "#D95319"   # MATLAB 默认第 2 色
WIDTH, HEIGHT, DPI = 1500, 1125, 200   # = 旧图分辨率；figsize 7.5×5.625 in 与 MATLAB [600,450]*1.2 px 同比例
TICK_FS, LABEL_FS, TITLE_FS = 13, 16, 18


def matlab_figure():
    """白底画布 + 单 axes，四边框、刻度朝内，字号同旧脚本。"""
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0.13, 0.11, 0.775, 0.815])
    ax.tick_params(direction="in", labelsize=TICK_FS, top=True, right=True)
    ax.yaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))   # MATLAB 式刻度步长（不出 2.5 / 0.025）
    return fig, ax


def plot_nn_histogram(ax, samples: np.ndarray, edges: np.ndarray, pdf_at_centers: np.ndarray, title: str) -> np.ndarray:
    """旧脚本的 `bar(...,'facealpha',0.5,'edgecolor','none') + plot(pdf,'linewidth',2.5)`：直方图按 pdf 归一化
    （MATLAB `histcounts(...,'normalization','pdf')` = `np.histogram(density=True)`），返回各 bin 的密度。"""
    centers = (edges[:-1] + edges[1:]) / 2
    density, _ = np.histogram(samples, edges, density=True)
    # 一整块阶梯多边形而不是逐根 bar：半透明相邻 bar 的抗锯齿接缝会留下淡竖线
    bars = ax.stairs(density, edges, fill=True, color=MATLAB_BLUE, alpha=0.5, label="Empirical histogram")
    line, = ax.plot(centers, pdf_at_centers, color=MATLAB_ORANGE, lw=2.5, label="Analytical pdf")
    ax.set_xlim(0, edges[-1])
    ax.set_ylim(0, None)
    ax.legend(handles=[bars, line], fontsize=TICK_FS, loc="upper right", edgecolor="black", fancybox=False)
    ax.set_xlabel("Nearest neighbor (rad)", fontsize=LABEL_FS)
    ax.set_ylabel("Probability density", fontsize=LABEL_FS)
    ax.set_title(title, fontsize=TITLE_FS, fontweight="bold")
    return density
