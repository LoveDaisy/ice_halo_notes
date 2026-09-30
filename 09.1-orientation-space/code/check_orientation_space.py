# 核验 9.1 番外提纲的数字：ZYZ 欧拉角均匀网格在极点过密（体积元 ∝ sinβ），柱晶族是嵌入 SO(3) 的环面 T²
# 且 Haar 在其上诱导均匀测度，各姿态族的维数，(u, θ) 坐标下 Haar = du dθ（u 均匀、θ 均匀、二者独立），
# 以及姿态族的包含关系（片晶、Parry ⊂ Lowitz 环面，Parry = 柱晶 ∩ Lowitz，D6 意义下）。
import argparse
import sys

import numpy as np
from scipy import stats
from scipy.spatial.transform import Rotation

from lumice_integral.pose_density import c_axis_roll, c_axis_zenith
from lumice_integral.so3 import haar_rotations
from lumice_integral.so3 import rotation_distances
from lumice_integral.symmetry.attitude import Ry, column_attitude
from lumice_integral.symmetry.reflection_group import Rz

SEED = 20260927
N_HAAR = 400_000     # Haar 样本数：秒级；卡方 / KS 在此规模下对 1% 级偏差已敏感
POLE_DEG = 10.0      # 检验 1 的近极点桶 β∈[0°, 10°]
GRID = 37            # 检验 2 柱晶网格 37×37（步长 10°，含 0°/360° 端点以检周期性）
BAND_DEG = 5.0       # 检验 2(c) 从 Haar 样本里筛 |zenith−90°| < 5° 的赤道带
P_MIN = 1e-3         # 统计检验判据：p > 0.001 视为与均匀 / 独立相容
H = 1e-6             # 数值 Jacobian 差分步长（弧度）


def rng():
    return np.random.default_rng(SEED)


def body_jacobian(param_to_R, x):
    """参数 x ↦ R 的 Jacobian，列 = vee(Rᵀ ∂R/∂x_i)（左不变度量下的体坐标，Haar 体积元 = |det|）。"""
    x = np.asarray(x, float)
    R = param_to_R(x)
    cols = []
    for i in range(len(x)):
        dx = np.zeros_like(x)
        dx[i] = H
        dR = (param_to_R(x + dx) - param_to_R(x - dx)) / (2 * H)
        W = R.T @ dR
        cols.append([W[2, 1], W[0, 2], W[1, 0]])
    return np.array(cols).T


def smoke():
    """5 个复用函数先各跑一次，签名不符在此处提前失败。"""
    R = haar_rotations(3, rng())
    print(f"[smoke] haar_rotations(3) -> {np.asarray(R).shape}")
    C = column_attitude(30.0, 40.0)
    print(f"[smoke] column_attitude(30, 40) -> {C.shape}, zenith={np.degrees(c_axis_zenith(C)):.6f}°, "
          f"roll={np.degrees(c_axis_roll(C)):.6f}° (应 = θ+180° ≡ -140°)")
    d = rotation_distances(C, np.stack([C, column_attitude(30.0, 50.0)]))
    print(f"[smoke] rotation_distances -> {np.degrees(d).round(6)}°")
    assert np.asarray(R).shape == (3, 3, 3)
    assert abs(np.degrees(c_axis_zenith(C)) - 90) < 1e-9
    assert abs(np.degrees(c_axis_roll(C)) - (-140.0)) < 1e-9
    assert abs(d[0]) < 1e-7 and abs(np.degrees(d[1]) - 10) < 1e-9


