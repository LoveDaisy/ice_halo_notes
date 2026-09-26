# 核验 ch11 提纲的数字（确定性，无网络，末行 OK）：同一条 3-5 光路（M = I、60° 楔）在五个理想姿态族（随机 / 片 / 柱 / Parry /
# Lowitz）下落到天空上的形状——像的维数（天空映射 Jacobian 秩）、每个半径圆 D 被填上的方位角（绕太阳的位置角）、单条
# labelled path 只点亮命名晕的一侧 / 一支、D6h 轨道 12 条同类光路合起来才左右对称；与 LI docs/ch11-pose-density-families.md
# §5.2 的落点表（Haar MC + 密度加权，另一条链路）对照；ch1 思考题「为什么只有幻日是单边的」的镜像判据。约 4 s。
import numpy as np

from halo_notes.math.wedge import min_deviation_deg
from lumice_integral.geometry import N_ICE, HexPrism, fold_matrix
from lumice_integral.so3 import haar_rotations
from lumice_integral.symmetry.attitude import Ry
from lumice_integral.symmetry.reflection_group import Rz
from lumice_integral.symmetry.signature import phi_batch, wedge_angle

PATH = (3, 5)
CRYSTAL = HexPrism()          # phi 只用面法向（无限长棱镜），与 h/a 无关；几何走廊、入射面积权不在本脚本范围
N = N_ICE
SUN_H = 15.0                  # 与 LI canonical scene（CANONICAL_SUN_ALTITUDE_DEG）同一个太阳高度，便于和 §5.2 对照
D_MIN = min_deviation_deg(60.0, N)
D_PROBE = (22.5, 25.0, 30.0, 40.0)   # 读「半径圆被填上的位置角」的几个半径
BAND = 0.25                   # 半径带宽（度）
PA_BIN = 1.0                  # 位置角直方图步长（度）
PA_GAP = 3.0                  # 小于此宽度的空隙视作采样稀疏、并入相邻区间（随机族 Haar 样本在窄半径带里偏稀）
LOWITZ_STD = 40.0             # Lumice kAxisPresets / LI 族表的 Lowitz zenith 宽度（sphere density ⇒ 权重 g(zen)·sin(zen)）
RNG_SEED = 20260927
N_HAAR = 2_000_000


def unit_from(h_deg, az_deg):
    h, a = np.radians(h_deg), np.radians(np.asarray(az_deg, float))
    return np.stack([np.cos(h) * np.cos(a), np.cos(h) * np.sin(a), np.full_like(a, np.sin(h))], axis=-1)


def az_el(v):
    v = np.asarray(v, float)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])), np.degrees(np.arcsin(np.clip(v[..., 2], -1, 1)))


def chain(az, zen, roll):
    """Lumice / LI 姿态链 R = Rz(az − 180°)·Ry(−zenith)·Rz(roll)（LI pose_density.c_axis_roll docstring；roll = 0 ⇔ 面 3 朝上）。"""
    az, zen, roll = (np.radians(np.asarray(a, float).ravel()) for a in np.broadcast_arrays(az, zen, roll))
    a = az - np.pi
    ca, sa, cz, sz, cr, sr = np.cos(a), np.sin(a), np.cos(-zen), np.sin(-zen), np.cos(roll), np.sin(roll)
    o, z = np.ones_like(a), np.zeros_like(a)
    A = np.stack([np.stack([ca, -sa, z], -1), np.stack([sa, ca, z], -1), np.stack([z, z, o], -1)], 1)
    B = np.stack([np.stack([cz, z, sz], -1), np.stack([z, o, z], -1), np.stack([-sz, z, cz], -1)], 1)
    C = np.stack([np.stack([cr, -sr, z], -1), np.stack([sr, cr, z], -1), np.stack([z, z, o], -1)], 1)
    return A @ B @ C


