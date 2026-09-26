"""番外图 1 `kaleidoscope` 的机械核验：Tricker 1973 的逐次镜像（点位由脚本自己的函数算出，这里用独立的 I − 2nnᵀ 复算），
以及 R1.1 的拆图约束——(a)(b)(c) 每格只做一次镜像、只画一面镜一段弧，(d) 合成格不画弧、标两个 120°。"""

from __future__ import annotations

import numpy as np
import pytest

import fig_kaleidoscope as fig
from halo_notes.draw.tests.test_figures import run_figure
from lumice_integral.symmetry import reflection_group as rg

SCRIPT = "08.1-tape-vs-matrix/code/fig_kaleidoscope.py"
Z = np.array([0.0, 0.0, 1.0])     # 晶体轴 R


def _plane_reflection(azimuth_deg: float) -> np.ndarray:
    """过 z 轴、方位 ``azimuth_deg`` 的镜面：法向在 xy 平面内、与镜面方向垂直——用 I − 2nnᵀ 独立复算（不走 sxy）。"""
    t = np.deg2rad(azimuth_deg + 90.0)
    n = np.array([np.cos(t), np.sin(t), 0.0])
    return np.eye(3) - 2.0 * np.outer(n, n)


def _angle_deg(a, b) -> float:
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b)))


def _az(v) -> float:
    return float(np.degrees(np.arctan2(v[1], v[0])))


def test_images_lie_on_one_small_circle_around_the_crystal_axis():
    images = fig.kaleidoscope_images()
    assert set(images) == {"S0", "S1", "S2", "S3", "S5", "S7"}
    polar = [_angle_deg(v, Z) for v, _ in images.values()]
    assert max(polar) - min(polar) < 1e-12
    assert np.isclose(polar[0], fig.POLAR_DEG, atol=1e-12)
    vs = [v for v, _ in images.values()]
    assert min(np.linalg.norm(a - b) for i, a in enumerate(vs) for b in vs[i + 1:]) > 0.1


def test_images_follow_tricker_1973_construction():
    """S_3 = S_0 关于 RB；S_1 = S_3 关于 RC；S_7 = S_0 关于 RA；S_2 = S_7 关于 RF；S_5 = S_1 关于 RD = S_2 关于 RE（Tricker 1973 p.4）。"""
    im = {k: v for k, (v, _) in fig.kaleidoscope_images().items()}
    P = {k: _plane_reflection(a) for k, a in fig.PLANES.items()}
    for new, src, plane in (("S3", "S0", "B"), ("S1", "S3", "C"), ("S7", "S0", "A"), ("S2", "S7", "F"),
                            ("S5", "S1", "D"), ("S5", "S2", "E")):
        assert np.allclose(P[plane] @ im[src], im[new], atol=1e-12), (new, src, plane)
    for a, b, xy in (("A", "D", "s30"), ("B", "E", "s90"), ("C", "F", "s-30")):
        assert np.allclose(P[a], P[b]) and np.allclose(P[a], rg.XY_MATRIX[xy])
    orders = {k: o for k, (_, o) in fig.kaleidoscope_images().items()}
    assert orders == {"S0": 0, "S3": 1, "S7": 1, "S1": 2, "S2": 2, "S5": 3}


def test_tricker_120_degree_angles_and_composite_m():
    """∠S_0RS_1 = ∠S_0RS_2 = 120°（绕晶体轴的二面角）；链 RB→RC→RD 合成一个 M：两次 = 绕 z 转 120°，三次 = 一面镜。"""
    im = {k: v for k, (v, _) in fig.kaleidoscope_images().items()}
    for k in ("S1", "S2"):
        a, b = im["S0"][:2], im[k][:2]
        assert np.isclose(np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))), 120.0,
                          atol=1e-9), k
    P = {k: _plane_reflection(a) for k, a in fig.PLANES.items()}
    two, three = P["C"] @ P["B"], P["D"] @ P["C"] @ P["B"]
    c, s = np.cos(np.deg2rad(120.0)), np.sin(np.deg2rad(120.0))
    assert np.allclose(two, [[c, -s, 0], [s, c, 0], [0, 0, 1]], atol=1e-12)
    assert np.isclose(np.linalg.det(three), -1.0) and np.allclose(three @ three, np.eye(3), atol=1e-12)
    assert np.allclose(three @ im["S0"], im["S5"], atol=1e-12)


def test_step_panels_show_one_mirror_and_one_arc_each():
    """R1.1：(a)(b)(c) 各只做一次镜像（一面镜、一段弧，弧中点跨过那面镜），沿链 S_0→S_3→S_1→S_5 推进；(d) 无弧、标两个 120°。"""
    images = fig.kaleidoscope_images()
    chain = []
    for k in range(3):
        spec = fig.panel_content(k)
        assert len(spec["mirrors"]) == 1 and len(spec["arcs"]) == 1 and spec["faint_mirrors"] == []
        new, src, plane, _ = spec["arcs"][0]
        assert spec["mirrors"] == [plane] and spec["points"] == [src, new]
        a0, a1 = _az(images[src][0]), _az(images[new][0])
        a1 = a0 + (a1 - a0 + 180) % 360 - 180
        assert np.isclose(((a0 + a1) / 2) % 360, fig.PLANES[plane] % 360, atol=1e-9)
        chain.append((src, new, plane))
    assert chain == [("S0", "S3", "B"), ("S3", "S1", "C"), ("S1", "S5", "D")]
    d = fig.panel_content(3)
    assert d["arcs"] == [] and d["mirrors"] == [] and d["angles"] == ["S1", "S2"]
    assert d["points"] == ["S0", "S3", "S1", "S5"] and set(d["faint_points"]) == {"S7", "S2"}
    assert set(d["faint_mirrors"]) == {"A", "F"}


def test_figure_renders_four_panels_one_flip_axis_each_step(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {} and cap.paths == []
    assert len(cap.bodies) == 4 and all(sorted(f.number for f in b.faces) == [3, 4, 5, 6, 7, 8] for b in cap.bodies)
    assert [sum(ax is a for a, _, _ in cap.flip_axes) for ax in cap.axes2d] == [1, 1, 1, 0]
    got = [round(float(np.degrees(np.arctan2(d[1], d[0]))) % 180, 9) for _, _, d in cap.flip_axes]
    assert got == [90.0, 150.0, 30.0]                        # RB / RC / RD 所在的镜面线


def test_counterexample_swapped_plane_turns_red(monkeypatch):
    """反证：把 S_3 的镜面换成 RA，Tricker 构造断言必须失败。"""
    monkeypatch.setattr(fig, "STEPS", [("S3", "S0", "A", 1)] + fig.STEPS[1:])
    with pytest.raises(AssertionError):
        test_images_follow_tricker_1973_construction()
