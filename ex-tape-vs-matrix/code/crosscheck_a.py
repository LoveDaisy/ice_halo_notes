"""互证 A（逐点）：同一条光路、同一取向、同一太阳方向，Tape 的 halo function 与本系列 $\\Phi$ 算出同一个光点。
产出 ../data/crosscheck_a_A60-12.csv、crosscheck_a_A60-10_plate.csv、crosscheck_a_A60-10_column_negative.csv、crosscheck_a_summary.md。

三组：
1. A60-12（`3-5`，$M=I$）：1000 组 Haar 均匀姿态 × $S^2$ 均匀太阳方向（种子 0），本系列 :func:`crosscheck_bridge.light_point_batch`
   vs TK1999 :func:`tape_halo_function.halo_point_batch`，比角距离与可达判定。
2. A60-10（`3-4-5-7`，$M=R_{\\mathbf c}(120°)$）片晶族：200 组 $(\\phi,\\Sigma)$，验证 $RMR^{-1}=\\mathrm{zrot}(120°)$ 与
   Rule-1 恒等式 $\\mathbf H_{3457}(R,\\mathbf S)=\\mathrm{zrot}(120°)\\,\\mathbf H_{35}(R,\\mathbf S)$（右端是 Tape 侧算的幻日光点）。
3. A60-10 柱晶族负例：同一组 $(\\phi,\\Sigma)$（加一个绕 c 轴的自转角），量化 $RMR^{-1}$ 偏离绕竖直旋转的程度
   （$\\angle(RMR^{-1}\\mathbf k,\\mathbf k)$）、以及「强行套 Rule-1 技巧」与本系列真值的差——Tape 框架里没有 $M$ 这一维的数值证据。

两侧的可达判定判据等价性（plan Step 4 风险）：TK1999 的 $\\mathbf S\\cdot\\mathbf N\\ge0$ ⇔ `phi_batch` 的 `outside`
（$\\mathbf d\\cdot\\mathbf n_a<0$，$\\mathbf d=-\\mathbf S$）；第二次投影的 $\\mathbf T\\cdot\\mathbf X\\ge0$ 且根号内 $\\ge0$ ⇔ `exit_ok`
（$\\hat{\\mathbf d}_1\\cdot\\tilde{\\mathbf n}_b\\ge\\cos\\theta_c$，因 $(\\mathbf T\\cdot\\mathbf X)^2\\ge n^2-1\\iff(\\hat{\\mathbf d}_1\\cdot\\tilde{\\mathbf n}_b)^2\\ge1-1/n^2$）；
`entry_ok`（$-\\hat{\\mathbf d}_1\\cdot\\mathbf n_a\\ge\\cos\\theta_c$）对从外侧进入的光线由 Snell 自动满足（内角 ≤ 临界角），
TK1999 没有对应判据——差别只在掠入射的浮点边界上。
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from lumice_integral.geometry import HexPrism, fold_matrix

from crosscheck_bridge import (
    K_HAT, angular_distance, haar_so3, light_point_batch, plate_attitude, sun_direction, wedge_orientation,
)
from halo_notes.math.attitude import column_attitude
from halo_notes.math.sampling import uniform_s2
from tape_halo_function import halo_point_batch, standard_normals, zrot

DATA = Path(__file__).resolve().parents[1] / "data"
SEED = 0
TOL_RAD = 1e-6                       # issue 的逐点通过阈值
CRYSTAL = HexPrism.from_ratio(1.0)   # Φ 不依赖 h/a，取值只为复现
I3 = np.eye(3)
M_3457 = fold_matrix(CRYSTAL, [3, 4, 5, 7])   # = R_c(120°)


def _fmt(x) -> str:
    if isinstance(x, (bool, np.bool_)):
        return "1" if x else "0"
    if isinstance(x, (float, np.floating)):
        return "nan" if np.isnan(x) else f"{x:.12g}"
    return str(x)


def write_csv(path: Path, header: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([_fmt(x) for x in r])


# ---- 1. A60-12 ---------------------------------------------------------------------


def run_a60_12(n: int = 1000, seed: int = SEED) -> dict:
    """返回逐点明细与统计：``R``、``S``、两侧光点、角距离、可达标记。"""
    rng = np.random.default_rng(seed)
    R = haar_so3(n, rng)
    S = uniform_s2(n, rng)
    H_m = light_point_batch(CRYSTAL, I3, 3, 5, R, S)
    H_t = halo_point_batch(wedge_orientation(CRYSTAL, I3, 3, 5, R), 60.0, S)
    reach_m = ~np.isnan(H_m).any(axis=1)
    reach_t = ~np.isnan(H_t).any(axis=1)
    both = reach_m & reach_t
    dist = np.full(n, np.nan)
    dist[both] = angular_distance(H_m[both], H_t[both])
    # 到入射侧定义域边界的距离 S·N（掠入射 → 0；负值 = 从背面照楔，"no ray"），风险 3 用来区分边界敏感与公式错误
    N = wedge_orientation(CRYSTAL, I3, 3, 5, R) @ standard_normals(60.0)[0]
    s_dot_n = np.einsum("ij,ij->i", S, N)
    return dict(R=R, S=S, H_m=H_m, H_t=H_t, reach_m=reach_m, reach_t=reach_t, dist=dist, s_dot_n=s_dot_n,
                n=n, n_reach_m=int(reach_m.sum()), n_reach_t=int(reach_t.sum()),
                n_agree=int((reach_m == reach_t).sum()),
                max_dist=float(np.nanmax(dist)) if both.any() else float("nan"),
                mean_dist=float(np.nanmean(dist)) if both.any() else float("nan"),
                n_over_tol=int((dist[both] > TOL_RAD).sum()))


# ---- 2 / 3. A60-10：片晶族与柱晶族共用同一组采样 ------------------------------------------


def sample_attitudes(n: int = 200, seed: int = SEED) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """$(\\phi,\\Sigma,\\theta_{\\mathrm{roll}})$：$\\phi\\in[0,360)$ 方位、$\\Sigma\\in[-30,80]$ 太阳高度、$\\theta_{\\mathrm{roll}}\\in[0,360)$
    绕 c 轴自转（只有柱晶族用到；片晶的自转与 $\\phi$ 合并）。"""
    rng = np.random.default_rng(seed + 1)
    return rng.uniform(0, 360, n), rng.uniform(-30, 80, n), rng.uniform(0, 360, n)


def run_a60_10_plate(phi: np.ndarray, sigma: np.ndarray) -> dict:
    """片晶：$R=\\mathrm{zrot}(\\phi)$。断言 $RMR^{-1}=\\mathrm{zrot}(120°)$；比 $\\mathbf H_{3457}$（本系列）与
    $\\mathrm{zrot}(120°)\\mathbf H_{35}$（Tape 侧 + Rule 1）。"""
    n = len(phi)
    R = np.stack([plate_attitude(p) for p in phi])
    S = np.stack([sun_direction(s) for s in sigma])
    conj = R @ M_3457 @ np.transpose(R, (0, 2, 1))
    conj_err = np.abs(conj - zrot(120.0)).reshape(n, -1).max(axis=1)
    H_true = light_point_batch(CRYSTAL, M_3457, 3, 7, R, S)
    H_35_tape = halo_point_batch(wedge_orientation(CRYSTAL, I3, 3, 5, R), 60.0, S)
    H_rule1 = H_35_tape @ zrot(120.0).T
    reach_true = ~np.isnan(H_true).any(axis=1)
    reach_tape = ~np.isnan(H_35_tape).any(axis=1)
    both = reach_true & reach_tape
    dist = np.full(n, np.nan)
    dist[both] = angular_distance(H_true[both], H_rule1[both])
    return dict(phi=phi, sigma=sigma, R=R, S=S, conj_err=conj_err, H_true=H_true, H_rule1=H_rule1,
                reach_true=reach_true, reach_tape=reach_tape, dist=dist,
                n=n, n_reach=int(both.sum()), n_agree=int((reach_true == reach_tape).sum()),
                max_conj_err=float(conj_err.max()),
                max_dist=float(np.nanmax(dist)) if both.any() else float("nan"))


def run_a60_10_column(phi: np.ndarray, sigma: np.ndarray, roll: np.ndarray) -> dict:
    """柱晶：$R=$ `column_attitude(phi, roll)`。$RMR^{-1}$ 是绕水平轴 $R\\mathbf k$ 转 120°，不是绕竖直的旋转：
    记 $\\angle(RMR^{-1}\\mathbf k,\\mathbf k)$；比本系列真值 $\\mathbf H_{3457}$、强行套 Rule-1 的 $\\mathrm{zrot}(120°)\\mathbf H_{35}$、
    以及本系列自己的共轭式 $RMR^{-1}\\mathbf H_{35}$（后者应与真值相等——这是 $\\Phi_{3457}=M\\circ\\Phi_{35}$ 搬到天球上的形式）。"""
    n = len(phi)
    R = np.stack([column_attitude(p, r) for p, r in zip(phi, roll)])
    S = np.stack([sun_direction(s) for s in sigma])
    conj = R @ M_3457 @ np.transpose(R, (0, 2, 1))
    k_img = conj @ K_HAT
    dev_k = np.degrees(angular_distance(k_img, np.broadcast_to(K_HAT, (n, 3))))
    H_true = light_point_batch(CRYSTAL, M_3457, 3, 7, R, S)
    H_35_tape = halo_point_batch(wedge_orientation(CRYSTAL, I3, 3, 5, R), 60.0, S)
    H_rule1 = H_35_tape @ zrot(120.0).T
    H_conj = np.einsum("kij,kj->ki", conj, H_35_tape)
    reach_true = ~np.isnan(H_true).any(axis=1)
    reach_tape = ~np.isnan(H_35_tape).any(axis=1)
    both = reach_true & reach_tape
    dist_rule1 = np.full(n, np.nan)
    dist_conj = np.full(n, np.nan)
    dist_rule1[both] = np.degrees(angular_distance(H_true[both], H_rule1[both]))
    dist_conj[both] = angular_distance(H_true[both], H_conj[both])
    return dict(phi=phi, sigma=sigma, roll=roll, R=R, S=S, dev_k=dev_k, H_true=H_true, H_rule1=H_rule1,
                reach_true=reach_true, reach_tape=reach_tape, dist_rule1_deg=dist_rule1, dist_conj=dist_conj,
                n=n, n_reach=int(both.sum()), n_agree=int((reach_true == reach_tape).sum()),
                dev_k_min=float(dev_k.min()), dev_k_max=float(dev_k.max()),
                rule1_min_deg=float(np.nanmin(dist_rule1)) if both.any() else float("nan"),
                rule1_max_deg=float(np.nanmax(dist_rule1)) if both.any() else float("nan"),
                rule1_mean_deg=float(np.nanmean(dist_rule1)) if both.any() else float("nan"),
                max_conj_dist=float(np.nanmax(dist_conj)) if both.any() else float("nan"))


# ---- 落盘 --------------------------------------------------------------------------


def main() -> None:
    a = run_a60_12()
    write_csv(DATA / "crosscheck_a_A60-12.csv",
              ["i", "Sx", "Sy", "Sz", "reach_matrix", "reach_tape", "Hx_matrix", "Hy_matrix", "Hz_matrix",
               "Hx_tape", "Hy_tape", "Hz_tape", "dist_rad", "over_tol", "S_dot_N"],
              ((i, *a["S"][i], a["reach_m"][i], a["reach_t"][i], *a["H_m"][i], *a["H_t"][i], a["dist"][i],
                bool(a["dist"][i] > TOL_RAD), a["s_dot_n"][i]) for i in range(a["n"])))

    phi, sigma, roll = sample_attitudes()
    p = run_a60_10_plate(phi, sigma)
    write_csv(DATA / "crosscheck_a_A60-10_plate.csv",
              ["i", "phi_deg", "sigma_deg", "conj_err", "reach_matrix", "reach_tape",
               "Hx_matrix", "Hy_matrix", "Hz_matrix", "Hx_rule1", "Hy_rule1", "Hz_rule1", "dist_rad"],
              ((i, phi[i], sigma[i], p["conj_err"][i], p["reach_true"][i], p["reach_tape"][i],
                *p["H_true"][i], *p["H_rule1"][i], p["dist"][i]) for i in range(p["n"])))

    c = run_a60_10_column(phi, sigma, roll)
    write_csv(DATA / "crosscheck_a_A60-10_column_negative.csv",
              ["i", "phi_deg", "sigma_deg", "roll_deg", "dev_k_deg", "reach_matrix", "reach_tape",
               "Hx_matrix", "Hy_matrix", "Hz_matrix", "Hx_rule1", "Hy_rule1", "Hz_rule1",
               "dist_rule1_deg", "dist_conj_rad"],
              ((i, phi[i], sigma[i], roll[i], c["dev_k"][i], c["reach_true"][i], c["reach_tape"][i],
                *c["H_true"][i], *c["H_rule1"][i], c["dist_rule1_deg"][i], c["dist_conj"][i]) for i in range(c["n"])))

    (DATA / "crosscheck_a_summary.md").write_text(f"""# 互证 A（逐点）统计

