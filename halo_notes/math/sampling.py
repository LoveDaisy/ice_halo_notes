"""S² / S³ 均匀采样与最近邻角距离——逐行翻译 ch5 旧脚本 `code/legacy/spherical_distance.m`、`llr_quat_dist.m`。

所有采样函数显式接收 ``rng: numpy.random.Generator``（不用全局种子），fig 脚本自行固定种子以保证 byte-identical。
"""

from __future__ import annotations

import numpy as np


def uniform_s2(n: int, rng: np.random.Generator) -> np.ndarray:
    """S² 上 n 个均匀分布点：三维高斯归一化（正文第 122 行「偷懒的办法」）。返回 (n, 3)。"""
    xyz = rng.standard_normal((n, 3))
    return xyz / np.linalg.norm(xyz, axis=1, keepdims=True)


def uniform_so3_llr(n: int, rng: np.random.Generator) -> np.ndarray:
    """SO(3) 上「均匀」姿态的欧拉角样本 (λ, φ, θ)：主轴方向 (λ, φ) 均匀于 S²、roll θ 均匀于 [0, 2π)。
    返回 (n, 3)，列序与 `llr_quat_dist.m` 第 11 行一致（λ=atan2(y,x)，φ=asin(z)，θ=rand·2π）。"""
    xyz = uniform_s2(n, rng)
    lon = np.arctan2(xyz[:, 1], xyz[:, 0])
    lat = np.arcsin(xyz[:, 2])
    roll = rng.random(n) * 2 * np.pi
    return np.column_stack([lon, lat, roll])


def quat_multiply(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Hamilton 积 p·q，四元数按 (w, x, y, z) 排列，与 MATLAB `quatmultiply(p, q)` 同序。支持 (n, 4) 批量。"""
    p, q = np.asarray(p, float), np.asarray(q, float)
    w1, x1, y1, z1 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    w2, x2, y2, z2 = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ], axis=-1)


def llr_to_quat(llr: np.ndarray) -> np.ndarray:
    """欧拉角 (λ, φ, θ) → 单位四元数 (w, x, y, z)，照抄 `llr_quat_dist.m` 第 13–17 行的三步构造：
    q1 = 绕 z 转 −θ、q2 = 绕 y 转 −(π/2 − φ)（半角写成 π/4 − φ/2）、q3 = 绕 z 转 −λ，q = q1·q2·q3。
    不换成其它欧拉角约定——图要与已发表的吻合。"""
    llr = np.asarray(llr, float)
    lon, lat, roll = llr[:, 0], llr[:, 1], llr[:, 2]
    zero = np.zeros_like(lon)
    q1 = np.column_stack([np.cos(roll / 2), zero, zero, -np.sin(roll / 2)])
    half = np.pi / 4 - lat / 2
    q2 = np.column_stack([np.cos(half), zero, -np.sin(half), zero])
    q3 = np.column_stack([np.cos(lon / 2), zero, zero, -np.sin(lon / 2)])
    return quat_multiply(quat_multiply(q1, q2), q3)


def nearest_neighbor_angle(points: np.ndarray, block: int = 1000) -> np.ndarray:
    """每个点到其最近邻的角距离 acos(max_{j≠i} p_i·p_j)，S²（(n,3)）与 S³（(n,4)）通用。
    旧脚本逐点做 `xyz * xyz(i,:)'`，这里分块矩阵乘（每块 ``block`` 行），语义相同。"""
    pts = np.asarray(points, float)
    n = pts.shape[0]
    if n < 2:
        raise ValueError("need at least two points")
    best = np.empty(n)
    for start in range(0, n, block):
        stop = min(start + block, n)
        dots = pts[start:stop] @ pts.T
        dots[np.arange(stop - start), np.arange(start, stop)] = -1.0  # 排除自身（旧脚本 d2(i) = -1）
        best[start:stop] = dots.max(axis=1)
    return np.arccos(np.clip(best, -1.0, 1.0))


__all__ = ["llr_to_quat", "nearest_neighbor_angle", "quat_multiply", "uniform_s2", "uniform_so3_llr"]
