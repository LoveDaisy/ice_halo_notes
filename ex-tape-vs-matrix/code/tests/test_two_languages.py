"""番外图 3 `two_languages` 的机械核验（issue 表「机械核验」列）：三组互证 CSV 的角距离断言，外加画图用的坐标换算自检。

CSV 里的光点坐标按 12 位有效数字落盘（`crosscheck_a._fmt`），从坐标复算角距离的分辨率只有 ~1e-12 rad；所以 1e-13 rad 的断言
落在文件自己的全精度列（`dist_rad` / `dist_conj_rad`，互证时由未截断的向量算出）上，从坐标独立复算的一侧用打印精度给的
上界 2e-12 rad（每个分量舍入 ≤ 5e-13）。"""

from __future__ import annotations

import numpy as np
import pytest
from lumice_integral.geometry import HexPrism, fold_matrix

import fig_two_languages as fig
from crosscheck_bridge import angular_distance, s_centered
from halo_notes.draw.tests.test_figures import run_figure
from halo_notes.math.attitude import column_attitude
from tape_halo_function import zrot

SCRIPT = "ex-tape-vs-matrix/code/fig_two_languages.py"
PRINT_TOL = 2e-12            # 12 位有效数字的坐标复算上界（rad）
ANGLE_PRINT_TOL = 1e-10      # 姿态角 φ / roll 也按 12 位有效数字落盘（~1e-9° ≈ 2e-11 rad），经 R 传到光点后的复算上界
M_3457 = fold_matrix(HexPrism.from_ratio(1.0), [3, 4, 5, 7])


def test_a_35_both_languages_give_the_same_point():
    d = fig.load("a")
    assert len(d["tape"]) == 161                                   # data/notes.md：1000 组里 161 可达，两侧判定一致
    assert np.all(d["dist_rad"] < 1e-13)
    assert np.all(angular_distance(d["tape"], d["matrix"]) < PRINT_TOL)


def test_b_plate_rule1_recovers_the_fold():
    d = fig.load("b")
    assert len(d["tape"]) > 20
    assert np.all(d["dist_rad"] < 1e-13)
    assert np.all(angular_distance(d["tape"], d["matrix"]) < PRINT_TOL)


def test_c_column_rule1_separates_but_conjugate_holds():
    d = fig.load("c")
    # 分离量：从坐标复算与文件列一致（文件列同样是 12 位有效数字，复算差 < 1e-8°）
    sep = np.degrees(angular_distance(d["tape"], d["matrix"]))
    assert np.allclose(sep, d["dist_rule1_deg"], atol=1e-8)
    assert sep.min() > 10.0                                        # 每一对都明显分离（图上看得见）
    # 共轭式：真值 = R M R⁻¹ · H_35，H_35 由 Rule 1 列反转 zrot(−120°) 得到——绕水平的晶体 c 轴转 120°
    assert np.all(d["dist_conj_rad"] < 1e-13)
    R = np.stack([column_attitude(p, r) for p, r in zip(d["phi_deg"], d["roll_deg"])])
    h35 = fig.h35_from_rule1(d["tape"])
    conj = np.einsum("kij,kj->ki", R @ M_3457 @ np.transpose(R, (0, 2, 1)), h35)
    assert np.all(angular_distance(conj, d["matrix"]) < ANGLE_PRINT_TOL)
    wrong = np.einsum("kij,kj->ki", np.broadcast_to(zrot(120.0), R.shape), h35)   # 同一 H_35 绕竖直轴转：远超上界
    assert np.all(angular_distance(wrong, d["matrix"]) > 1e3 * ANGLE_PRINT_TOL)
    axis = R @ np.array([0.0, 0.0, 1.0])                           # 晶体 c 轴在天空里：水平
    assert np.allclose(axis[:, 2], 0.0, atol=1e-12)


def test_plot_coordinates_preserve_the_quantities_they_display():
    d = fig.load("a")
    S = np.stack([d["Sx"], d["Sy"], d["Sz"]], axis=1)
    xy = fig.sun_polar(S[:5], d["matrix"][:5])
    for (x, y), s, h in zip(xy, S[:5], d["matrix"][:5]):
        assert np.isclose(np.hypot(x, y), s_centered(s, h)[0])     # 半径 = 到太阳的角距
    # 天空图：绕天顶转 120° 就是平面上转 120°
    H = fig.load("b")["matrix"]
    a, b = fig.sky_polar(H), fig.sky_polar(H @ zrot(120.0).T)
    ang = np.degrees(np.arctan2(b[:, 1], b[:, 0]) - np.arctan2(a[:, 1], a[:, 0])) % 360
    assert np.allclose(ang, 120.0, atol=1e-9)


def test_figure_renders_without_precision_numbers(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {} and cap.paths == []
    import matplotlib.pyplot as plt  # noqa: F401  (run_figure 已关图；这里检查脚本源码里不出现精度字样)
    src = (fig.HERE / "fig_two_languages.py").read_text()
    body = src.split("\nimport csv", 1)[1]                         # 头注之外的代码里不写 1e-1x / 误差
    assert "e-1" not in body and "误差" not in body


@pytest.mark.parametrize("group", ["a", "b"])
def test_counterexample_perturbed_point_turns_red(group):
    """反证：把一侧光点绕天顶转 0.01°，角距离断言必须失败。"""
    d = fig.load(group)
    moved = d["tape"] @ zrot(0.01).T
    assert not np.all(angular_distance(moved, d["matrix"]) < PRINT_TOL)
