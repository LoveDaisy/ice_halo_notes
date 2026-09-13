"""柱晶姿态：``column_attitude`` 与 ch3 ``fig_rotation_steps.py`` 的三步矩阵逐项一致（直接 runpy 取该脚本的 R3）；
``sky_direction(br, ·)`` 对任意 θ 都逐点重现 ``_tricker_arc.tricker_arc``（< 1e-12），证明 θ 确实被 $br$ 与 $R_z(\\theta)$
的对易吃掉；反例：$M = s$（#2）时 θ 不同天空点就不同。"""

from __future__ import annotations

import contextlib
import io
import runpy
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from halo_notes.draw.geometry import rotation  # noqa: E402
from halo_notes.math import reflection_group as rg  # noqa: E402
from halo_notes.math.attitude import Ry, column_attitude, sky_direction, sun_vector  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CH3 = ROOT / "03-parallel-raypaths" / "code"


@pytest.fixture(scope="module")
def tricker():
    sys.path.insert(0, str(CH3))
    try:
        import _tricker_arc  # noqa: E402  (ch3 章内 helper)
    finally:
        sys.path.pop(0)
    return _tricker_arc


def test_ry_matches_draw_rotation():
    for deg in (90.0, 37.0, -120.0):
        assert np.abs(Ry(deg) - rotation((0, 1, 0), deg)).max() < 1e-12
        assert np.abs(rg.Rz(deg) - rotation((0, 0, 1), deg)).max() < 1e-12


def test_column_attitude_equals_fig_rotation_steps_r3(monkeypatch):
    """与已发表 3.4 脚本的 R3 = Rz(α)·Ry(90°)·Rz(θ) 逐项一致（脚本 import 但不跑 main，不触碰 img/）。"""
    monkeypatch.syspath_prepend(str(CH3))
    with contextlib.redirect_stdout(io.StringIO()):
        ns = runpy.run_path(str(CH3 / "fig_rotation_steps.py"), run_name="not_main")
    R1, R2, R3 = ns["ROTATIONS"]
    R = column_attitude(ns["ALPHA_DEG"], ns["THETA_DEG"])
    assert np.abs(R - R3).max() < 1e-12
    assert np.abs(R - rotation((0, 0, 1), ns["ALPHA_DEG"]) @ rotation((0, 1, 0), 90.0) @ R1).max() < 1e-12
    # c 轴（第三列）水平、方位角 ψ；正交
    for psi, theta in ((0.0, 0.0), (33.0, 210.0), (-70.0, 5.0)):
        R = column_attitude(psi, theta)
        assert np.abs(R.T @ R - np.eye(3)).max() < 1e-12 and abs(np.linalg.det(R) - 1) < 1e-12
        assert np.abs(R[:, 2] - [np.cos(np.radians(psi)), np.sin(np.radians(psi)), 0.0]).max() < 1e-12


def test_sky_direction_of_br_reproduces_the_tricker_arc_for_every_theta(tricker):
    br = rg.by_number(3).matrix
    sun = sun_vector(tricker.SUN_ELEVATION_DEG)
    psis = np.linspace(0.0, 360.0, 73)
    expected = tricker.tricker_arc(np.radians(psis))
    for theta in (0.0, 17.0, 100.0, 259.5, 359.0):
        got = np.stack([sky_direction(br, column_attitude(psi, theta), sun) for psi in psis])
        assert np.abs(got - expected).max() < 1e-12, theta
    assert np.abs(sky_direction(br, column_attitude(0.0, 0.0), sun) - tricker.tricker_arc(0.0)).max() < 1e-12
    # 反日点自交：sin ψ = √3 tan Σ 的两个根都落在反日点上（与 3.5 单测同一判据，这里经 sky_direction 复现）
    s = np.radians(tricker.SUN_ELEVATION_DEG)
    for a in (np.arcsin(np.sqrt(3) * np.tan(s)), np.pi - np.arcsin(np.sqrt(3) * np.tan(s))):
        assert np.linalg.norm(sky_direction(br, column_attitude(np.degrees(a), 123.0), sun)
                              - tricker.anthelic_point()) < 1e-9


def test_sky_direction_of_s_depends_on_theta(tricker):
    """反例：#2（$S_{90°}$）不与 $R_z(\\theta)$ 对易，同一 ψ 下 θ 变天空点就变（> 2°）。"""
    s_matrix = rg.by_number(2).matrix
    sun = sun_vector(tricker.SUN_ELEVATION_DEG)
    p0, p1 = (sky_direction(s_matrix, column_attitude(40.0, th), sun) for th in (10.0, 50.0))
    assert np.linalg.norm(p0 - p1) > np.radians(2.0)


def test_sky_direction_batch_matches_single():
    M = rg.by_number(8).matrix
    R = column_attitude(12.0, 34.0)
    suns = np.stack([sun_vector(e) for e in (0.0, 10.0, 40.0)])
    batch = sky_direction(M, R, suns)
    assert batch.shape == (3, 3)
    for k, sv in enumerate(suns):
        assert np.abs(batch[k] - sky_direction(M, R, sv)).max() < 1e-15