S = unit_from(SUN_H, 0.0)
UP = np.array([-np.sin(np.radians(SUN_H)), 0.0, np.cos(np.radians(SUN_H))])   # 太阳处切平面：「正上方」
SIDE = np.array([0.0, 1.0, 0.0])                                                # 「+方位侧」（LI 称 right）


def sky(R, path=PATH):
    """姿态 R（(n,3,3)）下 path 的光点天空方向 x = −R Φ_P(−Rᵀ s)；NaN = 光学定义域外。"""
    M = fold_matrix(CRYSTAL, list(path))
    u = np.einsum("nji,j->ni", R, S)
    x_body = -phi_batch(CRYSTAL, M, path[0], path[-1], -u)
    return np.einsum("nij,nj->ni", R, x_body)


def dist_pa(x):
    """光点离太阳的角距离 D 与绕太阳的位置角 pa（0 = 太阳正上方，+90 = +方位侧，±180 = 正下方）。"""
    D = np.degrees(np.arccos(np.clip(x @ S, -1, 1)))
    pa = np.degrees(np.arctan2(x @ SIDE, x @ UP))
    return D, pa


def intervals(pa):
    """位置角集合 → 覆盖区间（按 PA_BIN 直方图连通段；跨 ±180 的段合并）。"""
    if len(pa) == 0:
        return []
    edges = np.arange(-180, 180 + PA_BIN, PA_BIN)
    hit = np.histogram(pa, edges)[0] > 0
    segs, start = [], None
    for i, h in enumerate(hit):
        if h and start is None:
            start = i
        if not h and start is not None:
            segs.append([edges[start], edges[i]]); start = None
    if start is not None:
        segs.append([edges[start], 180.0])
    if len(segs) > 1 and segs[0][0] == -180 and segs[-1][1] == 180:
        segs[0][0] = segs.pop()[0] - 360
    merged = [segs[0]]
    for a, b in segs[1:]:
        if a - merged[-1][1] < PA_GAP:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    if len(merged) > 1 and merged[0][0] + 360 - merged[-1][1] < PA_GAP:
        merged[0][0] = merged.pop()[0] - 360
    return merged


def fmt(segs):
    return " ∪ ".join(f"[{a:+.0f}, {b:+.0f}]" for a, b in segs) if segs else "∅"


def fill_table(name, D, pa):
    out = {}
    for d0 in D_PROBE:
        m = (D >= d0) & (D < d0 + BAND)
        segs = intervals(pa[m])
        width = sum(b - a for a, b in segs)
        out[d0] = segs
        print(f"    D ∈ [{d0:.2f}, {d0 + BAND:.2f})°：位置角 {fmt(segs)}（共约 {width:.0f}°）")
    return out


def rank_of(fun, p0, eps=1e-5):
    """sky 映射在参数点 p0 处的 Jacobian 秩（中心差分，奇异值相对阈 1e-6）。"""
    p0 = np.asarray(p0, float)
    cols = []
    for k in range(len(p0)):
        dp = np.zeros_like(p0); dp[k] = eps
        cols.append((fun(p0 + dp) - fun(p0 - dp)) / (2 * eps))
    sv = np.linalg.svd(np.stack(cols, 1), compute_uv=False)
    return int((sv > 1e-6 * sv.max()).sum())


def family_rank(fun, samples):
    ranks = [rank_of(fun, p) for p in samples]
    return sorted(set(ranks))


# 五个理想族（宽度 → 0；Lowitz 保留 zenith 分布作权重）：参数 → 姿态链
FAMILIES = {
    "random": dict(dim=3, pose=lambda p: chain(p[0], p[1], p[2])),
    "plate":  dict(dim=1, pose=lambda p: chain(p[0], 0.0, 0.0)),
    "column": dict(dim=2, pose=lambda p: chain(p[0], 90.0, p[1])),
    "parry":  dict(dim=1, pose=lambda p: chain(p[0], 90.0, 0.0)),
    "lowitz": dict(dim=2, pose=lambda p: chain(p[0], p[1], 0.0)),
}