由 `code/crosscheck_a.py` 产出（种子 {SEED}，`HexPrism.from_ratio(1.0)`，$n=1.31$）。角距离用 $2\\arcsin(|\\mathbf a-\\mathbf b|/2)$。

## 1. A60-12（`3-5`，$M=I$）：本系列 $-R\\Phi(-R^{{-1}}\\mathbf S)$ vs TK1999 $\\mathbf H(Ru_0,60°,\\mathbf S)$

| 项 | 值 |
|---|---|
| 样本数（Haar 均匀 $R$ × $S^2$ 均匀 $\\mathbf S$） | {a['n']} |
| 本系列可达 / Tape 可达 | {a['n_reach_m']} / {a['n_reach_t']} |
| 可达判定一致（`None`↔"no ray"） | {a['n_agree']} / {a['n']} = {100 * a['n_agree'] / a['n']:.1f}% |
| 两侧都可达时最大角距离 (rad) | {a['max_dist']:.3e} |
| 两侧都可达时平均角距离 (rad) | {a['mean_dist']:.3e} |
| 超阈值（> {TOL_RAD:g} rad）样本数 | {a['n_over_tol']} |

## 2. A60-10（`3-4-5-7`，$M=R_{{\\mathbf c}}(120°)$）片晶族：$RMR^{{-1}}=\\mathrm{{zrot}}(120°)$，Rule-1 恒等式

