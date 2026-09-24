# 产出 ../img/fold_edge_density.png（图 10「反日侧窗口内族外类的单独剖面与加总剖面」）+ ../data/fold_edge_density.numbers.json：
# 参考几何 (1, 0.5)、随机取向。探针 `scratchpad/probe-fold-edges/probe_edges.py` 的正式版——不跑 Lumice，几何直接积分：
#   随机取向 ⇔ 晶体系里入射方向 u 在球面均匀。对每个族外类（`analysis/rows_h1_t0.5.csv` 里 family 空、status ok、长度 ≥ 2 的 MC 行按
#   `pbd_rep` 分组，共 ~250 类，与 `_ch9_sim.top_out_of_family` 同一分组口径），取 N_DIRS 个均匀 u（固定种子），
#   θ(u) = ∠(Φ(u), u)（`lumice_integral.symmetry.signature.phi_batch`，出射与入射传播方向的夹角 = 天上离太阳的角距），权重
#   w(u) = 入射截面 `lumice_integral.geometry.entry_measure_batch`（几何走廊 + 入射 / 出射约束下的有效截面，探针没用）
#        × 沿途 Fresnel 因子（入射透射 × 每次内反射的反射率（全反射 = 1）× 出射透射，s/p 平均；`fresnel_path_weight`）。
#   每类剖面 = w 按 θ 分桶再除以环带立体角（→ 平均辐亮度，与渲染剖面同一种量），形状由几何 + Fresnel 定；每类总量按该类 MC 能量份额定标
#   （MC 份额还含 PBD 对称像与分支概率，几何这边只算代表光路，所以只取形状、不取绝对量），全部类相加 = 加总粗线。
# 图面：左 = 族外余量天顶渲染的反日半球（返工 R1，`render_zenith.py` 的 remainder 一景，dual_fisheye_equidistant 右盘：盘心 θ = 180°、
# 盘沿 θ = 90°，与右栏横轴同一窗口），让「密而小的锐边」与「看上去只有一两道环、其余缓变背景」并排对照；
# 右：θ ∈ 90°–180°，上下两栏共用横轴、纵轴都从 0 起的线性刻度：上栏细线 = 该窗口内能量最大的 N_THIN 类（同一亮度单位）+ 虚线 `13-24-26`
# （全篇能量最大的族外类，弥散，没有锐边）；下栏粗线 = 全部族外类加总。
# 机械对账（`test_ch9_figs.py`，plan Step 10 预先锁定的容差，不随结果调整）：加总曲线在 [110°, 160°) 的峰 / 中位数与族外余量渲染侧
# 1.55 相对偏差 ≤ 10%，峰位在 124.6° ± 8°。另记同口径（峰 / 中位数、同分桶）的渲染侧数字作参照，见 numbers.json `reconcile`。
# `--recompute` 重算（约几分钟）；默认从 numbers.json 重画。
# 读者要看出：锐边很多、很小、很密；加起来只剩缓慢起伏；`13-24-26` 这种类根本没有锐边。
from __future__ import annotations

import argparse
import csv

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import analyze_energy as AE
from lumice_integral.symmetry.signature import phi_batch
from lumice_integral.geometry import Pyramid, entry_measure_batch, fold_matrix
from lumice_integral.geometry.core import N_ICE

NAME = "fold_edge_density"
TIER = S.TIER
N_DIRS = 1_000_000
SEED = 20260923
BIN_DEG = 0.25
WINDOW = (90.0, 180.0)
RECON_WINDOW = (110.0, 160.0)
N_THIN = 14
THIN_SMOOTH, SUM_SMOOTH = 4, 2          # 显示用相邻桶平均：细线 1°、粗线 0.5°（压 MC 采样噪声；对账用原 0.25° 桶）
DIFFUSE = "13-24-26"
WORLD_INCIDENT = np.array([0.0, 0.0, -1.0])     # entry_measure 的世界系入射方向（任取；每个 u 配一个把 u 转到它的姿态）
WIDTH, HEIGHT, DPI = 2600, 1250, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


# ---- 取数 ----


