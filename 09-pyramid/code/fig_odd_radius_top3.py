# 产出 ch9 §4「族外 top-3」的仿真数据（task-odd-radius-instances）：族外能量前 3 的光路各自单独渲染，落在哪个半径、是弧还是点。
#   ../data/odd_radius_top3.<rank>_<pbd_rep>.lumice.json + ../data/odd_radius_top3/<rank>_<pbd_rep>/   全天 rectangular，bright 曝光，单光路过滤器（PBD 展开对称像）
#   ../data/odd_radius_top3.numbers.json   每条：楔角、最小偏向角（晕半径）、MC 能量份额（PBD 轨道求和）、渲染份额（÷ 全景）、环带方位覆盖率与弧/点判定、
#                                          径向剖面在半径窗内的峰/背景比（环锐不锐）
# 排名口径：`analysis/rows_h1_t0.5.csv` 里 family 空、status ok 的行按 pbd_rep 分组求和 energy_pct（`_ch9_sim.top_out_of_family`）——
# 与族份额的加总口径同源；未分组单行第一 `28-13-15`（0.0129%）只是分组第一 `13-24-26`（0.300%）的一个对称像。
# 光落在哪：先按「楔角 → 最小偏向角」算一个半径 R（plan 的预设），再从渲染图上机械取光实际的位置——径向能量分位 q10/q50/q90、R 环带内的能量占比、
# 平均辐亮度最高处。2×10⁶ 探针已经看到三条光路的光**都不在 R 上**（R 环带内能量 0），而散在 θ ≈ 90°–180° 的反日侧：它们都带中间反射，折叠矩阵 M 把
# 楔的偏向搬到了别处（ch8「楔 × 折叠」），随机取向下就是反日侧一片弥散——所以两处都算、都记。
# 弧/点判据（机械，`_ch9_sim.arc_or_spot`）：环带 [θ − 0.5°, θ + 2.5°] 按绕太阳的方位角分 5° 格，格内均值 ≥ 2 × 局部径向背景算「亮起」，亮起格占比
# ≥ 10% 判弧。注意随机取向下天空关于太阳方向旋转对称，任何光路的像都是整圈，覆盖率恒接近 1——这条判据在本场景是退化的，如实给出；
# 真正区分「有自己的弧 / 散成背景」的是最亮处的径向峰/背景比（同全景的 PEAK_RATIO=3 阈值），两个数都记。
# `--replot` 在本脚本里 = 不跑 Lumice，只从 data/ 已有产物重算取数并重写 numbers.json。
from __future__ import annotations

import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_sim as S  # noqa: E402
import fig_odd_radius_families as F  # noqa: E402

NAME = "odd_radius_top3"
RAY_NUM = 200_000_000
N_TOP = 3


def variant_of(rank: int, path: S.OffFamilyPath) -> str:
    return f"{rank}_{path.label}"


def build(path: S.OffFamilyPath):
    def make(intensity: float, ray_num: int) -> dict:
        return C.build_config([S.crystal()], S.single_raypath_filter(path.faces), S.scene(ray_num), [S.rect_render(intensity)])
    return make


def analyze(paths: list[S.OffFamilyPath], exposures: dict[str, dict[str, dict]], out_root: Path | None) -> dict:
    pano = S.read_numbers(F.PANORAMA, out_root)
    rows = {}
    for rank, p in enumerate(paths, 1):
        v = variant_of(rank, p)
        ex = exposures[v]
        e = S.total_energy_per_i(ex["bright"], ex["dim"])
        share = e / pano["energy_per_i"] * 100.0
        img, cfg = S.load_product(NAME, v, out_root)
        render = cfg["render"][0]
        centers, radiance, energy = S.angular_radial_profile(img, render, S.sun_direction())
        at_min_dev = S.arc_or_spot(img, render, S.sun_direction(), p.radius_deg)          # 光在不在「楔角 → 最小偏向角」的半径上
        peak = S.observed_peak(img, render, S.sun_direction(), zones=())                   # 光实际最亮在哪（1° 桶；单光路图没有别的环，不剔环带）
        at_peak = S.arc_or_spot(img, render, S.sun_direction(), float(peak["peak_deg"]), zones=())
        nearest = min(S.KNOWN_RADII.items(), key=lambda kv: abs(kv[1] - p.radius_deg))
        rows[v] = {"rank": rank, "raypath": p.label, "faces": list(p.faces), "wedge_deg": p.wedge_deg, "min_deviation_deg": p.radius_deg,
                   "nearest_family": f"{nearest[0]:g}", "nearest_family_radius_deg": nearest[1], "mc_energy_pct": p.energy_pct,
                   "mc_rows": p.n_rows, "exposures": ex, "energy_per_i": e, "share_render_pct": share,
                   "rel_dev": (share - p.energy_pct) / p.energy_pct,
                   "energy_quantiles_deg": S.energy_quantiles(centers, energy),
                   "at_min_deviation": at_min_dev, "observed_peak": peak, "at_observed_peak": at_peak,
                   "sharp_ring": bool(peak["detected"]), "verdict": at_peak["verdict"]}
    return {"tier": list(S.TIER), "sun_alt": S.SUN_ALT, "max_hits": S.MAX_HITS, "n_top": N_TOP, "peak_ratio": S.PEAK_RATIO,
            "arc_coverage": S.ARC_COVERAGE, "paths": rows}


def main(argv: list[str] | None = None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description="ch9 §4 族外 top-3：能量前 3 的族外光路单独渲染 + 半径 / 弧点判定；"
                      "--replot 在本脚本里 = 不跑 Lumice、只从 data/ 已有产物重算 numbers.json", replot=True)
    paths = S.top_out_of_family(N_TOP)
    if not args.replot:
        S.ensure_lumice_version()
    exposures = {}
    for rank, p in enumerate(paths, 1):
        v = variant_of(rank, p)
        if args.replot:
            exposures[v] = S.reload_product(NAME, v, args.out)
        else:
            exposures[v] = S.render_product(NAME, v, build(p), ray_num=args.ray_num, out_root=args.out, workers=args.workers, backend=args.backend)
            b = exposures[v]["bright"]
            print(f"  {v}: i={b['intensity']:.4g} max_out={b['max_out']} sat_out={b['sat_out']} sat_disk={b['sat_disk']}", flush=True)
    numbers = analyze(paths, exposures, args.out)
    path = S.write_numbers(NAME, numbers, args.out)
    for v, r in numbers["paths"].items():
        q, md, pk, ap = r["energy_quantiles_deg"], r["at_min_deviation"], r["observed_peak"], r["at_observed_peak"]
        ratio = "∞" if pk["ratio"] is None else f"{pk['ratio']:.1f}"
        print(f"#{r['rank']} {r['raypath']:<12} 楔角 {r['wedge_deg']:.1f}° 最小偏向角 {r['min_deviation_deg']:.2f}°（最近的族 {r['nearest_family']}°）"
              f" MC {r['mc_energy_pct']:.4f}% render {r['share_render_pct']:.4f}%（{r['rel_dev']:+.1%}）")
        print(f"   光落在：能量分位 q10/q50/q90 = {q['q10']:.1f}° / {q['q50']:.1f}° / {q['q90']:.1f}°；最小偏向角环带内能量占比 {md['ring_energy_frac']:.3f}；"
              f"最亮处 θ={pk['peak_deg']:.2f}° 峰/背景 {ratio} → {'锐环' if r['sharp_ring'] else '弥散'}；该处环带方位覆盖率 {ap['coverage']:.2f} → {r['verdict']}")
    print(f"取数 → {path}")
    return path


if __name__ == "__main__":
    main()
