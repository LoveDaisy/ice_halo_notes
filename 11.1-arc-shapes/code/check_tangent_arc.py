# 核验 11.1 番外提纲的数字（确定性，无网络，末行 OK）：切弧（柱晶 × 3-5，60° 楔、M = I）用两种算法各算一遍——
# 古典：Pernter / Tricker 1970 的球面三角作图（轴 P 在地平圈上，最小偏折点 M 的极坐标 (Δ, σ1/σ2)），另对照书里手算印出的
# Table IV:1 / IV:3；本系列：姿态链 + Φ = M∘W 光点（08.1 crosscheck_bridge），绕 c 轴数值求偏折极小。再顺带确认 ch3 的特里克尔弧
# 就是 TM2006 p.71 的「顶点在反日点、半顶角 30° 的圆锥 ∩ 天球」，并在柱晶 / Lowitz 两族上比「最小偏折轨迹」与真正的亮边
# （天空映射 Jacobian 行列式为 0 的 fold caustic）：切弧上两者重合，Lowitz 上不重合（Tape 1980 p.15 的数值版）。约 20 s。
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from lumice_integral.geometry import HexPrism, fold_matrix
from lumice_integral.symmetry.signature import wedge_angle

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    """按文件路径加载别章脚本（不把别章 code/ 放进 sys.path；先例 09-pyramid/code/_ch9_fig.py）。"""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# crosscheck_bridge 内部 `from tape_halo_function import ...`，故先以该名注册
tape = load("tape_halo_function", ROOT / "08.1-tape-vs-matrix/code/tape_halo_function.py")
bridge = load("_crosscheck_bridge", ROOT / "08.1-tape-vs-matrix/code/crosscheck_bridge.py")
ch11 = load("_check_pose_shapes", ROOT / "11-five-halos-one-wedge/code/check_pose_shapes.py")

CRYSTAL = HexPrism()
PATH = (3, 5)
M = fold_matrix(CRYSTAL, list(PATH))
N = tape.N_ICE                      # 1.31，与 Tricker 1970 书 p.72「yellow light 1·31」同值
ALPHA = 60.0


def dm(d, m=0.0):
    return d + m / 60.0


