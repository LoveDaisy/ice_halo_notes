"""姿态插值单测：四元数往返、slerp 端点 / 等角速度 / 最短路径与双覆盖、矩阵线性插值确实塌陷、
欧拉角插值与 slerp 中途姿态不同。"""

import numpy as np
import pytest

from halo_notes.draw.geometry import rotation
from halo_notes.draw.interp import (lerp_euler, lerp_matrix, lon_lat_roll_to_matrix, matrix_to_lon_lat_roll,
                                    matrix_to_quat, quat_to_matrix, relative_angle_deg, rotation_angle_deg,
                                    slerp, slerp_matrix)


def random_rotations(n: int, seed: int = 7):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        axis = rng.normal(size=3)
        yield rotation(axis, rng.uniform(-180, 180))


@pytest.mark.parametrize("R", list(random_rotations(12)) + [np.eye(3), rotation((1, 0, 0), 180),
                                                             rotation((0, 1, 0), 180), rotation((0, 0, 1), 180)])
def test_quaternion_round_trip(R):
    q = matrix_to_quat(R)
    assert np.isclose(np.linalg.norm(q), 1.0)
    assert np.abs(quat_to_matrix(q) - R).max() < 1e-9


@pytest.mark.parametrize("R", list(random_rotations(8, seed=3)))
def test_lon_lat_roll_round_trip(R):
    lon, lat, roll = matrix_to_lon_lat_roll(R)
    assert -180 <= lon <= 180 and -90 <= lat <= 90 and -180 <= roll <= 180
    assert np.abs(lon_lat_roll_to_matrix(lon, lat, roll) - R).max() < 1e-9


def test_lon_lat_roll_matches_ch3_convention():
    """φ=0 时就是 ch3 的 R_z(α)·R_y(π/2)·R_z(θ)；c 轴（第三列）指向 (λ, φ) 方向。"""
    a, th = 37.0, 111.0
    assert np.allclose(lon_lat_roll_to_matrix(a, 0.0, th),
                       rotation((0, 0, 1), a) @ rotation((0, 1, 0), 90) @ rotation((0, 0, 1), th))
    R = lon_lat_roll_to_matrix(30.0, 50.0, 0.0)
    lam, phi = np.deg2rad(30.0), np.deg2rad(50.0)
    assert np.allclose(R[:, 2], [np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])


def test_rotation_angle_uses_arctan2():
    for deg in (0.0, 1e-7, 30.0, 90.0, 179.9, 180.0):
        assert np.isclose(rotation_angle_deg(rotation((1, 2, 3), deg)), deg, atol=1e-7)
    R0, R1 = rotation((0, 0, 1), 20), rotation((0, 0, 1), 95)
    assert np.isclose(relative_angle_deg(R0, R1), 75.0)


@pytest.mark.parametrize("total", [20.0, 90.0, 170.0, 179.0])
def test_slerp_endpoints_constant_speed_and_shortest_path(total):
    R0 = rotation((0.3, -0.5, 0.8), 40.0)
    R1 = rotation((1.0, 2.0, -0.5), total) @ R0
    n = 61
    frames = [slerp_matrix(R0, R1, k / (n - 1)) for k in range(n)]
    assert np.abs(frames[0] - R0).max() < 1e-12 and np.abs(frames[-1] - R1).max() < 1e-12
    steps = [relative_angle_deg(a, b) for a, b in zip(frames, frames[1:])]
    assert np.ptp(steps) < 1e-6                              # 等角速度
    assert np.isclose(sum(steps), total, atol=1e-6)          # 总角 = 起终相对旋转角（最短路径，不绕 360°−total）
    # 沿测地线：每帧都是 R0 再绕同一根轴转过 t·total
    axis = np.array([1.0, 2.0, -0.5])
    for k, F in enumerate(frames):
        assert np.abs(F - rotation(axis, total * k / (n - 1)) @ R0).max() < 1e-9


def test_slerp_double_cover_takes_short_way():
    q0 = matrix_to_quat(np.eye(3))
    q1 = matrix_to_quat(rotation((0, 0, 1), 170.0))
    for q in (q1, -q1):                                       # 同一个旋转的两个四元数
        mid = quat_to_matrix(slerp(q0, q, 0.5))
        assert np.isclose(rotation_angle_deg(mid), 85.0, atol=1e-9)
    assert np.allclose(slerp(q0, q1, 0.0), q0) and np.allclose(quat_to_matrix(slerp(q0, -q1, 1.0)), quat_to_matrix(q1))
    # 几乎重合的两个四元数：退化分支仍归一
    q2 = matrix_to_quat(rotation((0, 0, 1), 1e-9))
    assert np.isclose(np.linalg.norm(slerp(q0, q2, 0.3)), 1.0)


def test_lerp_matrix_collapses_in_the_middle():
    R0 = lon_lat_roll_to_matrix(20.0, -75.0, 30.0)
    R1 = lon_lat_roll_to_matrix(200.0, 75.0, -20.0)
    M = lerp_matrix(R0, R1, 0.5)
    assert abs(np.linalg.det(M) - 1.0) > 0.1
    assert np.abs(M.T @ M - np.eye(3)).max() > 0.1
    assert np.allclose(lerp_matrix(R0, R1, 0.0), R0) and np.allclose(lerp_matrix(R0, R1, 1.0), R1)


def test_euler_lerp_and_slerp_take_different_routes():
    pose0, pose1 = (20.0, -75.0, 30.0), (200.0, 75.0, -20.0)
    R0, R1 = lon_lat_roll_to_matrix(*pose0), lon_lat_roll_to_matrix(*pose1)
    E, S = lerp_euler(pose0, pose1, 0.5), slerp_matrix(R0, R1, 0.5)
    assert np.allclose(lerp_euler(pose0, pose1, 0.0), R0) and np.allclose(lerp_euler(pose0, pose1, 1.0), R1)
    assert np.abs(E - S).max() > 0.1                          # 中途姿态不同（用矩阵差范数，不用 arccos）
    assert relative_angle_deg(E, S) > 10.0
    # 欧拉角插值中间帧的 c 轴躺在赤道上（φ 线性经过 0），slerp 的不
    assert abs(matrix_to_lon_lat_roll(E)[1]) < 1e-9
    assert abs(matrix_to_lon_lat_roll(S)[1]) > 1.0


def test_lerp_euler_uses_explicit_poses_at_the_poles():
    """φ=±90° 处经度不定：:func:`lerp_euler` 不反解矩阵，调用方给定的三元组（含非零 λ/θ）必须原样
    参与插值，而不是被 :func:`matrix_to_lon_lat_roll` 的 λ=0 默认解吃掉。"""
    pose0, pose1 = (180.0, -90.0, 0.0), (0.0, 90.0, 0.0)
    R0, R1 = lon_lat_roll_to_matrix(*pose0), lon_lat_roll_to_matrix(*pose1)
    assert np.allclose(lerp_euler(pose0, pose1, 0.0), R0) and np.allclose(lerp_euler(pose0, pose1, 1.0), R1)
    # matrix_to_lon_lat_roll 在两极会给出 λ=0，与我们显式给的 λ=180° 不同——证明真用了三元组而非反解
    assert matrix_to_lon_lat_roll(R0)[0] == 0.0 and pose0[0] != 0.0