def check_euler():
    print("\n[1] ZYZ 欧拉角：均匀网格 vs Haar")
    zyz = lambda x: Rz(np.degrees(x[0])) @ Ry(np.degrees(x[1])) @ Rz(np.degrees(x[2]))
    # (a) 体积元：|det J| = sinβ，β=0 处秩降为 2（与万向节锁死同一处）
    print("    β(°)   |det J|    sinβ      rank J")
    for b in (0.0, 1.0, 10.0, 45.0, 90.0, 170.0, 180.0):
        J = body_jacobian(zyz, [0.3, np.radians(b), 1.1])
        det, s = abs(np.linalg.det(J)), np.sin(np.radians(b))
        rank = np.linalg.matrix_rank(J, tol=1e-6)
        print(f"    {b:5.1f}  {det:.6f}  {s:.6f}  {rank}")
        assert abs(det - s) < 1e-6
        assert rank == (2 if b in (0.0, 180.0) else 3)
    # (b) naive 网格：α, β, γ 各自均匀（β 不按 sinβ 加权）vs Haar 样本经 as_euler('ZYZ') 取 β
    g = rng()
    beta_naive = g.uniform(0, np.pi, N_HAAR)
    beta_haar = Rotation.from_matrix(haar_rotations(N_HAAR, rng())).as_euler("ZYZ")[:, 1]
    edges = np.radians(np.arange(0, 181, POLE_DEG))
    f_naive = np.histogram(beta_naive, edges)[0] / N_HAAR
    f_haar = np.histogram(beta_haar, edges)[0] / N_HAAR
    exp_naive = np.diff(edges) / np.pi
    exp_haar = -np.diff(np.cos(edges)) / 2
    print("    β 桶(°)     naive 份额  Haar 份额  比值(样本)  比值(解析)")
    for k in range(len(edges) - 1):
        print(f"    {np.degrees(edges[k]):5.0f}–{np.degrees(edges[k+1]):3.0f}  {f_naive[k]:.5f}    {f_haar[k]:.5f}   "
              f"{f_naive[k]/f_haar[k]:7.3f}    {exp_naive[k]/exp_haar[k]:7.3f}")
    pole = f_naive[0] / f_haar[0]
    pole_exact = exp_naive[0] / exp_haar[0]
    eq = f_naive[len(f_naive) // 2] / f_haar[len(f_haar) // 2]
    print(f"    近极点桶 β∈[0°,{POLE_DEG:.0f}°]：naive/Haar = {pole:.3f}（解析 {pole_exact:.3f}）；"
          f"赤道桶 = {eq:.3f}（解析 {exp_naive[9]/exp_haar[9]:.3f}）")
    # 份额比在 β→0 按 2/(πβ) 发散：这就是「反向换元的 1/sinβ」
    assert pole > 3 and abs(pole - pole_exact) / pole_exact < 0.05
    # (c) 过密倍数不是普适常数：极冠带 β∈[0, δ] 的份额比 (δ/π)/((1−cosδ)/2) ≈ 4/(πδ)，与带宽成反比、δ→0 发散
    print("    极冠带宽 δ(°)  份额比(解析)  4/(πδ)")
    caps = (20.0, 10.0, 5.0, 1.0, 0.1)
    ratios = []
    for dd in caps:
        d = np.radians(dd)
        r = (d / np.pi) / ((1 - np.cos(d)) / 2)
        ratios.append(r)
        print(f"    {dd:10.1f}     {r:9.3f}    {4 / (np.pi * d):9.3f}")
        assert dd > 10 or abs(r - 4 / (np.pi * d)) / r < 0.01
    assert all(a < b for a, b in zip(ratios, ratios[1:]))
    assert stats.chisquare(np.histogram(beta_haar, edges)[0], exp_haar * N_HAAR).pvalue > P_MIN


def check_column():
    print("\n[2] 柱晶族 (ψ, θ) ↦ R_z(ψ)R_y(90°)R_z(θ)：单射性、嵌入、Haar 诱导测度")
    step = 360.0 / (GRID - 1)
    grid = [(i * step, j * step) for i in range(GRID) for j in range(GRID)]
    Rs = np.stack([column_attitude(p, t) for p, t in grid])
    # (a) 单射性：端点 0°/360° 应重合（周期），其余点两两不重合、最近邻 ≈ 网格步长
    interior = np.array([i < GRID - 1 and j < GRID - 1 for i in range(GRID) for j in range(GRID)])
    R_in = Rs[interior]
    nn = np.array([np.min(rotation_distances(R_in[i], np.delete(R_in, i, axis=0))) for i in range(len(R_in))])
    wrap = max(float(rotation_distances(column_attitude(0, t), column_attitude(360, t)[None])[0]) for t in (0, 90, 200))
    print(f"    内部网格 {GRID-1}×{GRID-1}={len(R_in)} 点，最近邻测地距离 min/max = "
          f"{np.degrees(nn.min()):.4f}° / {np.degrees(nn.max()):.4f}°（步长 {step:.1f}°）；0°↔360° 端点距离 {wrap:.1e}")
    assert np.degrees(nn.min()) > 0.5 * step and wrap < 1e-9
    # 秩：(ψ, θ) 处处秩 2（浸入），体积元 |det(JᵀJ)|^½ 恒定 → Haar 诱导的面积元均匀
    col = lambda x: column_attitude(np.degrees(x[0]), np.degrees(x[1]))
    areas = []
    for p, t in [(0, 0), (37, 111), (200, 290), (359, 5)]:
        J = body_jacobian(col, [np.radians(p), np.radians(t)])
        areas.append(np.sqrt(np.linalg.det(J.T @ J)))
        assert np.linalg.matrix_rank(J, tol=1e-6) == 2
    print(f"    Jacobian 秩 = 2（4 个抽查点），面积元 √det(JᵀJ) = {np.round(areas, 6)}（恒定 ⇒ 诱导测度均匀）")
    assert np.ptp(areas) < 1e-6
    # (b) 嵌入自检：全部网格点 zenith = 90°
    zen = np.degrees([c_axis_zenith(R) for R in Rs])
    print(f"    网格点 c 轴天顶角 max|zenith−90°| = {np.max(np.abs(zen - 90)):.1e}°")
    assert np.max(np.abs(zen - 90)) < 1e-9
    # (c) Haar 样本筛赤道带，(方位, roll) 两边际均匀、彼此独立
    R = haar_rotations(N_HAAR, rng())
    z = np.degrees([c_axis_zenith(r) for r in R])
    band = R[np.abs(z - 90) < BAND_DEG]
    az = np.arctan2(band[:, 1, 2], band[:, 0, 2]) % (2 * np.pi)          # c 轴 R e₃ 的方位角
    roll = np.array([c_axis_roll(r) for r in band]) % (2 * np.pi)
    ks_az = stats.kstest(az / (2 * np.pi), "uniform").pvalue
    ks_roll = stats.kstest(roll / (2 * np.pi), "uniform").pvalue
    table = np.histogram2d(az, roll, bins=12, range=[[0, 2 * np.pi]] * 2)[0]
    p_ind = stats.chi2_contingency(table).pvalue
    print(f"    赤道带 |zenith−90°|<{BAND_DEG:.0f}°：{len(band)} 个样本（期望份额 sin{BAND_DEG:.0f}° = "
          f"{np.sin(np.radians(BAND_DEG)):.4f}，实测 {len(band)/N_HAAR:.4f}）")
    print(f"    KS 均匀：方位 p = {ks_az:.3f}，roll p = {ks_roll:.3f}；12×12 独立性卡方 p = {p_ind:.3f}")
    assert min(ks_az, ks_roll, p_ind) > P_MIN


def check_families():
    print("\n[3] 各姿态族的维数（参数化 → SO(3) 的 Jacobian 秩）")
    # 片晶：c 轴竖直，绕竖直轴转 φ → 一条圆（ZYZ 中 β=0，α、γ 合并为一个角）
    fams = {
        "片晶  R_z(φ)": (lambda x: Rz(np.degrees(x[0])), [0.7]),
        "Parry R_z(ψ)R_y(90°)R_z(θ₀)，θ₀ 锁定": (lambda x: column_attitude(np.degrees(x[0]), 180.0), [0.7]),
        "柱晶  R_z(ψ)R_y(90°)R_z(θ)": (lambda x: column_attitude(np.degrees(x[0]), np.degrees(x[1])), [0.7, 1.9]),
        "Lowitz R_z(φ)R_y(t)，绕长对角线 e₂ 摆 t": (lambda x: Rz(np.degrees(x[0])) @ Ry(np.degrees(x[1])), [0.7, 0.4]),
        "随机  ZYZ(α,β,γ)": (lambda x: Rz(np.degrees(x[0])) @ Ry(np.degrees(x[1])) @ Rz(np.degrees(x[2])), [0.7, 1.0, 2.0]),
    }
    ranks = {}
    for name, (f, x0) in fams.items():
        ranks[name] = int(np.linalg.matrix_rank(body_jacobian(f, x0), tol=1e-6))
        print(f"    {name:42s} 维数 = {ranks[name]}")
    assert list(ranks.values()) == [1, 1, 2, 2, 3]
    # Lowitz 族 = {R : R e₂ 水平}，与柱晶族 {R : R e₃ 水平} 同构（换一根体轴）；(φ, t) 同样单射
    L = np.stack([Rz(p) @ Ry(t) for p in range(0, 360, 10) for t in range(0, 360, 10)])
    e2_z = np.abs(L[:, 2, 1]).max()
    nn = min(np.min(rotation_distances(L[i], np.delete(L, i, axis=0))) for i in range(len(L)))
    print(f"    Lowitz 全摆幅 (φ,t)∈[0,360)² 网格：max|(R e₂)_z| = {e2_z:.1e}，最近邻 min = {np.degrees(nn):.4f}°（步长 10°）")
    assert e2_z < 1e-12 and np.degrees(nn) > 5


def min_rotation_to(u, t):
    """把每个 u（(N, 3) 单位向量）沿大圆最短地转到 t 的旋转（Rodrigues）；u = −t 处无定义（零测集）。"""
    k = np.cross(u, t)
    c = u @ t
    K = np.zeros((len(u), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 2] = -k[:, 2], k[:, 1], -k[:, 0]
    K -= K.transpose(0, 2, 1)
    return np.eye(3) + K + K @ K / (1 + c)[:, None, None]


def check_u_theta():
    print("\n[4] (u, θ) 坐标：u = Rᵀŝ ∈ S²，θ = 绕 ŝ 的转角")
    s = np.array([0.0, 0.0, 1.0])
    R = haar_rotations(N_HAAR, rng())
    u = R.transpose(0, 2, 1) @ s                                   # (N, 3)

    M = R @ min_rotation_to(u, s).transpose(0, 2, 1)                               # 固定 ŝ，= 绕 ŝ 转 θ
    theta = np.arctan2(M[:, 1, 0], M[:, 0, 0]) % (2 * np.pi)
    fix = np.max(np.abs(M @ s - s))
    uz, uaz = u[:, 2], np.arctan2(u[:, 1], u[:, 0]) % (2 * np.pi)
    ks = {"u_z~U(-1,1)": stats.kstest((uz + 1) / 2, "uniform").pvalue,
          "u 方位~U(0,2π)": stats.kstest(uaz / (2 * np.pi), "uniform").pvalue,
          "θ~U(0,2π)": stats.kstest(theta / (2 * np.pi), "uniform").pvalue}
    p_z = stats.chi2_contingency(np.histogram2d(uz, theta, bins=12, range=[[-1, 1], [0, 2 * np.pi]])[0]).pvalue
    p_a = stats.chi2_contingency(np.histogram2d(uaz, theta, bins=12, range=[[0, 2 * np.pi]] * 2)[0]).pvalue
    print(f"    RR₀(u)⁻¹ 固定 ŝ：max|Mŝ−ŝ| = {fix:.1e}")
    print("    KS 均匀：" + "，".join(f"{k} p = {v:.3f}" for k, v in ks.items()))
    print(f"    独立性 12×12 卡方：(u_z, θ) p = {p_z:.3f}，(u 方位, θ) p = {p_a:.3f}")
    assert fix < 1e-9 and min(*ks.values(), p_z, p_a) > P_MIN
    # 参考转角没有全局无奇点的取法：R₀(u) 相对于 −ŝ 附近光滑的局部截面，绕 −ŝ 一圈转角卷绕 2 圈
    # （SO(3)→S² 是 S² 的单位切丛，Euler 数 2；对比柱晶 T² 是 S¹ 上的平凡丛）
    phi = np.linspace(0, 2 * np.pi, 721)
    eps = np.radians(5.0)
    loop = np.column_stack([np.sin(eps) * np.cos(phi), np.sin(eps) * np.sin(phi), -np.cos(eps) * np.ones_like(phi)])
    flip = np.diag([1.0, -1.0, -1.0])                               # R_x(180°)：把 −ŝ 送到 ŝ

    local = flip @ min_rotation_to(loop, -s)                                # −ŝ 附近光滑，local·u = ŝ
    D = min_rotation_to(loop, s) @ local.transpose(0, 2, 1)
    ang = np.unwrap(np.arctan2(D[:, 1, 0], D[:, 0, 0]))
    winding = (ang[-1] - ang[0]) / (2 * np.pi)
    print(f"    绕 u = −ŝ 的 5° 小圈一周，最短旋转截面相对局部光滑截面的转角卷绕数 = {winding:+.4f}")
    assert abs(abs(winding) - 2) < 1e-6


# 六方柱的转动对称群 D6（D6h 的转动子群，阶 12）：绕 c 轴 60°k，及 6 个绕水平体轴的 180° 翻转。
# 姿态 R 与 RQ（Q ∈ D6）是同一个物理姿态（右乘 = 重贴面号）。镜面属 improper 部分，不作用于 SO(3)。
D6_ATTITUDE = np.stack([Rz(60.0 * k) for k in range(6)] + [Rz(60.0 * k) @ np.diag([1.0, -1.0, -1.0]) for k in range(6)])


def d6_index(Q):
    """Q 在 D6_ATTITUDE 里的下标；不在群里返回 None。"""
    d = np.abs(D6_ATTITUDE - Q).max(axis=(1, 2))
    return int(np.argmin(d)) if d.min() < 1e-12 else None


def check_containments():
    """姿态族的包含关系。口径（Lumice doc/coordinate-convention.md §1/§5/§7，LI docs/ch11-pose-density-families.md §2）：
    体轴 e1 = 面 3 法向，e2 = N1×N3 = 六边形顶角方向（长对角线），e3 = c 轴；
      片晶   {R e3 = +z}
      柱晶   {R e3 水平}                          = column_attitude(ψ, θ) 全体
      Parry  {R e3 水平, R e1 = +z}（roll 锁 0）   = column_attitude(ψ, 180°)
      Lowitz 环面 {R e2 水平}（roll ∈ {0, 180°}）  = R_z(φ)R_y(t)；LI / Lumice 的 Lowitz = roll 锁 0 的半环 t = −zenith ∈ [−180°, 0]
    判定分两层：原始点集（不商对称）与 D6 意义下（允许右乘 Q ∈ D6）。"""
    print("\n[5] 姿态族包含关系（原始点集 / D6 意义下）")
    # (0) D6 自检：正交、det = +1、12 个两两不同、乘法封闭；且每个元素把六方柱 8 个面法向置换为自身（几何白盒）
    idx = np.array([[d6_index(A @ B) for B in D6_ATTITUDE] for A in D6_ATTITUDE], dtype=object)
    normals = np.array([Rz(60.0 * j)[:, 0] for j in range(6)] + [[0, 0, 1.0], [0, 0, -1.0]])
    perm_ok = all(max(np.min(np.abs(normals - Q @ n).max(axis=1)) for n in normals) < 1e-12 for Q in D6_ATTITUDE)
    ortho = max(np.abs(Q.T @ Q - np.eye(3)).max() for Q in D6_ATTITUDE)
    dets = np.linalg.det(D6_ATTITUDE)
    distinct = min(np.abs(D6_ATTITUDE[i] - D6_ATTITUDE[j]).max() for i in range(12) for j in range(i))
    print(f"    D6 自检：max|QᵀQ−I| = {ortho:.1e}，det ∈ [{dets.min():.12f}, {dets.max():.12f}]，两两最小差 {distinct:.3f}，"
          f"12×12 乘法表封闭 = {not any(v is None for v in idx.flat)}，面法向集合不变 = {perm_ok}")
    assert ortho < 1e-12 and np.abs(dets - 1).max() < 1e-12 and distinct > 0.5
    assert not any(v is None for v in idx.flat) and perm_ok
    Rz180, flip_e2 = D6_ATTITUDE[3], D6_ATTITUDE[3] @ D6_ATTITUDE[6]           # 绕 c 轴 180°；绕 e2 翻转 180°
    assert np.allclose(flip_e2, np.diag([-1.0, 1.0, -1.0]))

    grid = np.arange(0.0, 360.0, 5.0)
    lowitz = lambda p, t: Rz(p) @ Ry(t)
    parry = np.stack([column_attitude(p, 180.0) for p in grid])
    plate = np.stack([Rz(p) for p in grid])
    dmin = lambda A, B: max(np.min(rotation_distances(a, B)) for a in A)     # A 每个点到点集 B 的最近距离，取最大
    # (a) 片晶圆 = Lowitz 环面 t = 0 那一圈（摆角 0）；t = 180° 那一圈 = 片晶 · (绕 e2 翻转)，D6 意义下同一个片晶
    d_plate = dmin(plate, np.stack([lowitz(p, 0.0) for p in grid]))
    d_plate_flip = dmin(plate @ flip_e2, np.stack([lowitz(p, 180.0) for p in grid]))
    print(f"    (a) 片晶 ⊂ Lowitz：片晶圆到 t=0 圈最大距离 {d_plate:.1e}；片晶·flip_e2 到 t=180° 圈 {d_plate_flip:.1e}")
    assert d_plate < 1e-9 and d_plate_flip < 1e-9
    # (b) Parry = Lowitz 环面 t = −90° 那一圈（roll 锁 0、zenith 摆到 90°），原始点集即成立，不需对称操作；
    #     t = +90° 那一圈（roll = 180°，面 6 朝上）= Parry · R_z(180°)，是 D6 意义下的同一族
    L_m90 = np.stack([lowitz(p, -90.0) for p in grid])
    L_p90 = np.stack([lowitz(p, 90.0) for p in grid])
    d_parry = max(dmin(parry, L_m90), dmin(L_m90, parry))
    d_parry_flip = max(dmin(parry @ Rz180, L_p90), dmin(L_p90, parry @ Rz180))
    d_parry_raw90 = dmin(parry, L_p90)
    rolls = np.degrees([c_axis_roll(R) for R in L_m90])
    print(f"    (b) Parry = Lowitz t=−90° 圈：Hausdorff 距离 {d_parry:.1e}（该圈 roll ∈ [{rolls.min():.1e}, {rolls.max():.1e}]°）；"
          f"t=+90° 圈 = Parry·R_z(180°)：{d_parry_flip:.1e}（与 Parry 原始点集最近 {np.degrees(d_parry_raw90):.1f}°）")
    assert d_parry < 1e-9 and d_parry_flip < 1e-9 and np.abs(rolls).max() < 1e-9 and np.degrees(d_parry_raw90) > 90
    # (c) Parry ⊂ 柱晶环面：θ = 180° 那一圈，逐点 zenith = 90°、roll = 0°、R e1 = +z
    zen = np.degrees([c_axis_zenith(R) for R in parry])
    rl = np.degrees([c_axis_roll(R) for R in parry])
    e1z = parry[:, 2, 0]
    print(f"    (c) Parry ⊂ 柱晶（θ=180°）：max|zenith−90°| = {np.abs(zen - 90).max():.1e}°，max|roll| = {np.abs(rl).max():.1e}°，"
          f"min (R e1)_z = {e1z.min():.12f}")
    assert np.abs(zen - 90).max() < 1e-9 and np.abs(rl).max() < 1e-9 and np.abs(e1z - 1).max() < 1e-12
    # (d) 柱晶 ∩ Lowitz 环面。柱晶点 column(ψ,θ) 在 Lowitz 环面上 ⇔ (R e2)_z = 0；解析 (R e2)_z = sin θ，与 ψ 无关
    #     ⇒ 原始交集恰是 θ = 0°、180° 两圈 = Parry 与 Parry·R_z(180°)；LI / Lumice 的 roll 锁 0 半环只交出 Parry 一圈
    fine = np.arange(0.0, 360.0, 0.5)
    e2z = np.array([[column_attitude(p, t)[2, 1] for t in fine] for p in grid[::6]])
    zero_th = fine[np.abs(e2z).max(axis=0) < 1e-9]
    resid = np.abs(e2z - np.sin(np.radians(fine))[None]).max()
    half = [float(t) for t in zero_th if np.abs(c_axis_roll(column_attitude(0.0, t))) < 1e-9]   # roll = 0 的那一半
    print(f"    (d) 柱晶 ∩ Lowitz 环面：θ 步长 0.5° 扫描，(R e2)_z 与 sinθ 最大偏差 {resid:.1e}；"
          f"(R e2)_z ≡ 0 的 θ = {zero_th.tolist()}°；其中 roll = 0（LI Lowitz 半环）的 θ = {half}°")
    assert resid < 1e-12 and zero_th.tolist() == [0.0, 180.0] and half == [180.0]
    #     D6 意义下：Lowitz 环面的 D6 像是 3 张环面 {R v 水平}（v = 3 条长对角线），各与柱晶交 2 圈，共 6 圈；
    #     每一圈都是「某个柱面朝上」，逐点找到 Q ∈ D6 把它送回 Parry（R Q e1 = +z）
    tori, n_circles, all_parry = set(), 0, True
    for Q in D6_ATTITUDE:
        v = Q @ np.array([0.0, 1.0, 0.0])
        tori.add(tuple(np.round(v * np.sign(v[np.argmax(np.abs(v))]), 9)))
    for v in tori:
        v = np.array(v)
        on = [t for t in fine if max(abs((column_attitude(p, t) @ v)[2]) for p in grid[::6]) < 1e-9]
        n_circles += len(on)
        for t in on:
            for p in grid[::6]:
                R = column_attitude(p, t)
                all_parry &= any(abs((R @ Q)[2, 0] - 1) < 1e-12 and abs((R @ Q)[2, 2]) < 1e-12 for Q in D6_ATTITUDE)
    print(f"    (d′) Lowitz 环面的 D6 像 {len(tori)} 张，与柱晶环面共交出 {n_circles} 圈；每圈逐点经某个 Q∈D6 落入 Parry = {all_parry}")
    assert len(tori) == 3 and n_circles == 6 and all_parry
    # (e) 随机 = 整个 SO(3)，以上全部平凡包含，不另核验
    print("    (e) ⊂ 随机（= 整个 SO(3)）：平凡，不另核验")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    smoke()
    checks = [("euler", check_euler), ("column", check_column), ("families", check_families),
              ("u_theta", check_u_theta), ("containments", check_containments)]
    for name, fn in checks:
        try:
            fn()
        except AssertionError as e:
            print(f"FAIL: {name} {e!r}")
            sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