# Tricker 1970 书 p.98 Table IV:1（取自 Pernter）：θ = 轴与太阳的夹角（polar distance），D = 法平面最小偏折，Δ = 到太阳的真实角距
TABLE_IV1 = [  # (θ, D, Δ)，度
    (90, dm(21, 50), dm(21, 50)), (85, dm(22, 2), dm(21, 57)), (80, dm(22, 30), dm(22, 10)),
    (75, dm(23, 20), dm(22, 32)), (70, dm(24, 34), dm(23, 4)), (65, dm(26, 22), dm(23, 50)),
    (60, dm(28, 44), dm(24, 49)), (55, dm(31, 56), dm(26, 3)), (50, dm(36, 20), dm(27, 38)),
    (45, dm(42, 30), dm(29, 42)), (40, dm(51, 30), dm(32, 26)), (35, dm(66, 2), dm(36, 26)),
    (30, dm(98, 48), dm(44, 38)), (dm(29, 15), dm(120, 0), dm(50, 4)),
]
# 书 p.112–113 Table IV:3：每档太阳高度 Σ 下逐行 (e, σ0+e, σ0−e)，行与 Table IV:1 的 θ 一一对应；Σ = 30° 末行印「—」
TABLE_IV3 = {
    0: [(0, 0, 0), (0, dm(0, 58), dm(0, 58)), (0, dm(1, 58), dm(1, 58)), (0, dm(3, 3), dm(3, 3)),
        (0, dm(4, 17), dm(4, 17)), (0, dm(5, 45), dm(5, 45)), (0, dm(7, 19), dm(7, 19)), (0, dm(9, 20), dm(9, 20)),
        (0, dm(11, 54), dm(11, 54)), (0, dm(15, 23), dm(15, 23)), (0, dm(20, 16), dm(20, 16)),
        (0, dm(28, 3), dm(28, 3)), (0, dm(45, 18), dm(45, 18)), (0, dm(56, 30), dm(56, 30))],
    10: [(0, 0, 0), (dm(0, 52), dm(1, 50), dm(0, 6)), (dm(1, 46), dm(3, 44), dm(0, 12)),
         (dm(2, 42), dm(5, 45), dm(0, 21)), (dm(3, 41), dm(7, 58), dm(0, 36)), (dm(4, 44), dm(10, 29), dm(1, 1)),
         (dm(5, 50), dm(13, 9), dm(1, 29)), (dm(7, 6), dm(16, 26), dm(2, 14)), (dm(8, 30), dm(20, 24), dm(3, 24)),
         (dm(10, 10), dm(25, 33), dm(5, 13)), (dm(12, 8), dm(32, 24), dm(8, 8)), (dm(14, 35), dm(42, 38), dm(13, 28)),
         (dm(17, 47), dm(63, 5), dm(27, 31)), (dm(18, 21), dm(74, 51), dm(38, 9))],
    20: [(0, 0, 0), (dm(1, 49), dm(2, 47), -dm(0, 51)), (dm(3, 41), dm(5, 39), -dm(1, 43)),
         (dm(5, 36), dm(8, 39), -dm(2, 33)), (dm(7, 38), dm(11, 55), -dm(3, 21)), (dm(9, 47), dm(15, 32), -dm(4, 2)),
         (dm(12, 8), dm(19, 27), -dm(4, 49)), (dm(14, 46), dm(24, 6), -dm(5, 26)), (dm(17, 47), dm(29, 41), -dm(5, 53)),
         (dm(21, 21), dm(36, 44), -dm(5, 58)), (dm(25, 42), dm(45, 58), -dm(5, 26)), (dm(31, 19), dm(59, 22), -dm(3, 16)),
         (dm(39, 5), dm(84, 23), dm(6, 13)), (dm(40, 32), dm(97, 2), dm(15, 58))],
    30: [(0, 0, 0), (dm(2, 52), dm(3, 50), -dm(1, 54)), (dm(5, 50), dm(7, 48), -dm(3, 52)),
         (dm(8, 54), dm(11, 57), -dm(5, 51)), (dm(12, 8), dm(16, 25), -dm(7, 51)), (dm(15, 37), dm(21, 22), -dm(9, 52)),
         (dm(19, 28), dm(26, 47), -dm(12, 9)), (dm(23, 51), dm(33, 11), -dm(14, 31)), (dm(28, 59), dm(40, 53), -dm(17, 5)),
         (dm(35, 16), dm(50, 39), -dm(19, 53)), (dm(43, 29), dm(63, 45), -dm(23, 13)), (dm(55, 33), dm(83, 36), -dm(27, 30)),
         (dm(90, 0), dm(135, 18), -dm(44, 42)), None],
}


# ---- 古典侧：Tricker 1970 的球面三角（只用他的公式；D、Δ 用 Tape 1980 的 Bravais 链算精确值，不用印出的表）----------------

def pernter_D_Delta(theta):
    """法平面最小偏折 D 与真实角距 Δ（度）：Bravais n'(θ) 下 60° 楔的最小偏折 [Tape1980 p.2 Eq. (11)]，
    sin(Δ/2) = sin θ sin(D/2)（= Tricker 书 p.109 的 sin(Δ/2)/sin(D/2) = sin θ）。"""
    D = -tape.min_deviation_D(theta, ALPHA, N)
    return D, tape.true_deviation(theta, -D)


