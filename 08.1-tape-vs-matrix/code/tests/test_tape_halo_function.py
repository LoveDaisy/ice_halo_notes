"""`tape_halo_function` / `crosscheck_bridge` 的单测（plan Step 1–3 的测试点）+ 互证 A / B 的固定种子小样本复算。"""

from __future__ import annotations

import math

import numpy as np
import pytest
from lumice_integral.geometry import HexPrism, fold_matrix

import crosscheck_a
import crosscheck_b
import tape_halo_function as thf
from crosscheck_bridge import (
    angular_distance, haar_so3, light_point, light_point_batch, plate_attitude, s_centered, sun_direction,
    unfolded_normals, wedge_orientation,
)
from lumice_integral.symmetry.attitude import column_attitude
from lumice_integral.symmetry.reflection_group import Rz
from halo_notes.math.sampling import uniform_s2
from lumice_integral.symmetry.signature import phi

CRYSTAL = HexPrism.from_ratio(1.0)
I3 = np.eye(3)
M_3457 = fold_matrix(CRYSTAL, [3, 4, 5, 7])


# ---- Step 1：wedge frame 与符号换算 ------------------------------------------------------


def test_wedge_frame_is_right_handed_orthonormal():
    rng = np.random.default_rng(1)
    for _ in range(20):
        N = rng.normal(size=3)
        N /= np.linalg.norm(N)
        X = rng.normal(size=3)
        X -= (X @ N) * N * 0.5          # 任意非平行的单位向量
        X /= np.linalg.norm(X)
        u = np.column_stack(thf.wedge_frame(N, X))
        assert np.allclose(u.T @ u, I3, atol=1e-12)
        assert np.isclose(np.linalg.det(u), 1.0, atol=1e-12)


def test_standard_normals_match_eq10_and_wedge_frame_is_identity():
    """Eq. (10) 的 $(\\mathbf N_0,\\mathbf X_0)$ 本身就处在 standard orientation：其 wedge frame 是单位阵，$\\mathbf N_0\\cdot\\mathbf X_0=\\cos\\alpha$。"""
    for alpha in (28.0, 60.0, 90.0):
        N0, X0 = thf.standard_normals(alpha)
        assert np.isclose(N0 @ X0, math.cos(math.radians(alpha)))
        assert np.allclose(thf.orientation_from_normals(N0, X0), I3, atol=1e-12)


def test_wedge_orientation_roundtrip_eq9():
    """$u_0\\mathbf N_0=\\mathbf n_a$、$u_0\\mathbf X_0=-\\tilde{\\mathbf n}_b$（Eq. (9) 的验证式）；随机 $R$ 下 $u\\mathbf N_0=R\\mathbf n_a$。"""
    for M, a, b in ((I3, 3, 5), (M_3457, 3, 7), (I3, 3, 4), (I3, 1, 3)):
        N, X = unfolded_normals(CRYSTAL, M, a, b)
        alpha = math.degrees(math.acos(N @ X))
        N0, X0 = thf.standard_normals(alpha)
        u0 = wedge_orientation(CRYSTAL, M, a, b, I3)
        assert np.allclose(u0 @ N0, N, atol=1e-12)
        assert np.allclose(u0 @ X0, X, atol=1e-12)
        R = haar_so3(1, np.random.default_rng(3))[0]
        assert np.allclose(wedge_orientation(CRYSTAL, M, a, b, R) @ N0, R @ N, atol=1e-12)
    # 楔角与本系列一致：3-5 与 3-4-5-7 都是 60°
    N, X = unfolded_normals(CRYSTAL, M_3457, 3, 7)
    assert np.isclose(math.degrees(math.acos(N @ X)), 60.0)


def test_light_point_is_minus_R_phi_minus_Rinv_S():
    """退化情形 $R=I$、$M=I$：`light_point` = $-\\Phi(-\\mathbf S)$，与 `signature.phi` 手工核对（断言级）。"""
    S = np.array([math.cos(math.radians(-20)), math.sin(math.radians(-20)), 0.05])   # 幻日可达区内（互证 B φ≈20° 那一点）
    S /= np.linalg.norm(S)
    H = light_point(CRYSTAL, I3, 3, 5, I3, S)
    ref = phi(CRYSTAL, I3, 3, 5, -S)
    assert H is not None and ref is not None
    assert np.allclose(H, -ref, atol=1e-15)
    # 定义域外：从背面照面 3
    assert light_point(CRYSTAL, I3, 3, 5, I3, -S) is None
    # 批量版 NaN 语义与单点版一致
    out = light_point_batch(CRYSTAL, I3, 3, 5, I3, np.stack([S, -S]))
    assert np.allclose(out[0], H) and np.isnan(out[1]).all()


