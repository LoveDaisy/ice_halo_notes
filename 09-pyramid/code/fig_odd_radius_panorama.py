# 产出 ch9 §4「9 族全景」的仿真数据（task-odd-radius-instances；拼版与正式版式留后续绘图任务，本脚本不出 ../img/）：
#   ../data/odd_radius_panorama.fisheye.lumice.json  + ../data/odd_radius_panorama/fisheye/   天顶朝上等面积鱼眼 1800²（relative 曝光，只看图：同心晕环）
#   ../data/odd_radius_panorama.rect.lumice.json     + ../data/odd_radius_panorama/rect/      全天 rectangular 1440×720，bright 曝光（取数：盘外能量 + 径向剖面）
#   ../data/odd_radius_panorama.rect_dim.lumice.json + ../data/odd_radius_panorama/rect_dim/  同上 dim 曝光（只取太阳盘内能量——0° 族不偏折的光路，bright 下削顶）
#   ../data/odd_radius_panorama.numbers.json   全部取数：各曝光统计、按 intensity 归一的全天能量（逐族 / 余量 / top-3 三个脚本的分母）、
#                                              8 个已知晕半径在径向剖面上的峰/背景判据（哪些半径「可辨」）、整条剖面过阈值的峰清单
# 场景：默认档 (h/a, tip_ratio) = (1, 0.5) 锥晶、随机取向、太阳 20°、D65、max_hits=4（与 energy_table.md 的 MC 口径对齐）、无过滤器；口径与常量见 _ch9_sim.py。
# 「可辨」判据（机械）：以太阳为极点的径向剖面（0.25° 桶，桶内平均辐亮度）上先找全部局部极大，峰值 / 局部背景（±10° 窗内剔除峰位 ±2°、8 个已知环带
# 与太阳盘外沿后的中位数，即「非峰窗口的中位数」）≥ PEAK_RATIO=3 的算峰，再把峰归到「峰位 − 0.25° 以下最近的已知半径」（峰在最小偏向角外侧
# 0.4–1.6°）；一个已知半径收到峰即「可辨」。能看出几个算几个，如实记录；未过阈的半径另记窗内最高点离阈值多远。
# `--replot`：本任务没有拼版正式图，`--replot` 的含义是**不跑 Lumice，只从 data/ 里已有的渲染产物重算取数并重写 numbers.json**（与 ch8 的
# 「重画正式图」不同）。光线数：起始 2×10⁸（与 ch8 B2 同量级；探针 2×10⁷ 时 35°/46° 两环峰/背景比 1.6，不过阈值），升档协议与最终取值记 data/notes.md。
# `--tier <label>`（task-pyramid-realistic-tiers）：换几何档位（`enumerate_signatures.TIERS` 的 `tier_label`，如 `h3_t0.25`），太阳高度 / 光线数 /
# 判据全部沿用默认档；不传时行为与产物名与原来完全一致（`odd_radius_panorama.*`），非默认档产物名带后缀 `odd_radius_panorama_<label>.*`。
# 机械核对（每档一条、聚合级）：bright 图上 8 个已知半径环带（[R − 0.5°, R + 2.5°]，取并集不重复计像素——20°–24° 四环窗口互相重叠）的能量 +
# dim 图太阳盘内能量（0° 族），÷ 全天能量，与 energy_table.md 该档「9 族能量合计」比。环带是族能量的粗代理（环带内也有族外 / 背景，族的拖尾也
# 出环带），不设容差不作断言，只记 numbers.json 供作者判断——逐族过滤渲染（fig_odd_radius_families.py，17% 容差）才是族级对账的正式链路。
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args, sim_figure

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_sim as S  # noqa: E402
from fig_odd_radius_families import mc_family_shares  # noqa: E402

NAME = "odd_radius_panorama"
RAY_NUM = 200_000_000
FISHEYE_INTENSITY = 1.0        # relative 曝光下只是相对系数
TIER_LABELS = {S.ES.tier_label(t): t for t in S.ES.TIERS}


def product_name(tier: tuple[float, float]) -> str:
    """默认档保持 `odd_radius_panorama`（向后兼容），其它档 `odd_radius_panorama_<tier_label>`。"""
    return NAME if tier == S.TIER else f"{NAME}_{S.ES.tier_label(tier)}"