def tricker_polar(theta, sigma, D=None, Delta=None):
    """Tricker 书 p.109–112：切弧上最小偏折点 M1（上）/ M2（下）以太阳为极点的极坐标 (Δ, σ1, σ2, e)。
    sin ω = sin θ sin D / sin Δ；sin β = √(sin(θ+Σ) sin(θ−Σ)) / (sin θ cos Σ)，e = 90° − β；σ1 = 180° − β − ω，σ2 = β − ω。"""
    exact = D is None
    if exact:
        D, Delta = pernter_D_Delta(theta)
    r = np.radians
    omega = np.degrees(np.arcsin(np.sin(r(theta)) * np.sin(r(D)) / np.sin(r(Delta))))
    if exact:                                                   # 书 p.109 的另一写法 cos σ0 = cos(D/2)/cos(Δ/2)，自检 ω 取锐角
        sigma0 = np.degrees(np.arccos(min(1.0, np.cos(r(D / 2)) / np.cos(r(Delta / 2)))))
        assert abs((90 - omega) - sigma0) < 1e-6
    beta = np.degrees(np.arcsin(np.sqrt(max(0.0, np.sin(r(theta + sigma)) * np.sin(r(theta - sigma))))
                                / (np.sin(r(theta)) * np.cos(r(sigma)))))
    return Delta, 180 - beta - omega, beta - omega, 90 - beta


# ---- 本系列侧：姿态链 + Φ = M∘W，绕 c 轴求偏折极小 ------------------------------------------------------------

def sun_frame(sigma):
    S = bridge.sun_direction(sigma)
    up = np.array([-np.sin(np.radians(sigma)), 0.0, np.cos(np.radians(sigma))])
    return S, up, np.cross(S, up) * -1           # side = +y（与 ch11 的 SIDE 同向）


def light(R, S):
    return bridge.light_point_batch(CRYSTAL, M, *PATH, R, S)


def column_minima(az, sigma):
    """c 轴水平、方位 az 的柱晶，绕 c 轴（roll）转一圈，偏折 Δ 的全部局部极小 → [(roll, 光点)]。"""
    S, _, _ = sun_frame(sigma)
    grid = np.arange(0.0, 360.0, 0.1)
    H = light(ch11.chain(az, 90.0, grid), S)
    d = bridge.angular_distance(H, np.broadcast_to(S, H.shape))
    out = []
    for i in range(len(grid)):
        a, b, c = d[i - 1], d[i], d[(i + 1) % len(grid)]
        if np.isfinite([a, b, c]).all() and b <= a and b < c:
            f = lambda t: bridge.angular_distance(light(ch11.chain(az, 90.0, t), S), S[None])[0]
            res = minimize_scalar(f, bounds=(grid[i] - 0.1, grid[i] + 0.1), method="bounded",
                                  options=dict(xatol=1e-11))
            out.append((res.x, light(ch11.chain(az, 90.0, res.x), S)[0]))
    return out


def polar(H, sigma):
    S, up, side = sun_frame(sigma)
    Delta = np.degrees(bridge.angular_distance(H[None], S[None])[0])
    return Delta, np.degrees(np.arctan2(H @ side, H @ up))


def wrap(x):
    return (x + 180.0) % 360.0 - 180.0


def check_setup():
    print(f"[0] 光路 {'-'.join(map(str, PATH))}：M = I ? {np.allclose(M, np.eye(3))}，楔角 {wedge_angle(CRYSTAL, M, *PATH):.6f}°，n = {N}")
    assert np.allclose(M, np.eye(3)) and abs(wedge_angle(CRYSTAL, M, *PATH) - ALPHA) < 1e-9
    rows = TABLE_IV1[:-1]                                   # 末行是掠出射端点（D = 120° 按定义），单独比 θ_min
    err_D = max(abs(pernter_D_Delta(t)[0] - D) for t, D, _ in rows) * 60
    err_De = max(abs(pernter_D_Delta(t)[1] - De) for t, _, De in rows) * 60
    print(f"    Pernter 表（Tricker 书 p.98 Table IV:1，前 13 行）vs Tape 1980 Bravais 链（n = 1.31）：D 最大差 {err_D:.2f}′，"
          f"Δ 最大差 {err_De:.2f}′（表印到整弧分；手算误差量级）")
    assert err_D < 3.0 and err_De < 3.0
    tmin = tape.min_theta(ALPHA, N)
    print(f"    掠出射端点：Tricker 印 θ = 29°15′（D = 120°），Tape 1980 θ_min = {tmin:.4f}° = 29°{(tmin - 29) * 60:.1f}′")
    assert abs(tmin - dm(29, 15)) < 1 / 60


