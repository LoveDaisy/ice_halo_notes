r"""番外图 4 `plate_vs_column` 的机械核验（issue R1.4）：片晶 / 柱晶下 $RMR^{-1}$ 的旋转轴与转角由矩阵独立反解（特征向量 + 迹），
与 Rc、天顶 k 的夹角分别为 0° / 90°；片晶下 $RMR^{-1}=\mathrm{zrot}(120°)$，柱晶下离一切 zrot 都有下界。图上画的弧 / 箭头 / 晶体
与这些矩阵一致（晶体姿态由 plate / column 姿态矩阵给出，不手摆）。"""

from __future__ import annotations

import numpy as np
import pytest

import fig_plate_vs_column as fig
from halo_notes.draw.tests.test_figures import run_figure
from lumice_integral.symmetry.reflection_group import Rz

SCRIPT = "08.1-tape-vs-matrix/code/fig_plate_vs_column.py"
K = np.array([0.0, 0.0, 1.0])
TOL = 1e-12


def _angle_deg(a, b) -> float:
    """夹角用 atan2(|a×b|, a·b)，避开 arccos 在 0° 附近的分辨率损失。"""
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b)))


def _panel(name):
    return next(p for p in fig.PANELS if p[0] == name)


def _rotation_axis_by_eig(A) -> np.ndarray:
    w, v = np.linalg.eig(A)
    axis = np.real(v[:, np.argmin(np.abs(w - 1.0))])
    return axis / np.linalg.norm(axis)


@pytest.mark.parametrize("name, expected", [("plate", 0.0), ("column", 90.0)])
def test_rc_vs_zenith(name, expected):
    R = _panel(name)[2]
    assert abs(_angle_deg(R @ fig.C, K) - expected) < TOL


@pytest.mark.parametrize("name", ["plate", "column"])
def test_conjugate_is_120_rotation_about_rc(name):
    R = _panel(name)[2]
    A = R @ fig.M_3457 @ R.T
    assert np.allclose(A @ A.T, np.eye(3), atol=TOL) and np.isclose(np.linalg.det(A), 1.0, atol=TOL)
    axis = _rotation_axis_by_eig(A)
    rc = R @ fig.C
    assert min(np.linalg.norm(axis - rc), np.linalg.norm(axis + rc)) < TOL        # 旋转轴 = Rc（特征值 1 的特征向量）
    assert abs(np.degrees(np.arccos((np.trace(A) - 1) / 2)) - 120.0) < TOL        # 转角 120°（迹）
    # 脚本自己的 axis_angle（skew 部分）与特征分解一致，且带右手转向
    ax2, ang = fig.axis_angle(A)
    assert np.linalg.norm(ax2 - rc) < TOL and abs(ang - 120.0) < TOL


def test_plate_conjugate_is_zrot_120():
    R = _panel("plate")[2]
    assert np.abs(R @ fig.M_3457 @ R.T - Rz(120.0)).max() < TOL


def test_column_conjugate_is_not_any_zrot():
    """‖A − zrot(θ)‖_F ≥ |A_zz − 1|（zrot 的 zz 元恒为 1），而柱晶下 A_zz = cos120° = −0.5：对任意 θ 距离 ≥ 1.5。"""
    R = _panel("column")[2]
    A = R @ fig.M_3457 @ R.T
    assert abs(A[2, 2] - 1.0) >= 1.5 - TOL
    thetas = np.linspace(0, 360, 3601)
    assert min(np.linalg.norm(A - Rz(t)) for t in thetas) >= 1.5 - TOL


def test_figure_draws_crystal_axes_and_arcs_from_the_matrices(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {} and cap.paths == []
    assert len(cap.bodies) == 2 and len(cap.arcs) == 2
    for body, (ax, axis, angle, _), (name, crystal, R, *_) in zip(cap.bodies, cap.arcs, fig.PANELS):
        rc = R @ fig.C
        top = body.normal(body.face(1))                          # 晶体上底面法向 = 画出来的 c 轴方向
        assert np.linalg.norm(top - rc) < TOL
        assert np.allclose(body.vertices, crystal.vertices @ R.T, atol=TOL)
        assert np.linalg.norm(axis - rc) < TOL and abs(angle - 120.0) < TOL
        drawn = [d for a, _, d in cap.arrows if a is ax]
        assert any(np.linalg.norm(d - K) < TOL for d in drawn) and any(np.linalg.norm(d - rc) < TOL for d in drawn)


def test_counterexample_column_laid_as_plate_turns_red(monkeypatch):
    """反证：把柱晶的姿态换成片晶姿态（c 轴竖直），「Rc ⟂ k」与「离一切 zrot 有下界」都必须失败。"""
    bad = [p if p[0] != "column" else (p[0], p[1], Rz(fig.COLUMN_PSI), *p[3:]) for p in fig.PANELS]
    monkeypatch.setattr(fig, "PANELS", bad)
    with pytest.raises(AssertionError):
        test_rc_vs_zenith("column", 90.0)
    with pytest.raises(AssertionError):
        test_column_conjugate_is_not_any_zrot()