def make_build_rect(tier: tuple[float, float]):
    def build_rect(intensity: float, ray_num: int) -> dict:
        return C.build_config([S.crystal(tier)], [], S.scene(ray_num, filtered=False), [S.rect_render(intensity)])
    return build_rect


def make_build_fisheye(tier: tuple[float, float]):
    def build_fisheye(ray_num: int) -> dict:
        return C.build_config([S.crystal(tier)], [], S.scene(ray_num, filtered=False), [S.fisheye_render(FISHEYE_INTENSITY, ev_mode="relative")])
    return build_fisheye


build_rect = make_build_rect(S.TIER)
build_fisheye = make_build_fisheye(S.TIER)


def family_crosscheck(img: np.ndarray, render: dict, exposures: dict[str, dict], tier: tuple[float, float]) -> dict:
    """聚合级机械核对（见文件头）：``render_family_frac`` = (8 个已知半径环带并集的 bright 能量 + dim 盘内能量) / 全天能量，
    ``mc_family_frac`` = energy_table.md 该档 9 族能量合计 / 100；另附每个半径单独的 :func:`_ch9_sim.arc_or_spot`（环带能量份额 / 峰背景比 / 判定）。"""
    b, d = exposures["bright"], exposures["dim"]
    energy, _, dirs = S.energy_map(img, render)
    theta = np.degrees(np.arccos(np.clip(dirs @ S.sun_direction(), -1.0, 1.0)))
    union = np.zeros(theta.shape, bool)
    for r in S.KNOWN_RADII.values():
        union |= (theta >= r - S.RING_INNER_DEG) & (theta <= r + S.RING_OUTER_DEG)
    bright_total_per_i = b["energy_out_per_i"] + b["energy_disk_per_i"]                 # = energy.sum() / i（同一张 bright 图）
    ring_union_per_i = float(energy[union].sum() / energy.sum()) * bright_total_per_i
    total_per_i = S.total_energy_per_i(b, d)
    mc = mc_family_shares(tier)
    mc_frac = sum(mc[f"{w:g}"] for w in S.KNOWN_WEDGES) / 100.0
    render_frac = (ring_union_per_i + d["energy_disk_per_i"]) / total_per_i
    rings = {f"{w:g}": S.arc_or_spot(img, render, S.sun_direction(), r) for w, r in S.KNOWN_RADII.items()}
    return {
        "ring_union_energy_frac": ring_union_per_i / total_per_i,
        "disk_energy_frac": d["energy_disk_per_i"] / total_per_i,
        "render_family_frac": render_frac,
        "mc_family_frac": mc_frac,
        "rel_dev": (render_frac - mc_frac) / mc_frac,
        "ring_energy_frac_sum": sum(x["ring_energy_frac"] for x in rings.values()),      # 逐环相加（重叠像素重复计），与并集对照
        "rings": rings,
    }


def analyze(exposures: dict[str, dict], out_root: Path | None, *, tier: tuple[float, float] = S.TIER, name: str = NAME) -> dict:
    """bright 图上的径向剖面 + 8 个已知半径的峰判据 + 全曲线峰清单；能量按 intensity 归一；末尾附族能量的聚合级机械核对。"""
    img, cfg = S.load_product(name, "rect", out_root)
    render = cfg["render"][0]
    centers, radiance, energy = S.angular_radial_profile(img, render, S.sun_direction())
    peaks = S.detect_peaks(centers, radiance)
    assigned = S.assign_peaks(peaks)
    weak = S.assign_peaks(S.detect_peaks(centers, radiance, ratio=1.0))      # 全部局部极大（含未过阈的）：未过阈时记「弱峰」离阈值多远
    radii = {}
    for wedge, r in S.KNOWN_RADII.items():
        pk = assigned[wedge]
        radii[f"{wedge:g}"] = {"halo": S.ES.family_name(wedge), "radius_deg": r, "detected": pk is not None, "peak": pk,
                               "weak_peak": None if pk is not None else weak[wedge], "window": list(S.radius_window(r))}
    return {
        "tier": list(tier), "sun_alt": S.SUN_ALT, "max_hits": S.MAX_HITS, "resolution": list(S.RECT_RESOLUTION),
        "profile_bin_deg": S.PROFILE_BIN_DEG, "peak_ratio": S.PEAK_RATIO, "bg_window_deg": S.BG_WINDOW_DEG,
        "bg_exclude_deg": S.BG_EXCLUDE_DEG, "radius_window": [-S.WINDOW_BELOW_DEG, S.WINDOW_ABOVE_DEG], "disk_deg": S.DISK_DEG,
        "exposures": exposures,
        "energy_per_i": S.total_energy_per_i(exposures["bright"], exposures["dim"]),
        "radii": radii,
        "detected_radii": [k for k, v in radii.items() if v["detected"]],
        "peaks": peaks,
        "profile": {"theta_deg": [float(x) for x in centers], "radiance": [float(x) for x in radiance], "energy": [float(x) for x in energy]},
        "family_crosscheck": family_crosscheck(img, render, exposures, tier),
    }