def _mc_rows() -> list[dict]:
    """默认档 MC 逐行表（`analysis/rows_<tier>.csv`）。"""
    AE.ensure_unpacked()
    with (AE.CACHE / f"rows_{S.ES.tier_label(TIER)}.csv").open() as fp:
        return list(csv.DictReader(line for line in fp if not line.startswith("#")))


def _energy_by_rep(keep) -> list[tuple[str, float]]:
    """``keep(row)`` 为真的行按 ``pbd_rep`` 累加 ``energy_pct``，按能量降序（同能量按名字）。"""
    acc: dict[str, float] = {}
    for r in _mc_rows():
        if keep(r):
            acc[r["pbd_rep"]] = acc.get(r["pbd_rep"], 0.0) + float(r["energy_pct"])
    return sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))


def off_family_classes() -> list[tuple[str, float]]:
    """[(pbd_rep, MC 能量 %)]，族外、status ok、长度 ≥ 2，按能量降序。"""
    return _energy_by_rep(lambda r: r["family"] == "" and r["status"] == "ok" and int(r["length"]) >= 2)


def single_face_classes() -> list[tuple[str, float]]:
    """[(面号, MC 能量 %)]：单面外反射（长度 1，族框架外；族外余量渲染里包含它们）。"""
    return _energy_by_rep(lambda r: r["status"] == "single_face")


def single_reflection_shape(u: np.ndarray, edges: np.ndarray, n: float = N_ICE) -> np.ndarray:
    """单面外反射的径向剖面形状（平均辐亮度，未定标）：随机取向下与面无关——θ = 180° − 2i，权重 = 投影截面 cos i × 外反射率 R(i)。
    （整面都是入射截面，没有走廊约束，所以不需要 entry_measure。）"""
    ci = -u[:, 2]                                        # 取 +z 为面法向：面朝光 ⇔ u_z < 0
    ok = ci > 0
    ci = ci[ok]
    ct = np.sqrt(1 - (1 - ci ** 2) / n ** 2)
    w = ci * (1 - _transmittance(1.0, ci, n, ct))
    theta = 180.0 - 2 * np.degrees(np.arccos(np.clip(ci, -1, 1)))
    hist, _ = np.histogram(theta, bins=edges, weights=w)
    return hist / (2 * np.pi * (np.cos(np.radians(edges[:-1])) - np.cos(np.radians(edges[1:]))))


def _transmittance(n1: float, cos_i: np.ndarray, n2: float, cos_t: np.ndarray) -> np.ndarray:
    """单界面非偏振透射率（s / p 平均）——`lumice_integral.optics.fresnel_unpolarized_transmittance` 的向量化版（单测逐点对照）。"""
    rs = (n1 * cos_i - n2 * cos_t) / (n1 * cos_i + n2 * cos_t)
    rp = (n2 * cos_i - n1 * cos_t) / (n2 * cos_i + n1 * cos_t)
    return 1.0 - 0.5 * (rs ** 2 + rp ** 2)


def fresnel_path_weight(p: Pyramid, faces: tuple[int, ...], u: np.ndarray, n: float = N_ICE) -> np.ndarray:
    """沿面序列 ``faces`` 的 Fresnel 因子乘积（入射透射 × 内反射反射率（全反射 = 1）× 出射透射）；u 是晶体系入射传播方向 (N, 3)。
    某一步几何上不成立（入射面背光、内反射 / 出射面方向不对、出射全反射）的行记 0——这些方向本来也在 Φ 的定义域外。"""
    normals = {f: np.asarray(p.normal(p.face(f)), float) for f in set(faces)}
    na = normals[faces[0]]
    cos_i = -(u @ na)
    ok = cos_i > 0
    sin_t2 = (1 - cos_i ** 2) / n ** 2
    cos_t = np.sqrt(np.clip(1 - sin_t2, 0, 1))
    w = np.where(ok, _transmittance(1.0, np.clip(cos_i, 1e-12, 1), n, cos_t), 0.0)
    d = u / n + (cos_i / n - cos_t)[:, None] * na           # Snell 矢量式：d = u/n + (cos_i/n − cos_t) n_a
    for f in faces[1:-1]:
        nk = normals[f]
        c = d @ nk
        ok &= c > 0
        s2 = n ** 2 * (1 - c ** 2)
        tir = s2 >= 1
        ct = np.sqrt(np.clip(1 - s2, 0, 1))
        R = np.where(tir, 1.0, 1.0 - _transmittance(n, np.clip(c, 1e-12, 1), 1.0, ct))
        w = w * R
        d = d - 2 * c[:, None] * nk
    nb = normals[faces[-1]]
    c = d @ nb
    s2 = n ** 2 * (1 - c ** 2)
    ok &= (c > 0) & (s2 < 1)
    w = w * np.where(ok, _transmittance(n, np.clip(c, 1e-12, 1), 1.0, np.sqrt(np.clip(1 - s2, 0, 1))), 0.0)
    return w


