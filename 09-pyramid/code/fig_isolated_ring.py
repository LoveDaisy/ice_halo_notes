# 产出 ../img/isolated_ring.png（图 5「逐族过滤的 18° 晕与一个容易辨认的经典环对照」）：参考几何、随机取向，两列——
#   左：只留 52.4° 族（18° 晕）的全部 ≤ 4 面代表光路；右：只留 63.8° 族（24° 晕，与 18° 同在 18°–24° 那一团里、全景里最亮最好认）。
#   上：以太阳为中心的等距鱼眼（外圈 30°），从已入库 `data/odd_radius_families/w{52.4,63.8}/img_01.png` 重投影（不重渲）；
#   下：径向剖面（两条曲线各自以窗口内最大值为 1，比形状）：彩色 = 这一族单独，灰色 = 全景（`odd_radius_panorama/rect`），竖虚线 = 该族
#       最小偏向角（`enumerate_signatures.min_deviation_deg` 现场算）。18° 族单独看内缘锐利、紧贴最小偏向角，而全景在同一位置只是
#       邻环内坡上的一个肩；24° 在全景里本来就是一个峰。
# 对照族是具名常量 `COMPARISON_WEDGE`：plan 裁定 24°（与 18° 同在拥挤团内，「拿出来仍然锐利」的对照更贴题），作者若要 9°（最亮最孤立）
# 改成 28.0 重跑即可。两列各用各自入库曝光显示（逐族图曝光到盘外最亮像素 ≈ 200/255）。
# 读者要看出：18° 晕单独拿出来是一个完整、内缘锐利的环；在全景剖面上它只剩肩部。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "isolated_ring"
TARGET_WEDGE = 52.4
COMPARISON_WEDGE = 63.8
DISK_PX, MAX_THETA = 760, 30.0
WIDTH, HEIGHT, DPI = 2400, 1700, 200
WINDOW = (12.0, 32.0)
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def family_variant(wedge: float) -> str:
    return f"w{wedge:g}"


def profiles(wedge: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(θ, 该族剖面 / intensity, 全景剖面 / intensity)``。"""
    c, fam = F.product_profile("odd_radius_families", family_variant(wedge))
    c2, pan = F.product_profile("odd_radius_panorama", "rect")
    assert np.array_equal(c, c2)
    return c, fam, pan


def inner_edge_deg(c: np.ndarray, prof: np.ndarray, *, frac: float = 0.5) -> float:
    """内缘位置：剖面从内侧第一次升到峰值 ``frac`` 倍的桶中心（「锐利的内缘紧贴最小偏向角」的机械读数）。"""
    i_pk = int(np.argmax(prof))
    idx = np.flatnonzero(prof[: i_pk + 1] >= frac * prof[i_pk])
    return float(c[idx[0]])


def draw_column(fig, x0: float, wedge: float, title: str) -> None:
    color = F.FAMILY_COLOR[wedge]
    img, cfg = S.load_product("odd_radius_families", family_variant(wedge))
    disk = F.rect_to_fisheye(img, cfg["render"][0], S.sun_direction(), DISK_PX, MAX_THETA,
                             background=tuple(int(PAL["background"][k:k + 2], 16) for k in (1, 3, 5)))
    w, h = DISK_PX / WIDTH, DISK_PX / HEIGHT
    ax = fig.add_axes([x0 + (0.5 - w) / 2, 1 - h - 0.02, w, h])
    ax.imshow(disk, interpolation="none")
    ax.set_axis_off()
    fig.text(x0 + 0.25, 1 - h - 0.045, title, ha="center", va="center", fontsize=13, color=PAL["ink"], **FONT)
    c, fam, pan = profiles(wedge)
    R = ES.min_deviation_deg(wedge)
    m = (c >= WINDOW[0]) & (c <= WINDOW[1])
    ax = fig.add_axes([x0 + 0.06, 0.11, 0.40, 0.31])
    ax.plot(c[m], pan[m] / pan[m].max(), color=PAL["slate"], lw=1.4, label="全景（全部光路）")
    ax.plot(c[m], fam[m] / fam[m].max(), color=color, lw=1.8, label="只留这一族")
    ax.axvline(R, color=color, lw=0.9, ls=(0, (4, 3)))
    ax.text(R - 0.25, 0.97, f"最小偏向角 {R:.1f}°", transform=ax.get_xaxis_transform(), ha="right", va="top", fontsize=9.5,
            color=color, **FONT)
    F.theta_axis(ax, *WINDOW, 4)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.5, 1])
    ax.set_ylabel("平均亮度（各自以窗口内最大值为 1）")
    ax.legend(loc="upper right", fontsize=9.5, bbox_to_anchor=(1.0, 0.86))


def main() -> None:
    F.apply_style()
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    for x0, wedge in ((0.0, TARGET_WEDGE), (0.5, COMPARISON_WEDGE)):
        halo = f"{ES.min_deviation_deg(wedge):.0f}° 晕"
        draw_column(fig, x0, wedge, f"只留 {wedge:g}° 楔一族：{halo}")
    fig.text(0.5, 0.012, f"上：以太阳为中心的等距鱼眼，外圈 {MAX_THETA:.0f}°；下：径向剖面",
             ha="center", va="bottom", fontsize=10, color=PAL["slate"], **FONT)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