def main(argv: list[str] | None = None) -> Path:
    pre = argparse.ArgumentParser(add_help=False)      # 先摘出 --tier，其余 argv 原样交给共享的 parse_args（不改 halo_notes）
    pre.add_argument("--tier", choices=sorted(TIER_LABELS), default=S.ES.tier_label(S.TIER))
    pre_args, rest = pre.parse_known_args(argv)
    tier = TIER_LABELS[pre_args.tier]
    name = product_name(tier)
    args = parse_args(rest, default_ray_num=RAY_NUM, description="ch9 §4 九族全景：鱼眼 + 全天 rectangular（bright / dim 两档曝光）+ 径向剖面判据；"
                      "--replot 在本脚本里 = 不跑 Lumice、只从 data/ 已有产物重算 numbers.json；--tier <label> 换几何档位（默认档产物名不变）", replot=True)
    if args.replot:
        exposures = S.reload_product(name, "rect", args.out)
    else:
        S.ensure_lumice_version()
        exposures = S.render_product(name, "rect", make_build_rect(tier), ray_num=args.ray_num, dim="always", out_root=args.out,
                                     workers=args.workers, backend=args.backend)
        sim_figure(name, S.CHAPTER, make_build_fisheye(tier)(args.ray_num), out_root=args.out, workers=args.workers, backend=args.backend, variant="fisheye")
    numbers = analyze(exposures, args.out, tier=tier, name=name)
    path = S.write_numbers(name, numbers, args.out)
    b, d = exposures["bright"], exposures["dim"]
    print(f"[{pre_args.tier}] bright i={b['intensity']:.4g} max_out={b['max_out']} sat_out={b['sat_out']} | dim i={d['intensity']:.4g} max_disk={d['max_disk']} "
          f"sat_disk={d['sat_disk']} | E/i 全天 {numbers['energy_per_i']:.1f}（盘外 {b['energy_out_per_i']:.1f} + 盘内 {d['energy_disk_per_i']:.1f}）")
    for k, v in numbers["radii"].items():
        pk, wk = v["peak"], v["weak_peak"]
        where = f"峰 {pk['peak_deg']:.2f}° 峰/背景 {pk['ratio']:.2f}" if pk else \
            (f"弱峰 {wk['peak_deg']:.2f}° 峰/背景 {wk['ratio']:.2f} < {S.PEAK_RATIO:g}" if wk else "窗内无局部极大（肩部 / 单调坡）")
        print(f"  {k:>5}° 族 {v['halo']:>6} R={v['radius_deg']:.2f}° {'可辨' if v['detected'] else '不可辨'}：{where}")
    print(f"  全曲线过阈值的峰：{[(p['peak_deg'], round(p['ratio'], 2)) for p in numbers['peaks']]}")
    fc = numbers["family_crosscheck"]
    print(f"  族能量聚合核对：环带并集 {fc['ring_union_energy_frac']:.1%} + 盘内 {fc['disk_energy_frac']:.1%} = {fc['render_family_frac']:.1%} "
          f"vs energy_table 9 族合计 {fc['mc_family_frac']:.1%}，相对偏差 {fc['rel_dev']:+.1%}（逐环相加 {fc['ring_energy_frac_sum']:.1%}，粗代理，不设容差）")
    print(f"取数 → {path}")
    return path


if __name__ == "__main__":
    main()
