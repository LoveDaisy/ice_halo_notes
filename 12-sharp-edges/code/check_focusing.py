# 核验 ch12 提纲的数字（确定性，无网络，末行 OK）：调 LI 官方 focusing.classify 现场取 (光路, 姿态密度) 的聚光标签——
# 3-5 在随机取向下的 22° 内缘是孤立非退化极小点（finite_jump，不算 Jacobian focusing）、五族密度下的标签、LI ch10
# parallel-face 表（6 条光路 × 5 族）里只有 1-3-5-2 是 Jacobian focusing；与本仓闭式（halo_notes.math.wedge）交叉核对临界值；
# 核对提纲转录的 LI 记录数字（docs/phase2.md 附录「Chapter-10 verdicts」）之间的算术自洽。不调任何 contour quadrature
# （inner_edge / liljequist / parhelic_circle 的像素值不在本仓重算，见文末 [6] 清单）；142° 边缘（A60-10）的标签。约 10 s。
import math

import numpy as np

from halo_notes.math.wedge import min_deviation_deg
from lumice_integral import focusing
from lumice_integral.canonical_scene import CANONICAL_REFRACTIVE_INDEX, canonical_crystal
from lumice_integral.ch10_verdicts import A60_10_MEMBERS, A60_10_REFERENCE_DEG, ParallelFaceOptions
from lumice_integral.dp_field import DPField
from lumice_integral.geometry import halo_map_rank
from lumice_integral.pose_density import build_pose_density

N = CANONICAL_REFRACTIVE_INDEX        # 1.31，与 LI ch10 裁定同一场景
PATH = (3, 5)
# LI docs/phase2.md 附录「Chapter-10 verdicts」（2026-09-25）逐字转录，下面只核它们之间及与本脚本现场值的自洽
LI_D_MIN_DEG = 21.839300
LI_HESSIAN = (0.337575, 0.964567)
LI_MEASURE_LIMIT = 11.011045          # 2π/√det H
LI_W_STAR = 1.444561
LI_LEVEL_SET_LIMIT = 15.906128        # w* · 2π/√det H
LI_LILJEQUIST_PEAK_DEG = 153.069685   # 「Chapter-10 verdicts rerun」：TIR 起始拐点，不是 D_P 临界值


def deg(x):
    return float(np.degrees(x))


def check_setup():
    """[0] 环境：LI 包含 focusing / ch10_verdicts（本仓 pyproject 钉的 LI rev ≥ 97e7785）。"""
    print("[0] setup")
    crystal = canonical_crystal()
    print(f"  LI canonical crystal {type(crystal).__name__}，n = {N}；ParallelFaceOptions 族参数（LI 单一权威，不另抄）：")
    for family, par in ParallelFaceOptions().families:
        print(f"    {family:7s} {dict(par)}")
    return crystal


def check_random(crystal, field):
    """[1] 随机取向：3-5 的全部临界值与各自的剖面类型。"""
    print("\n[1] 3-5 × random：临界值与剖面类型")
    r = focusing.classify(crystal, PATH, build_pose_density("random"), N, field=field)
    for o in r.onsets:
        extra = f"，measure_limit = 2π/√det H = {o.measure_limit:.6f}" if o.measure_limit is not None else ""
        print(f"  {deg(o.value):10.6f}°  {o.location:8s} {o.source:17s} {o.profile:15s} Jacobian={o.jacobian_focusing}"
              f"  ×{o.multiplicity}{extra}")
    interior = [o for o in r.onsets if o.location == "interior"]
    assert len(interior) == 1 and interior[0].source == "interior_minimum" and interior[0].profile == "finite_jump"
    assert not r.jacobian_focusing and r.mechanism == "none" and r.confined_dimensions == 0
    assert all(o.profile == "boundary_onset" for o in r.onsets if o.location == "boundary")
    m = interior[0]
    print(f"  ⇒ 内缘是唯一的内部临界点（孤立非退化极小），finite_jump，不计入 JACOBIAN_FOCUSING_PROFILES "
          f"{sorted(focusing.JACOBIAN_FOCUSING_PROFILES)}；mechanism = {r.mechanism!r}")
    print("  ⇒ 其余临界值都在可行域边界上（boundary_onset：弧长 ~ √|δ−c| 的平方根尖角，被积函数有界），不是锐边")
    return r, m


