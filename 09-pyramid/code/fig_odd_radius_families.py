# 产出 ch9 §4「逐族归因」的仿真数据（task-odd-radius-instances）：9 族各一张过滤渲染 + 与 energy_table.md 的族级能量机械互证。
#   ../data/odd_radius_families.w<楔角>.lumice.json + ../data/odd_radius_families/w<楔角>/       全天 rectangular，bright 曝光（该族 ≤4 面全部代表的 OR 复合过滤器，PBD）
#   ../data/odd_radius_families.w0_dim.lumice.json  + ../data/odd_radius_families/w0_dim/       0° 族多一份 dim 曝光（无反射的平行光路全落在太阳盘内，bright 下削顶）
#   ../data/odd_radius_families.numbers.json   9 族的曝光统计、按 intensity 归一的能量、份额（÷ 全景，分母读 odd_radius_panorama.numbers.json）、
#                                              energy_table.md 同口径的 MC 份额（从 analysis/rows_h1_t0.5.csv 按族求和重算，与表逐位一致，有单测）、
#                                              相对偏差与是否在容差内；以及每族在自己图上的径向峰（该族的环在不在它该在的半径上）
# 选 9 张而非按侧↔锥 / 锥↔锥 / 底↔锥 分 4 组拼版：族级能量对账天然要每族一张（plan §2 假设 3）。
# 机械核对 1：份额_render = E_族 / E_全景（都按 intensity 归一、同光线数、同 max_hits=4），与 MC 份额比，相对偏差 |Δ|/MC ≤ SHARE_TOL_REL。
# 容差来源：像素积分 vs MC 光子计数两条链路的口径差（D65 vs 550 nm、R+G+B vs Y、8-bit 量化残余、正式光线数下的噪声），先在 63.8° 族（最亮、
# 30 条代表）上实测一次偏差后写死（见 SHARE_TOL_REL 旁注）；超容差的族如实记录，不调过滤器成员凑数。
# `--replot` 在本脚本里 = 不跑 Lumice，只从 data/ 已有产物重算取数并重写 numbers.json。
from __future__ import annotations

import csv
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_sim as S  # noqa: E402

NAME = "odd_radius_families"
PANORAMA = "odd_radius_panorama"
RAY_NUM = 200_000_000
SHARE_TOL_REL = 0.17    # 相对容差 17% = 2 × 校准实测的最大偏差。校准（2026-09-20，2×10⁸ 光线、同一套曝光包围，产物在 scratchpad，数字记 data/notes.md）：
                        # 63.8° 族（最亮、30 条代表）+1.25%（20.42% vs MC 20.17%）、0° 族（盘内 dim + 盘外 bright 两档合成）+2.5%、90° 族（最稀薄，
                        # 1.29%，46° 环最弥散、量化残余最大）−8.4%（1.18% vs 1.29%）；单轨道探针（2×10⁷）−2%…+9%。按 plan「实测偏差 Y 取 2Y」用最大
                        # 的 8.4% → 17%。容差是同一族两条链路（像素积分 vs MC 计数）的一致性判据，不是族间可分性；超出它才提示过滤器成员有问题


def variant_of(wedge: float) -> str:
    return f"w{wedge:g}"


def build(wedge: float):
    def make(intensity: float, ray_num: int) -> dict:
        return C.build_config([S.crystal()], S.family_filters(wedge), S.scene(ray_num), [S.rect_render(intensity)])
    return make


def mc_family_shares(tier: tuple[float, float] = S.TIER) -> dict[str, float]:
    """energy_table.md 主表同口径：`analysis/rows_<tier>.csv` 按 `family` 列求和 `energy_pct`（`ok` + `violation` 行，违反行能量本就是 0）；
    另给 ``off``（族外多次反射）与 ``single``（单面外反射）两个桶。"""
    S.AE.ensure_unpacked()
    path = S.AE.CACHE / f"rows_{S.ES.tier_label(tier)}.csv"
    with path.open() as fp:
        rows = list(csv.DictReader(line for line in fp if not line.startswith("#")))
    out: dict[str, float] = {f"{w:g}": 0.0 for w in S.KNOWN_WEDGES}
    out.update(off=0.0, single=0.0)
    for r in rows:
        e = float(r["energy_pct"])
        if r["status"] == "single_face":
            out["single"] += e
        elif r["status"] in ("ok", "violation"):
            out[r["family"] if r["family"] else "off"] += e
    return out


