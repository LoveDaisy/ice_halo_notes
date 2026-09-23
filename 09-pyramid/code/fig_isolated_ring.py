# 产出 ../img/isolated_ring.png（图 5「逐族过滤的 18° 晕与一个容易辨认的经典环对照」）+ ../data/isolated_ring.numbers.json：
# 参考几何、随机取向（返工 R1：太阳放天顶重渲，`render_zenith.py` 的 w52.4 / w63.8 / panorama 三景，10⁹ 光线）。
#   上排三栏：只留 52.4° 族（18° 晕）的全部 ≤ 4 面代表光路 / 只留 63.8° 族（24° 晕，与 18° 同在 18°–24° 那一团里、全景里最亮最好认）/
#     全景总晕图——以太阳为中心的等距鱼眼（dual_fisheye_equidistant 太阳半球裁到 30°），**三张同一绝对曝光**；
#   下：三条径向剖面画在**同一绝对纵轴**上（线性，不各自归一化——各自归一化会让人问「这么高的峰怎么会看不见」），竖虚线 = 两族
#     最小偏向角（`enumerate_signatures.min_deviation_deg` 现场算）。18° 族单独看内缘锐利、紧贴最小偏向角，而全景在同一位置只是
#     邻环内坡上的一个肩；24° 在全景里本来就是一个峰。
# 对照族是具名常量 `COMPARISON_WEDGE`：plan 裁定 24°（与 18° 同在拥挤团内），作者若要 9°（最亮最孤立）改成 28.0 并补渲一景即可。
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
MAX_THETA = 30.0
RINGS = (10.0, 20.0)
DISK_PX = 700
WIDTH, HEIGHT, DPI = 2400, 1720, 200
WINDOW = (12.0, 32.0)
WHITE_HEADROOM = 1.3      # 满白 = 1.3 × 全景剖面在 WINDOW 内的最大值（9° 环在窗外、会削顶——它不是这张图的对象）
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def family_scene(wedge: float) -> F.DualScene:
    return F.DualScene(f"zenith/w{wedge:g}")


def profiles(wedge: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(θ, 该族剖面, 全景剖面)``，绝对单位（每单位发射能量每 sr）——下栏画的就是它们。"""
    c, fam, _ = family_scene(wedge).profile()
    c2, pan, _ = F.DualScene("zenith/panorama").profile()
    assert np.array_equal(c, c2)
    return c, fam, pan


def inner_edge_deg(c: np.ndarray, prof: np.ndarray, *, frac: float = 0.5) -> float:
    """内缘位置：剖面从内侧第一次升到峰值 ``frac`` 倍的桶中心（「锐利的内缘紧贴最小偏向角」的机械读数）。"""
    i_pk = int(np.argmax(prof))
    idx = np.flatnonzero(prof[: i_pk + 1] >= frac * prof[i_pk])
    return float(c[idx[0]])


def numbers() -> dict:
    out = {}
    for w in (TARGET_WEDGE, COMPARISON_WEDGE):
        c, fam, pan = profiles(w)
        R = ES.min_deviation_deg(w)
        inside = (c < R - 0.5) & (c > R - 5)
        out[f"{w:g}"] = {"min_deviation_deg": R, "inner_edge_deg": inner_edge_deg(c, fam),
                         "peak": float(fam.max()), "inside_max_over_peak": float(fam[inside].max() / fam.max()),
                         "panorama_at_family_peak": float(pan[int(np.argmax(fam))])}
    c, _, pan = profiles(TARGET_WEDGE)
    pk = S.assign_peaks(S.detect_peaks(c, pan))
    out["panorama_visible"] = sorted(f"{w:g}" for w, p in pk.items() if p is not None)
    return out


def build():
    """画整张图（不落盘）：返回 ``(fig, numbers)``——单测据此检查画上去的剖面就是绝对单位的原剖面、且同图共用纵轴。"""
    F.apply_style()
    nums = numbers()
    c, fam18, pan = profiles(TARGET_WEDGE)
    _, fam24, _ = profiles(COMPARISON_WEDGE)
    m = (c >= WINDOW[0]) & (c <= WINDOW[1])
    white = WHITE_HEADROOM * float(pan[m].max())
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    cols = [(family_scene(TARGET_WEDGE), f"只留 {TARGET_WEDGE:g}° 楔一族：18° 晕", F.FAMILY_COLOR[TARGET_WEDGE]),
            (family_scene(COMPARISON_WEDGE), f"只留 {COMPARISON_WEDGE:g}° 楔一族：24° 晕", F.FAMILY_COLOR[COMPARISON_WEDGE]),
            (F.DualScene("zenith/panorama"), "全景（全部光路）", PAL["ink"])]
    w, h = DISK_PX / WIDTH, DISK_PX / HEIGHT
    top = 1 - h - 15 / HEIGHT
    for k, (sc, title, color) in enumerate(cols):
        x0 = k / 3
        ax = fig.add_axes([x0 + (1 / 3 - w) / 2, top, w, h])
        rad, _ = F.disc_radiance(sc, "sun", MAX_THETA)
        F.show_disc(ax, F.tone(rad, white), MAX_THETA, rings=RINGS, center="太阳")
        fig.text(x0 + 1 / 6, top - 38 / HEIGHT, title, ha="center", va="center", fontsize=13, color=color, **FONT)
    ax = fig.add_axes([0.07, 0.1, 0.9, 0.36])
    ax.plot(c[m], pan[m], color=PAL["slate"], lw=1.4, label="全景（全部光路）", gid="profile:panorama")
    for wedge, prof in ((TARGET_WEDGE, fam18), (COMPARISON_WEDGE, fam24)):
        color = F.FAMILY_COLOR[wedge]
        R = ES.min_deviation_deg(wedge)
        ax.plot(c[m], prof[m], color=color, lw=1.8, label=f"只留 {wedge:g}° 楔一族（{R:.0f}° 晕）", gid=f"profile:w{wedge:g}")
        ax.axvline(R, color=color, lw=0.9, ls=(0, (4, 3)))
        ax.text(R - 0.15, 0.97, f"最小偏向角 {R:.1f}°", transform=ax.get_xaxis_transform(), ha="right", va="top", fontsize=9.5,
                color=color, **FONT)
    F.theta_axis(ax, *WINDOW, 2)
    ax.set_ylim(0, float(pan[m].max()) * 1.12)
    ax.set_yticks([])
    ax.set_ylabel("平均亮度（三条同一标尺）")
    ax.legend(loc="upper left", fontsize=9.5, bbox_to_anchor=(0.0, 0.88))
    fig.text(0.5, 0.012, f"上：以太阳为中心的等距鱼眼，外圈 {MAX_THETA:.0f}°，三张同一曝光；下：径向剖面",
             ha="center", va="bottom", fontsize=10, color=PAL["slate"], **FONT)
    return fig, nums


def main() -> None:
    fig, nums = build()
    S.write_numbers(NAME, nums)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}  {nums}")


if __name__ == "__main__":
    main()
