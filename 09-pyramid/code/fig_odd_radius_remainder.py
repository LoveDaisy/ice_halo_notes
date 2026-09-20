# 产出 ch9 §4「族外余量」的仿真数据（task-odd-radius-instances）：全天 − 9 族，剩下的是散成背景还是有自己的弧？
#   ../data/odd_radius_remainder.rect.lumice.json + ../data/odd_radius_remainder/rect/   全天 rectangular，bright 曝光；过滤器 = 9 族 ≤4 面全部代表（207 条）
#                                                                                       的并集装一个 complex(action="filter_out", PBD)——issue 方案 (a)
#   ../data/odd_radius_remainder.numbers.json   曝光统计、按 intensity 归一的能量、占全景的份额与 energy_table.md 的「族外 + 单面外反射」份额比对
#                                               （机械核对 2a）、径向剖面上过阈值的峰清单及其归属（机械核对 2b：有峰 = 族外并非纯背景）
# `filter_out` 语义已用单光路最小复现钉住（2026-09-20，2×10⁷ 光线：filter_in(3-15) + filter_out(3-15) = 0.994 × 全部，差额是全图削顶像素），
# 见 data/notes.md。余量同时含「族外多次反射」与「单面外反射」（长度 1 不在并集里），与表的口径一致；方案 (b)（像素相减）只在 (a) 核对失败时做。
# 峰判据与全景脚本同一套（`_ch9_sim.detect_peaks` / `assign_peaks`）：局部极大且峰值 / 非峰窗口中位数 ≥ 3；归到已知半径的峰说明族外光路在
# 已知晕的半径上也有贡献（如 60.7° 楔的 `13-15-26-28`，最小偏向角 22.2°，只差 60° 族 0.7°），归不到的峰才是族外「自己的弧」。
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

NAME = "odd_radius_remainder"
RAY_NUM = 200_000_000


def build(intensity: float, ray_num: int) -> dict:
    return C.build_config([S.crystal()], S.remainder_filter(), S.scene(ray_num), [S.rect_render(intensity)])


def analyze(exposures: dict[str, dict], out_root: Path | None) -> dict:
    pano = S.read_numbers(F.PANORAMA, out_root)
    mc = F.mc_family_shares()
    mc_share = mc["off"] + mc["single"]
    e = S.total_energy_per_i(exposures["bright"], exposures["dim"])
    share = e / pano["energy_per_i"] * 100.0
    img, cfg = S.load_product(NAME, "rect", out_root)
    centers, radiance, energy = S.angular_radial_profile(img, cfg["render"][0], S.sun_direction())
    peaks = S.detect_peaks(centers, radiance)
    assigned = S.assign_peaks(peaks)
    known = {f"{w:g}": pk for w, pk in assigned.items() if pk is not None}
    own = [pk for pk in peaks if all(pk is not k for k in known.values())]
    return {
        "tier": list(S.TIER), "sun_alt": S.SUN_ALT, "max_hits": S.MAX_HITS, "share_tol_rel": F.SHARE_TOL_REL,
        "n_filtered_out": len(S.remainder_filter()) - 1, "exposures": exposures, "energy_per_i": e,
        "panorama_energy_per_i": pano["energy_per_i"], "share_render_pct": share, "share_mc_pct": mc_share,
        "share_mc_off_pct": mc["off"], "share_mc_single_pct": mc["single"],
        "rel_dev": (share - mc_share) / mc_share, "within_tol": abs(share - mc_share) / mc_share <= F.SHARE_TOL_REL,
        "peak_ratio": S.PEAK_RATIO, "peaks": peaks, "peaks_at_known_radii": known, "own_peaks": own,
        "profile": {"theta_deg": [float(x) for x in centers], "radiance": [float(x) for x in radiance], "energy": [float(x) for x in energy]},
    }


def main(argv: list[str] | None = None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description="ch9 §4 族外余量：全天 − 9 族（complex filter_out）+ 能量占比与径向峰判据；"
                      "--replot 在本脚本里 = 不跑 Lumice、只从 data/ 已有产物重算 numbers.json", replot=True)
    if args.replot:
        exposures = S.reload_product(NAME, "rect", args.out)
    else:
        S.ensure_lumice_version()
        exposures = S.render_product(NAME, "rect", build, ray_num=args.ray_num, out_root=args.out, workers=args.workers, backend=args.backend)
    numbers = analyze(exposures, args.out)
    path = S.write_numbers(NAME, numbers, args.out)
    b = exposures["bright"]
    print(f"bright i={b['intensity']:.4g} max_out={b['max_out']} sat_out={b['sat_out']} sat_disk={b['sat_disk']}；排除 {numbers['n_filtered_out']} 条代表")
    print(f"余量份额 render {numbers['share_render_pct']:.3f}% vs MC 族外 {numbers['share_mc_off_pct']:.4f}% + 单面 {numbers['share_mc_single_pct']:.4f}% "
          f"= {numbers['share_mc_pct']:.4f}%，相对偏差 {numbers['rel_dev']:+.1%}，{'容差内' if numbers['within_tol'] else '超容差'}")
    print(f"过阈值的峰：{[(p['peak_deg'], round(p['ratio'], 2)) for p in numbers['peaks']]}")
    print(f"  归到已知半径：{ {k: v['peak_deg'] for k, v in numbers['peaks_at_known_radii'].items()} }；族外自己的峰：{[p['peak_deg'] for p in numbers['own_peaks']]}")
    print(f"取数 → {path}")
    return path


if __name__ == "__main__":
    main()
