"""task-draw-ch9-figs：ch9 十一张正文插图的机械核验——**唯一权威位置**（每图一条语义断言，fig 脚本不再内联重复判据）。
被检量都由对应 `fig_*.py` / `_ch9_fig.py` 里的纯函数给出，这里只 import 调用、断言正文图题的语义；图面美观不在此列（owner 签核）。
不跑 Lumice：图 4/5/6/8/9 只读已入库渲染，图 11 读已入库的 `data/plate_arcs*` 产物。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_fig as F  # noqa: E402
import _ch9_sim as S  # noqa: E402
import check_pyramid as CP  # noqa: E402
import enumerate_signatures as ES  # noqa: E402
import fig_closure_growth as G3  # noqa: E402
import fig_corridor_1_3 as G7  # noqa: E402
import fig_crowded_profiles as G8  # noqa: E402
import fig_direct_wedges as G2  # noqa: E402
import fig_family_remainder as G4  # noqa: E402
import fig_fold_edge_density as G10  # noqa: E402
import fig_isolated_ring as G5  # noqa: E402
import fig_off_family_ring as G9  # noqa: E402
import fig_panorama_triptych as G6  # noqa: E402
import fig_plate_arcs as G11  # noqa: E402
import fig_pyramid_faces as G1  # noqa: E402
from lumice_integral.geometry import pyramid_face_angle  # noqa: E402

ALL_FACES = {1, 2, *range(3, 9), *range(13, 19), *range(23, 29)}


# ---- 图 1：二十个面的编号 ----


def test_fig1_two_views_label_all_twenty_faces():
    up, lo = set(G1.labelled_faces("upper")), set(G1.labelled_faces("lower"))
    assert up | lo == ALL_FACES and len(ALL_FACES) == 20


def test_fig1_face_angle_is_geometry_not_parameter():
    """标注的角度从法向现场算出、等于闭式 arctan((2/√3)c/a)，且与截顶比例 / 柱段高无关。"""
    ang = G1.face_angle_deg()
    assert ang == pytest.approx(pyramid_face_angle(), abs=1e-9)
    assert round(ang, 1) == 62.0
    for h, t in ((0.3, 0.85), (3.0, 0.25)):
        assert G1.face_angle_deg(G1.Pyramid(a=1.0, h=h, tip_ratio=t)) == pytest.approx(ang, abs=1e-9)


# ---- 图 2：九个直接楔 ----


def test_fig2_nine_transmittable_wedges_and_colouring():
    wedges = G2.pair_wedges()
    ok = G2.transmittable(wedges)
    assert tuple(ok) == ES.KNOWN_WEDGES
    assert ok == CP.transmittable_wedges(True)                      # 定理 7 核验脚本的独立实现（法向手写）一致
    assert G2.A_MAX == pytest.approx(2 * math.degrees(math.asin(1 / 1.31)))
    kinds = {A: G2.wedge_kind(A, wedges[A]) for A in ok}
    gray = {A for A, k in kinds.items() if k in G2.PRISM_KINDS}
    assert gray == {0.0, 60.0, 90.0} == set(CP.transmittable_wedges(False))   # 灰色 = 六棱柱已有
    assert {kinds[A] for A in ok if A not in gray} == set(G2.NEW_KINDS)       # 新增三组都出现
    blocked = sorted(A for A in wedges if A >= G2.A_MAX)
    assert blocked[0] == 99.8 and wedges[99.8] == {"YY"}            # 上限刚好卡掉的是一个锥↔锥楔
    assert set(G2.representatives()) == set(ES.KNOWN_WEDGES)


# ---- 图 3：闭包增长 ----


def test_fig3_prism_caps_at_12_pyramid_keeps_growing():
    data = G3.growth_data(max_len=7)
    assert data[False][3:] == [12] * 5
    assert data[True][:7] == CP.KNOWN_PYRAMID_GROWTH_6
    ratios = [b / a for a, b in zip(data[True][3:], data[True][4:])]
    assert all(r > 4 for r in ratios)                                # 字长 4…7 每级仍 ×4 以上，未见减速


# ---- 图 7：`1-3` 走廊 ----


def test_fig7_corridor_open_then_closed():
    assert G7.corridor_area_sr(G7.TIPS[0]) > 0
    assert G7.corridor_area_sr(G7.TIPS[1]) == 0
    hits = {t: {face for _, _, face in G7.trace_fan(t)} for t in G7.TIPS}
    assert 3 in hits[G7.TIPS[0]] and hits[G7.TIPS[1]] == {13}      # 截面示意与三维结论同向
    assert G7.first_length_90(G7.TIPS[0]) == 2 and G7.first_length_90(G7.TIPS[1]) == 5


# ---- 画图侧工具：Lumice 像素语义与重投影 ----


def test_rect_pixel_is_energy_not_radiance():
    """随机取向下天空关于太阳旋转对称：同一 θ 环带上，按 L/cos(lat) 算的辐亮度在高纬 / 低纬两段一致，而 L 本身不一致——
    这就是「像素 = 辐亮度 × 像素立体角」的实测证据（`_ch9_fig` 天空图一节）。"""
    img, cfg = S.load_product("odd_radius_remainder", "rect")
    render = cfg["render"][0]
    dirs, w = F.rectangular_pixel_directions(render)
    lin = F._srgb_decode(img).sum(axis=-1)
    theta = np.degrees(np.arccos(np.clip(dirs @ S.sun_direction(), -1, 1)))
    lat = np.degrees(np.arcsin(dirs[..., 2]))
    ring = (theta > 65) & (theta < 72)
    hi, lo = ring & (lat >= 70) & (lat < 80), ring & (lat >= 40) & (lat < 70)
    rad = lin / w
    assert rad[hi].mean() == pytest.approx(rad[lo].mean(), rel=0.1)
    assert lin[hi].mean() < 0.6 * lin[lo].mean()


def test_rect_to_fisheye_is_equidistant_and_centered():
    """合成一张「只有与中心夹角 ∈ [20°, 21°] 的环是亮的」rectangular 图（像素值按像素语义 ∝ cos lat），重投影后亮环半径 = 20.5/60 × 半径。"""
    render = {"lens": {"type": "rectangular"}, "resolution": [1440, 720]}
    dirs, w = F.rectangular_pixel_directions(render)
    center = S.sun_direction()
    theta = np.degrees(np.arccos(np.clip(dirs @ center, -1, 1)))
    lin = np.where((theta >= 20) & (theta <= 21), 0.5, 0.0) * w
    img = F._srgb_encode(np.repeat(lin[..., None], 3, axis=-1))
    out = F.rect_to_fisheye(img, render, center, 600, 60.0).astype(float).sum(axis=-1)
    row = out[300, 300:]                                     # 圆心向右一条半径
    r_px = float(np.average(np.arange(row.size) + 0.5, weights=row))
    assert r_px == pytest.approx(20.5 / 60.0 * 300, abs=1.5)
    assert out[300, :].sum() == pytest.approx(out[:, 300].sum(), rel=0.05)     # 上下 / 左右对称：中心确在圆心


# ---- 图 4：族外余量 ----


def test_fig4_remainder_has_no_ring():
    c, r = G4.profile()
    assert S.detect_peaks(c, r) == []                         # 没有任何局部极大高过 3 × 局部背景
    assert np.all(r[c >= S.DISK_ZONE_DEG] < G4.threshold_curve(c, r)[c >= S.DISK_ZONE_DEG])
    s = G4.shares()
    assert s["area"]["off"] > 50 and s["energy"]["off"] + s["energy"]["single"] < 20       # 面积过半、能量不到两成


# ---- 图 5：18° 晕单独拿出来 ----


def test_fig5_isolated_18_is_sharp_panorama_is_shoulder():
    for w in (G5.TARGET_WEDGE, G5.COMPARISON_WEDGE):
        c, fam, pan = G5.profiles(w)
        R = ES.min_deviation_deg(w)
        assert R <= G5.inner_edge_deg(c, fam) <= R + 1.0       # 内缘（升过半峰）紧贴最小偏向角外 1° 内
        assert fam[(c < R - 0.5) & (c > R - 5)].max() == 0    # 最小偏向角以内是黑的（留 0.5°：太阳盘直径 + 1 桶）
    c, _, pan = G5.profiles(G5.TARGET_WEDGE)
    peaks = S.assign_peaks(S.detect_peaks(c, pan))
    assert peaks[G5.TARGET_WEDGE] is None and peaks[G5.COMPARISON_WEDGE] is not None


# ---- 图 6：三档全景 ----


def test_fig6_same_wedges_different_visible_rings():
    vis = {name: tuple(G6.visible_halos(name)) for name, _ in G6.TIERS}
    assert len(set(vis.values())) == 3                        # 三档点亮的环互不相同
    assert [G6.tier_numbers(n)["tier"] for n, _ in G6.TIERS] == [[3.0, 0.25], [1.0, 0.5], [0.3, 0.85]]


# ---- 图 8：拥挤团加总 ----


def test_fig8_sum_loses_18_and_23():
    c, prof = G8.family_profiles()
    peaks = G8.sum_peaks(c, G8.summed(prof))
    assert {w for w, p in peaks.items() if p is None} == set(G8.FADED) == {52.4, 62.0}
    for w in G8.WEDGES:                                       # 每一族单独都有锐利内缘
        R = ES.min_deviation_deg(w)
        assert R <= G5.inner_edge_deg(c, prof[w]) <= R + 1.0


# ---- 图 9：族外光路搬到反日侧 ----


def test_fig9_light_is_moved_to_antisolar_ring():
    R = G9.min_deviation()
    assert R == pytest.approx(22.19, abs=0.01) and G9.wedge_deg() == 60.7
    c, r = G9.profile()
    near = (c >= R - 2) & (c <= R + 5)
    assert r[near].max() == 0                                  # 楔角给出的半径附近一点光都没有
    obs = G9.observed(c, r)
    assert obs["peak_deg"] > 170 and obs["is_local_max"] and obs["ratio"] >= S.PEAK_RATIO   # 反日点旁的锐环
    assert r[-1] < 0.2 * obs["peak"]                           # 正中暗洞


# ---- 图 10：族外锐边密集区（几何直接积分）----

# plan Step 10 预先锁定、不随对账结果调整的容差（工程判断，非严格误差传播）：探针未加权 1.51 与渲染 1.55 两条互不共享失败模式的链路
# 已知偏差 2.6%，加 Fresnel / 入射截面权重再引入一层差异，取约 4 倍余量 → 相对偏差 ≤ 10%；峰位落在探针锐边密集区 121°–146° 下半段、
# 与渲染峰同侧 → 124.6° ± 8°。
RECON_RATIO_TOL = 0.10
RECON_PEAK_TOL_DEG = 8.0


def test_fig10_fresnel_matches_library():
    from lumice_integral.optics import fresnel_unpolarized_transmittance as T
    ci, ct = np.array([0.95, 0.6, 0.12]), np.array([0.97, 0.8, 0.66])
    assert np.allclose(G10._transmittance(1.0, ci, 1.31, ct), [float(T(1.0, a, 1.31, b)) for a, b in zip(ci, ct)])
    assert np.allclose(G10._transmittance(1.31, ct, 1.0, ci), [float(T(1.31, b, 1.0, a)) for a, b in zip(ci, ct)])


def test_fig10_geometry_matches_render_for_top3():
    """独立链路互证：几何直接积分（entry_measure × Fresnel）的能量分位与 Lumice 单光路渲染（odd_radius_top3）逐条相差 < 3°。"""
    p = G10.Pyramid(a=1.0, h=1.0, tip_ratio=0.5)
    u = G10.sample_directions(200_000, seed=1)
    rot = G10._rotations_to(u, G10.WORLD_INCIDENT)
    edges = np.arange(0.0, 180.25, 0.25)
    c = (edges[:-1] + edges[1:]) / 2
    top = S.read_numbers("odd_radius_top3")["paths"]
    for key, v in top.items():
        shape, _ = G10.class_profile(p, tuple(v["faces"]), u, rot, edges)
        e = shape * np.sin(np.radians(c))
        cum = np.cumsum(e) / e.sum()
        for q in ("q10", "q50", "q90"):
            got = c[np.searchsorted(cum, int(q[1:]) / 100)]
            assert abs(got - v["energy_quantiles_deg"][q]) < 3.0, (key, q, got)


@pytest.mark.xfail(strict=True, reason="2026-09-23 实测未通过、回抛作者（progress.md DECISION）：加总曲线峰/中位数 1.90 vs 预锁参照 1.55（+22%）；"
                   "参照是渲染余量的峰/局部背景、且余量含单面外反射（7.25%），与几何侧只含族外不同成分 / 不同口径。"
                   "同口径 + 同成分诊断见 numbers.json reconcile.diagnostics（+1.7%）。判据不放宽")
def test_fig10_reconciles_with_render_remainder():
    d = S.read_numbers(G10.NAME)
    rec = d["reconcile"]
    assert abs(rec["rel_dev_vs_ref"]) <= RECON_RATIO_TOL, rec
    assert abs(rec["peak_shift_vs_ref_deg"]) <= RECON_PEAK_TOL_DEG, rec


def test_fig10_peak_position_and_like_for_like_diagnostic():
    """对账里通过的部分：峰位（预锁 ±8°）；同成分（族外 + 单面外反射）同口径（峰/中位数）的诊断数字——这条比较口径是在预锁判据
    未通过之后才补的，只作诊断记录，不替代上面的预锁判据。"""
    rec = S.read_numbers(G10.NAME)["reconcile"]
    assert abs(rec["peak_shift_vs_ref_deg"]) <= RECON_PEAK_TOL_DEG
    diag = rec["diagnostics"]
    assert abs(diag["geometry_plus_single"]["peak_deg"] - diag["render_same_metric"]["peak_deg"]) <= 1.0
    assert abs(diag["rel_dev_plus_single_same_metric"]) <= RECON_RATIO_TOL


@pytest.mark.xfail(strict=True, reason="2026-09-23 实测未通过、回抛作者（progress.md DECISION）：加 Fresnel / 入射截面权重后，14 条细线的"
                   "峰/中位数中位 3.9，加总 2.6，不到预设的 3 倍；只有约三分之一的细线有陡崖式锐边，与正文「细线各自带有锐边」有出入")
def test_fig10_thin_lines_sharp_sum_smooth():
    d = S.read_numbers(G10.NAME)
    c = np.asarray(d["theta_deg"])
    m = (c >= G10.WINDOW[0]) & (c < G10.WINDOW[1])
    def sharp(y):                                       # 峰 / 窗口内非零中位数（探针口径）
        y = np.asarray(y)[m]
        nz = y[y > 0]
        return y.max() / np.median(nz)
    thin = [sharp(v["profile"]) for v in d["thin"].values()]
    assert len(thin) >= 10 and np.median(thin) > 3 * sharp(d["sum"])     # 细线各自尖锐，加总平缓得多
    assert sharp(d["diffuse"]["profile"]) < np.median(thin)                # `13-24-26` 比典型细线弥散
    assert d["n_classes"] >= 200 and d["mc_off_pct"] == pytest.approx(5.79, abs=0.01)


# ---- 图 11：片晶姿态 max_hits 三联 ----


def test_fig11_more_hits_more_structures():
    counts = S.read_numbers(G11.NAME)["counts"]
    s = [counts[f"mh{k}"]["structures"] for k in G11.MAX_HITS]
    assert s[0] < s[1] < s[2], counts
