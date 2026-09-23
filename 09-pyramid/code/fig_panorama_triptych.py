# 产出 ../img/panorama_triptych.png（图 6「三档随机取向全景并列」）+ ../data/panorama_triptych.numbers.json：
# 棱柱占主导 (h/a, tip_ratio) = (3, 0.25)、参考几何 (1, 0.5)、锥面占主导 (0.3, 0.85) 三档锥晶随机取向全景（返工 R1：太阳放天顶重渲，
# `render_zenith.py` 的 panorama* 三景，10⁹ 光线、max_hits 4、D65）。
#   上排：以太阳为中心的等距鱼眼（dual_fisheye_equidistant 的太阳半球裁到 60°，半径线性 = 与太阳的夹角），叠 10°/20°/30°/40°/50° 同心刻度圈；
#         三张**同一绝对曝光**（像素辐亮度 / 发射能量，满白 = WHITE_HEADROOM × 三档剖面 2°–60° 最大值），亮暗可直接比；
#   下排：三档的径向剖面（dual_fisheye_equal_area 取数：每像素立体角恒定，桶内求和即可），三栏共用同一绝对纵轴（对数）——不各自归一化；
#         淡灰竖线 = 八个经典晕半径。
# 每档下方的「清晰可见」= 该档剖面上 `_ch9_sim.detect_peaks` + `assign_peaks`（峰 / 局部背景 ≥ 3，判据与上一轮同一份实现、未改）的机械结果，不手填；
# 新旧（上一轮 rectangular 2×10⁸ 渲染的 numbers.json `detected_radii`）对照落 numbers.json `vs_previous`。
# Lumice 渲染不可逐字节复现；本脚本对同一份 zip 逐字节可复现。
# 读者要看出：三档的直接楔一样，点亮的环不一样。
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "panorama_triptych"
TIERS = (("panorama_h3_t0.25", "棱柱占主导", "odd_radius_panorama_h3_t0.25"), ("panorama", "参考几何", "odd_radius_panorama"),
         ("panorama_h0.3_t0.85", "锥面占主导", "odd_radius_panorama_h0.3_t0.85"))
MAX_THETA = 60.0
RINGS = (10.0, 20.0, 30.0, 40.0, 50.0)
DISK_PX = 760
WHITE_HEADROOM = 1.3        # 满白 = 1.3 × 三档剖面 2°–60° 最大值（最亮的 9° 环不削顶）
WIDTH, HEIGHT, DPI = 2400, 1680, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def scene(key: str) -> F.DualScene:
    return F.DualScene(f"zenith/{key}")


def profiles() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """三档的径向剖面（绝对单位：每单位发射能量每 sr），``{key: (θ, 辐亮度)}``——下排三栏画的就是它，不做任何归一化。"""
    out = {}
    for key, _, _ in TIERS:
        c, r, _ = scene(key).profile()
        out[key] = (c, r)
    return out


def visible(c: np.ndarray, r: np.ndarray) -> list[float]:
    """清晰可见的环（楔角，按半径排）：`detect_peaks` + `assign_peaks`，判据与上一轮同一实现。"""
    pk = S.assign_peaks(S.detect_peaks(c, r))
    return sorted((w for w, p in pk.items() if p is not None), key=lambda w: S.KNOWN_RADII[w])


def halo_name(w: float) -> str:
    return f"{ES.min_deviation_deg(w):.0f}°"


def numbers(prof: dict) -> dict:
    out = {"criterion": {"peak_ratio": S.PEAK_RATIO, "bin_deg": S.PROFILE_BIN_DEG, "impl": "_ch9_sim.detect_peaks + assign_peaks"},
           "tiers": {}}
    for key, label, old in TIERS:
        c, r = prof[key]
        pk = S.assign_peaks(S.detect_peaks(c, r))
        prev = json.loads((F.DATA / f"{old}.numbers.json").read_text())
        out["tiers"][key] = {
            "label": label, "tier": scene(key).meta["tier"],
            "visible": [halo_name(w) for w in visible(c, r)],
            "peaks": {f"{w:g}": {"peak_deg": p["peak_deg"], "ratio": round(p["ratio"], 3)} for w, p in pk.items() if p},
            "vs_previous": {"previous_visible": [halo_name(float(w)) for w in sorted(prev["detected_radii"], key=float)],
                            "previous_source": f"data/{old}.numbers.json（rectangular 1440×720、2×10⁸、太阳 20°）"}}
    return out


def build():
    """画整张图（不落盘）：返回 ``(fig, numbers)``——单测据此检查画上去的剖面就是绝对单位的原剖面、且同图共用纵轴。"""
    F.apply_style()
    prof = profiles()
    nums = numbers(prof)
    white = WHITE_HEADROOM * max(float(r[(c >= 2) & (c <= MAX_THETA)].max()) for c, r in prof.values())
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    col_w = 1 / 3
    w, h = DISK_PX / WIDTH, DISK_PX / HEIGHT
    top = 1 - h - 15 / HEIGHT
    axes = []
    for k, (key, label, _) in enumerate(TIERS):
        x0 = k * col_w
        ax = fig.add_axes([x0 + (col_w - w) / 2, top, w, h])
        rad, _ = F.disc_radiance(scene(key), "sun", MAX_THETA)
        F.show_disc(ax, F.tone(rad, white), MAX_THETA, rings=RINGS, center="太阳")
        fig.text(x0 + col_w / 2, top - 40 / HEIGHT, label, ha="center", va="center", fontsize=14, color=PAL["ink"], **FONT)
        fig.text(x0 + col_w / 2, top - 88 / HEIGHT, "清晰可见：" + "、".join(nums["tiers"][key]["visible"]) + " 晕", ha="center",
                 va="center", fontsize=11.5, color=PAL["ink_soft"], **FONT)
        pax = fig.add_axes([x0 + 0.06 if k == 0 else x0 + 0.03, 0.115, col_w - (0.08 if k == 0 else 0.05), 0.31],
                           sharey=axes[0] if axes else None)
        axes.append(pax)
        c, r = prof[key]
        m = (c >= 1.0) & (c <= MAX_THETA)
        F.mark_radii(pax, sorted(S.KNOWN_RADII.values()))
        pax.plot(c[m], r[m], color=F.SUM_COLOR, lw=1.1, gid=f"profile:{key}")
        pax.set_yscale("log")
        F.theta_axis(pax, 0, MAX_THETA, 10)
        if k == 0:
            pax.set_ylabel("平均亮度（对数，三档同一标尺）")
        else:
            plt.setp(pax.get_yticklabels(), visible=False)
    lo = min(float(r[(c >= 1) & (c <= MAX_THETA)].min()) for c, r in prof.values())
    axes[0].set_ylim(lo * 0.7, white * 1.2)
    axes[0].yaxis.set_major_formatter(plt.NullFormatter())
    axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
    fig.text(0.5, 0.012, f"上：以太阳为中心的等距鱼眼，圆心到外圈 {MAX_THETA:.0f}°，三张同一曝光；下：径向剖面，淡灰竖线是八个经典晕半径",
             ha="center", va="bottom", fontsize=10, color=PAL["slate"], **FONT)
    return fig, nums


def main() -> None:
    fig, nums = build()
    S.write_numbers(NAME, nums)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}  {nums}")


if __name__ == "__main__":
    main()