def check_tangent_arc():
    print("[1] 切弧两种算法：Tricker 球面三角（古典）vs 姿态链 + Φ = M∘W 绕 c 轴求极小（本系列）")
    max_cl, max_tape, n_pts = 0.0, 0.0, 0
    tab = {"regular": 0.0, 65: 0.0, "end": 0.0}
    for sigma, rows in TABLE_IV3.items():
        for (theta, _, _), row in zip(TABLE_IV1, rows):
            if row is None or theta < sigma + 1e-9:
                continue
            Delta, s1, s2, e = tricker_polar(theta, sigma)
            # 与书里印出的 (e, σ0+e, σ0−e) 比（弧分）。不拿印出的 D、Δ 回代：σ0 = arccos[cos(D/2)/cos(Δ/2)] 在 θ → 90° 附近
            # 病态（比值接近 1），弧分级舍入会被放大到几十弧分，Tricker 显然是用更多位的中间值算的
            key = "end" if theta < 29.5 else (65 if theta == 65 else "regular")
            tab[key] = max(tab[key], *(abs(a - b) * 60 for a, b in zip((e, s1, s2), row)))
            if theta >= 89.999:
                continue                                    # θ = 90°：M1 = M2 = 切点，σ 退化为 0，另在下面单测
            az = np.degrees(np.arccos(np.cos(np.radians(theta)) / np.cos(np.radians(sigma))))
            # 同一条轴线 P 的两个指向（c 轴朝 az 与朝 az + 180°）：单条标号光路 3-5 在每个指向下只有一个极小，
            # 两个指向各给 Tricker 的 M1、M2 之一（把 PS 绕 P 正转 / 反转 D）
            mins = [(az + k * 180.0, roll, H) for k in (0, 1) for roll, H in column_minima(az + k * 180.0, sigma)]
            assert len(mins) == 2, (sigma, theta, len(mins))
            pols = [polar(H, sigma) for _, _, H in mins]
            # 两个极小一个是上切弧点、一个是下切弧点：σ1 从正上方量、σ2 从正下方量，都量向上切弧点所在一侧
            best = None
            for up_i in (0, 1):
                (D1, p1), (D2, p2) = pols[up_i], pols[1 - up_i]
                s = np.sign(p1) if p1 != 0 else 1.0
                errs = (abs(D1 - Delta), abs(D2 - Delta), abs(wrap(s * p1 - s1)), abs(wrap(180 - s * p2 - s2)))
                if best is None or max(errs) < max(best):
                    best = errs
            max_cl = max(max_cl, *best)
            # 同一姿态下 Tape / TK1999 光点公式（08.1 已验证的古典光点法实现）也算一遍
            for azk, roll, H in mins:
                R = ch11.chain(azk, 90.0, roll)[0]
                u = bridge.wedge_orientation(CRYSTAL, M, *PATH, R)
                Ht = tape.halo_point_batch(u, ALPHA, sun_frame(sigma)[0])[0]
                max_tape = max(max_tape, bridge.angular_distance(Ht[None], H[None])[0])
            n_pts += 2
    print(f"    {n_pts} 个最小偏折点：Tricker 公式 vs 本系列数值极小，(Δ, σ) 最大差 {max_cl:.2e}°；"
          f"同一姿态 TK1999 光点公式 vs Φ = M∘W 光点 {np.degrees(max_tape):.2e}°")
    print(f"    书 p.112–113 印出的 Table IV:3（Σ = 0/10/20/30°，53 行 × (e, σ0+e, σ0−e)）vs 精确几何：常规行最大差 {tab['regular']:.1f}′；"
          f"θ = 65° 一行 {tab[65]:.1f}′（σ0 印 5°45′，四档一致偏小）；掠出射端点行 {tab['end']:.1f}′（端点对 θ 极敏感：θ 从 29°14.8′ 到 29°15′，"
          f"D 就从 120° 掉到 {pernter_D_Delta(dm(29, 15))[0]:.2f}°）")
    assert max_cl < 1e-6 and np.degrees(max_tape) < 1e-9 and tab["regular"] < 3.0 and tab[65] < 8.0
    # θ = 90°：轴与太阳垂直 ⇒ 切点在太阳正上 / 正下，Δ = 22° 晕半径
    for sigma in (0, 10, 20, 30):
        H = [h for k in (0, 1) for _, h in column_minima(90.0 + k * 180.0, sigma)]
        pa = sorted(abs(polar(h, sigma)[1]) for h in H)
        print(f"    Σ = {sigma:>2}°，θ = 90°：两个极小的位置角 {pa[0]:.2e}° / {pa[1]:.9f}°，Δ = "
              f"{polar(H[0], sigma)[0]:.6f}°（D_min(60°) = {tape.min_deviation_tk(ALPHA, N):.6f}°）")
        assert pa[0] < 1e-6 and abs(pa[1] - 180) < 1e-6
    # 书 p.105 Table IV:2 与 p.112 Table IV:3 的 σ0 列同名同义（Σ = 0 时的 σ），却前五行不一致——哪边对
    tab2 = [(dm(22, 10), dm(2, 45)), (dm(23, 4), dm(4, 20)), (dm(24, 49), dm(7, 18)), (dm(27, 38), dm(11, 53)),
            (dm(32, 26), dm(20, 10))]
    theta_of = {round(De, 4): t for t, _, De in TABLE_IV1}
    for De, s in tab2:
        t = theta_of[round(De, 4)]
        s0 = tricker_polar(t, 0.0)[1]
        print(f"    Table IV:2 σ = {s:.3f}° vs 公式 σ0 = {s0:.3f}°（Δ = {De:.3f}°，θ = {t}°）")
    return max_cl