def _rotations_to(u: np.ndarray, s: np.ndarray) -> np.ndarray:
    """(N, 3, 3) 旋转，把每个 u 转到 s（Rodrigues；u = −s 的退化行本采样不会出现）。"""
    v = np.cross(u, s)
    c = u @ s
    K = np.zeros((len(u), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 0] = -v[:, 2], v[:, 1], v[:, 2]
    K[:, 1, 2], K[:, 2, 0], K[:, 2, 1] = -v[:, 0], -v[:, 1], v[:, 0]
    return np.eye(3) + K + np.einsum("nij,njk->nik", K, K) / (1 + c)[:, None, None]


def sample_directions(n: int = N_DIRS, seed: int = SEED) -> np.ndarray:
    u = np.random.default_rng(seed).normal(size=(n, 3))
    return u / np.linalg.norm(u, axis=1, keepdims=True)


def class_profile(p: Pyramid, faces: tuple[int, ...], u: np.ndarray, rotations: np.ndarray, edges: np.ndarray
                  ) -> tuple[np.ndarray, float]:
    """一个类的径向剖面形状（平均辐亮度，未定标）与 Σw / N（该代表光路的几何 × Fresnel 通量，诊断用）。"""
    out = phi_batch(p, fold_matrix(p, list(faces)), faces[0], faces[-1], u)
    ok = ~np.isnan(out[:, 0])
    w = np.zeros(len(u))
    if ok.any():
        em = entry_measure_batch(rotations[ok], list(faces), WORLD_INCIDENT, p)
        w[ok] = em * fresnel_path_weight(p, faces, u[ok])
    theta = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", np.nan_to_num(out), u), -1, 1)))
    hist, _ = np.histogram(theta[ok], bins=edges, weights=w[ok])
    ring_sr = 2 * np.pi * (np.cos(np.radians(edges[:-1])) - np.cos(np.radians(edges[1:])))
    return hist / ring_sr, float(w.sum() / len(u))


def compute() -> dict:
    p = Pyramid(a=1.0, h=TIER[0], tip_ratio=TIER[1])
    u = sample_directions()
    rot = _rotations_to(u, WORLD_INCIDENT)
    edges = np.arange(0.0, 180.0 + BIN_DEG, BIN_DEG)
    centers = (edges[:-1] + edges[1:]) / 2
    classes = off_family_classes()
    total = np.zeros(len(centers))
    per: dict[str, dict] = {}
    for rep, e in classes:
        faces = tuple(int(x) for x in rep.split("-"))
        shape, flux = class_profile(p, faces, u, rot, edges)
        energy = float((shape * 2 * np.pi * (np.cos(np.radians(edges[:-1])) - np.cos(np.radians(edges[1:])))).sum())
        prof = shape * (e / energy) if energy > 0 else np.zeros_like(shape)          # 定标：该类剖面的全天能量 = MC 份额 e（%）
        total += prof
        per[rep] = {"mc_energy_pct": e, "geom_flux": flux, "profile": prof}
    m = (centers >= WINDOW[0]) & (centers < WINDOW[1])
    in_window = {rep: float((d["profile"][m] * np.sin(np.radians(centers[m]))).sum()) for rep, d in per.items()}
    thin = [rep for rep, _ in sorted(in_window.items(), key=lambda kv: -kv[1]) if rep != DIFFUSE][:N_THIN]
    rnd = lambda a: [round(float(x), 8) for x in a]     # noqa: E731
    return {
        "tier": list(TIER), "n_dirs": N_DIRS, "seed": SEED, "bin_deg": BIN_DEG, "n_classes": len(classes),
        "mc_off_pct": round(sum(e for _, e in classes), 4),
        "weights": "entry_measure_batch × Fresnel（s/p 平均）；每类按 MC 份额定标；剖面 = 平均辐亮度（%/sr）",
        "theta_deg": rnd(centers), "sum": rnd(total),
        "thin": {rep: {"mc_energy_pct": per[rep]["mc_energy_pct"], "profile": rnd(per[rep]["profile"])} for rep in thin},
        "diffuse": {"raypath": DIFFUSE, "mc_energy_pct": per[DIFFUSE]["mc_energy_pct"], "profile": rnd(per[DIFFUSE]["profile"])},
        "geom_flux": {rep: round(d["geom_flux"], 8) for rep, d in per.items()},
    }


# ---- 对账 ----

RENDER_REF = {"peak_deg": 124.6, "ratio": 1.55}      # data/notes.md §3：族外余量渲染剖面 [110°,160°) 里的残影（峰 / 局部背景）


def peak_over_median(centers: np.ndarray, prof: np.ndarray, window: tuple[float, float] = RECON_WINDOW) -> dict[str, float]:
    m = (centers >= window[0]) & (centers < window[1])
    i = int(np.argmax(prof[m]))
    return {"peak_deg": float(centers[m][i]), "ratio": float(prof[m][i] / np.median(prof[m]))}


def render_side() -> dict[str, float]:
    """族外余量渲染（按正确像素语义现算剖面）在同一窗口、同一口径（峰 / 中位数）下的数字——对账的同口径参照。"""
    img, cfg = S.load_product("odd_radius_remainder", "rect")
    c, r, _ = F.radiance_profile(img, cfg["render"][0], S.sun_direction(), bin_deg=BIN_DEG)
    return peak_over_median(c, r)


def with_single_reflection(centers: np.ndarray, total: np.ndarray) -> tuple[np.ndarray, float]:
    """族外加总 + 单面外反射（按其 MC 份额定标）——与族外余量渲染同一成分集合（渲染的 filter_out 余量里两者都在）。"""
    edges = np.append(centers - BIN_DEG / 2, centers[-1] + BIN_DEG / 2)
    shape = single_reflection_shape(sample_directions(), edges)
    ring_sr = 2 * np.pi * (np.cos(np.radians(edges[:-1])) - np.cos(np.radians(edges[1:])))
    e_single = sum(e for _, e in single_face_classes())
    return total + shape * (e_single / float((shape * ring_sr).sum())), e_single


def reconcile(centers: np.ndarray, total: np.ndarray) -> dict:
    """plan Step 10 的对账：加总曲线 vs 族外余量渲染（容差在 test_ch9_figs.py 里预先锁定）。另记两条诊断：同口径渲染数字、
    补上单面外反射后的几何侧数字（成分与渲染余量一致）。"""
    geo = peak_over_median(centers, total)
    same = render_side()
    plus, e_single = with_single_reflection(centers, total)
    geo_plus = peak_over_median(centers, plus)
    return {"window_deg": list(RECON_WINDOW), "geometry": geo, "render_notes_ref": RENDER_REF,
            "rel_dev_vs_ref": geo["ratio"] / RENDER_REF["ratio"] - 1, "peak_shift_vs_ref_deg": geo["peak_deg"] - RENDER_REF["peak_deg"],
            "diagnostics": {
                "render_same_metric": same, "rel_dev_same_metric": geo["ratio"] / same["ratio"] - 1,
                "single_reflection_mc_pct": round(e_single, 4), "geometry_plus_single": geo_plus,
                "rel_dev_plus_single_same_metric": geo_plus["ratio"] / same["ratio"] - 1}}


# ---- 画图 ----


def smooth(y: np.ndarray, k: int = 2) -> np.ndarray:
    """细线显示用：相邻 k 桶平均（0.25° → 0.5°），只为压 MC 采样噪声，不进对账。"""
    y = np.asarray(y, float)
    n = len(y) // k * k
    return np.repeat(y[:n].reshape(-1, k).mean(axis=1), k)


RENDER_SCENE = "zenith/remainder"
WHITE_HEADROOM = 1.15


def draw_render(fig) -> None:
    """左：族外余量渲染（返工 R1 的天顶渲染）的反日半球——等距鱼眼，圆心 = 反日点（θ = 180°），盘沿 = θ = 90°，正好是右栏横轴的窗口。
    曝光：满白 = WHITE_HEADROOM × 余量剖面在 [90°, 175°] 的最大值（175° 以外是反日点旁那一小撮尖峰，不让它定曝光）。"""
    sc = F.DualScene(RENDER_SCENE)
    c, r, _ = sc.profile()
    white = WHITE_HEADROOM * float(r[(c >= 90) & (c <= 175)].max())
    s = 1000 / WIDTH
    ax = fig.add_axes([0.005, (1 - 1000 / HEIGHT) / 2 + 0.03, s, 1000 / HEIGHT])
    rad, _ = F.disc_radiance(sc, "anti", 90.0)
    F.show_disc(ax, F.tone(rad, white), 90.0, rings=(30.0, 60.0), ring_labels=False, center="反日点")
    fig.text(0.005 + s / 2, 0.03, "族外余量的渲染（反日半球）：圆心是反日点，边缘与太阳成 90°", ha="center", va="center", fontsize=10.5,
             color=PAL["ink_soft"], **FONT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recompute", action="store_true", help="重算几何直接积分（约几分钟）；默认读 numbers.json 重画")
    args = ap.parse_args()
    if args.recompute or not S.numbers_path(NAME).exists():
        S.write_numbers(NAME, compute())
    d = S.read_numbers(NAME)
    d["reconcile"] = reconcile(np.asarray(d["theta_deg"]), np.asarray(d["sum"]))
    S.write_numbers(NAME, d)
    F.apply_style()
    c = np.asarray(d["theta_deg"])
    m = (c >= WINDOW[0]) & (c <= WINDOW[1])
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    draw_render(fig)
    ax1 = fig.add_axes([0.47, 0.5, 0.51, 0.39])
    ax2 = fig.add_axes([0.47, 0.1, 0.51, 0.36], sharex=ax1)
    plt.setp(ax1.get_xticklabels(), visible=False)
    colors = [PAL[k] for k in ("face_4", "face_5", "face_6", "face_8", "face_3", "face_7", "sample_1", "sample_3")]
    for i, (rep, v) in enumerate(d["thin"].items()):
        ax1.plot(c[m], smooth(v["profile"], THIN_SMOOTH)[m], color=colors[i % len(colors)], lw=0.9, alpha=0.9)
    ax1.plot(c[m], smooth(d["diffuse"]["profile"], THIN_SMOOTH)[m], color=PAL["slate"], lw=1.6, ls=(0, (4, 2.5)))
    ax1.set_ylim(0, None)
    ax1.set_yticks([])
    ax1.set_ylabel("平均亮度")
    ax1.grid(axis="y", color=PAL["ink_faint"], lw=0.6, alpha=0.7)
    ax1.text(0.0, 1.03, f"窗口内能量最大的 {len(d['thin'])} 个族外类，各自一条细线\n虚线：{DIFFUSE}（族外能量最大的一类，弥散）",
             transform=ax1.transAxes, ha="left", va="bottom", fontsize=10, color=PAL["ink_soft"], linespacing=1.4, **FONT)
    ax2.plot(c[m], smooth(d["sum"], SUM_SMOOTH)[m], color=F.SUM_COLOR, lw=2.2)
    ax2.set_ylim(0, None)
    ax2.set_yticks([])
    ax2.set_ylabel("平均亮度")
    ax2.text(0.01, 0.95, f"全部 {d['n_classes']} 个族外类按能量加总", transform=ax2.transAxes, ha="left", va="top", fontsize=10,
             color=PAL["ink_soft"], **FONT)
    F.theta_axis(ax2, WINDOW[0], WINDOW[1], 15)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")
    print("reconcile:", d["reconcile"])


if __name__ == "__main__":
    main()
