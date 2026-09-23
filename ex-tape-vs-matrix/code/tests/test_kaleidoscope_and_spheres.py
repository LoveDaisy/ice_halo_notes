"""番外图 1 `kaleidoscope_and_spheres` 的机械核验（issue 表「机械核验」列）：左栏 Tricker 1973 的逐次镜像、右栏 TM2006 的同心圆投影。
点位全部来自脚本自己的计算函数（与出图同一份），这里用独立的矩阵 / 定律复算。"""

from __future__ import annotations

import numpy as np
import pytest

import fig_kaleidoscope_and_spheres as fig
from halo_notes.draw.raypath import N_ICE
from halo_notes.draw.tests.test_figures import run_figure
from halo_notes.math import reflection_group as rg

SCRIPT = "ex-tape-vs-matrix/code/fig_kaleidoscope_and_spheres.py"
Z = np.array([0.0, 0.0, 1.0])     # 晶体轴 R


def _plane_reflection(azimuth_deg: float) -> np.ndarray:
    """过 z 轴、方位 ``azimuth_deg`` 的镜面：法向在 xy 平面内、与镜面方向垂直——用 I − 2nnᵀ 独立复算（不走 sxy）。"""
    t = np.deg2rad(azimuth_deg + 90.0)
    n = np.array([np.cos(t), np.sin(t), 0.0])
    return np.eye(3) - 2.0 * np.outer(n, n)


def _angle_deg(a, b) -> float:
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b)))


def test_left_images_lie_on_one_small_circle_around_the_crystal_axis():
    images = fig.kaleidoscope_images()
    assert set(images) == {"S0", "S1", "S2", "S3", "S5", "S7"}
    polar = [_angle_deg(v, Z) for v, _ in images.values()]
    assert max(polar) - min(polar) < 1e-12
    assert np.isclose(polar[0], fig.POLAR_DEG, atol=1e-12)
    # 六个像两两不同（φ_0 避开了退化角）
    vs = [v for v, _ in images.values()]
    assert min(np.linalg.norm(a - b) for i, a in enumerate(vs) for b in vs[i + 1:]) > 0.1


def test_left_images_follow_tricker_1973_construction():
    """S_3 = S_0 关于 RB；S_1 = S_3 关于 RC；S_7 = S_0 关于 RA；S_2 = S_7 关于 RF；S_5 = S_1 关于 RD = S_2 关于 RE（Tricker 1973 p.4）。"""
    im = {k: v for k, (v, _) in fig.kaleidoscope_images().items()}
    P = {k: _plane_reflection(a) for k, a in fig.PLANES.items()}
    for new, src, plane in (("S3", "S0", "B"), ("S1", "S3", "C"), ("S7", "S0", "A"), ("S2", "S7", "F"),
                            ("S5", "S1", "D"), ("S5", "S2", "E")):
        assert np.allclose(P[plane] @ im[src], im[new], atol=1e-12), (new, src, plane)
    # 半平面 RA / RD 同属一面镜（与 ch7 的三面侧面镜 S_30 / S_90 / S_-30 一一对应）
    for a, b, xy in (("A", "D", "s30"), ("B", "E", "s90"), ("C", "F", "s-30")):
        assert np.allclose(P[a], P[b]) and np.allclose(P[a], rg.XY_MATRIX[xy])
    # 反射次数：一次 = S_3/S_7，两次 = S_1/S_2（绕 R 的旋转，det=+1），三次 = S_5
    orders = {k: o for k, (_, o) in fig.kaleidoscope_images().items()}
    assert orders == {"S0": 0, "S3": 1, "S7": 1, "S1": 2, "S2": 2, "S5": 3}


def test_left_tricker_120_degree_angles():
    """∠S_0RS_1 = ∠S_0RS_2 = 120°：绕晶体轴量的二面角（两像到 R 的方位差）。"""
    im = {k: v for k, (v, _) in fig.kaleidoscope_images().items()}
    for k in ("S1", "S2"):
        a, b = im["S0"][:2], im[k][:2]
        dihedral = np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1)))
        assert np.isclose(dihedral, 120.0, atol=1e-9), k


def test_right_projection_points_are_collinear_along_the_normal_and_obey_snell():
    p = fig.concentric_points()
    s, s_ref, r, h, n3, n5 = p["S"], p["S'"], p["R"], p["H"], p["n_in"], p["n_out"]
    cross = lambda a, b: float(a[0] * b[1] - a[1] * b[0])  # noqa: E731
    for q in (s_ref, r):
        assert abs(cross(q - s, n3)) < 1e-12                       # 三点共线，且平行于界面法向 n_3
    assert abs(cross(h - r, n5)) < 1e-12                           # 第二次投影平行于 n_5
    assert np.isclose(np.linalg.norm(s), 1.0, atol=1e-12) and np.isclose(np.linalg.norm(h), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(r) / np.linalg.norm(s), N_ICE, atol=1e-12)   # 两圆半径比 = n
    assert N_ICE == 1.31
    sin = lambda v, n: abs(cross(v / np.linalg.norm(v), n))  # noqa: E731
    assert abs(1.0 * sin(s, n3) - N_ICE * sin(r, n3)) < 1e-12      # Snell @ 面 3
    assert abs(N_ICE * sin(r, n5) - 1.0 * sin(h, n5)) < 1e-12      # Snell @ 面 5
    assert np.isclose(abs(cross(n3, n5)), np.sin(np.deg2rad(60.0)))  # 两面组成 60° 楔（法向夹 120°）


def test_figure_renders_the_section_and_no_raypath(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {} and cap.paths == []
    assert len(cap.bodies) == 1 and sorted(f.number for f in cap.bodies[0].faces) == [3, 4, 5, 6, 7, 8]
    assert len(cap.flip_axes) == 3                                 # 三面镜各画一次


@pytest.mark.parametrize("bad", ["swap_plane", "wrong_n"])
def test_counterexamples_turn_red(bad, monkeypatch):
    """反证：把 S_3 的镜面换成 RA，或把 N_ICE 换成 1/n，对应断言必须失败。"""
    if bad == "swap_plane":
        monkeypatch.setattr(fig, "STEPS", [("S3", "S0", "A", 1)] + fig.STEPS[1:])
        with pytest.raises(AssertionError):
            test_left_images_follow_tricker_1973_construction()
    else:
        monkeypatch.setattr(fig, "N_ICE", 1.0 / N_ICE)
        with pytest.raises(AssertionError):
            test_right_projection_points_are_collinear_along_the_normal_and_obey_snell()