def check_ch11_tie():
    print("[2] 与 ch11 §3（太阳 15°、柱晶像的切片式填充，LI 互证过）衔接：D ≈ 25° 处上切弧点的位置角")
    sigma = 15.0
    from scipy.optimize import brentq
    theta = brentq(lambda t: pernter_D_Delta(t)[1] - 25.125, 40.0, 89.0)
    Delta, s1, s2, _ = tricker_polar(theta, sigma)
    print(f"    Δ = {Delta:.3f}°（θ = {theta:.3f}°）：上切弧点 σ1 = ±{s1:.2f}°，下切弧点距正下方 σ2 = {s2:+.2f}°；"
          f"ch11 §3 给 D ∈ [25, 25.25)° 上方 ±18°、下方 ±2°（1° 格）")
    assert abs(abs(s1) - 18) < 1.5 and abs(abs(s2) - 2) < 1.5


def check_tricker_cone():
    print("[3] ch3 的特里克尔弧参数方程 = TM2006 p.71 的「顶点在反日点、半顶角 30° 的圆锥 ∩ 天球」（只确认，不重推）")
    worst, nappes = 0.0, set()
    for sigma in (0.0, 15.0, 30.0):
        s, c = np.sin(np.radians(sigma)), np.cos(np.radians(sigma))
        a = np.radians(np.arange(0, 360, 0.5))
        r = np.stack([-0.25 * (3 + np.cos(2 * a)) * c - np.sqrt(3) / 2 * np.sin(a) * s,
                      -0.25 * np.sin(2 * a) * c + np.sqrt(3) / 2 * np.cos(a) * s,
                      np.sqrt(3) / 2 * np.sin(a) * c - 0.5 * s], -1)                # ch3 正文第 104–110 行
        v = r - np.array([-c, 0.0, s])                                              # 减反日点 s_a
        keep = np.linalg.norm(v, axis=1) > 1e-9
        ang = np.degrees(np.arccos(np.clip(np.abs(v[keep, 2]) / np.linalg.norm(v[keep], axis=1), -1, 1)))
        worst = max(worst, np.abs(ang - 30.0).max(), abs(np.linalg.norm(r, axis=1) - 1).max())
        nappes |= set(np.sign(v[keep, 2]).astype(int))
    print(f"    Σ = 0/15/30°：|∠(r′ − s_a, 竖直) − 30°| 最大 {worst:.1e}°；r′ − s_a 的竖直分量两种符号都出现 "
          f"{sorted(nappes)} ⇒ 弧落在圆锥的两叶上（issue 所说「双圆锥」）")
    assert worst < 1e-9 and nappes == {-1, 1}


