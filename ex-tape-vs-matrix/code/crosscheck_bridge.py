"""两套语言之间的翻译层——互证脚本 A / B 唯一允许拼符号的地方（源笔记 §5 记号差异表、附录 A.3 / A.4）。

- Tape 侧的输入是楔取向 $u\\in SO(3)$（列 = wedge frame $\\mathbf A,\\mathbf B,\\mathbf C$）与太阳光点 $\\mathbf S$；
  本系列侧的输入是晶体姿态 $R$、折叠 $M$、入 / 出面 $a,b$ 与**入射传播方向** $\\mathbf d$。
- :func:`wedge_orientation`：$u=R\\,u_0$，$u_0$ 由 TK1999 Eq. (8) 以 $\\mathbf N=\\mathbf n_a$、$\\mathbf X=-\\tilde{\\mathbf n}_b=-M^{-1}\\mathbf n_b$
  算出（源笔记 §5「取向参数化」行、附录 A.1 第 6 步）。
- :func:`light_point`：$\\mathbf H=-R\\,\\Phi(-R^{-1}\\mathbf S)$——光点 = $-$出射方向、入射方向 = $-$太阳方向（源笔记 §5「光线 vs 光点」行；
  `docs/framework.md` 定理 8 写的 $R\\Phi(R^{-1}\\mathbf s)$ 少两个负号，源笔记 §7 第 7 条已上抛，本文件按严格写法）。
- :func:`s_centered`：TK1999 的 S-centered 坐标 $(\\Delta,\\tau)$ [TK1999 p.16–17 Eq. (53)]。

姿态族与采样：:func:`plate_attitude`（片晶 $R=\\mathrm{zrot}(\\phi)$，$\\mathbf n_1=\\mathbf k$）、
`halo_notes.math.attitude.column_attitude`（柱晶）、:func:`haar_so3`（QR 分解 Haar 均匀 $SO(3)$）、
`halo_notes.math.sampling.uniform_s2`（$S^2$）。
"""

from __future__ import annotations

import math

import numpy as np
from lumice_integral.geometry import Polyhedron

from halo_notes.math.reflection_group import Rz
from halo_notes.math.signature import phi_batch
from tape_halo_function import orientation_from_normals


# ---- 取向换算 ----------------------------------------------------------------------


def unfolded_normals(crystal: Polyhedron, M: np.ndarray, a: int, b: int) -> tuple[np.ndarray, np.ndarray]:
    """晶体系里的 $(\\mathbf N,\\mathbf X)=(\\mathbf n_a,\\ -M^{-1}\\mathbf n_b)$：入射面外法向、展开后出射面**内**法向。"""
    n_a, n_b = crystal.normal(crystal.face(a)), crystal.normal(crystal.face(b))
    return np.asarray(n_a, float), -(np.asarray(M, float).T @ np.asarray(n_b, float))


def wedge_orientation(crystal: Polyhedron, M: np.ndarray, a: int, b: int, R: np.ndarray) -> np.ndarray:
    """晶体姿态 $R$ → TK1999 楔取向 $u=R\\,u_0$；$u_0$ = 楔 $ab$ 在晶体系里的 wedge frame [TK1999 p.4 Eq. (8)]。
    ``R`` 可为 ``(3, 3)`` 或 ``(K, 3, 3)``。"""
    u0 = orientation_from_normals(*unfolded_normals(crystal, M, a, b))
    return np.asarray(R, float) @ u0


# ---- 光点 --------------------------------------------------------------------------


def light_point_batch(crystal: Polyhedron, M: np.ndarray, a: int, b: int, R: np.ndarray, S: np.ndarray) -> np.ndarray:
    """本系列侧光点，批量：``R (K, 3, 3)`` 或 ``(3, 3)``，``S (K, 3)`` 或 ``(3,)`` → ``(K, 3)``，定义域外的行为 ``NaN``
    （与 :func:`halo_notes.math.signature.phi_batch` 同语义）。$\\mathbf H_i=-R_i\\,\\Phi(-R_i^{T}\\mathbf S_i)$。"""
    R = np.asarray(R, float)
    S = np.asarray(S, float)
    if R.ndim == 2:
        R = R[None]
    if S.ndim == 1:
        S = S[None]
    K = max(R.shape[0], S.shape[0])
    R = np.broadcast_to(R, (K, 3, 3))
    S = np.broadcast_to(S, (K, 3))
    d = -np.einsum("kji,kj->ki", R, S)                       # -R^T S，逐行
    out = phi_batch(crystal, M, a, b, d)
    return -np.einsum("kij,kj->ki", R, out)                  # -R Φ(d)