def check_setup():
    M = fold_matrix(CRYSTAL, list(PATH))
    print(f"[0] 光路 {'-'.join(map(str, PATH))}：M = I ? {np.allclose(M, np.eye(3))}，楔角 {wedge_angle(CRYSTAL, M, *PATH):.6f}°，"
          f"n = {N}，D_min = {D_MIN:.4f}°；太阳高度 {SUN_H}°、方位 0°")
    assert np.allclose(M, np.eye(3)) and abs(wedge_angle(CRYSTAL, M, *PATH) - 60.0) < 1e-9
    # 姿态链自检：roll = 0 ⇔ 面 3（体 e1）在过 c 轴的竖直面内、朝上；zenith = 90 时面 3 水平朝上（Parry）
    R = chain(37.0, 90.0, 0.0)[0]
    print(f"    自检：chain(az, 90°, 0) 的面 3 法向 = {np.round(R[:, 0], 12)}（应为 +z），c 轴 = {np.round(R[:, 2], 6)}（水平）")
    assert np.allclose(R[:, 0], [0, 0, 1]) and abs(R[2, 2]) < 1e-12
    R = chain(37.0, 30.0, 0.0)[0]
    print(f"    自检：roll = 0 时体 e2（长对角线方向）= {np.round(R[:, 1], 6)}（水平 ⇒ Lowitz 族绕它摆）")
    assert abs(R[2, 1]) < 1e-12


def sample_family(name, rng):
    """返回 (参数样本, 天空方向, 权重, LI 口径权重)。一维 / 二维族用确定性网格，随机族用 Haar。

    权重 = 该族在参数网格上的姿态测度（Haar 面积元 × 族密度）。LI §5.2 的百分位是在「显著样本」（ρ_pose > 1e-3·max）上
    **不加权**取的，即支撑集上的 Haar 测度；只有 Lowitz（zenith 宽 40°）两种口径有差别，LI 口径权重单列。"""
    if name == "random":
        R = haar_rotations(N_HAAR, rng)
        return None, sky(R), np.ones(N_HAAR), np.ones(N_HAAR)
    if name == "plate":
        az = np.arange(0, 360, 0.002)
        return (az,), sky(chain(az, 0.0, 0.0)), np.ones_like(az), np.ones_like(az)
    if name == "parry":
        az = np.arange(0, 360, 0.002)
        return (az,), sky(chain(az, 90.0, 0.0)), np.ones_like(az), np.ones_like(az)
    if name == "column":
        az, roll = np.meshgrid(np.arange(0, 360, 0.25), np.arange(0, 360, 0.25), indexing="ij")
        return (az.ravel(), roll.ravel()), sky(chain(az.ravel(), 90.0, roll.ravel())), np.ones(az.size), np.ones(az.size)
    if name == "lowitz":
        az, zen = np.meshgrid(np.arange(0, 360, 0.25), np.arange(0.125, 180, 0.25), indexing="ij")
        g = np.exp(-0.5 * (zen.ravel() / LOWITZ_STD) ** 2)
        haar = np.sin(np.radians(zen.ravel()))            # 网格 (az, zen) 上的 Haar 面积元
        return (az.ravel(), zen.ravel()), sky(chain(az.ravel(), zen.ravel(), 0.0)), g * haar, haar * (g > 1e-3)
    raise KeyError(name)


def wpct(v, w, q):
    i = np.argsort(v)
    c = np.cumsum(w[i]); c /= c[-1]
    return [float(v[i][np.searchsorted(c, qq / 100)]) for qq in q]


LI_52 = {   # LI docs/ch11-pose-density-families.md §5.2：elevation / azimuth 百分位 1/50/99（Haar MC 64k + ρ_pose 加权，0.5° 族宽）
    "random": ((-24, 13, 53), (-41, 0, 41)),
    "column": ((-27, 32, 55), (-40, 0, 37)),
    "plate":  ((14, 15, 16), (24, 26, 40)),
    "parry":  ((30, 45, 48), (-40, -1, 36)),
    "lowitz": ((15, 39, 56), (-35, 10, 39)),
}


