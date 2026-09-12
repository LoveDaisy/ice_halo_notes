"""采样与最近邻：单位性、已知点集手算、四元数构造与 Hamilton 积。"""

import numpy as np
import pytest

from halo_notes.math.sampling import llr_to_quat, nearest_neighbor_angle, quat_multiply, uniform_s2, uniform_so3_llr


def test_uniform_s2_unit_vectors_and_isotropy():
    pts = uniform_s2(20000, np.random.default_rng(0))
    assert pts.shape == (20000, 3)
    assert np.allclose(np.linalg.norm(pts, axis=1), 1.0)
    assert np.abs(pts.mean(axis=0)).max() < 0.02          # 各分量均值 ≈ 0（1/√N 量级）
    assert np.allclose((pts ** 2).mean(axis=0), 1 / 3, atol=0.02)


def test_uniform_so3_llr_ranges():
    llr = uniform_so3_llr(5000, np.random.default_rng(1))
    lon, lat, roll = llr.T
    assert (-np.pi <= lon).all() and (lon <= np.pi).all()
    assert (-np.pi / 2 <= lat).all() and (lat <= np.pi / 2).all()
    assert (0 <= roll).all() and (roll < 2 * np.pi).all()
    # 主轴方向 (cos φ cos λ, cos φ sin λ, sin φ) 落回 S²，且 z 分量均匀于 [−1, 1]（S² 均匀的判据）
    z = np.sin(lat)
    assert np.allclose(np.histogram(z, bins=10, range=(-1, 1))[0] / 500, 1.0, atol=0.15)


def test_quat_multiply_matches_hamilton_convention():
    i, j, k = [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]
    assert np.allclose(quat_multiply(i, j), k)         # ij = k
    assert np.allclose(quat_multiply(j, i), [0, 0, 0, -1])   # ji = −k（非交换）
    assert np.allclose(quat_multiply(i, i), [-1, 0, 0, 0])
    p, q = [1, 2, 3, 4], [5, 6, 7, 8]
    assert np.allclose(quat_multiply(p, q), [-60, 12, 30, 24])  # 手算


def test_llr_to_quat_unit_and_batch():
    llr = uniform_so3_llr(300, np.random.default_rng(2))
    q = llr_to_quat(llr)
    assert q.shape == (300, 4)
    assert np.allclose(np.linalg.norm(q, axis=1), 1.0)


def test_llr_to_quat_zero_pose_is_the_matlab_three_step_product():
    """λ=φ=θ=0：q1 = q3 = 单位，q2 = (cos π/4, 0, −sin π/4, 0)——照抄 `llr_quat_dist.m` 第 14 行的 π/4 − φ/2。"""
    q = llr_to_quat([[0.0, 0.0, 0.0]])[0]
    assert np.allclose(q, [np.cos(np.pi / 4), 0, -np.sin(np.pi / 4), 0])
    q = llr_to_quat([[0.0, np.pi / 2, 0.0]])[0]   # φ = 90°：q2 退化为单位
    assert np.allclose(q, [1, 0, 0, 0])


def test_nearest_neighbor_angle_on_octahedron():
    pts = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
    assert np.allclose(nearest_neighbor_angle(pts), np.pi / 2)
    pts2 = np.vstack([pts, [np.cos(0.1), np.sin(0.1), 0]])  # 再加一个离 +x 只有 0.1 rad 的点
    d = nearest_neighbor_angle(pts2)
    assert np.isclose(d[0], 0.1) and np.isclose(d[-1], 0.1)
    assert np.isclose(d[2], np.pi / 2 - 0.1)                    # +y 到新点 (cos .1, sin .1, 0) 的角距离
    assert np.allclose(d[[1, 3, 4, 5]], np.pi / 2)


def test_nearest_neighbor_angle_blocking_is_transparent():
    pts = uniform_s2(2500, np.random.default_rng(3))
    assert np.allclose(nearest_neighbor_angle(pts, block=1000), nearest_neighbor_angle(pts, block=2500))
    assert np.allclose(nearest_neighbor_angle(pts, block=7), nearest_neighbor_angle(pts, block=2500))


def test_nearest_neighbor_angle_s3_generic():
    q = llr_to_quat(uniform_so3_llr(500, np.random.default_rng(4)))
    q = np.vstack([q, -q])
    d = nearest_neighbor_angle(q)
    assert d.shape == (1000,) and (d > 0).all() and (d < np.pi / 2).all()   # 对径点在 π 处，不是最近邻


def test_nearest_neighbor_angle_rejects_single_point():
    with pytest.raises(ValueError):
        nearest_neighbor_angle(np.array([[1.0, 0, 0]]))
