# 产出 ../img/off_family_ring.png（图 9「族外光路 `13-15-26-28` 的单独渲染」）：参考几何、随机取向、只留 `13-15-26-28`（PBD 对称像全留）
# 这一条族外光路，数据是已入库 `data/odd_radius_top3/3_13-15-26-28/img_01.png`（不重渲）。三块：
#   左上：以**太阳**为中心的等距鱼眼（外圈 40°），虚线圆 = 这条光路的折叠楔角 60.7° 给出的最小偏向角（`enumerate_signatures.min_deviation_deg`
#         现场算，≈ 22.2°，紧挨 22° 晕）——那里没有光；
#   右上：以**反日点**为中心的等距鱼眼（外圈 12°）：光被中间反射搬到反日侧，围着反日点一圈亮环、正中一个暗洞；
#   下：以太阳为极点的径向剖面（1° 桶，按 Lumice 像素语义现算），标出最小偏向角与实际最亮处。
# 设计偏离 plan（plan：rectangular 全天图 + 反日点 inset + 引线）：改成「太阳中心 / 反日点中心」两张等距鱼眼 + 一条剖面，
# 「该在的半径」与「实际在的位置」分别在各自最自然的中心下看，剖面把两者放在同一条横轴上（progress DECISION）。
# 两张天空图显示增益同为 DISPLAY_GAIN（只为看清，不进取数）。
# 读者要看出：光没有落在楔角给出的半径上，而是被折叠搬到了反日侧，成一个以反日点为心的亮环 + 暗洞。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "off_family_ring"
PRODUCT, VARIANT = "odd_radius_top3", "3_13-15-26-28"
PATH = (13, 15, 26, 28)
SUN_DISK_DEG, ANTI_DISK_DEG = 40.0, 12.0
DISK_PX = 820
DISPLAY_GAIN = 2.0
PROFILE_BIN = S.OBSERVED_BIN_DEG             # 1°：反日点附近 0.25° 桶只剩几个像素
WIDTH, HEIGHT, DPI = 2400, 1850, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def wedge_deg() -> float:
    return float(S.read_numbers(PRODUCT)["paths"][VARIANT]["wedge_deg"])


def min_deviation() -> float:
    return ES.min_deviation_deg(wedge_deg())


def profile() -> tuple[np.ndarray, np.ndarray]:
    return F.product_profile(PRODUCT, VARIANT, bin_deg=PROFILE_BIN)


def observed(c: np.ndarray, r: np.ndarray) -> dict:
    """实际最亮处（θ ≥ DISK_ZONE_DEG）及其峰 / 局部背景（`_ch9_sim.peak_over_background`，窗 ±3°，同 observed_peak 口径）。"""
    m = c >= S.DISK_ZONE_DEG
    i = int(np.flatnonzero(m)[np.argmax(r[m])])
    return S.peak_over_background(c, r, (c[i] - 3.0, c[i] + 3.0))


def disk(center: np.ndarray, max_deg: float) -> np.ndarray:
    img, cfg = S.load_product(PRODUCT, VARIANT)
    bg = tuple(int(PAL["background"][k:k + 2], 16) for k in (1, 3, 5))
    return F.rect_to_fisheye(img, cfg["render"][0], center, DISK_PX, max_deg, background=bg, gain=DISPLAY_GAIN)


def ring(ax, r: float, **kw) -> None:
    t = np.linspace(0, 2 * np.pi, 361)
    ax.plot(r * np.cos(t), r * np.sin(t), **kw)


def main() -> None:
    F.apply_style()
    R = min_deviation()
    c, r = profile()
    obs = observed(c, r)
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    w, h = DISK_PX / WIDTH, DISK_PX / HEIGHT
    top = 1 - h - 0.02
    # 左上：太阳中心
    ax = fig.add_axes([0.25 - w / 2, top, w, h])
    ax.imshow(disk(S.sun_direction(), SUN_DISK_DEG), interpolation="none",
              extent=(-SUN_DISK_DEG, SUN_DISK_DEG, -SUN_DISK_DEG, SUN_DISK_DEG))
    ring(ax, R, color=PAL["highlight"], lw=1.3, ls=(0, (5, 3)))
    ax.text(0, -R - 1.5, f"最小偏向角 {R:.1f}°：这里没有光", ha="center", va="top", fontsize=10, color=PAL["highlight"], **FONT)
    ax.text(0, 1.2, "太阳", ha="center", va="bottom", fontsize=9, color="white", alpha=0.8, **FONT)
    ax.set_axis_off()
    fig.text(0.25, top - 0.025, f"以太阳为中心（外圈 {SUN_DISK_DEG:.0f}°）", ha="center", va="center", fontsize=12.5,
             color=PAL["ink"], **FONT)
    # 右上：反日点中心
    ax = fig.add_axes([0.75 - w / 2, top, w, h])
    ax.imshow(disk(-S.sun_direction(), ANTI_DISK_DEG), interpolation="none",
              extent=(-ANTI_DISK_DEG, ANTI_DISK_DEG, -ANTI_DISK_DEG, ANTI_DISK_DEG))
    ax.plot(0, 0, marker="+", ms=9, mew=1.0, color="white", alpha=0.7)
    ax.set_axis_off()
    fig.text(0.75, top - 0.025, f"以反日点为中心（外圈 {ANTI_DISK_DEG:.0f}°）", ha="center", va="center", fontsize=12.5,
             color=PAL["ink"], **FONT)
    # 下：剖面
    ax = fig.add_axes([0.08, 0.07, 0.88, 0.33])
    ax.plot(c, r, color=F.SUM_COLOR, lw=1.5)
    ax.axvline(R, color=PAL["face_5"], lw=1.0, ls=(0, (5, 3)))
    ax.text(R + 1.5, 0.93, f"最小偏向角 {R:.1f}°\n（折叠楔角 {wedge_deg():.1f}°）", transform=ax.get_xaxis_transform(),
            ha="left", va="top", fontsize=10, color=PAL["face_5"], **FONT)
    ax.annotate(f"实际最亮处 {obs['peak_deg']:.0f}°：离反日点 {180 - obs['peak_deg']:.1f}°", xy=(obs["peak_deg"], obs["peak"]),
                xytext=(obs["peak_deg"] - 6, obs["peak"] * 0.98), ha="right", va="center", fontsize=10, color=PAL["ink_soft"],
                arrowprops=dict(arrowstyle="-|>", color=PAL["ink_soft"], lw=0.8, mutation_scale=8), **FONT)
    F.theta_axis(ax, 0, 180, 30)
    ax.set_ylim(0, r[c >= S.DISK_ZONE_DEG].max() * 1.12)
    ax.set_yticks([])
    ax.set_ylabel(F.RADIANCE_LABEL)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
