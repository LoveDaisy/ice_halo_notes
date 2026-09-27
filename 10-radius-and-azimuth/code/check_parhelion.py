# 核验 ch10 提纲的数字（确定性，无网络，末行 OK）：3-5 光路的出射点角距离 D_P(u) 只看 u；片晶把 u 限在仰角 = h 的纬度圆上，
# 圆上 D_P 的最小值（幻日）随 h 外移，与 Bravais 等效折射率闭式一致；纬度圆整条出光学定义域的临界高度；柱晶取到全局
# D_min（切弧与 22° 晕相切）、切点在太阳正上 / 正下，与太阳高度无关。Lumice 独立链路见 check_parhelion_lumice.py。
import numpy as np

from halo_notes.math.wedge import min_deviation_deg
from lumice_integral.geometry import N_ICE, HexPrism, fold_matrix
from lumice_integral.symmetry.attitude import column_attitude
from lumice_integral.symmetry.signature import phi_batch, wedge_angle

PATH = (3, 5)
CRYSTAL = HexPrism()          # phi 只用面法向（无限长棱镜），与 h/a 无关；几何走廊不在本脚本范围（见提纲待裁定）
N = N_ICE                     # 1.31，LI geometry 包的唯一权威折射率
H_LIST = (0, 10, 20, 30, 40, 50, 55, 60, 60.5, 60.7, 60.75)
THETA_STEP = 0.01             # 纬度圆方位粗扫步长（度）
TOL_DEG = 1e-6                # 数值 D_P 最小值 / 方位差 vs 闭式：局部精化到 xatol=1e-9 后的实测残差 < 1e-7°
TOL_HC = 1e-3                 # 临界高度：二分到 1e-5°，窗口网格 5e-4°
COLUMN_SUN_H = (0, 20, 45)    # 柱晶在三个太阳高度上各扫一次，D_min 与切点应与 h 无关
COLUMN_STEP = 1.0             # 柱晶 (ψ, θ) 粗网格（度），最优点附近再局部精化


def unit_from(h_deg, az_deg):
    h, a = np.radians(h_deg), np.radians(np.asarray(az_deg, float))
    return np.stack([np.cos(h) * np.cos(a), np.cos(h) * np.sin(a), np.full_like(a, np.sin(h))], axis=-1)


def az_el(v):
    v = np.asarray(v, float)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])), np.degrees(np.arcsin(np.clip(v[..., 2], -1, 1)))


M = fold_matrix(CRYSTAL, list(PATH))


def light_point(u):
    """u（晶体系里指向太阳）→ 光点方向 x = −Φ_P(−u)（晶体系，NaN = 光学定义域外）。"""
    return -phi_batch(CRYSTAL, M, PATH[0], PATH[1], -np.atleast_2d(u))


def dp(u):
    x = light_point(u)
    u = np.atleast_2d(u)
    return np.degrees(np.arccos(np.clip((x * u).sum(1), -1, 1))), x