def check_families(rng):
    print("\n[1]–[5] 五族 × 3-5：像的维数、每个半径圆被填上的位置角、与 LI §5.2 落点百分位对照")
    res = {}
    for name, spec in FAMILIES.items():
        params, x, w, w_li = sample_family(name, rng)
        ok = ~np.isnan(x[:, 0])
        x, w, w_li = x[ok], w[ok], w_li[ok]
        D, pa = dist_pa(x)
        # 维数：在可行样本里抽 40 个内点，天空映射 Jacobian 的秩
        pts = rng.choice(np.flatnonzero(ok), 40, replace=False)
        if name == "random":
            fun = lambda p: sky(chain(*[np.array([v]) for v in p]))[0]
            az_, zen_, roll_ = rng.uniform(0, 360, 400), np.degrees(np.arccos(rng.uniform(-1, 1, 400))), rng.uniform(0, 360, 400)
            cand = [p for p in zip(az_, zen_, roll_) if not np.isnan(fun(p)[0])][:40]
        else:
            fun = lambda p, f=spec["pose"]: sky(f([np.array([v]) for v in p]))[0]
            cand = [tuple(par[i] for par in params) for i in pts]
        ranks = family_rank(fun, cand)
        dim_img = max(ranks)
        el_pct = wpct(az_el(x)[1], w, (1, 50, 99))
        az_pct = wpct(az_el(x)[0], w, (1, 50, 99))
        el_li = wpct(az_el(x)[1], w_li, (1, 50, 99))
        az_li = wpct(az_el(x)[0], w_li, (1, 50, 99))
        above = float(w[az_el(x)[1] > SUN_H].sum() / w.sum())
        side = np.sign(pa[np.abs(pa) < 179.5])
        print(f"\n  [{list(FAMILIES).index(name) + 1}] {name}：姿态族 {spec['dim']} 维，天空像的维数（Jacobian 秩）{ranks} "
              f"⇒ 纤维 {spec['dim'] - dim_img} 维；D ∈ [{D.min():.4f}, {D.max():.2f}]°")
        k0 = int(np.argmin(D))
        a0, e0 = az_el(x[k0])
        print(f"    最近处：D = {D[k0]:.4f}°，位置角 {pa[k0]:+.2f}°（方位 {float(a0):+.2f}°、仰角 {float(e0):.2f}°）；"
              f"最远处位置角 {pa[int(np.argmax(D))]:+.2f}°")
        print(f"    位置角两侧：+侧 {np.mean(side > 0) * 100:.1f} %、−侧 {np.mean(side < 0) * 100:.1f} %（按样本数，不加权）")
        fills = fill_table(name, D, pa)
        li_el, li_az = LI_52[name]
        print(f"    加权百分位 1/50/99：仰角 {el_pct[0]:.0f} / {el_pct[1]:.0f} / {el_pct[2]:.0f}°（LI {li_el[0]} / {li_el[1]} / {li_el[2]}），"
              f"方位 {az_pct[0]:.0f} / {az_pct[1]:.0f} / {az_pct[2]:.0f}°（LI {li_az[0]} / {li_az[1]} / {li_az[2]}）")
        if not np.array_equal(w, w_li):
            print(f"    LI 口径（支撑集上不加权）：仰角 {el_li[0]:.0f} / {el_li[1]:.0f} / {el_li[2]:.0f}°，方位 {az_li[0]:.0f} / {az_li[1]:.0f} / {az_li[2]:.0f}°")
        print(f"    落在太阳之上的份额（姿态测度加权）{above * 100:.1f} %")
        res[name] = dict(D=D, pa=pa, x=x, w=w, dim=dim_img, fills=fills, el=el_pct, az=az_pct, above=above)
        assert D.min() > D_MIN - 1e-6, "五族的最近处都不可能小于 D_min"
    # 断言：随机 2 维且每个半径圆整圈填满；片晶、Parry 1 维；柱晶、Lowitz 2 维
    r = res
    assert r["random"]["dim"] == 2 and r["plate"]["dim"] == 1 and r["parry"]["dim"] == 1
    assert r["column"]["dim"] == 2 and r["lowitz"]["dim"] == 2
    for d0 in D_PROBE:
        assert sum(b - a for a, b in r["random"]["fills"][d0]) >= 359, "随机：每个半径圆整圈填满"
    # 片晶：单条 3-5 只在 +侧，光点与太阳同高度（幻日在右，拖尾沿幻日环往外）
    assert np.all(r["plate"]["pa"] > 0) and np.max(np.abs(az_el(r["plate"]["x"])[1] - SUN_H)) < 1e-9
    assert r["plate"]["D"].min() > D_MIN + 0.1          # h = 15° 时幻日已离开 22° 晕内缘
    # 柱晶：D_min 取到（与晕相切），切点在正上 / 正下
    k = np.argmin(r["column"]["D"])
    assert abs(r["column"]["D"][k] - D_MIN) < 0.01 and min(abs(r["column"]["pa"][k]), 180 - abs(r["column"]["pa"][k])) < 2
    # 与 LI §5.2 的定性对照：片晶仰角中位 = 太阳高度、方位为正；Parry / Lowitz 中位仰角在太阳之上
    assert abs(r["plate"]["el"][1] - SUN_H) < 1 and r["plate"]["az"][1] > 0
    assert r["parry"]["el"][1] > SUN_H + 20 and r["lowitz"]["el"][1] > SUN_H
    return res