def check_cross(m, r):
    """[2] 交叉核对：LI 数值临界值 vs 本仓闭式；LI 记录数字之间的算术。"""
    print("\n[2] 交叉核对")
    d_closed = min_deviation_deg(60.0, N)
    d_li = deg(m.value)
    print(f"  内缘：LI DPField 极小值 {d_li:.9f}°，本仓闭式 2·arcsin(n/2) − 60° = {d_closed:.9f}°，差 {d_li - d_closed:+.1e}°")
    assert abs(d_li - d_closed) < 1e-6 and abs(d_closed - LI_D_MIN_DEG) < 5e-7
    det_rec = LI_HESSIAN[0] * LI_HESSIAN[1]
    det_live = (2 * math.pi / m.measure_limit) ** 2
    print(f"  Hessian：记录特征值之积 {det_rec:.6f}，现场 measure_limit 反推 det H = {det_live:.6f}；"
          f"现场 measure_limit {m.measure_limit:.6f} vs 记录 {LI_MEASURE_LIMIT}")
    assert abs(det_rec - det_live) < 1e-5 and abs(m.measure_limit - LI_MEASURE_LIMIT) < 1e-6
    prod = LI_W_STAR * LI_MEASURE_LIMIT
    print(f"  w* × 2π/√det H = {LI_W_STAR} × {LI_MEASURE_LIMIT} = {prod:.6f}（记录 {LI_LEVEL_SET_LIMIT}，差来自 6 位舍入）")
    assert abs(prod - LI_LEVEL_SET_LIMIT) < 1e-5
    # 主截面掠射入射的最大偏向（楔角 60°）：90° + arcsin(n·sin(A − arcsin(1/n))) − A
    graze = 90.0 + math.degrees(math.asin(N * math.sin(math.radians(60.0) - math.asin(1 / N)))) - 60.0
    b = min((o for o in r.onsets if o.location == "boundary"), key=lambda o: abs(deg(o.value) - graze))
    print(f"  外侧：边界临界值 {deg(b.value):.6f}° = 主截面掠射入射的最大偏向闭式 {graze:.6f}°（差 {deg(b.value) - graze:+.1e}°）")
    assert abs(deg(b.value) - graze) < 1e-6
    far = max(deg(o.value) for o in r.onsets)
    print(f"  像的最外端 {far:.4f}°（可行域角点，canonical 晶体的有限走廊；无限长棱镜口径不同，见 ch11）")
    return d_closed


def check_families(crystal, field):
    """[3] 同一条 3-5，五族密度：标签只由密度类型给出「约束了几个姿态自由度」。"""
    print("\n[3] 3-5 × 五族：mechanism 与 confined_dimensions")
    print("  （confined_dimensions = 密度里窄高斯因子的个数，不是 ch11 的「天空像维数」，也不是 9.1 的「姿态族维数」）")
    got = {}
    for family, par in ParallelFaceOptions().families:
        r = focusing.classify(crystal, PATH, build_pose_density(family, **dict(par)), N, field=field)
        got[family] = (r.mechanism, r.confined_dimensions)
        print(f"  {family:7s} mechanism = {r.mechanism:20s} confined_dimensions = {r.confined_dimensions}"
              f"  widths = {[round(deg(w), 3) for w in r.confinement_widths_rad]}°")
    assert got == {"random": ("none", 0), "column": ("dimension_collapse", 1), "plate": ("dimension_collapse", 1),
                   "parry": ("dimension_collapse", 2), "lowitz": ("dimension_collapse", 2)}
    print("  ⇒ 柱晶切点的 1/√ 与片晶幻日环的「σ 减半峰值翻倍」在 classify 里是同一个标签 dimension_collapse；"
          "两者的区分来自 ch10_verdicts 的像素测量，不来自标签")


