"""互证 B（图级）：22° 幻日的光点轨迹（TK1999 Fig. 33 一类 pole 图里 $(0,\\pm1,0)$ 处那张的形状），
两套语言各算一遍、数据级叠合。产出 ../data/crosscheck_b_locus_sigma{0,10,20,30}.csv 与 ../data/crosscheck_b_inner_edge.csv。

- 姿态：片晶 $R=\\mathrm{zrot}(\\phi)$，$\\phi$ 取 361 个等距点覆盖 $[0°,360°]$；太阳 $\\mathbf S=(\\cos\\Sigma,0,\\sin\\Sigma)$。
- 每点：本系列 :func:`crosscheck_bridge.light_point`（A60-12：$M=I$，`3-5`）与 TK1999 :func:`tape_halo_function.halo_point`
  （$u=\\mathrm{zrot}(\\phi)u_0$，$\\alpha=60$），都换算到 S-centered 坐标 $(\\Delta,\\tau)$ [TK1999 Eq. (53)]。
- 内边：三条链路各算一次幻日内边角距 $\\min_\\phi\\Delta$——TK1999 光点扫描、Tape 1980 Bravais 链路
  :func:`tape_halo_function.sundog_inner_edge_1980`、本系列光点扫描；$\\Sigma=0$ 时再核 A60-10 的 $21.8°+120°=141.8°$
  （ch8 §6「142° 锐边」的理论值；ch8 报告的 142.56° 是半高点，定义不同，见 ../data/notes.md）。

只出数据不出图（issue 范围 3「图只做到能对照即可」；正式图留绘图任务）。
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from lumice_integral.geometry import HexPrism, fold_matrix

from crosscheck_a import write_csv
from crosscheck_bridge import light_point, plate_attitude, s_centered, sun_direction, wedge_orientation
from tape_halo_function import deviation_deg, halo_point, min_deviation_tk, sundog_inner_edge_1980

DATA = Path(__file__).resolve().parents[1] / "data"
SIGMAS = (0, 10, 20, 30)
N_PHI = 361
CRYSTAL = HexPrism.from_ratio(1.0)
I3 = np.eye(3)
M_3457 = fold_matrix(CRYSTAL, [3, 4, 5, 7])


def locus(sigma_deg: float, n_phi: int = N_PHI) -> list[tuple]:
    """逐 $\\phi$ 的行：``(phi, delta_matrix, delta_tape, tau_matrix, tau_tape, reach_matrix, reach_tape)``。"""
    S = sun_direction(sigma_deg)
    rows = []
    for phi in np.linspace(0.0, 360.0, n_phi):
        R = plate_attitude(phi)
        H_m = light_point(CRYSTAL, I3, 3, 5, R, S)
        H_t = halo_point(wedge_orientation(CRYSTAL, I3, 3, 5, R), 60.0, S)
        d_m, t_m = s_centered(S, H_m) if H_m is not None else (math.nan, math.nan)
        d_t, t_t = s_centered(S, H_t) if H_t is not None else (math.nan, math.nan)
        rows.append((phi, d_m, d_t, t_m, t_t, H_m is not None, H_t is not None))
    return rows


def _golden_min(f, lo: float, hi: float, tol: float = 1e-10) -> tuple[float, float]:
    """区间 ``[lo, hi]`` 上单峰函数的黄金分割极小，返回 ``(x, f(x))``。"""
    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    while b - a > tol:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    x = (a + b) / 2
    return x, f(x)


def inner_edge(sigma_deg: float, M: np.ndarray, a: int, b: int, tape: bool) -> float:
    """幻日内边角距 $\\min_\\phi\\arccos(\\mathbf S\\cdot\\mathbf H)$（度）：粗扫 3601 点定桥、黄金分割细化。
    ``tape=True`` 走 TK1999 光点（只对 $M=I$ 有意义——Tape 侧没有 $M$），否则走本系列光点。"""
    S = sun_direction(sigma_deg)

    def dev(phi: float) -> float:
        R = plate_attitude(phi)
        H = halo_point(wedge_orientation(CRYSTAL, I3, a, b, R), 60.0, S) if tape else light_point(CRYSTAL, M, a, b, R, S)
        return deviation_deg(S, H) if H is not None else math.inf

    grid = np.linspace(0.0, 360.0, 3601)
    vals = np.array([dev(p) for p in grid])
    i = int(np.argmin(vals))
    return _golden_min(dev, grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)])[1]


def inner_edge_rows() -> list[tuple]:
    rows = []
    for s in SIGMAS:
        tk = inner_edge(s, I3, 3, 5, tape=True)
        t80 = sundog_inner_edge_1980(s)
        mx = inner_edge(s, I3, 3, 5, tape=False)
        a6010 = inner_edge(s, M_3457, 3, 7, tape=False)
        rows.append((s, tk, t80, mx, a6010, a6010 - mx))
    return rows


def main() -> None:
    header = ["phi_deg", "delta_matrix_deg", "delta_tape_deg", "tau_matrix_deg", "tau_tape_deg", "reachable_matrix", "reachable_tape"]
    for s in SIGMAS:
        rows = locus(s)
        write_csv(DATA / f"crosscheck_b_locus_sigma{s}.csv", header, rows)
        d = np.array([(r[1], r[2]) for r in rows if r[5] and r[6]])
        t = np.array([(r[3], r[4]) for r in rows if r[5] and r[6]])
        agree = sum(r[5] == r[6] for r in rows)
        print(f"Σ={s:2d}: {len(d)} reachable, reach agree {agree}/{len(rows)}, "
              f"max |Δ diff| {np.abs(d[:, 0] - d[:, 1]).max():.2e}°, max |τ diff| {np.abs(t[:, 0] - t[:, 1]).max():.2e}°")
    rows = inner_edge_rows()
    write_csv(DATA / "crosscheck_b_inner_edge.csv",
              ["sigma_deg", "inner_edge_tk1999_deg", "inner_edge_tape1980_deg", "inner_edge_matrix_deg",
               "inner_edge_A60_10_deg", "A60_10_minus_A60_12_deg"], rows)
    for r in rows:
        print(f"Σ={r[0]:2d}: TK1999 {r[1]:.6f}  Tape1980 {r[2]:.6f}  matrix {r[3]:.6f}  A60-10 {r[4]:.6f}  (+{r[5]:.6f})")
    print(f"Δ_m(60°) by Eq. (41) = {min_deviation_tk(60.0):.6f}")


if __name__ == "__main__":
    main()