def analyze(exposures: dict[str, dict[str, dict]], out_root: Path | None) -> dict:
    pano = S.read_numbers(PANORAMA, out_root)
    mc = mc_family_shares()
    fams = {}
    for wedge in S.KNOWN_WEDGES:
        key = f"{wedge:g}"
        ex = exposures[key]
        e = S.total_energy_per_i(ex["bright"], ex["dim"])
        share = e / pano["energy_per_i"] * 100.0
        rel = (share - mc[key]) / mc[key]
        img, cfg = S.load_product(NAME, variant_of(wedge), out_root)
        row = {"halo": S.ES.family_name(wedge), "n_members_total": len(S.family_members()[wedge]),
               "n_members_filtered": len(S.renderable_members(wedge)), "exposures": ex, "energy_per_i": e,
               "share_render_pct": share, "share_mc_pct": mc[key], "rel_dev": rel, "within_tol": abs(rel) <= SHARE_TOL_REL}
        if wedge > 0:
            r = S.KNOWN_RADII[wedge]
            centers, radiance, _ = S.angular_radial_profile(img, cfg["render"][0], S.sun_direction())
            row.update(radius_deg=r, ring=S.peak_over_background(centers, radiance, S.radius_window(r)))
        fams[key] = row
    return {
        "tier": list(S.TIER), "sun_alt": S.SUN_ALT, "max_hits": S.MAX_HITS, "share_tol_rel": SHARE_TOL_REL,
        "panorama_energy_per_i": pano["energy_per_i"], "mc_shares": mc, "families": fams,
        "sum_share_render_pct": sum(f["share_render_pct"] for f in fams.values()),
        "sum_share_mc_pct": sum(mc[f"{w:g}"] for w in S.KNOWN_WEDGES),
        "n_within_tol": sum(1 for f in fams.values() if f["within_tol"]),
    }


def main(argv: list[str] | None = None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description="ch9 §4 逐族归因：9 族各一张过滤渲染 + 族级能量与 energy_table.md 互证；"
                      "--replot 在本脚本里 = 不跑 Lumice、只从 data/ 已有产物重算 numbers.json", replot=True)
    exposures = {}
    if not args.replot:
        S.ensure_lumice_version()
    for wedge in S.KNOWN_WEDGES:
        v = variant_of(wedge)
        if args.replot:
            exposures[f"{wedge:g}"] = S.reload_product(NAME, v, args.out)
        else:
            exposures[f"{wedge:g}"] = S.render_product(NAME, v, build(wedge), ray_num=args.ray_num, dim="always" if wedge == 0 else "auto",
                                                       out_root=args.out, workers=args.workers, backend=args.backend)
            b = exposures[f"{wedge:g}"]["bright"]
            print(f"  {v}: i={b['intensity']:.4g} max_out={b['max_out']} sat_out={b['sat_out']} sat_disk={b['sat_disk']}", flush=True)
    numbers = analyze(exposures, args.out)
    path = S.write_numbers(NAME, numbers, args.out)
    print(f"族   晕      成员(≤{S.MAX_HITS}/全)  份额_render  份额_MC   相对偏差  容差内  环峰位/峰背比")
    for k, f in numbers["families"].items():
        ring = f.get("ring")
        ring_s = "—" if ring is None else (f"{ring['peak_deg']:.2f}° / " + ("∞" if ring["ratio"] is None else f"{ring['ratio']:.1f}")
                                           + ("" if ring["detected"] else " (未过阈)"))
        print(f"{k:>5}° {f['halo']:>6} {f['n_members_filtered']:>3}/{f['n_members_total']:<3}     {f['share_render_pct']:7.3f}%  "
              f"{f['share_mc_pct']:7.3f}%  {f['rel_dev']:+7.1%}   {'✓' if f['within_tol'] else '✗'}    {ring_s}")
    print(f"9 族合计 render {numbers['sum_share_render_pct']:.3f}% vs MC {numbers['sum_share_mc_pct']:.3f}%；容差内 {numbers['n_within_tol']}/9")
    print(f"取数 → {path}")
    return path


if __name__ == "__main__":
    main()
