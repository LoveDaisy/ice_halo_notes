# 产出 ../img/off_family_ring.png（图 9「族外光路 `13-15-26-28` 的单独渲染」）+ ../data/off_family_ring.numbers.json：参考几何、随机取向、
# 只留 `13-15-26-28`（PBD 对称像全留）这一条族外光路（返工 R1：太阳放天顶重渲，`render_zenith.py` 的 13-15-26-28 一景，10¹⁰ 光线）。
#   左：反日半球（dual_fisheye_equidistant 的右盘：太阳在天顶 ⇒ 反日点在盘心，盘沿 = 与太阳成 90° 的一圈），完整半球——
#       太阳半球不画（这条光路的光 100% 落在反日半球，numbers.json `energy_frac_antisolar_hemisphere`）；
#   右：到反日点角距离 ψ 的径向剖面（dual_fisheye_equal_area 取数，1° 桶），横轴 0°–180°（上方副轴标「与太阳的夹角」= 180° − ψ），
#       标出这条光路的折叠楔角 60.7° 给出的最小偏向角（`enumerate_signatures.min_deviation_deg` 现场算，离太阳 ≈ 22.2°，紧挨 22° 晕）——那里没有光。
# 读者要看出：光没有落在楔角给出的半径上，而是被折叠搬到了反日侧，成一片以反日点为心的很宽的环带，内缘锐利，心里是暗洞。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "off_family_ring"
SCENE = "zenith/13-15-26-28"
PRODUCT, VARIANT = "odd_radius_top3", "3_13-15-26-28"      # 楔角读上一轮 top-3 的 numbers.json（与枚举器同源），不重算
PATH = (13, 15, 26, 28)
PROFILE_BIN = S.OBSERVED_BIN_DEG             # 1°：反日点附近 0.25° 桶只剩几个像素
WHITE_HEADROOM = 1.15
WIDTH, HEIGHT, DPI = 2400, 1150, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def wedge_deg() -> float:
    return float(S.read_numbers(PRODUCT)["paths"][VARIANT]["wedge_deg"])


def min_deviation() -> float:
    return ES.min_deviation_deg(wedge_deg())


def scene() -> F.DualScene:
    return F.DualScene(SCENE)


def profile() -> tuple[np.ndarray, np.ndarray]:
    """以太阳为极点的径向剖面 ``(θ, 辐亮度)``（1° 桶，绝对单位）；图上横轴用 ψ = 180° − θ。"""
    c, r, _ = scene().profile(PROFILE_BIN)
    return c, r


def observed(c: np.ndarray, r: np.ndarray) -> dict:
    """实际最亮处（θ ≥ DISK_ZONE_DEG）及其峰 / 局部背景（`_ch9_sim.peak_over_background`，窗 ±3°，同 observed_peak 口径）。"""
    m = c >= S.DISK_ZONE_DEG
    i = int(np.flatnonzero(m)[np.argmax(r[m])])
    return S.peak_over_background(c, r, (c[i] - 3.0, c[i] + 3.0))


def numbers() -> dict:
    c, r = profile()
    _, _, e = scene().profile(PROFILE_BIN)
    obs = observed(c, r)
    psi = 180.0 - c
    cum = np.cumsum(e[::-1]) / e.sum()
    q = {f"q{int(x * 100)}": float(psi[::-1][int(np.searchsorted(cum, x))]) for x in (0.1, 0.5, 0.9)}
    return {"wedge_deg": wedge_deg(), "min_deviation_deg": min_deviation(), "observed_peak": obs,
            "energy_frac_antisolar_hemisphere": float(e[c > 90].sum() / e.sum()), "energy_quantiles_psi_deg": q}


def build():
    """画整张图（不落盘）：返回 ``(fig, numbers)``——单测据此检查画上去的剖面就是绝对单位的原剖面、且同图共用纵轴。"""
    F.apply_style()
    nums = numbers()
    R = min_deviation()
    c, r = profile()
    obs = nums["observed_peak"]
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    s = 1000 / WIDTH
    ax = fig.add_axes([0.01, (1 - 1000 / HEIGHT) / 2 + 0.03, s, 1000 / HEIGHT])
    rad, _ = F.disc_radiance(scene(), "anti", 90.0)
    F.show_disc(ax, F.tone(rad, WHITE_HEADROOM * float(r.max())), 90.0, rings=(30.0, 60.0), label_angle_deg=-50.0)
    fig.text(0.01 + s / 2, 0.035, "反日半球：圆心 = 反日点，边缘 = 与太阳成 90° 的一圈", ha="center", va="center", fontsize=11,
             color=PAL["ink_soft"], **FONT)
    pax = fig.add_axes([0.5, 0.17, 0.47, 0.68])
    psi = 180.0 - c
    pax.plot(psi, r, color=F.SUM_COLOR, lw=1.5, gid="profile:13-15-26-28")
    psi_R = 180.0 - R
    pax.axvline(psi_R, color=PAL["face_5"], lw=1.0, ls=(0, (5, 3)))
    pax.text(psi_R - 1.5, 0.93, f"楔角给出的半径：离太阳 {R:.1f}°\n（折叠楔角 {wedge_deg():.1f}°）——这里没有光",
             transform=pax.get_xaxis_transform(), ha="right", va="top", fontsize=10, color=PAL["face_5"], **FONT)
    pk_psi = 180.0 - obs["peak_deg"]
    pax.annotate(f"内缘亮边：离反日点 {pk_psi:.1f}°", xy=(pk_psi, obs["peak"]), xytext=(pk_psi + 14, obs["peak"] * 0.97),
                 ha="left", va="center", fontsize=10, color=PAL["ink_soft"],
                 arrowprops=dict(arrowstyle="-|>", color=PAL["ink_soft"], lw=0.8, mutation_scale=8), **FONT)
    pax.text(1.0, obs["peak"] * 0.08, "暗洞", ha="left", va="bottom", fontsize=10, color=PAL["ink_soft"], **FONT)
    pax.set_xlim(0, 180)
    ticks = np.arange(0, 181, 30)
    pax.set_xticks(ticks)
    pax.set_xticklabels([F.deg(t) for t in ticks])
    pax.set_xlabel("与反日点的夹角")
    top = pax.secondary_xaxis("top", functions=(lambda x: 180 - x, lambda x: 180 - x))
    top.set_xticks(ticks)
    top.set_xticklabels([F.deg(t) for t in ticks])
    top.set_xlabel("与太阳的夹角")
    pax.grid(axis="y", color=PAL["ink_faint"], lw=0.6, alpha=0.7)
    pax.set_ylim(0, obs["peak"] * 1.12)
    pax.set_yticks([])
    pax.set_ylabel(F.RADIANCE_LABEL)
    return fig, nums


def main() -> None:
    fig, nums = build()
    S.write_numbers(NAME, nums)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}  {nums}")


if __name__ == "__main__":
    main()