def light_point(crystal: Polyhedron, M: np.ndarray, a: int, b: int, R: np.ndarray, S: np.ndarray) -> np.ndarray | None:
    """本系列侧光点 $\\mathbf H=-R\\,\\Phi(-R^{-1}\\mathbf S)$，单个姿态 / 太阳方向；定义域外返回 ``None``。"""
    o = light_point_batch(crystal, M, a, b, R, S)[0]
    return None if np.isnan(o).any() else o


# ---- 天球坐标 ----------------------------------------------------------------------


def angular_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """两组单位向量的逐行角距离（弧度）：$2\\arcsin(|\\mathbf a-\\mathbf b|/2)$——不用 $\\arccos(\\mathbf a\\cdot\\mathbf b)$，
    后者在夹角趋于 0 时浮点分辨率只有 $\\sim10^{-8}$（`scratchpad/learnings.md` code-quality）。任一侧含 ``NaN`` 的行给 ``NaN``。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    half = 0.5 * np.linalg.norm(np.atleast_2d(a) - np.atleast_2d(b), axis=1)
    return 2.0 * np.arcsin(np.clip(half, 0.0, 1.0))


K_HAT = np.array([0.0, 0.0, 1.0])
"""天顶 $\\mathbf k$ [TK1999 p.2]。"""


def s_centered(S: np.ndarray, H: np.ndarray) -> tuple[float, float]:
    """S-centered 坐标 $(\\Delta,\\tau)$（度）[TK1999 p.16–17 Eq. (53)]：$\\Delta$ = 到太阳的角距；$\\tau$ = 从太阳量起的 bearing，
    12:00（朝天顶）为 0，从天球**内部**看顺时针为正（3:00 = 90°，与 TM2006 p.231 的 compass bearing 一致）。
    从球心望向 $\\mathbf S$、以 $\\mathbf k$ 为上时，右手边是 $\\mathbf S\\times\\mathbf e_{\\uparrow}$。"""
    S, H = np.asarray(S, float), np.asarray(H, float)
    delta = math.degrees(math.acos(max(-1.0, min(1.0, float(S @ H)))))
    up = K_HAT - (K_HAT @ S) * S
    up /= np.linalg.norm(up)
    right = np.cross(S, up)
    tau = math.degrees(math.atan2(float(H @ right), float(H @ up)))
    return delta, tau


# ---- 姿态族与采样 ------------------------------------------------------------------


def plate_attitude(phi_deg: float) -> np.ndarray:
    """片晶姿态 $R=\\mathrm{zrot}(\\phi)$：$\\mathbf n_1=\\mathbf c$ 已是 $+z$，只差绕竖直的方位角（TK1999 point halo 的陪集 $Zu_0$）。"""
    return Rz(phi_deg)


def sun_direction(sigma_deg: float, azimuth_deg: float = 0.0) -> np.ndarray:
    """太阳光点 $\\mathbf S$：高度 $\\Sigma$、方位角（从 $+x$ 逆时针）。默认在 $xz$ 平面内（Tape 1980 p.4 的放法）。"""
    s, a = math.radians(sigma_deg), math.radians(azimuth_deg)
    return np.array([math.cos(s) * math.cos(a), math.cos(s) * math.sin(a), math.sin(s)])


def haar_so3(n: int, rng: np.random.Generator) -> np.ndarray:
    """Haar 均匀的 $SO(3)$ 样本 ``(n, 3, 3)``：高斯矩阵 QR 分解，按 $R$ 对角符号修正后取 $\\det=+1$。"""
    out = np.empty((n, 3, 3))
    for i in range(n):
        q, r = np.linalg.qr(rng.standard_normal((3, 3)))
        q = q * np.sign(np.diag(r))                         # 消除 QR 的符号歧义，使分布为 Haar
        if np.linalg.det(q) < 0:
            q[:, 0] = -q[:, 0]
        out[i] = q
    return out


__all__ = [
    "K_HAT", "angular_distance", "haar_so3", "light_point", "light_point_batch", "plate_attitude", "s_centered", "sun_direction",
    "unfolded_normals", "wedge_orientation",
]