def golden_min(f, a, b, xatol=1e-9):
    g = (np.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    while b - a > xatol:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    return (a + b) / 2


def bravais(h_deg, n=N):
    """片晶 60° 楔：n' = √(n² − sin²h)/cos h；水平面上的最小方位差 Δφ = 2 arcsin(n'/2) − 60°（n' ≥ 2 时 None）。"""
    h = np.radians(h_deg)
    n_eff = np.sqrt(n * n - np.sin(h) ** 2) / np.cos(h)
    if n_eff >= 2:
        return n_eff, None
    return n_eff, 2 * np.degrees(np.arcsin(n_eff / 2)) - 60.0


def spherical_distance(h_deg, dphi_deg):
    """同高度 h、方位差 Δφ 的两点角距离：cos D = sin²h + cos²h cos Δφ。"""
    h, p = np.radians(h_deg), np.radians(dphi_deg)
    return np.degrees(np.arccos(np.sin(h) ** 2 + np.cos(h) ** 2 * np.cos(p)))


def check_setup():
    print(f"[0] 光路 {'-'.join(map(str, PATH))}：M = I ? {np.allclose(M, np.eye(3))}，"
          f"楔角 {wedge_angle(CRYSTAL, M, *PATH):.6f}°，n = {N}")
    assert np.allclose(M, np.eye(3))
    assert abs(wedge_angle(CRYSTAL, M, *PATH) - 60.0) < 1e-9
    # 薄片晶里 3-5 直穿被底面截断时顶上来的 3-2-1-5（check_parhelion_lumice.py [L3]）：两次底面反射 M 仍 = I、同一个楔
    M4 = fold_matrix(CRYSTAL, [3, 2, 1, 5])
    print(f"    3-2-1-5：M = I ? {np.allclose(M4, np.eye(3))}，楔角 {wedge_angle(CRYSTAL, M4, 3, 5):.6f}° ⇒ 与 3-5 同一个 Φ，落点相同")
    assert np.allclose(M4, np.eye(3)) and abs(wedge_angle(CRYSTAL, M4, 3, 5) - 60.0) < 1e-9


def check_plate():
    """[1] 片晶纬度圆：数值 D_P 最小值 → 幻日同高度 → 球面余弦换算 → Bravais 闭式，三段两两对照。"""
    print("\n[1] 片晶：u 在仰角 = h 的纬度圆上扫方位 θ，D_P 的最小值 = 幻日")
    print("   h(°)  可行弧长(°)  θ*(°)       D_min(°)     Δφ*(°)      球面换算D(°)  n'        Bravais Δφ(°)  出射仰角偏差")
    th = np.arange(0.0, 360.0, THETA_STEP)
    rows = []
    for h in H_LIST:
        D, x = dp(unit_from(h, th))
        ok = ~np.isnan(D)
        # 3-5 两面都竖直、M = I ⇒ 出射方向的 z 分量守恒 ⇒ 圆上每一点的光点都与太阳同高度
        elev_err = float(np.max(np.abs(az_el(x[ok])[1] - h)))
        i = int(np.nanargmin(D))
        f = lambda t: dp(unit_from(h, t))[0][0]
        t_star = golden_min(f, th[i] - THETA_STEP, th[i] + THETA_STEP)
        d_min = f(t_star)
        dphi = abs(((az_el(light_point(unit_from(h, t_star)))[0][0] - t_star) + 180) % 360 - 180)
        d_sph = spherical_distance(h, dphi)
        n_eff, dphi_b = bravais(h)
        rows.append((h, d_min, dphi, dphi_b))
        print(f"  {h:6.2f}  {ok.sum() * THETA_STEP:9.2f}  {t_star % 360:10.5f}  {d_min:11.7f}  {dphi:11.7f}  "
              f"{d_sph:11.7f}   {n_eff:.6f}  {dphi_b:11.7f}   {elev_err:.1e}")
        assert elev_err < 1e-9
        assert abs(d_sph - d_min) < TOL_DEG, (h, d_sph, d_min)
        assert abs(dphi - dphi_b) < TOL_DEG, (h, dphi, dphi_b)
    d = [r[1] for r in rows]
    assert all(b > a for a, b in zip(d, d[1:])), "幻日角距离应随 h 单调外移"
    print(f"  幻日角距离随 h 单调增大：{d[0]:.4f}° (h=0) → {d[-1]:.4f}° (h={H_LIST[-1]})；"
          f"Δφ 与 D 在 h=40° 处相差 {rows[H_LIST.index(40)][2] - rows[H_LIST.index(40)][1]:.4f}°")
    return rows


def feasible_near(h, center, half=1.5, step=5e-4):
    th = np.arange(center - half, center + half, step)
    D, _ = dp(unit_from(h, th))
    ok = ~np.isnan(D)
    return (bool(ok.any()), float(th[ok].mean()) if ok.any() else center)


def check_critical():
    """[2] 临界高度：纬度圆整条出光学定义域（phi 全 None）的最小 h；二分 vs Bravais n' = 2 闭式 sin²h = (4 − n²)/3。"""
    print("\n[2] 临界高度：纬度圆整条出 3-5 的光学定义域")
    lo, hi = 60.7, 61.0
    ok_lo, center = feasible_near(lo, 272.9, half=10)
    assert ok_lo and not feasible_near(hi, center, half=30)[0]
    while hi - lo > 1e-5:
        mid = (lo + hi) / 2
        ok, c = feasible_near(mid, center)
        if ok:
            lo, center = mid, c
        else:
            hi = mid
    hc_num = (lo + hi) / 2
    hc_closed = float(np.degrees(np.arcsin(np.sqrt((4 - N * N) / 3))))
    print(f"  二分（phi 定义域）：h_c = {hc_num:.5f}°    Bravais n' = 2：h_c = {hc_closed:.5f}°    差 {hc_num - hc_closed:+.1e}°")
    print(f"  临界处光线在圆上的方位 θ ≈ {center % 360:.3f}°（掠射极限：入射 / 出射都贴着面）")
    assert abs(hc_num - hc_closed) < TOL_HC
    return hc_num


def check_column():
    """[3] 柱晶：c 轴水平，(ψ, θ) 两个自由度让 u 能落进截面主平面 ⇒ 取到全局 D_min；切点在太阳正上 / 正下。"""
    print("\n[3] 柱晶：(ψ, θ) 网格上 D_P 的全局最小值与切点")
    d_min_closed = min_deviation_deg(60.0, N)
    grid = np.arange(0.0, 360.0, COLUMN_STEP)
    out = []
    for h in COLUMN_SUN_H:
        s = unit_from(h, 0.0)
        R = np.stack([column_attitude(p, t) for p in grid for t in grid])
        u = np.einsum("nji,j->ni", R, s)                     # u = Rᵀ s
        D, _ = dp(u)
        # 柱晶能取到的 u：c 轴（晶体 z）水平 ⇒ u_z = cos h · cos(ψ − 太阳方位) ⇒ |u_z| ≤ cos h，一条总含赤道（主平面）的带
        uz = np.abs(u[:, 2])
        print(f"  太阳高度 {h:4.1f}°：可取 u 的 |u_z| ∈ [{uz.min():.2e}, {uz.max():.6f}]，cos h = {np.cos(np.radians(h)):.6f}")
        assert uz.min() < 1e-12 and abs(uz.max() - np.cos(np.radians(h))) < 1e-12
        best = []
        # 两个局部最小（切点上 / 下）：按光点仰角高于 / 低于太阳分别取
        x_sky = np.einsum("nij,nj->ni", R, light_point(u))
        el = az_el(x_sky)[1]
        for sign in (+1, -1):
            mask = ~np.isnan(D) & (sign * (el - h) > 0)
            k = int(np.nanargmin(np.where(mask, D, np.nan)))
            p0, t0 = grid[k // len(grid)], grid[k % len(grid)]

            def f2(pt):
                Rk = column_attitude(*pt)
                return dp(Rk.T @ s)[0][0]
            p, t = p0, t0
            for _ in range(60):                               # 坐标轮换 + 黄金分割，收敛到 1e-9°
                p = golden_min(lambda q: f2((q, t)), p - COLUMN_STEP, p + COLUMN_STEP)
                t = golden_min(lambda q: f2((p, q)), t - COLUMN_STEP, t + COLUMN_STEP)
            Rk = column_attitude(p, t)
            xs = Rk @ light_point(Rk.T @ s)[0]
            a, e = az_el(xs)
            best.append((f2((p, t)), float(a), float(e), p % 360))
        for dm, a, e, p in best:
            print(f"  太阳高度 {h:4.1f}°：D_min = {dm:.7f}°（闭式 {d_min_closed:.7f}°），切点 方位 {a:+.4f}° 仰角 {e:8.4f}°"
                  f"（= h {e - h:+.4f}°），c 轴方位 ψ = {p:.3f}°")
            assert abs(dm - d_min_closed) < TOL_DEG
            assert abs(a) < 1e-4                                 # 切点在太阳所在的竖直面内（h + D_min < 90° 时）
            assert abs(abs(e - h) - d_min_closed) < 1e-4        # 正上 / 正下 D_min 处
        out.append(best)
    print(f"  全局 D_min 与太阳高度无关、切点恒在太阳正上方 / 正下方 {d_min_closed:.4f}° 处（c 轴水平且与太阳方位垂直）")
    return d_min_closed


def main():
    check_setup()
    rows = check_plate()
    hc = check_critical()
    dmin = check_column()
    print(f"\n[小结] 22° 晕内缘 / 柱晶切点 D_min = {dmin:.4f}°；幻日 h=0 时 {rows[0][1]:.4f}°、h=40° 时 "
          f"{rows[H_LIST.index(40)][1]:.4f}°、h=60° 时 {rows[H_LIST.index(60)][1]:.4f}°；消失临界高度 {hc:.3f}°")
    print("OK")


if __name__ == "__main__":
    main()