def check_table(crystal):
    """[4] LI ch10 parallel-face 表：6 条光路 × 5 族，谁是 Jacobian focusing。"""
    print("\n[4] LI parallel-face 表（ParallelFaceOptions.paths × families）")
    opts = ParallelFaceOptions()
    jac = set()
    for faces in opts.paths:
        rank = halo_map_rank(crystal, faces)
        field = DPField.build(crystal, faces, N) if rank else None
        labels = []
        for family, par in opts.families:
            r = focusing.classify(crystal, faces, build_pose_density(family, **dict(par)), N, field=field)
            labels.append(r.mechanism)
            if r.jacobian_focusing:
                jac.add(r.path)
        rr = focusing.classify(crystal, faces, build_pose_density("random"), N, field=field)
        onsets = ", ".join(f"{deg(o.value):.4f}° {o.profile}" for o in rr.onsets) or "—"
        g = "—" if rr.gradient_norm_range is None else f"[{rr.gradient_norm_range[0]:.4g}, {rr.gradient_norm_range[1]:.4g}]"
        print(f"  {rr.path:10s} rank {rank}  |∇D_P| ∈ {g:22s} random: {labels[0]:9s} 其余族: {sorted(set(labels[1:]))}")
        print(f"             临界值: {onsets}")
        if faces in ((1, 3, 2), (3, 5, 6, 7, 3)):             # 镜面平板：|∇D_P| ≡ 2，不聚光
            assert abs(rr.gradient_norm_range[0] - 2) < 1e-9 and abs(rr.gradient_norm_range[1] - 2) < 1e-9
        if faces == (3, 5, 6, 7, 3):                          # Liljequist 峰不在临界值里
            gap = min(abs(deg(o.value) - LI_LILJEQUIST_PEAK_DEG) for o in rr.onsets)
            print(f"             Liljequist 峰 {LI_LILJEQUIST_PEAK_DEG}° 离最近临界值 {gap:.2f}°：不是 D_P 的临界值")
            assert gap > 1.0
        if faces == (3, 6):
            assert rank == 0 and rr.mechanism == "point_mass"
    print(f"  ⇒ Jacobian focusing 只出现在 {sorted(jac)}（120° 处的 1/√ 折叠圆，随机取向下就发散）")
    assert jac == {"1-3-5-2"}


def check_a60_10(crystal, d_closed):
    """[5] 142° 边缘：A60-10 两个成员的临界值与标签；转录常量 = 120° + D_min(3-5)。"""
    print("\n[5] 142° 边缘（A60-10：3-5-6-7、3-4-5-7，各含一次部分内反射）× random")
    print(f"  ch10_verdicts.A60_10_REFERENCE_DEG = {A60_10_REFERENCE_DEG:.6f}°；120° + 闭式 D_min = {120 + d_closed:.6f}°")
    assert f"{A60_10_REFERENCE_DEG:.6f}" == "141.839300" and abs(A60_10_REFERENCE_DEG - 120 - d_closed) < 1e-6
    for faces in A60_10_MEMBERS:
        r = focusing.classify(crystal, faces, build_pose_density("random"), N)
        print(f"  {r.path:8s} mechanism = {r.mechanism}；临界值: "
              + ", ".join(f"{deg(o.value):.6f}° {o.location}/{o.source}/{o.profile}" for o in r.onsets))
        edge = [o for o in r.onsets if abs(deg(o.value) - A60_10_REFERENCE_DEG) < 1e-5]
        assert len(edge) == 1 and edge[0].location == "boundary" and edge[0].profile == "degenerate"
        assert r.mechanism == "jacobian" and not any(o.location == "interior" for o in r.onsets)
    print("  ⇒ 142° 是可行域边界上梯度消失的点（LI：光滑延拓的鞍点），标签 degenerate——计入 Jacobian focusing，"
          "但强度未分类；没有内部临界点")


def report_unverified():
    """[6] 提纲引用、本脚本不核的 LI 数字（需重跑 contour quadrature，issue 明确不在本仓重算）。"""
    print("\n[6] 仅转录引用、未在本仓核验（出处：LI docs/phase2.md 附录「Chapter-10 verdicts」/「… rerun」）")
    for s in ("22° 内缘像素值极限 I = 0.541535；逼近 1 − 1.956√ε（kink 预测 1.945），ε = 1e-6 时比值 0.99805，外推 1.000023",
              "柱晶 σ = 0.5°：局部斜率在 −1/2 的 0.1 内的窗口 [1e-3, 3.2e-3] rad；σ = 0.1° 时 [5.6e-6, 3.2e-3]；"
              "cap 拐点 6.9e-5 / 2.9e-6 ⇒ ε_c ∝ σ^1.97；cap × σ = 0.431 / 0.419 rad",
              "片晶幻日环（1-3-2，环方位 110°）：σ 0.5° → 0.25° 峰值 ×1.988，横截积分 0.0022774 / 0.0022776",
              "Liljequist 峰 153.069685°（TIR 起始拐点），A60-10 鞍点实测 141.83929991°"):
        print(f"  - {s}")


def main():
    crystal = check_setup()
    field = DPField.build(crystal, PATH, N)
    r, m = check_random(crystal, field)
    d_closed = check_cross(m, r)
    check_families(crystal, field)
    check_table(crystal)
    check_a60_10(crystal, d_closed)
    report_unverified()
    print("OK")


if __name__ == "__main__":
    main()
