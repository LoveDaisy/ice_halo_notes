"""解析 pdf：归一化、两种 S³ 写法相等、采样直方图 vs pdf 的 L1 距离、5.4 两种数值算法的误差断言。"""

import numpy as np

from halo_notes.math.density import (cos_power, exp_asymptotic, l1_distance, s2_nearest_neighbor_pdf,
                                     s3_nearest_neighbor_pdf, s3_nearest_neighbor_pdf_text_form)
from halo_notes.math.sampling import llr_to_quat, nearest_neighbor_angle, uniform_s2, uniform_so3_llr

L1_THRESHOLD = 0.15   # 5 个种子实测 0.04–0.07（20000 样本、100 bin），取约 2 倍余量


def test_pdfs_integrate_to_one():
    a = np.linspace(0, np.pi, 200001)
    for n in (100, 10000):
        assert abs(np.trapezoid(s2_nearest_neighbor_pdf(a, n), a) - 1) < 1e-3
        assert abs(np.trapezoid(s3_nearest_neighbor_pdf(a, n), a) - 1) < 1e-3


def test_s3_pdf_two_notations_agree():
    """`llr_quat_dist.m` 第 33 行（cos α sin α/π，指数 2M−2）与正文第 164 行（sin 2α/2π，指数 N−2）在 N=2M 下相等。"""
    a = np.linspace(0, 0.3, 1001)
    assert np.allclose(s3_nearest_neighbor_pdf(a, 20000), s3_nearest_neighbor_pdf_text_form(a, 20000), rtol=1e-9)


def hist_vs_pdf_s2(seed: int, n: int = 10000, reps: int = 2) -> float:
    rng = np.random.default_rng(seed)
    dm = np.concatenate([nearest_neighbor_angle(uniform_s2(n, rng)) for _ in range(reps)])
    edges = np.linspace(0, np.sqrt(4 / n) * 3, 101)
    centers = (edges[:-1] + edges[1:]) / 2
    h, _ = np.histogram(dm, edges, density=True)
    return l1_distance(h, s2_nearest_neighbor_pdf(centers, n), edges[1] - edges[0])


def test_s2_sampling_matches_pdf():
    assert hist_vs_pdf_s2(seed=0) < L1_THRESHOLD


def test_s3_sampling_matches_pdf():
    n, rng = 10000, np.random.default_rng(0)
    dm = []
    for _ in range(2):
        q = llr_to_quat(uniform_so3_llr(n, rng))
        dm.append(nearest_neighbor_angle(np.vstack([q, -q])))
    dm = np.concatenate(dm)
    edges = np.linspace(0, (4 / n) ** 0.33 * 2, 101)
    centers = (edges[:-1] + edges[1:]) / 2
    h, _ = np.histogram(dm, edges, density=True)
    assert l1_distance(h, s3_nearest_neighbor_pdf(centers, 2 * n), edges[1] - edges[0]) < L1_THRESHOLD


def test_pdf_peaks():
    """5.3 峰位 ≈ 0.014 rad（√(2/(N−2))），5.5 峰位 ≈ 0.055 rad（(π/(N−2))^{1/3}，N=20000）。"""
    a = np.linspace(1e-4, 0.2, 20000)
    assert abs(a[np.argmax(s2_nearest_neighbor_pdf(a, 10000))] - 0.014) < 0.001
    assert abs(a[np.argmax(s3_nearest_neighbor_pdf(a, 20000))] - 0.054) < 0.002


def test_l1_distance_of_identical_is_zero_and_scales_with_width():
    assert l1_distance([1, 2, 3], [1, 2, 3], 0.5) == 0
    assert l1_distance([1, 2, 3], [0, 0, 0], 0.5) == 3.0


def numerical_error_assertions(num, err_power, err_exp):
    """5.4 的两条断言，fig 脚本与本测试共用：指数渐近式误差全 < 1e-4；单精度幂法在 N ≥ 1e6 至少一点 |err| > 0.01。"""
    assert len(num) == 16
    assert np.abs(err_exp).max() < 1e-4
    assert np.abs(err_power[num >= 1e6]).max() > 0.01


def test_numerical_methods_float32():
    num = 10.0 ** np.arange(4, 7.01, 0.2)
    alpha = 2 / np.sqrt(num)
    gt = cos_power(alpha, num)
    single = cos_power(alpha, num, np.float32)
    exp32 = exp_asymptotic(alpha, num, np.float32)
    assert gt.dtype == np.float64 and single.dtype == np.float32 and exp32.dtype == np.float32
    numerical_error_assertions(num, single - gt, exp32 - gt)
    # 真值本身：α = 2/√N 时 ((1+cos α)/2)^(N−2) → e^{−1}
    assert np.allclose(gt, np.exp(-1), atol=2e-4)
