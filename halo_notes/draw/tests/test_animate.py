"""动画封装单测：gif 帧数 / 帧尺寸一致、常驻标题不被清掉、逐帧不同、静态导出与 gif 同一帧序列、重跑确定。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageSequence  # noqa: E402

from halo_notes.draw import PRESETS, multi_panel  # noqa: E402
from halo_notes.draw.animation import animate, export_frames_png  # noqa: E402

N = 5


def build_axes(n_rows):
    fig, axes = multi_panel(n_rows, 2, 200, 120 * n_rows, dpi=50, preset=PRESETS["default"],
                            titles=["$a$", "$b$"] * n_rows)
    return fig, axes


def render_frame(fig, row, i):
    t = i / (N - 1)
    for k, ax in enumerate(row):
        ax.plot([0, 1], [t, 1 - t * (k + 1) / 2], color="k")
        ax.text(0.5, 0.5, str(i), ha="center")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)


def frames_of(path):
    with Image.open(path) as im:
        return [np.asarray(f.convert("RGB")) for f in ImageSequence.Iterator(im)], im.info


def test_gif_has_n_frames_of_equal_shape_and_frames_differ(tmp_path):
    out = tmp_path / "a.gif"
    animate(render_frame, N, out, fps=50, build_axes=build_axes, dpi=50)
    frames, info = frames_of(out)
    assert len(frames) == N
    assert len({f.shape for f in frames}) == 1 and frames[0].shape[:2] == (120, 200)
    assert info.get("loop") == 0 and info.get("duration") == 20
    assert all(not np.array_equal(a, b) for a, b in zip(frames, frames[1:]))   # 逐帧不同（没有丢帧 / 重复帧）


def test_persistent_titles_survive_and_transient_artists_are_removed(monkeypatch):
    import halo_notes.draw.animation as mod
    grabbed = []

    class FakeWriter:
        def __init__(self, fps):
            self.fps = fps

        def saving(self, fig, path, dpi):
            self.fig = fig
            import contextlib
            return contextlib.nullcontext()

        def grab_frame(self):
            row = self.fig.axes
            grabbed.append([len(ax.lines) + len(ax.texts) for ax in row])

    monkeypatch.setattr(mod, "PillowWriter", FakeWriter)
    fig_holder = {}

    def build(n):
        fig, rows = build_axes(n)
        fig_holder["fig"] = fig
        return fig, rows

    animate(render_frame, 3, "unused.gif", fps=10, build_axes=build, dpi=50)
    fig = fig_holder["fig"]
    # 每次 grab 时每个 ax 恰好：1 条常驻标题 + 1 线 + 1 帧号文字；grab 完帧内新增的被移除，只剩标题
    assert grabbed == [[3, 3]] * 3
    assert [len(ax.lines) for ax in fig.axes] == [0, 0]
    assert [t.get_text() for ax in fig.axes for t in ax.texts] == ["$a$", "$b$"]   # plt.close 后 figure 对象仍可查


def test_static_export_uses_same_frame_indices_as_gif(tmp_path, monkeypatch):
    seen = {"gif": [], "png": []}

    def spy_gif(fig, row, i):
        seen["gif"].append(i)
        render_frame(fig, row, i)

    def spy_png(fig, row, i):
        seen["png"].append(i)
        render_frame(fig, row, i)

    animate(spy_gif, N, tmp_path / "b.gif", fps=50, build_axes=build_axes, dpi=50)
    indices = [0, N // 2, N - 1]
    export_frames_png(spy_png, indices, tmp_path / "b.png", build_axes=build_axes, dpi=50)
    assert seen["gif"] == list(range(N))
    assert seen["png"] == indices and set(indices) <= set(seen["gif"])
    with Image.open(tmp_path / "b.png") as im:
        assert im.size == (200, 120 * 3)
    # 静态图每行画的就是 gif 对应下标那一帧：比较两条路径下同一帧新增 artist 的数据
    fig, rows = build_axes(3)
    for row, i in zip(rows, indices):
        render_frame(fig, row, i)
    fig_g, rows_g = build_axes(1)
    for row, i in zip(rows, indices):
        render_frame(fig_g, rows_g[0], i)
        for ax_s, ax_g in zip(row, rows_g[0]):
            assert np.array_equal(ax_s.lines[-1].get_xydata(), ax_g.lines[-1].get_xydata())
    plt.close("all")


def test_gif_is_reproducible(tmp_path):
    a, b = tmp_path / "x.gif", tmp_path / "y.gif"
    animate(render_frame, N, a, fps=50, build_axes=build_axes, dpi=50)
    animate(render_frame, N, b, fps=50, build_axes=build_axes, dpi=50)
    assert a.read_bytes() == b.read_bytes()


def _noisy_backdrop_axes(n_rows):
    """右半幅是一张色彩噪声铺满的「底图」（吃光自适应调色板），左半幅留白画一条细蓝线。"""
    rng = np.random.default_rng(0)
    fig = plt.figure(figsize=(4, 2), dpi=50)
    rows = []
    for r in range(n_rows):
        ax_l = fig.add_axes([0.0, r / n_rows, 0.5, 1 / n_rows])
        ax_r = fig.add_axes([0.5, r / n_rows, 0.5, 1 / n_rows])
        ax_r.imshow(rng.integers(0, 256, (100, 100, 3), dtype=np.uint8))
        for ax in (ax_l, ax_r):
            ax.set_axis_off()
        rows.append((ax_l, ax_r))
    return fig, rows


def _thin_blue_line(fig, row, i):
    ax_l, _ = row
    ax_l.plot([0.1, 0.9], [0.2 + 0.1 * i, 0.8], color="#1f5fd0", linewidth=1.5, solid_capstyle="butt")
    ax_l.set_xlim(0, 1)
    ax_l.set_ylim(0, 1)


def test_fixed_colors_survive_gif_quantization(tmp_path):
    """R2-4 根因复现：底图噪声占满 256 色时，细线的蓝在默认量化下丢失（帧里没有一个像素等于该蓝）；``fixed_colors`` 给定后
    该蓝原样出现在调色板里且线条像素命中它（≥ 30 个像素）；底图区域仍是多色（不被固定色淹没）。"""
    blue = np.array([0x1F, 0x5F, 0xD0])
    plain = tmp_path / "plain.gif"
    animate(_thin_blue_line, 3, plain, fps=10, build_axes=_noisy_backdrop_axes, dpi=50)
    frames, _ = frames_of(plain)
    exact_plain = [int(np.all(f == blue, axis=-1).sum()) for f in frames]
    fixed = tmp_path / "fixed.gif"
    animate(_thin_blue_line, 3, fixed, fps=10, build_axes=_noisy_backdrop_axes, dpi=50, fixed_colors=["#1f5fd0", "white"])
    frames_f, _ = frames_of(fixed)
    exact_fixed = [int(np.all(f == blue, axis=-1).sum()) for f in frames_f]
    assert max(exact_plain) < 5, exact_plain                     # 默认量化：蓝几乎全丢
    assert min(exact_fixed) >= 30, exact_fixed                   # 固定色：线条主体精确保留
    right = frames_f[0][:, 100:, :]
    assert len(np.unique(right.reshape(-1, 3), axis=0)) > 150    # 底图仍是多色
    assert len(frames_f) == 3 and all(f.shape == frames_f[0].shape for f in frames_f)
