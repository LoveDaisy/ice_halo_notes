"""番外图 2 `unfold_3457` 的机械核验（issue 表「机械核验」列）：面序列由追迹得出、$M=\\mathcal S_{n_5}\\mathcal S_{n_4}=R_z(120°)$、
$M^{-1}\\mathbf n_7=\\mathbf n_5$、展开楔角 60°，且与 `3-5` 小图是同一个楔。"""

from __future__ import annotations

import numpy as np
import pytest

import fig_unfold_3457 as fig
from halo_notes.draw import CrossSection, solve_raypath_2d
from halo_notes.draw.raypath import face_sequence
from halo_notes.draw.tests.test_figures import run_figure
from lumice_integral.symmetry import reflection_group as rg

SCRIPT = "ex-tape-vs-matrix/code/fig_unfold_3457.py"


def test_traced_face_sequence_is_3457():
    path, corridor, _, _ = fig.unfold_3457(CrossSection(1.0))
    assert face_sequence(path) == [3, 4, 5, 7]
    assert face_sequence(corridor.straight) == [3, 4, 5, 7]
    assert len(corridor.ghosts) == 2                    # 面 4、面 5 上各展开一次


def test_fold_matrix_is_rz120_and_maps_n7_back_to_n5():
    N = rg.NORMALS
    M = rg.refl(N[5]) @ rg.refl(N[4])                   # 先在面 4 反射、再在面 5 反射
    assert np.allclose(M, rg.Rz(120.0), atol=1e-12)
    assert np.allclose(np.linalg.inv(M) @ N[7], N[5], atol=1e-12)
    assert np.allclose(M, rg.path_matrix([3, 4, 5, 7]), atol=1e-12)   # 与 ch7 权威实现一致


def test_unfolded_exit_face_is_the_virtual_face_n5_and_wedge_is_60():
    section = CrossSection(1.0)
    _, corridor, n_entry, n_virtual = fig.unfold_3457(section)
    assert np.allclose(n_virtual, section.normal(section.face(5)), atol=1e-12)
    assert np.allclose(n_virtual, rg.NORMALS[5][:2], atol=1e-12)
    assert abs(fig.wedge_between(n_entry, n_virtual) - 60.0) < 1e-9
    # 3-5 小图：同一截面、同一对法向 → 同一个 60° 楔
    p35 = solve_raypath_2d(section, [3, 5], tail=1.4, head=1.4)
    assert face_sequence(p35) == [3, 5]
    assert abs(fig.wedge_between(section.normal(section.face(3)), section.normal(section.face(5))) - 60.0) < 1e-9


def test_figure_draws_only_declared_paths(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    drawn = sorted({"-".join(map(str, face_sequence(p))) for p, _ in cap.paths})
    assert drawn == ["3-4-5-7", "3-5"]
    assert set(ns["PATHS"]) == {"3-4-5-7", "3-5"}


def test_counterexample_wrong_reflection_order_is_not_rz120():
    """反证：反射次序写反（S_{n_4}S_{n_5}）得 R_z(−120°)，M⁻¹n_7 不再是 n_5。"""
    N = rg.NORMALS
    wrong = rg.refl(N[4]) @ rg.refl(N[5])
    assert not np.allclose(wrong, rg.Rz(120.0), atol=1e-6)
    assert not np.allclose(np.linalg.inv(wrong) @ N[7], N[5], atol=1e-6)
    with pytest.raises(AssertionError):
        assert abs(fig.wedge_between(N[3][:2], N[4][:2]) - 60.0) < 1e-9   # 换错展开面（3-4）不是 60° 楔