# ---- 最小偏折轨迹 vs fold caustic：柱晶（切弧）重合、Lowitz 不重合 ---------------------------------------------

EPS = 1e-4


def _fam_pose(name, a, b, psi=0.0):
    """族参数 (a, b) + 绕 c 轴额外转 psi：柱晶 (az, roll)，Lowitz (az, zenith)；chain(az, zen, roll) 末端就是绕 c 轴的转动。"""
    if name == "column":
        return ch11.chain(a, 90.0, b + psi)
    return ch11.chain(a, b, psi)


def _fields(name, a, b):
    """逐点：光点 x、∂Δ/∂ψ（绕 c 轴）、∂²Δ/∂ψ²、以及 det[x, ∂x/∂a, ∂x/∂b]（天空映射的有向面积元）。"""
    S = ch11.S
    X = lambda aa, bb, pp=0.0: ch11.sky(_fam_pose(name, aa, bb, pp))
    x = X(a, b)
    dev = lambda y: np.arccos(np.clip(y @ S, -1, 1))
    dp, dm_ = dev(X(a, b, EPS)), dev(X(a, b, -EPS))
    g1 = (dp - dm_) / (2 * EPS)
    g2 = (dp - 2 * dev(x) + dm_) / EPS ** 2
    xa = (X(a + EPS, b) - X(a - EPS, b)) / (2 * EPS)
    xb = (X(a, b + EPS) - X(a, b - EPS)) / (2 * EPS)
    det = np.einsum("ni,ni->n", x, np.cross(xa, xb))
    return x, g1, g2, det


def _zero_set(name, fieldfun, a_grid, b_grid):
    """在 (a, b) 网格上找 fieldfun 的变号点——沿 b 扫、也沿 a 扫（零集曲线与哪条网格线近乎平行都不漏）——各二分 40 次
    → 零集上的 (天空点, a, b)。"""
    f = np.empty((len(a_grid), len(b_grid)))
    for i in range(0, len(a_grid), 100):                       # 分块，控制 (n, 3, 3) 姿态数组的内存
        A, B = np.meshgrid(a_grid[i:i + 100], b_grid, indexing="ij")
        f[i:i + 100] = fieldfun(A.ravel(), B.ravel()).reshape(A.shape)
    A, B = np.meshgrid(a_grid, b_grid, indexing="ij")
    xs, as_, bs = [], [], []
    for axis in (1, 0):
        sl0 = (slice(None), slice(None, -1)) if axis == 1 else (slice(None, -1), slice(None))
        sl1 = (slice(None), slice(1, None)) if axis == 1 else (slice(1, None), slice(None))
        lo_f, hi_f = f[sl0], f[sl1]
        ok = np.isfinite(lo_f) & np.isfinite(hi_f) & (np.sign(lo_f) != np.sign(hi_f))
        a0, b0, a1, b1, flo = A[sl0][ok], B[sl0][ok], A[sl1][ok], B[sl1][ok], lo_f[ok]
        t_lo, t_hi = np.zeros(len(flo)), np.ones(len(flo))
        at = lambda t: (a0 + t * (a1 - a0), b0 + t * (b1 - b0))
        for _ in range(40):
            mid = 0.5 * (t_lo + t_hi)
            fm = fieldfun(*at(mid))
            left = np.sign(fm) == np.sign(flo)
            t_lo, flo = np.where(left, mid, t_lo), np.where(left, fm, flo)
            t_hi = np.where(left, t_hi, mid)
        a, b = at(0.5 * (t_lo + t_hi))
        x = ch11.sky(_fam_pose(name, a, b))
        good = np.isfinite(x).all(1)
        xs.append(x[good]); as_.append(a[good]); bs.append(b[good])
    return np.concatenate(xs), np.concatenate(as_), np.concatenate(bs)


