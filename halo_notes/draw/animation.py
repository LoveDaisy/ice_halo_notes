"""逐帧动画 → gif（``PillowWriter``）与同一帧函数的静态多帧导出（5.1）。

调用方提供两个回调：``build_axes(n_rows)`` 建一次 figure 并返回 ``(fig, rows)``——``rows[r]`` 是
第 r 行的"轴组"（一个 axes 或 axes 列表，含标题等常驻元素）；``render_frame(fig, axes, i)`` 把第
``i`` 帧画进给定轴组。动画用**单个持久 figure**：每帧 ``render_frame`` 后 ``grab_frame()``，再把这一帧
新增的 artist 逐个 ``remove()``（不 ``clear()``，常驻标题得以保留）；静态导出则一次建 ``len(indices)``
行，每行画一帧。两条路径调用同一个 ``render_frame``，静态图与 gif 帧序列由此一致。

调色板（7.5 gif，R2-4）：Pillow 把每帧自适应量化到 256 色（中位切分按像素数分箱），底图是一张色彩噪声铺满的 Lumice 渲染时
调色板全被它占掉，几十个像素的出射箭头（蓝）被就近映成灰。``animate(..., fixed_colors=[...])`` 用 :class:`PaletteWriter`：
每帧先量化到 ``256 − len(fixed)`` 色，再把 ``fixed`` 里的颜色原样追加进调色板、把与之相近（每通道 ≤ ``tol``）的像素改指过去，
线条主体颜色因此精确保留（抗锯齿边缘仍走自适应调色板）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import PillowWriter
from matplotlib.axes import Axes
from matplotlib.colors import to_rgb
from PIL import Image

RenderFrame = Callable[[Any, Any, int], None]
BuildAxes = Callable[[int], tuple[Any, Sequence[Any]]]


def _axes_of(group) -> list[Axes]:
    """把轴组（单个 Axes / 任意嵌套的列表）摊平成 Axes 列表。"""
    if isinstance(group, Axes):
        return [group]
    out: list[Axes] = []
    for g in group:
        out.extend(_axes_of(g))
    return out


def _render_transient(fig, group, render_frame: RenderFrame, index: int) -> list:
    """画一帧并返回这一帧新增的 artist（供事后移除）。"""
    axes = _axes_of(group)
    before = {id(a) for ax in axes for a in ax.get_children()}
    render_frame(fig, group, index)
    return [a for ax in axes for a in ax.get_children() if id(a) not in before]


def quantize_with_fixed_colors(frame: Image.Image, fixed: Sequence[tuple[int, int, int]], *, tol: int = 40,
                               colors: int = 256) -> Image.Image:
    """RGB 帧 → P 模式：自适应 ``colors − len(fixed)`` 色 + ``fixed`` 原色追加；每通道与某个固定色相差 ≤ ``tol`` 的像素指到它。"""
    rgb = frame.convert("RGB")
    n_fixed = len(fixed)
    if n_fixed == 0:
        return rgb.quantize(colors=colors)
    q = rgb.quantize(colors=colors - n_fixed, dither=Image.Dither.NONE)
    idx = np.array(q, dtype=np.uint8)
    arr = np.asarray(rgb, dtype=np.int16)
    for k, c in enumerate(fixed):
        near = np.all(np.abs(arr - np.array(c, dtype=np.int16)) <= tol, axis=-1)
        idx[near] = colors - n_fixed + k
    palette = list(q.getpalette()[:3 * (colors - n_fixed)])
    palette += [0] * (3 * (colors - n_fixed) - len(palette))
    for c in fixed:
        palette += [int(v) for v in c]
    out = Image.fromarray(idx, "P")
    out.putpalette(palette)
    return out


class PaletteWriter(PillowWriter):
    """``PillowWriter`` + 固定色调色板（见模块 docstring）。``fixed_colors`` 接受任何 matplotlib 颜色。"""

    def __init__(self, fps: float, fixed_colors: Sequence[Any], tol: int = 40) -> None:
        super().__init__(fps=fps)
        self.fixed = [tuple(int(round(v * 255)) for v in to_rgb(c)) for c in fixed_colors]
        self.tol = tol

    def finish(self) -> None:
        frames = [quantize_with_fixed_colors(f, self.fixed, tol=self.tol) for f in self._frames]
        frames[0].save(self.outfile, save_all=True, append_images=frames[1:], duration=int(1000 / self.fps), loop=0)


def animate(render_frame: RenderFrame, n_frames: int, path: str | Path, *, fps: float,
            build_axes: BuildAxes, dpi: int, fixed_colors: Sequence[Any] | None = None) -> None:
    """把 ``n_frames`` 帧写成循环播放的 gif（``PillowWriter``，帧间隔 ``1000/fps`` ms）；``fixed_colors`` 给定时用
    :class:`PaletteWriter` 保证这些颜色原样进调色板。"""
    fig, rows = build_axes(1)
    writer = PillowWriter(fps=fps) if fixed_colors is None else PaletteWriter(fps=fps, fixed_colors=fixed_colors)
    with writer.saving(fig, str(path), dpi):
        for i in range(n_frames):
            added = _render_transient(fig, rows[0], render_frame, i)
            writer.grab_frame()
            for artist in added:
                artist.remove()
    plt.close(fig)


def export_frames_png(render_frame: RenderFrame, indices: Sequence[int], path: str | Path, *,
                      build_axes: BuildAxes, dpi: int, **savefig_kw) -> None:
    """用同一个 ``render_frame`` 把 ``indices`` 指定的几帧各画一行，存成一张静态图。"""
    fig, rows = build_axes(len(indices))
    for row, i in zip(rows, indices):
        render_frame(fig, row, i)
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor(), **savefig_kw)
    plt.close(fig)


__all__ = ["PaletteWriter", "animate", "export_frames_png", "quantize_with_fixed_colors"]
