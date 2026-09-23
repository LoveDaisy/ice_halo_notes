# 产出 ../img/crowded_profiles.png（图 8「18°–24° 五族各自的径向剖面与按能量加总的总剖面」）+ ../data/crowded_profiles.numbers.json：
# 参考几何、随机取向，52.4° / 56° / 60° / 62° / 63.8° 五族（18° / 20° / 22° / 23° / 24° 晕）各自单独渲染的径向剖面（细线），与五条
# 按能量相加的总剖面（粗线）。数据：已入库 `data/odd_radius_families/w*/img_01.png`（不重渲），剖面按 Lumice 像素语义现算
# （`_ch9_fig.product_profile`：ΣL / Σcos(lat)，再除以各自曝光的 intensity——absolute 曝光下 radiance / intensity 就是同一物理单位，
# 直接相加即「按能量加总」，不需要再乘份额）。
# 机械核验（`test_ch9_figs.py`）：加总曲线在 15°–30° 的全部局部极大（`_ch9_sim.detect_peaks`，ratio 门槛取 0 = 只看是不是局部极大）
# 归到已知半径后，20°/22°/24° 有、18°/23° 没有；每条细线单独都在各自最小偏向角外 1° 内升过半峰（锐利内缘）。
# 读者要看出：单看每一族都有锐利的内缘；加起来后 18° 与 23° 只在邻环内坡上留下一处斜率变化，不再有局部极大。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "crowded_profiles"
WEDGES = (52.4, 56.0, 60.0, 62.0, 63.8)
FADED = (52.4, 62.0)                 # 加总后只剩斜率变化的两族（正文断言，单测核）
WINDOW = (16.0, 28.0)
PEAK_SEARCH = (15.0, 30.0)
WIDTH, HEIGHT, DPI = 2000, 1150, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def family_profiles() -> tuple[np.ndarray, dict[float, np.ndarray]]:
    out = {}
    c = None
    for w in WEDGES:
        c, out[w] = F.product_profile("odd_radius_families", f"w{w:g}")
    return c, out


def summed(profiles: dict[float, np.ndarray]) -> np.ndarray:
    return np.sum([profiles[w] for w in WEDGES], axis=0)


def sum_peaks(c: np.ndarray, total: np.ndarray) -> dict[float, dict | None]:
    """加总曲线的局部极大归到已知半径（只认 5 族）。"""
    pk = S.detect_peaks(c, total, ratio=0.0, min_deg=PEAK_SEARCH[0], max_deg=PEAK_SEARCH[1])
    return S.assign_peaks(pk, {w: S.KNOWN_RADII[w] for w in WEDGES})


def main() -> None:
    F.apply_style()
    c, prof = family_profiles()
    total = summed(prof)
    peaks = sum_peaks(c, total)
    fig, ax = plt.subplots(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.12)
    m = (c >= WINDOW[0]) & (c <= WINDOW[1])
    labels = {S.KNOWN_RADII[w]: f"{S.KNOWN_RADII[w]:.0f}°" for w in WEDGES}
    F.mark_radii(ax, [S.KNOWN_RADII[w] for w in WEDGES], labels=labels, y=1.01)
    for w in WEDGES:
        ax.plot(c[m], prof[w][m], color=F.FAMILY_COLOR[w], lw=1.2, label=f"{ES.min_deviation_deg(w):.0f}° 晕（{w:g}° 楔）")
    ax.plot(c[m], total[m], color=F.SUM_COLOR, lw=2.6, label="五族按能量加总")
    for w in FADED:
        r = S.KNOWN_RADII[w]
        y = float(np.interp(r + 0.35, c, total))
        ax.annotate("只剩斜率变化", xy=(r + 0.35, y), xytext=(r - 1.6, y + 0.45), fontsize=9.5, color=PAL["ink_soft"],
                    ha="center", arrowprops=dict(arrowstyle="-|>", color=PAL["ink_soft"], lw=0.8, mutation_scale=8), **FONT)
    F.theta_axis(ax, *WINDOW, 2)
    ax.set_ylim(0, total[m].max() * 1.15)
    ax.set_yticks([])
    ax.set_ylabel(F.RADIANCE_LABEL)
    ax.legend(loc="upper right", fontsize=9, ncol=1)
    fig.savefig(F.out_png(NAME), dpi=DPI, metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")
    S.write_numbers(NAME, {
        "source": "data/odd_radius_families/w*/img_01.png（已入库，不重渲）；剖面 = _ch9_fig.product_profile（ΣL/Σcos(lat) ÷ intensity）",
        "wedges": list(WEDGES), "window_deg": list(WINDOW),
        "sum_peaks": {f"{w:g}": (None if p is None else round(p["peak_deg"], 3)) for w, p in peaks.items()},
        "theta_deg": [round(float(x), 3) for x in c[m]],
        "families": {f"{w:g}": [round(float(x), 6) for x in prof[w][m]] for w in WEDGES},
        "sum": [round(float(x), 6) for x in total[m]],
    })


if __name__ == "__main__":
    main()
