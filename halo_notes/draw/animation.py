"""逐帧动画 → gif（``PillowWriter``）与同一帧函数的静态多帧导出（5.1）。

调用方提供两个回调：``build_axes(n_rows)`` 建一次 figure 并返回 ``(fig, rows)``——``rows[r]`` 是
第 r 行的"轴组"（一个 axes 或 axes 列表，含标题等常驻元素）；``render_frame(fig, axes, i)`` 把第
``i`` 帧画进给定轴组。动画用**单个持久 figure**：每帧 ``render_frame`` 后 ``grab_frame()``，再把这一帧
新增的 artist 逐个 ``remove()``（不 ``clear()``，常驻标题得以保留）；静态导出则一次建 ``len(indices)``
行，每行画一帧。两条路径调用同一个 ``render_frame``，静态图与 gif 帧序列由此一致。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.axes import Axes

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


def animate(render_frame: RenderFrame, n_frames: int, path: str | Path, *, fps: float,
            build_axes: BuildAxes, dpi: int) -> None:
    """把 ``n_frames`` 帧写成循环播放的 gif（``PillowWriter``，帧间隔 ``1000/fps`` ms）。"""
    fig, rows = build_axes(1)
    writer = PillowWriter(fps=fps)
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


__all__ = ["animate", "export_frames_png"]