# ---- Step 2：TK1999 halo function ------------------------------------------------------


def test_equivariance_eq12_including_improper():
    """Eq. (12)：$\\mathbf F(w\\mathbf N,w\\mathbf X,w\\mathbf S)=w\\mathbf F(\\mathbf N,\\mathbf X,\\mathbf S)$，含 $\\det w=-1$。"""
    rng = np.random.default_rng(5)
    N0, X0 = thf.standard_normals(60.0)
    hits = 0
    for _ in range(200):
        u = haar_so3(1, rng)[0]
        S = uniform_s2(1, rng)[0]
        H = thf.halo_point_wedge(u @ N0, u @ X0, S)
        if H is None:
            continue
        hits += 1
        w = haar_so3(1, rng)[0]
        if hits % 2 == 0:
            w = w @ np.diag([1.0, -1.0, 1.0])            # yref：det = -1
        Hw = thf.halo_point_wedge(w @ u @ N0, w @ u @ X0, w @ S)
        assert Hw is not None
        assert np.allclose(Hw, w @ H, atol=1e-10)
    assert hits > 20


@pytest.mark.parametrize("alpha, expected", [(60.0, 21.8), (90.0, 45.7)])
def test_circular_halo_radius_eq41(alpha, expected):
    """Eq. (41) 的 $\\Delta_m$（源笔记 §5「圆晕半径」行：21.8 / 45.7）；且最小偏折取向下的光点偏折等于它。"""
    dm = thf.min_deviation_tk(alpha)
    assert abs(dm - expected) < 0.05
    # 最小偏折：T = n A，即 S 关于 N 的投影落在 A 方向；用 D_u = [cos(-Δm/2), 0, sin(-Δm/2)] [Eq. (43)]，u = I
    h = math.radians(dm) / 2
    D = np.array([math.cos(-h), 0.0, math.sin(-h)])
    H = thf.halo_point(I3, alpha, D)
    assert H is not None
    assert np.isclose(thf.deviation_deg(D, H), dm, atol=1e-9)


def test_no_ray_on_wrong_side_and_beyond_grazing_exit():
    N0, X0 = thf.standard_normals(60.0)
    # 从背面照入射面：S·N < 0
    assert thf.halo_point_wedge(N0, X0, -N0) is None
    # 沿 N 正入射：楔内光点 T = n N，T·X = n cos60° = 0.655，第二次投影根号内 0.43 + 1 − 1.716 < 0 → 出射面 TIR，no ray
    assert thf.halo_point_wedge(N0, X0, N0) is None
    assert thf.pr(np.array([0.0, 0.0, 1.0]), N0, 1.31) is not None
    assert thf.pr(N0 * 1.31, X0, 1.0, 1.31) is None


def test_batch_matches_scalar():
    rng = np.random.default_rng(7)
    u = haar_so3(50, rng)
    S = uniform_s2(50, rng)
    out = thf.halo_point_batch(u, 60.0, S)
    for i in range(50):
        h = thf.halo_point(u[i], 60.0, S[i])
        if h is None:
            assert np.isnan(out[i]).all()
        else:
            assert np.allclose(out[i], h, atol=1e-15)


# ---- Step 3：Tape 1980 路线（第二条链路）-----------------------------------------------


def test_tape1980_min_theta_equals_tk1999_theta0():
    """Eq. (6) 的 $\\theta_{\\min}$ = TK1999 Eq. (48) 的 $\\theta_0$：$\\sin\\theta_0=(n^2-1)^{1/2}\\tan(\\alpha/2)$；且 $\\alpha_{\\max}=99.5$。"""
    assert np.isclose(thf.min_theta(60.0), math.degrees(math.asin(math.sqrt(1.31 ** 2 - 1) * math.tan(math.radians(30)))))
    a_max = 2 * math.degrees(math.asin(1 / 1.31))
    assert abs(a_max - 99.5) < 0.05
    assert np.isclose(thf.min_theta(a_max), 90.0, atol=1e-9)


def test_tape1980_D_is_negative_and_min_at_mu_M():
    """$D<0$ 恒成立 [Eq. (12)]；$\\mu_M$ 处 $D$ 取极值（$|D|$ 最小），$D_{\\min}=\\alpha+2\\mu_M$ [Eq. (11)]。"""
    theta, alpha = 75.0, 60.0
    muM = thf.min_deviation_mu(theta, alpha)
    D0 = thf.normal_plane_deviation(theta, muM, alpha)
    assert np.isclose(D0, thf.min_deviation_D(theta, alpha), atol=1e-9)
    for mu in np.linspace(-89.0, thf.grazing_exit_mu(theta, alpha) - 1e-6, 50):
        D = thf.normal_plane_deviation(theta, mu, alpha)
        assert D < 0
        assert D <= D0 + 1e-9
    with pytest.raises(ValueError):
        thf.normal_plane_deviation(theta, thf.grazing_exit_mu(theta, alpha) + 1.0, alpha)