def orbit_paths():
    """3-5 所在 D6h 轨道里的 labelled 光路：从侧面 k 入、从侧面 k ± 2 出（C6 转 × 竖直镜面），共 12 条。"""
    return [(k, 3 + (k - 3 + s) % 6) for k in range(3, 9) for s in (2, -2)]


def check_orbit(res, rng):
    print("\n[6] D6h 轨道：同一个楔的 12 条 labelled 光路")
    paths = orbit_paths()
    for p in paths:
        M = fold_matrix(CRYSTAL, list(p))
        assert np.allclose(M, np.eye(3)) and abs(wedge_angle(CRYSTAL, M, *p) - 60.0) < 1e-9
    print(f"  {len(paths)} 条：{', '.join('-'.join(map(str, p)) for p in paths)}；全部 M = I、楔角 60°（同一个 Φ 类）")
    # C6 等变：path (k, k+2) 在姿态 R 下 ≡ path 3-5 在姿态 R·Rz(60°(k−3)) 下（点群作用搬到姿态上 = SO(3) 上的群卷积）
    R = haar_rotations(2000, rng)
    worst = 0.0
    for k in range(3, 9):
        p = (k, 3 + (k - 3 + 2) % 6)
        a, b = sky(R, p), sky(R @ Rz(60.0 * (k - 3)), PATH)
        both = ~np.isnan(a[:, 0]) & ~np.isnan(b[:, 0])
        assert np.array_equal(np.isnan(a[:, 0]), np.isnan(b[:, 0]))
        worst = max(worst, float(np.abs(a[both] - b[both]).max()))
    print(f"  C6 等变：path (k, k+2) @ R ≡ 3-5 @ R·Rz(60°(k−3))，2000 个 Haar 姿态最大残差 {worst:.1e}")
    assert worst < 1e-12
    # 每族：12 条合起来的像关于太阳竖直面（pa ↔ −pa）镜像对称；单条 3-5 不对称的族（片晶）由镜像伙伴 3-7 补另一侧
    print("  各族 12 条合起来：每个半径圆上的位置角集合 vs 单条 3-5")
    fams = {"plate": (np.arange(0, 360, 0.002), None), "parry": (np.arange(0, 360, 0.002), None)}
    out = {}
    for name in ("plate", "column", "parry", "lowitz"):
        if name in fams:
            az = fams[name][0]
            R = chain(az, 0.0 if name == "plate" else 90.0, 0.0)
        elif name == "column":
            az, roll = np.meshgrid(np.arange(0, 360, 0.5), np.arange(0, 360, 0.5), indexing="ij")
            R = chain(az.ravel(), 90.0, roll.ravel())
        else:
            az, zen = np.meshgrid(np.arange(0, 360, 0.5), np.arange(0.25, 150, 0.5), indexing="ij")
            R = chain(az.ravel(), zen.ravel(), 0.0)
        per = {}
        for p in paths:
            x = sky(R, p)
            x = x[~np.isnan(x[:, 0])]
            per[p] = dist_pa(x)
        allD = np.concatenate([v[0] for v in per.values()])
        allpa = np.concatenate([v[1] for v in per.values()])
        lit = [p for p in paths if len(per[p][0])]
        print(f"   {name}：12 条里有像的 {len(lit)} 条（{', '.join('-'.join(map(str, p)) for p in lit)}）")
        if name == "parry":           # 逐条：Parry 弧是一族，每条标号光路给哪一支
            for p in lit:
                Dp, pap = per[p]
                k = int(np.argmin(Dp))
                print(f"     {'-'.join(map(str, p))}：D ∈ [{Dp.min():.3f}, {Dp.max():.2f}]°，最近处位置角 {pap[k]:+.1f}°，"
                      f"位置角 ∈ [{pap.min():+.1f}, {pap.max():+.1f}]°")
        sym_ok = True
        for d0 in D_PROBE:
            m = (allD >= d0) & (allD < d0 + BAND)
            s_all = intervals(allpa[m])
            s_mir = intervals(-allpa[m])
            m1 = (per[PATH][0] >= d0) & (per[PATH][0] < d0 + BAND)
            s_one = intervals(per[PATH][1][m1])
            sym = s_all == s_mir
            sym_ok &= sym
            print(f"     D≈{d0:>4.1f}°：3-5 单条 {fmt(s_one):<28s} 12 条合起来 {fmt(s_all)}  左右对称 {sym}")
        out[name] = (per, sym_ok)
        assert sym_ok, f"{name}：轨道求和后应关于太阳竖直面镜像对称"
    # 片晶：3-5 与 3-7 恰好是一对镜像（左右幻日）
    D5, pa5 = out["plate"][0][(3, 5)]
    D7, pa7 = out["plate"][0][(3, 7)]
    print(f"  片晶 3-5 最近处 D = {D5.min():.4f}° 位置角 {pa5[np.argmin(D5)]:+.3f}°；3-7 最近处 D = {D7.min():.4f}° "
          f"位置角 {pa7[np.argmin(D7)]:+.3f}° ⇒ 右 / 左幻日")
    assert abs(D5.min() - D7.min()) < 1e-9 and abs(pa5[np.argmin(D5)] + pa7[np.argmin(D7)]) < 1e-6
    return out


