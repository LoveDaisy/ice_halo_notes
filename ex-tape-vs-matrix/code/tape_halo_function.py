"""Tape 的 halo function（取向 + 楔 → 天球光点）：两条互相独立的公式链路，逐条照抄 `源笔记-Tape.md` 附录 A。

- A.1 TK1999 路线（Tape & Können 1999 *A general setting for halo theory*）：Snell 定律写成平行投影 ``pr``，
  光点 $\\mathbf H=\\mathrm{pr}[\\mathrm{pr}(\\mathbf S,\\mathbf N,n),\\mathbf X,1]$——完整三维实现。
- A.2 Tape 1980 路线（*Analytic foundations of halo theory*）：Bravais 定律把三维折射化到 normal plane，
  只实现到「幻日内边角距」这一个标量链路（$n'$、$D$、$\\mu_M$、$D_{\\min}$、$\\Delta$），作为第二条不共享失败模式的校验。

本文件**只用 Tape 的语言**，不 import ``halo_notes``；与本系列 $\\Phi$ 的换算全部在 ``crosscheck_bridge.py``。
角度一律用度（Tape 1980 p.2 的约定），向量用 numpy。全文 $n=1.31$ [TK1999 p.3]。
"""

from __future__ import annotations

import math

import numpy as np

N_ICE = 1.31
"""折射率，TK1999 全文取 1.31 [TK1999 p.3]；Tape 1980 图中亦取 1.31 [Tape1980 p.1]。"""


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


# ---- A.1 TK1999 路线 -------------------------------------------------------------------