@pytest.mark.parametrize("sigma", [0, 10, 20, 30])
def test_sundog_inner_edge_two_tape_chains_agree(sigma):
    """M2：Tape 1980（Bravais 链路）与 TK1999（光点扫描）在幻日内边角距上互相对齐，容差 1e-6°。"""
    t80 = thf.sundog_inner_edge_1980(sigma)
    tk = crosscheck_b.inner_edge(sigma, I3, 3, 5, tape=True)
    assert abs(t80 - tk) < 1e-6
    if sigma == 0:
        assert abs(t80 - thf.min_deviation_tk(60.0)) < 1e-9     # Σ=0：θ=90，n'=n，Δ = -D_min(90) = Δ_m


# ---- Step 4 / 5：互证 A / B 的小样本复算（固定种子）--------------------------------------------


def test_crosscheck_a60_12_small_sample():
    a = crosscheck_a.run_a60_12(n=50, seed=0)
    assert a["n_agree"] == 50
    assert a["n_reach_m"] > 0
    assert a["max_dist"] < 1e-6
    assert a["n_over_tol"] == 0


def test_crosscheck_a60_10_plate_rule1_identity():
    phi, sigma, roll = crosscheck_a.sample_attitudes(n=40, seed=0)
    p = crosscheck_a.run_a60_10_plate(phi, sigma)
    assert p["max_conj_err"] < 1e-9
    assert p["n_agree"] == 40 and p["n_reach"] > 0
    assert p["max_dist"] < 1e-6


def test_crosscheck_a60_10_column_negative():
    """柱晶族：$RMR^{-1}\\mathbf k$ 与 $\\mathbf k$ 恒差 120°（几何事实，与代码对错无关）；Rule-1 技巧给错值，共轭式仍逐点成立。"""
    phi, sigma, roll = crosscheck_a.sample_attitudes(n=40, seed=0)
    c = crosscheck_a.run_a60_10_column(phi, sigma, roll)
    assert np.allclose(c["dev_k"], 120.0, atol=1e-9)
    assert c["n_agree"] == 40 and c["n_reach"] > 0
    assert c["rule1_min_deg"] > 1.0
    assert c["max_conj_dist"] < 1e-6
    # 直接的几何断言：任意柱晶姿态下 R k ⊥ k
    R = column_attitude(37.0, 111.0)
    assert abs((R @ np.array([0, 0, 1.0])) @ np.array([0, 0, 1.0])) < 1e-12


def test_a60_10_sharp_edge_141_8_at_sigma0():
    """M4：$\\Sigma=0$ 时 A60-10 最内点角距 = $\\Delta_m(60°)+120°=141.84°$（源笔记 §6.2 的「142° 锐边」理论值）。"""
    edge = crosscheck_b.inner_edge(0.0, M_3457, 3, 7, tape=False)
    assert abs(edge - (thf.min_deviation_tk(60.0) + 120.0)) < 1e-6
    assert abs(edge - 141.84) < 0.01


def test_s_centered_convention():
    """$(\\Delta,\\tau)$：太阳正前方时，天顶方向 τ=0，右手边（$-y$）τ=+90。"""
    S = np.array([1.0, 0.0, 0.0])
    d, t = s_centered(S, np.array([math.cos(0.3), 0.0, math.sin(0.3)]))
    assert np.isclose(d, math.degrees(0.3)) and np.isclose(t, 0.0)
    d, t = s_centered(S, np.array([math.cos(0.3), -math.sin(0.3), 0.0]))
    assert np.isclose(d, math.degrees(0.3)) and np.isclose(t, 90.0)
    # 3-5 是左幻日：τ = -90（TK1999 p.32「Plate 3 5 与 Plate 3 7 是左、右 22° 幻日」）
    rows = crosscheck_b.locus(0.0, n_phi=73)
    taus = [r[3] for r in rows if r[5]]
    assert taus and all(np.isclose(t, -90.0) for t in taus)


def test_haar_so3_and_plate_attitude():
    R = haar_so3(30, np.random.default_rng(0))
    assert np.allclose(np.einsum("kij,kil->kjl", R, R), np.broadcast_to(I3, (30, 3, 3)), atol=1e-12)
    assert np.allclose(np.linalg.det(R), 1.0)
    assert np.allclose(plate_attitude(123.0), Rz(123.0))
    assert np.allclose(sun_direction(30.0), [math.cos(math.radians(30)), 0.0, 0.5])
    assert np.isclose(angular_distance([1, 0, 0], [0, 1, 0])[0], math.pi / 2)
