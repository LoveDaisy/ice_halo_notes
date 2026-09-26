"""番外图 2 `concentric_projection` 的机械核验：右栏同心圆的光点（concentric_projection 逐次投影算出）与左栏真实追迹的 `3-5`
光路逐点对应——每个光点 = 对应线段方向的反向单位向量 × 该段介质折射率；外加共线、两圆半径、两面 Snell、60° 楔。"""

from __future__ import annotations

import numpy as np
import pytest

import fig_concentric_projection as fig
from halo_notes.draw.raypath import N_ICE, face_sequence
from halo_notes.draw.tests.test_figures import run_figure

SCRIPT = "08.1-tape-vs-matrix/code/fig_concentric_projection.py"


def _cross(a, b) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


def test_points_are_collinear_along_the_normal_and_obey_snell():
    _, dirs = fig.raypath_35()
    p = fig.concentric_points(dirs["S"])
    s, s_ref, r, h, n3, n5 = p["S"], p["S'"], p["R"], p["H"], p["n_in"], p["n_out"]
    for q in (s_ref, r):
        assert abs(_cross(q - s, n3)) < 1e-12                     # S、S'、R 共线，且平行于 n_3
    assert abs(_cross(h - r, n5)) < 1e-12                         # 第二次投影平行于 n_5
    assert np.isclose(np.linalg.norm(s), 1.0, atol=1e-12) and np.isclose(np.linalg.norm(h), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(r) / np.linalg.norm(s), N_ICE, atol=1e-12)
    assert N_ICE == 1.31
    sin = lambda v, n: abs(_cross(v / np.linalg.norm(v), n))  # noqa: E731
    assert abs(1.0 * sin(s, n3) - N_ICE * sin(r, n3)) < 1e-12     # Snell @ 面 3
    assert abs(N_ICE * sin(r, n5) - 1.0 * sin(h, n5)) < 1e-12     # Snell @ 面 5
    assert np.isclose(abs(_cross(n3, n5)), np.sin(np.deg2rad(60.0)))   # 两面组成 60° 楔（法向夹 120°）


def test_each_light_point_is_minus_segment_direction_times_index():
    """R1.2：右栏每个光点 = 左栏对应光线段方向的反向单位向量 × 该介质折射率（入射 / 反射 / 出射在空气里，内部段在冰里）。
    左栏方向取自 solve_raypath_2d 追迹出的折线，右栏点取自 concentric_projection——两条链路不共享计算。"""
    path, dirs = fig.raypath_35()
    assert face_sequence(path) == [3, 5]
    p = fig.concentric_points(dirs["S"])
    index = {"S": 1.0, "S'": 1.0, "R": N_ICE, "H": 1.0}
    seg = [q1 - q0 for q0, q1, _ in path.segments()]
    traced = {"S": seg[0], "R": seg[1], "H": seg[2]}
    n3 = fig.SECTION.normal(fig.SECTION.face(3))
    traced["S'"] = seg[0] - 2 * (seg[0] @ n3) * n3               # 面 3 上的镜面反射，独立于脚本的 reflect
    for key, d in traced.items():
        assert np.linalg.norm(p[key] - (-d / np.linalg.norm(d) * index[key])) < 1e-12, key


def test_segment_colors_match_point_colors():
    """点与线段同色：左栏三段 + 反射段的线样式颜色 = 右栏同名光点的颜色，且四者互不相同。"""
    assert {k: fig.seg_style(k).color for k in ("S", "S'", "R", "H")} == fig.COLORS
    assert len(set(fig.COLORS.values())) == 4


def test_figure_draws_one_traced_35_path(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {"3-5": [3, 5]}
    assert [face_sequence(p) for p, _ in cap.paths] == [[3, 5]]
    assert len(cap.bodies) == 1


def test_counterexample_wrong_index_turns_red(monkeypatch):
    """反证：右栏把 N_ICE 换成 1/n，逐点对应断言必须失败。"""
    monkeypatch.setattr(fig, "N_ICE", 1.0 / N_ICE)
    with pytest.raises(AssertionError):
        test_each_light_point_is_minus_segment_direction_times_index()