def check_mirror(rng):
    """[7] ch1 思考题：单条 3-5 为什么只有幻日是单边的？

    天空左右镜像 σ_w = diag(1, −1, 1)（过太阳的竖直面，太阳方向不动）；晶体底面镜像 σ_h = diag(1, 1, −1) 把每个柱面
    映成自己 ⇒ 3-5 不变。于是姿态 R 的像经 σ_w 镜像 = 姿态 σ_w·R·σ_h（仍是真旋转）的像。单条 3-5 的像左右对称，当且仅当
    姿态族在 R ↦ σ_w R σ_h 下不变；这个映射把 c 轴天顶角 ζ 变成 180° − ζ、面 3 的上下不变。"""
    print("\n[7] 左右镜像：3-5 @ σ_w·R·σ_h ≡ σ_w（3-5 @ R）")
    sw, sh = np.diag([1.0, -1.0, 1.0]), np.diag([1.0, 1.0, -1.0])
    R = haar_rotations(5000, rng)
    a, b = sky(sw @ R @ sh), sky(R) @ sw
    both = ~np.isnan(a[:, 0])
    assert np.array_equal(both, ~np.isnan(b[:, 0]))
    res = float(np.abs(a[both] - b[both]).max())
    print(f"  5000 个 Haar 姿态最大残差 {res:.1e}")
    assert res < 1e-12
    # 映射在各族参数上的作用：chain(az, ζ, roll) ↦ chain(?, 180° − ζ, ?)；逐族检查族是否映回自身
    az = rng.uniform(0, 360, 200)
    for name, zen, roll in (("plate", 0.0, 0.0), ("column", 90.0, None), ("parry", 90.0, 0.0), ("lowitz", 30.0, 0.0)):
        rl = rng.uniform(0, 360, 200) if roll is None else np.full(200, roll)
        Rm = sw @ chain(az, zen, rl) @ sh
        z_new = np.degrees(np.arccos(np.clip(Rm[:, 2, 2], -1, 1)))
        # roll（面 3 相对过 c 轴竖直面的转角）：c 轴不在极点时按 LI c_axis_roll
        r_new = np.degrees(np.arctan2(-Rm[:, 2, 1], Rm[:, 2, 0])) if abs(zen - 0) > 1 else np.full(200, np.nan)
        print(f"  {name:6s}：ζ = {zen:5.1f}° ↦ {np.unique(np.round(z_new, 9))[:3]}°"
              + (f"，roll {'自由' if roll is None else f'= {roll:.0f}°'} ↦ "
                 f"{'自由' if roll is None else np.unique(np.round(r_new % 360, 9))[:3]}" if not np.all(np.isnan(r_new)) else ""))
        assert np.allclose(z_new, 180.0 - zen, atol=1e-9)
        if roll is not None and zen > 1:
            assert np.allclose(np.cos(np.radians(r_new - roll)), 1.0, atol=1e-12), "面 3 的上下不变"
    # 片晶 ζ = 0 映到 ζ = 180°（c 轴朝下、标号顺序反过来的片晶）：理想片晶族不含它 ⇒ 3-5 只给一侧
    x0 = sky(chain(np.arange(0, 360, 0.01), 0.0, 0.0))
    x1 = sky(chain(np.arange(0, 360, 0.01), 180.0, 0.0))
    D0, pa0 = dist_pa(x0[~np.isnan(x0[:, 0])])
    D1, pa1 = dist_pa(x1[~np.isnan(x1[:, 0])])
    print(f"  片晶 ζ=0°：3-5 最近处位置角 {pa0[np.argmin(D0)]:+.3f}°；ζ=180°（翻面）：{pa1[np.argmin(D1)]:+.3f}° ⇒ 翻面 = 另一侧幻日")
    assert abs(pa0[np.argmin(D0)] + pa1[np.argmin(D1)]) < 1e-3 and np.all(pa1 < 0)
    print("  ⇒ 柱晶（ζ=90° 映回自身、roll 全取）、Parry（ζ=90°、面 3 仍朝上）、随机：族在镜像下不变 ⇒ 单条 3-5 就左右对称；"
          "片晶 ζ=0 ↦ 180°、理想族不含 ⇒ 单边；Lowitz 支撑 ζ∈[0,180) 两边都有、权重偏 ζ 小 ⇒ 支撑对称、亮度偏一侧")


def main():
    rng = np.random.default_rng(RNG_SEED)
    check_setup()
    res = check_families(rng)
    check_orbit(res, rng)
    check_mirror(rng)
    print("\n[小结] 维数：随机 3→2、片晶 1→1、柱晶 2→2、Parry 1→1、Lowitz 2→2（姿态族维数 → 天空像维数）；"
          "单条 3-5 在片晶下只点亮 +侧（右幻日；片晶族在左右镜像下不封闭），12 条同类光路合起来左右对称")
    print("OK")


if __name__ == "__main__":
    main()