| 项 | 值 |
|---|---|
| 样本数（$\\phi\\in[0,360)$，$\\Sigma\\in[-30,80]$） | {p['n']} |
| $\\max\\|RMR^{{-1}}-\\mathrm{{zrot}}(120°)\\|_\\infty$ | {p['max_conj_err']:.3e} |
| 可达判定一致（$\\Phi_{{3457}}$ 定义域 = $\\Phi_{{35}}$ 定义域） | {p['n_agree']} / {p['n']} |
| 两侧都可达的样本数 | {p['n_reach']} |
| $\\mathbf H_{{3457}}$（本系列）vs $\\mathrm{{zrot}}(120°)\\mathbf H_{{35}}$（Tape + Rule 1）最大角距离 (rad) | {p['max_dist']:.3e} |

## 3. A60-10 柱晶族负例：$RMR^{{-1}}$ 不是绕竖直的旋转

| 项 | 值 |
|---|---|
| 样本数（同一组 $(\\phi,\\Sigma)$ + 绕 c 轴自转 $\\theta_{{\\mathrm{{roll}}}}$） | {c['n']} |
| $\\angle(RMR^{{-1}}\\mathbf k,\\mathbf k)$ 的范围 (°) | [{c['dev_k_min']:.6f}, {c['dev_k_max']:.6f}] |
| 两侧都可达的样本数 | {c['n_reach']} |
| 强行套 Rule 1：$\\mathrm{{zrot}}(120°)\\mathbf H_{{35}}$ vs 本系列 $\\mathbf H_{{3457}}$ 的角距离 (°) min / mean / max | {c['rule1_min_deg']:.3f} / {c['rule1_mean_deg']:.3f} / {c['rule1_max_deg']:.3f} |
| 本系列自己的共轭式 $RMR^{{-1}}\\mathbf H_{{35}}$ vs $\\mathbf H_{{3457}}$ 最大角距离 (rad) | {c['max_conj_dist']:.3e} |

