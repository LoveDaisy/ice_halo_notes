"""球面族图元单测：朝向判定、赤道前后分段、锥面几何、网格线数，以及"切段只有一份实现"的结构断言。"""

import inspect
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import halo_notes.draw.sphere as sphere_mod  # noqa: E402
from halo_notes.draw import (PRESETS, Camera, Sphere, graticule, new_figure, render_cone,  # noqa: E402
                             render_curve, render_great_circle, render_point_cloud)
from halo_notes.draw.geometry import unit  # noqa: E402
from halo_notes.draw.sphere import cone_surface_points  # noqa: E402

PRESET = PRESETS["default"]


@pytest.fixture
def ax():
    fig, ax = new_figure(400, 400, dpi=50)
    yield ax
    plt.close(fig)


@pytest.mark.parametrize("projection", ["orthographic", "perspective"])
def test_point_cloud_marks_back_points_as_hidden(ax, projection):
    cam = Camera(azimuth=30, elevation=20, projection=projection, distance=6)
    s = Sphere()
    front = cam.view_dir                     # 正对观察者
    back = -cam.view_dir                     # 正后方
    rim = unit(np.cross(cam.view_dir, [0, 0, 1]))   # 轮廓上：正交投影恰好侧对（不朝向），透视投影更在背面
    mask = render_point_cloud(ax, s, [front, back, rim, front * 0.5 + back * 0.2], camera=cam, preset=PRESET)
    assert mask.tolist() == [True, False, False, True]
    assert len(ax.lines) == 2   # 可见 / 背面各一组 marker
    # 背面不画时只剩一组
    ax.lines[-1].remove(); ax.lines[-1].remove()
    render_point_cloud(ax, s, [front, back], camera=cam, preset=PRESET, hidden_semantic=None)
    assert len(ax.lines) == 1


def test_equator_splits_into_front_and_back_runs(ax):
    cam = Camera(azimuth=0, elevation=20, projection="orthographic")
    pts, mask = render_great_circle(ax, Sphere(), camera=cam, preset=PRESET, samples=361)
    # 仰角 20° 从 +x 看：赤道上 x>0 的一半朝向观察者，判定与 view_dir 点积一致
    assert np.array_equal(mask, (pts @ cam.view_dir) > 0)
    assert 0.45 < mask.mean() < 0.55
    styles = {(ln.get_linestyle(), ln.get_zorder()) for ln in ax.lines}
    assert styles == {("-", sphere_mod.Z_ON_SPHERE), ("--", sphere_mod.Z_ON_SPHERE_HIDDEN)}
    # 每种样式的连续段数：前半连成 1–2 段（首尾相接处可能切开），后半同理
    assert 2 <= len(ax.lines) <= 4


def test_graticule_line_count_and_hidden_mode(ax):
    cam = Camera(azimuth=30, elevation=20)
    lines = graticule(ax, Sphere(), camera=cam, preset=PRESET, lat_step=30, lon_step=45, samples=91)
    # 纬线 -60/-30/0/30/60 共 5 条 + 经线 0/45/…/315 共 8 条
    assert len(lines) == 13
    assert all(np.allclose(np.linalg.norm(ln, axis=1), 1.0) for ln in lines)
    n_both = len(ax.lines)
    for ln in list(ax.lines):
        ln.remove()
    graticule(ax, Sphere(), camera=cam, preset=PRESET, lat_step=30, lon_step=45, samples=91, hidden_semantic=None)
    assert 0 < len(ax.lines) < n_both
    assert all(ln.get_alpha() == 1.0 for ln in ax.lines)   # 只剩可见段


def test_cone_surface_points_keep_half_angle():
    apex, axis = np.array([-0.98, 0.0, 0.17]), np.array([0, 0, 1.0])
    for half in (30.0, 150.0):
        grid = cone_surface_points(apex, axis, half, [0.7], phi_from=(1, 0, 0), n_phi=24, n_r=4)
        rel = (grid - apex).reshape(-1, 3)
        rel = rel[np.linalg.norm(rel, axis=1) > 1e-12]      # 去掉顶点本身
        cos = rel @ axis / np.linalg.norm(rel, axis=1)
        assert np.allclose(cos, np.cos(np.deg2rad(half)), atol=1e-12)
        assert np.isclose(np.linalg.norm(rel, axis=1).max(), 0.7)
    # phi=0 指向 phi_from（去掉沿轴分量）
    g = cone_surface_points(apex, axis, 30.0, [1.0], phi_from=(1, 0, 5), n_phi=8, n_r=1)
    d = unit(g[1, 0] - apex)
    assert np.allclose(d, [np.sin(np.deg2rad(30)), 0, np.cos(np.deg2rad(30))])