def wedge_frame(N: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """wedge frame $(\\mathbf A,\\mathbf B,\\mathbf C)$ [TK1999 p.3 Eq. (8)]：
    $\\mathbf A=\\widehat{\\mathbf N+\\mathbf X}$，$\\mathbf B=\\widehat{\\mathbf N\\times\\mathbf X}$，$\\mathbf C=\\widehat{\\mathbf N-\\mathbf X}$。
    ``N`` 入射面外法向、``X`` 出射面内法向（"N for eNtry, X for eXit"）。"""
    N, X = np.asarray(N, float), np.asarray(X, float)
    return _unit(N + X), _unit(np.cross(N, X)), _unit(N - X)


def standard_normals(alpha_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """standard orientation 下的法向 [TK1999 p.4 Eq. (10)]：
    $\\mathbf N_0=[\\cos(\\alpha/2),0,\\sin(\\alpha/2)]$，$\\mathbf X_0=[\\cos(\\alpha/2),0,-\\sin(\\alpha/2)]$，$\\alpha$ 为楔角。"""
    h = math.radians(alpha_deg) / 2
    return np.array([math.cos(h), 0.0, math.sin(h)]), np.array([math.cos(h), 0.0, -math.sin(h)])


def orientation_from_normals(N: np.ndarray, X: np.ndarray) -> np.ndarray:
    """由法向对 $(\\mathbf N,\\mathbf X)$ 得取向矩阵 $u$：$u$ 的列就是 wedge frame $\\mathbf A,\\mathbf B,\\mathbf C$
    [TK1999 p.4]，满足 $u\\mathbf N_0=\\mathbf N$、$u\\mathbf X_0=\\mathbf X$ [Eq. (9)]。"""
    A, B, C = wedge_frame(N, X)
    return np.column_stack([A, B, C])


def pr(S: np.ndarray, N: np.ndarray, n2: float, n1: float = 1.0) -> np.ndarray | None:
    """$\\mathbf N$-projection [TK1999 p.2 Eqs. (2)–(3)]：$\\mathrm{pr}(\\mathbf S,\\mathbf N,n_2)=\\mathbf S+\\lambda\\mathbf N$，
    $\\lambda=[(\\mathbf S\\cdot\\mathbf N)^2+n_2^2-n_1^2]^{1/2}-\\mathbf S\\cdot\\mathbf N$，$|\\mathbf S|=n_1$、$|\\mathbf N|=1$。
    定义条件 [TK1999 p.3]：$\\mathbf S\\cdot\\mathbf N\\ge0$（从要求的一侧入射）且根号内 $\\ge0$（有透射光），否则返回 ``None``。"""
    S, N = np.asarray(S, float), np.asarray(N, float)
    c = float(S @ N)
    k = c * c + n2 * n2 - n1 * n1
    if c < 0.0 or k < 0.0:
        return None
    return S + (math.sqrt(k) - c) * N


def halo_point_wedge(N: np.ndarray, X: np.ndarray, S: np.ndarray, n: float = N_ICE) -> np.ndarray | None:
    """$\\mathbf H=\\mathbf F(\\mathbf N,\\mathbf X,\\mathbf S)=\\mathrm{pr}[\\mathrm{pr}(\\mathbf S,\\mathbf N,n),\\mathbf X,1]$
    [TK1999 p.3 Eqs. (6)–(7)]：先投到半径 $n$ 的球（楔内光点 $\\mathbf T$），再投回单位球。无定义 → ``None``（"no ray"）。"""
    T = pr(S, N, n, 1.0)
    if T is None:
        return None
    return pr(T, X, 1.0, n)


def halo_point(u: np.ndarray, alpha_deg: float, S: np.ndarray, n: float = N_ICE) -> np.ndarray | None:
    """$\\mathbf H(u,\\alpha,\\mathbf S)=\\mathbf F(u\\mathbf N_0,u\\mathbf X_0,\\mathbf S)$ [TK1999 p.4 Eqs. (9), (11)]。"""
    N0, X0 = standard_normals(alpha_deg)
    u = np.asarray(u, float)
    return halo_point_wedge(u @ N0, u @ X0, S, n)


def _pr_batch(S: np.ndarray, N: np.ndarray, n2: float, n1: float) -> np.ndarray:
    """:func:`pr` 的逐行批量版：``S (K, 3)``、``N (K, 3)`` 或 ``(3,)``；无定义的行为 ``NaN``。"""
    S = np.asarray(S, float)
    N = np.broadcast_to(np.asarray(N, float), S.shape)
    c = np.einsum("ij,ij->i", S, N)
    k = c * c + n2 * n2 - n1 * n1
    ok = (c >= 0.0) & (k >= 0.0)
    lam = np.where(ok, np.sqrt(np.where(ok, k, 0.0)) - c, np.nan)
    return S + lam[:, None] * N


def halo_point_batch(u: np.ndarray, alpha_deg: float, S: np.ndarray, n: float = N_ICE) -> np.ndarray:
    """:func:`halo_point` 的批量版：``u (K, 3, 3)`` 或 ``(3, 3)``，``S (K, 3)`` 或 ``(3,)`` → ``(K, 3)``，"no ray" 的行为 ``NaN``。"""
    N0, X0 = standard_normals(alpha_deg)
    u = np.asarray(u, float)
    S = np.asarray(S, float)
    if u.ndim == 2:
        u = u[None]
    if S.ndim == 1:
        S = S[None]
    K = max(u.shape[0], S.shape[0])
    u = np.broadcast_to(u, (K, 3, 3))
    S = np.broadcast_to(S, (K, 3))
    N, X = u @ N0, u @ X0                                     # 逐行 u_i N_0、u_i X_0
    T = _pr_batch(S, N, n, 1.0)
    return _pr_batch(T, X, 1.0, n)


def min_deviation_tk(alpha_deg: float, n: float = N_ICE) -> float:
    """最小偏折 $\\Delta_m$ [TK1999 p.9 Eq. (41)]：$\\sin[(\\alpha+\\Delta_m)/2]=n\\sin(\\alpha/2)$（度）。"""
    return 2 * math.degrees(math.asin(n * math.sin(math.radians(alpha_deg) / 2))) - alpha_deg


def deviation_deg(S: np.ndarray, H: np.ndarray) -> float:
    """真实偏折 $\\Delta=\\arccos(\\mathbf S\\cdot\\mathbf H)$ [TK1999 p.9 Eq. (40)]（度；两侧均为单位向量）。"""
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.asarray(S, float) @ np.asarray(H, float))))))


def zrot(phi_deg: float) -> np.ndarray:
    """绕 $z$（天顶 $\\mathbf k$）转 ``phi_deg`` 度，TK1999 的 $\\mathrm{zrot}(\\phi)$ [TK1999 p.7 Eq. (29)]。"""
    t = math.radians(phi_deg)
    return np.array([[math.cos(t), -math.sin(t), 0.0], [math.sin(t), math.cos(t), 0.0], [0.0, 0.0, 1.0]])


# ---- A.2 Tape 1980 路线（Bravais 定律）--------------------------------------------------


def bravais_index(theta_deg: float, n: float = N_ICE) -> float:
    """Bravais 折射率 $n'(\\theta)=(n^2-\\cos^2\\theta)^{1/2}/\\sin\\theta$ [Tape1980 p.2]，$\\theta$ 为轴向量 $\\hat{\\mathbf P}$
    与 $-\\hat{\\mathbf I}$（太阳方向）的夹角。"""
    t = math.radians(theta_deg)
    return math.sqrt(n * n - math.cos(t) ** 2) / math.sin(t)