解读：柱晶姿态下 $R\\mathbf k$ 水平，$RMR^{{-1}}$ 是绕水平轴转 120°，$\\mathbf k$ 被转出 120°——它不在 TK1999 的 $Z$（绕竖直旋转群）里，
Rule 1 不适用，atlas 里没有对象承载它；本系列的 $\\Phi_{{3457}}=M\\circ\\Phi_{{35}}$ 不依赖 Rule 1，共轭式逐点成立。
「需要怎样补一个折叠才等价」：在 TK1999 的楔对象上追加一个固定在**晶体**（而非楔）上的正交算子 $M$，
光点公式变为 $\\mathbf H=RMR^{{-1}}\\,\\mathbf F(u\\mathbf N_0,u\\mathbf X_0,\\mathbf S)$——这正是本系列 signature 的 $M$ 维。
""", encoding="utf-8")
    print(f"A60-12: agree {a['n_agree']}/{a['n']}, max dist {a['max_dist']:.3e} rad, over tol {a['n_over_tol']}")
    print(f"A60-10 plate: conj err {p['max_conj_err']:.3e}, max dist {p['max_dist']:.3e} rad ({p['n_reach']} reachable)")
    print(f"A60-10 column: dev_k [{c['dev_k_min']:.3f}, {c['dev_k_max']:.3f}]°, rule1 diff "
          f"{c['rule1_min_deg']:.2f}–{c['rule1_max_deg']:.2f}°, conj max {c['max_conj_dist']:.3e} rad")


if __name__ == "__main__":
    main()
