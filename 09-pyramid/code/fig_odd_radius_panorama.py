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
from __future__ import annotations

import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args, sim_figure

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_sim as S  # noqa: E402

NAME = "odd_radius_panorama"
RAY_NUM = 200_000_000
FISHEYE_INTENSITY = 1.0        # relative 曝光下只是相对系数


def build_rect(intensity: float, ray_num: int) -> dict:
    return C.build_config([S.crystal()], [], S.scene(ray_num, filtered=False), [S.rect_render(intensity)])


def build_fisheye(ray_num: int) -> dict:
    return C.build_config([S.crystal()], [], S.scene(ray_num, filtered=False), [S.fisheye_render(FISHEYE_INTENSITY, ev_mode="relative")])


def analyze(exposures: dict[str, dict], out_root: Path | None) -> dict:
    """bright 图上的径向剖面 + 8 个已知半径的峰判据 + 全曲线峰清单；能量按 intensity 归一。"""
    img, cfg = S.load_product(NAME, "rect", out_root)
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
        "tier": list(S.TIER), "sun_alt": S.SUN_ALT, "max_hits": S.MAX_HITS, "resolution": list(S.RECT_RESOLUTION),
        "profile_bin_deg": S.PROFILE_BIN_DEG, "peak_ratio": S.PEAK_RATIO, "bg_window_deg": S.BG_WINDOW_DEG,
        "bg_exclude_deg": S.BG_EXCLUDE_DEG, "radius_window": [-S.WINDOW_BELOW_DEG, S.WINDOW_ABOVE_DEG], "disk_deg": S.DISK_DEG,
        "exposures": exposures,
        "energy_per_i": S.total_energy_per_i(exposures["bright"], exposures["dim"]),
        "radii": radii,
        "detected_radii": [k for k, v in radii.items() if v["detected"]],
        "peaks": peaks,
        "profile": {"theta_deg": [float(x) for x in centers], "radiance": [float(x) for x in radiance], "energy": [float(x) for x in energy]},
    }


def main(argv: list[str] | None = None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description="ch9 §4 九族全景：鱼眼 + 全天 rectangular（bright / dim 两档曝光）+ 径向剖面判据；"
                      "--replot 在本脚本里 = 不跑 Lumice、只从 data/ 已有产物重算 numbers.json", replot=True)
    if args.replot:
        exposures = S.reload_product(NAME, "rect", args.out)
    else:
        S.ensure_lumice_version()
        exposures = S.render_product(NAME, "rect", build_rect, ray_num=args.ray_num, dim="always", out_root=args.out,
                                     workers=args.workers, backend=args.backend)
        sim_figure(NAME, S.CHAPTER, build_fisheye(args.ray_num), out_root=args.out, workers=args.workers, backend=args.backend, variant="fisheye")
    numbers = analyze(exposures, args.out)
    path = S.write_numbers(NAME, numbers, args.out)
    b, d = exposures["bright"], exposures["dim"]
    print(f"bright i={b['intensity']:.4g} max_out={b['max_out']} sat_out={b['sat_out']} | dim i={d['intensity']:.4g} max_disk={d['max_disk']} "
          f"sat_disk={d['sat_disk']} | E/i 全天 {numbers['energy_per_i']:.1f}（盘外 {b['energy_out_per_i']:.1f} + 盘内 {d['energy_disk_per_i']:.1f}）")
    for k, v in numbers["radii"].items():
        pk, wk = v["peak"], v["weak_peak"]
        where = f"峰 {pk['peak_deg']:.2f}° 峰/背景 {pk['ratio']:.2f}" if pk else \
            (f"弱峰 {wk['peak_deg']:.2f}° 峰/背景 {wk['ratio']:.2f} < {S.PEAK_RATIO:g}" if wk else "窗内无局部极大（肩部 / 单调坡）")
        print(f"  {k:>5}° 族 {v['halo']:>6} R={v['radius_deg']:.2f}° {'可辨' if v['detected'] else '不可辨'}：{where}")
    print(f"  全曲线过阈值的峰：{[(p['peak_deg'], round(p['ratio'], 2)) for p in numbers['peaks']]}")
    print(f"取数 → {path}")
    return path


if __name__ == "__main__":
    main()