def test_render_cone_draws_both_leaves_far_to_near(ax):
    cam = Camera(azimuth=-150, elevation=12)
    leaves = render_cone(ax, (-1, 0, 0.2), (0, 0, 1), 30.0, camera=cam, preset=PRESET, length_up=0.6,
                         length_down=1.0, phi_range=(-30, 170), phi_from=(1, 0, 0), n_phi=10, n_r=3)
    assert len(leaves) == 2 and leaves[0].shape == (4, 11, 3)
    assert len(ax.patches) == 2 * 10 * 3
    # 与球面交线上的点同时满足两个方程：|p| = 1 且 (p-apex) 与轴夹角 = 30°（上叶）—— 交线由 3.5/3.6 脚本给，
    # 这里只核验网格本身的锥面方程
    for grid, half in zip(leaves, (30.0, 150.0)):
        rel = (grid - np.array([-1, 0, 0.2])).reshape(-1, 3)
        rel = rel[np.linalg.norm(rel, axis=1) > 1e-12]
        assert np.allclose(rel @ [0, 0, 1] / np.linalg.norm(rel, axis=1), np.cos(np.deg2rad(half)))


def test_render_curve_split_modes(ax, monkeypatch):
    calls = []
    real = sphere_mod._plot_runs

    def spy(*a, **k):
        calls.append(a)
        return real(*a, **k)

    monkeypatch.setattr(sphere_mod, "_plot_runs", spy)
    cam = Camera(azimuth=0, elevation=0, projection="orthographic")
    t = np.linspace(0, 2 * np.pi, 181)
    circle = np.stack([np.cos(t), np.sin(t), np.zeros_like(t)], axis=1)
    out = render_curve(ax, Sphere(), circle, camera=cam, preset=PRESET, split=False)
    assert out is None and len(calls) == 0
    assert len(ax.lines) == 1 and ax.lines[0].get_alpha() == 1.0
    mask = render_curve(ax, Sphere(), circle, camera=cam, preset=PRESET, split=True)
    assert len(calls) == 1 and mask.sum() == ((circle @ cam.view_dir) > 0).sum()
    assert len(ax.lines) > 2


def test_sphere_module_reuses_scene_plot_runs_only():
    """a56 机械防叉：三种折线图元都直接调用 scene._plot_runs，本模块不写自己的"按掩码切 run"循环。"""
    src = inspect.getsource(sphere_mod)
    assert src.count("_plot_runs(") >= 3
    assert "from .scene import" in src and "_plot_runs" in src.split("from .scene import", 1)[1].split("\n")[0]
    assert "while" not in src                                # 没有手写的 run 扫描循环
    assert not re.search(r"mask\[\s*\w+\s*\+\s*1\s*\]", src)  # 没有逐点比较相邻掩码
    for fn in (graticule, render_great_circle, render_curve):
        assert "_plot_runs(" in inspect.getsource(fn)


def test_render_cone_can_clip_cells_inside_a_sphere(ax):
    cam = Camera(azimuth=-150, elevation=12)
    apex = (-0.98, 0.0, 0.17)
    kw = dict(camera=cam, preset=PRESET, length_up=0.8, length_down=1.4, n_phi=12, n_r=4)
    render_cone(ax, apex, (0, 0, 1), 30.0, **kw)
    n_all = len(ax.patches)
    for p in list(ax.patches):
        p.remove()
    leaves = render_cone(ax, apex, (0, 0, 1), 30.0, clip_inside=Sphere(), **kw)
    assert 0 < len(ax.patches) < n_all
    # 留下的单元数 = 网格里中心在球外的单元数（投影后拿不回 3D 中心，从返回的网格直接复算）
    kept = 0
    for grid in leaves:
        for i in range(grid.shape[0] - 1):
            for j in range(grid.shape[1] - 1):
                c = np.stack([grid[i, j], grid[i, j + 1], grid[i + 1, j + 1], grid[i + 1, j]]).mean(axis=0)
                kept += np.linalg.norm(c) >= 1.0
    assert kept == len(ax.patches)