def _nearest(p, q, chunk=2048):
    out = np.empty(len(p))
    for i in range(0, len(p), chunk):
        out[i:i + chunk] = np.degrees(np.arccos(np.clip(p[i:i + chunk] @ q.T, -1, 1))).min(1)
    return out


def _nearest_other(p, chunk=2048):
    out = np.empty(len(p))
    for i in range(0, len(p), chunk):
        g = np.degrees(np.arccos(np.clip(p[i:i + chunk] @ p.T, -1, 1)))
        g[np.arange(len(g)), np.arange(i, i + len(g))] = np.inf
        out[i:i + chunk] = g.min(1)
    return out


def check_min_locus_vs_caustic():
    print("[4] 最小偏折轨迹（古典作图画的线）vs fold caustic（天空映射 Jacobian 行列式 = 0，真正的亮边）；太阳 15°、单条 3-5")
    res = {}
    for name, b_grid in (("column", np.arange(0.0, 360.0, 0.5)), ("lowitz", np.arange(0.25, 180.0, 0.5))):
        a_grid = np.arange(0.0, 360.0, 0.2)
        pmin, a, b = _zero_set(name, lambda a, b: _fields(name, a, b)[1], a_grid, b_grid)
        pmin = pmin[_fields(name, a, b)[2] > 0]            # 只留绕 c 轴的极小（∂²Δ/∂ψ² > 0），极大不是古典作图画的线
        pcau, _, _ = _zero_set(name, lambda a, b: _fields(name, a, b)[3], a_grid, b_grid)
        d = _nearest(pmin, pcau)
        D = np.degrees(np.arccos(np.clip(pmin @ ch11.S, -1, 1)))
        res[name] = d
        spacing = np.median(_nearest_other(pcau))              # caustic 采样点的典型间距：最近距离的分辨率
        near = d < 0.05
        print(f"    {name:>6}：最小偏折轨迹 {len(pmin)} 点、caustic {len(pcau)} 点（点距中位 {spacing:.3f}°）；轨迹点到最近 caustic："
              f"中位 {np.median(d):.3g}°、95% {np.percentile(d, 95):.3g}°、最大 {d.max():.3g}°；")
        print(f"            离 caustic > 0.5° 的轨迹点占 {(d > 0.5).mean():.0%}；< 0.05° 的 {near.sum()} 点，"
              + (f"D ∈ [{D[near].min():.2f}, {D[near].max():.2f}]°" if near.any() else "无"))
    # 柱晶：最小偏折处 ∂x/∂roll = 0 且 roll 就是族的一个方向 ⇒ Jacobian 降秩，两条线逐点相同；
    # Lowitz：绕 c 轴不是族内方向，最小偏折不迫使 Jacobian 降秩，两条线分开
    assert res["column"].max() < 1e-3 and np.median(res["lowitz"]) > 1.0
    return res


def main():
    check_setup()
    check_tangent_arc()
    check_ch11_tie()
    check_tricker_cone()
    check_min_locus_vs_caustic()
    print("OK")


if __name__ == "__main__":
    main()