def normal_plane_deviation(theta_deg: float, mu_deg: float, alpha_deg: float, n: float = N_ICE) -> float:
    """normal plane 内的偏折 $D(\\theta,\\mu)$ [Tape1980 p.2 Eqs. (1)–(4)]：
    $\\sin r=\\sin\\mu/n'$，$\\mu'=r+\\alpha$，$\\sin r'=n'\\sin\\mu'$，$D=\\alpha+\\mu-r'$（度，恒负 [Eq. (12)]）。
    定义域外（$\\sin r'$ 超界，即掠出射之外）抛 ``ValueError``。"""
    np_ = bravais_index(theta_deg, n)
    r = math.degrees(math.asin(math.sin(math.radians(mu_deg)) / np_))
    mu_p = r + alpha_deg
    s = np_ * math.sin(math.radians(mu_p))
    if abs(s) > 1.0:
        raise ValueError(f"(theta={theta_deg}, mu={mu_deg}) outside the domain of D: sin r' = {s:.4f}")
    return alpha_deg + mu_deg - math.degrees(math.asin(s))


def grazing_exit_mu(theta_deg: float, alpha_deg: float, n: float = N_ICE) -> float:
    """掠出射的投影入射角 $\\mu_L(\\theta)$ [Tape1980 p.2 Eq. (6)]：
    $\\sin\\mu_L=\\cos\\alpha-(n^2-1)^{1/2}\\sin\\alpha/\\sin\\theta$（度）。"""
    a, t = math.radians(alpha_deg), math.radians(theta_deg)
    return math.degrees(math.asin(math.cos(a) - math.sqrt(n * n - 1) * math.sin(a) / math.sin(t)))


def min_theta(alpha_deg: float, n: float = N_ICE) -> float:
    """$\\theta_{\\min}$ [Tape1980 p.2 Eq. (6)]：$\\sin\\theta_{\\min}=(n^2-1)^{1/2}\\tan(\\alpha/2)$（度）；= TK1999 Eq. (48) 的 $\\theta_0$。"""
    return math.degrees(math.asin(math.sqrt(n * n - 1) * math.tan(math.radians(alpha_deg) / 2)))


def min_deviation_mu(theta_deg: float, alpha_deg: float, n: float = N_ICE) -> float:
    """固定 $\\theta$ 时 $D$ 取极值的 $\\mu_M(\\theta)$ [Tape1980 p.2 Eq. (10)]：$\\sin\\mu_M=-n'(\\theta)\\sin(\\alpha/2)$（度）。"""
    return math.degrees(math.asin(-bravais_index(theta_deg, n) * math.sin(math.radians(alpha_deg) / 2)))


def min_deviation_D(theta_deg: float, alpha_deg: float, n: float = N_ICE) -> float:
    """$D_{\\min}(\\theta)=\\alpha+2\\mu_M(\\theta)$ [Tape1980 p.2 Eq. (11)]（度，负值：$|D|$ 的最小 [p.18 note 17]）。"""
    return alpha_deg + 2 * min_deviation_mu(theta_deg, alpha_deg, n)


def true_deviation(theta_deg: float, D_deg: float) -> float:
    """真实偏折 $\\Delta$ [Tape1980 p.3 Eq. (15)]：$\\sin(\\Delta/2)=-\\sin\\theta\\sin(D/2)$（度，$0\\le\\Delta\\le180$）。"""
    return 2 * math.degrees(math.asin(-math.sin(math.radians(theta_deg)) * math.sin(math.radians(D_deg) / 2)))


def sundog_inner_edge_1980(sigma_deg: float, alpha_deg: float = 60.0, n: float = N_ICE) -> float:
    """太阳高度 $\\Sigma$ 下幻日内边到太阳的角距 [Tape1980 p.16；源笔记 §6.1 公式链]：
    $\\hat{\\mathbf P}$ 竖直 ⇒ $\\theta=90-\\Sigma$，$\\Delta=\\Delta(\\theta,\\mu_M(\\theta))$ 由 Eqs. (10)(11)(15) 得。"""
    theta = 90.0 - sigma_deg
    return true_deviation(theta, min_deviation_D(theta, alpha_deg, n))


__all__ = [
    "N_ICE", "bravais_index", "deviation_deg", "grazing_exit_mu", "halo_point", "halo_point_batch",
    "halo_point_wedge", "min_deviation_D", "min_deviation_mu", "min_deviation_tk", "min_theta",
    "normal_plane_deviation", "orientation_from_normals", "pr", "standard_normals", "sundog_inner_edge_1980",
    "true_deviation", "wedge_frame", "zrot",
]
