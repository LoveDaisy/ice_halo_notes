"""姿态插值（5.1 用）：旋转矩阵逐元素线性插值（反面教材：中间帧不再正交）、「经度 λ / 纬度 φ /
转角 θ」三参数线性插值（绕远）、单位四元数 slerp（最短路径、等角速度）。

三参数姿态沿用 ch5 正文记号：晶体 c 轴指向经度 λ、纬度 φ 的方向，再绕 c 轴转 θ，即
``R = R_z(λ) · R_y(90° − φ) · R_z(θ)``——与 ch3 的 ``R = R_z(α) R_y(π/2) R_z(θ)`` 在 φ=0 时一致。
纯 numpy 实现，不引入 scipy。
"""

from __future__ import annotations

import numpy as np

from .geometry import rotation

Z_AXIS, Y_AXIS = (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)


# ---- 矩阵 ------------------------------------------------------------------------

def lerp_matrix(R0: np.ndarray, R1: np.ndarray, t: float) -> np.ndarray:
    """逐元素线性插值 ``(1-t)·R0 + t·R1``，**不做任何正交化**——中间帧一般不再是旋转矩阵
    （行列式与 ``RᵀR`` 都偏离），5.1 左栏正是要展示这一点。"""
    return (1.0 - t) * np.asarray(R0, float) + t * np.asarray(R1, float)


def rotation_angle_deg(R: np.ndarray) -> float:
    """旋转矩阵的转角（度）：``trace(R) = 1 + 2cos θ``；用 ``arctan2`` 而不是 ``arccos`` 以免在 0° / 180° 附近失真。"""
    R = np.asarray(R, float)
    cos = (np.trace(R) - 1.0) / 2.0
    sin = np.linalg.norm([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2.0
    return float(np.rad2deg(np.arctan2(sin, cos)))


def relative_angle_deg(R0: np.ndarray, R1: np.ndarray) -> float:
    """从姿态 ``R0`` 转到 ``R1`` 所需的旋转角（度）。"""
    return rotation_angle_deg(np.asarray(R1, float) @ np.asarray(R0, float).T)


# ---- 经度 / 纬度 / 转角 ----------------------------------------------------------------

def lon_lat_roll_to_matrix(lon_deg: float, lat_deg: float, roll_deg: float) -> np.ndarray:
    """``R_z(λ) · R_y(90° − φ) · R_z(θ)``：c 轴（+z）转到经度 λ、纬度 φ 的方向，再绕自身转 θ。"""
    return rotation(Z_AXIS, lon_deg) @ rotation(Y_AXIS, 90.0 - lat_deg) @ rotation(Z_AXIS, roll_deg)


def matrix_to_lon_lat_roll(R: np.ndarray) -> tuple[float, float, float]:
    """:func:`lon_lat_roll_to_matrix` 的逆。c 轴恰在两极（φ = ±90°）时经度不定，取 λ = 0。"""
    R = np.asarray(R, float)
    c = R[:, 2]
    lat = np.rad2deg(np.arcsin(np.clip(c[2], -1.0, 1.0)))
    lon = 0.0 if np.hypot(c[0], c[1]) < 1e-12 else np.rad2deg(np.arctan2(c[1], c[0]))
    Rr = (rotation(Z_AXIS, lon) @ rotation(Y_AXIS, 90.0 - lat)).T @ R   # 应为 R_z(θ)
    roll = np.rad2deg(np.arctan2(Rr[1, 0], Rr[0, 0]))
    return float(lon), float(lat), float(roll)


def lerp_euler(pose0: tuple[float, float, float], pose1: tuple[float, float, float], t: float) -> np.ndarray:
    """对显式给定的起终 ``(λ, φ, θ)`` 三元组各自线性插值再转回矩阵。**不从矩阵反解**——φ=±90° 处
    （c 轴在两极）经度不定，:func:`matrix_to_lon_lat_roll` 会固定取 λ=0，抹掉本该由调用方选择的
    「多余旋转」自由度；三元组由调用方给定并保证精确表示所需的姿态矩阵（自行用
    :func:`lon_lat_roll_to_matrix` 核验）。角度按给定数值直接插（不取模 360°），所以经度差超过
    180° 时会"绕远"——正文说的欧拉角插值路径问题。"""
    a, b = np.array(pose0, float), np.array(pose1, float)
    return lon_lat_roll_to_matrix(*((1.0 - t) * a + t * b))


# ---- 四元数 ------------------------------------------------------------------------

def matrix_to_quat(R: np.ndarray) -> np.ndarray:
    """旋转矩阵 → 单位四元数 ``(w, x, y, z)``（Shepperd 法：按最大分量分支，数值稳定）。"""
    R = np.asarray(R, float)
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.asarray(q, float)
    return q / np.linalg.norm(q)


def quat_to_matrix(q: np.ndarray) -> np.ndarray:
    """单位四元数 ``(w, x, y, z)`` → 旋转矩阵。"""
    w, x, y, z = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def slerp(q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
    """单位四元数球面线性插值。``q`` 与 ``-q`` 是同一个旋转：``q0·q1 < 0`` 时取 ``-q1``，
    保证走最短路径；两者几乎重合时退化为归一化的线性插值。"""
    q0, q1 = np.asarray(q0, float), np.asarray(q1, float)
    dot = float(q0 @ q1)
    if dot < 0:
        q1, dot = -q1, -dot
    if dot > 1 - 1e-12:
        q = (1.0 - t) * q0 + t * q1
        return q / np.linalg.norm(q)
    omega = np.arccos(np.clip(dot, -1.0, 1.0))
    so = np.sin(omega)
    return (np.sin((1.0 - t) * omega) / so) * q0 + (np.sin(t * omega) / so) * q1


def slerp_matrix(R0: np.ndarray, R1: np.ndarray, t: float) -> np.ndarray:
    """矩阵进、矩阵出的 slerp（5.1 右栏）。"""
    return quat_to_matrix(slerp(matrix_to_quat(R0), matrix_to_quat(R1), t))


__all__ = ["lerp_euler", "lerp_matrix", "lon_lat_roll_to_matrix", "matrix_to_lon_lat_roll", "matrix_to_quat",
           "quat_to_matrix", "relative_angle_deg", "rotation_angle_deg", "slerp", "slerp_matrix"]
