# 产出 ../img/crowded_profiles.png（图 8「18°–24° 五族各自的径向剖面与按能量加总的总剖面」）+ ../data/crowded_profiles.numbers.json：
# 参考几何、随机取向，52.4° / 56° / 60° / 62° / 63.8° 五族（18° / 20° / 22° / 23° / 24° 晕）各自单独渲染的径向剖面（细线），与五条
# 按能量相加的总剖面（粗线）。返工 R2：改用太阳天顶新批次（`render_zenith.py` 的 w52.4 / w56 / w60 / w62 / w63.8 五景，10⁹ 光线，
# 与图 5 / 图 6 同源），剖面 = `DualScene.profile()`（dual_fisheye_equal_area 取数，raw / emitted_energy 的绝对单位——五景同一发射
# 口径，直接相加即「按能量加总」，不需要再乘份额）。上一轮的 rectangular 版本（`data/odd_radius_families/`）是历史记录，不再用。
# 机械核验（`test_ch9_figs.py`）：加总曲线在 15°–30° 的全部局部极大（`_ch9_sim.detect_peaks`，ratio 门槛取 0 = 只看是不是局部极大）
# 归到已知半径后，20°/22°/24° 有、18° 没有；23° 只剩一个高出前方谷底不到 BUMP_MAX 的小鼓包，桶宽放到 0.5° 即消失（作者裁定 (a)：
# 判据不动、如实写）；每条细线单独都在各自最小偏向角外 1° 内升过半峰（锐利内缘）。
# 读者要看出：单看每一族都有锐利的内缘；加起来后 18° 连起伏都没有，23° 只剩骑在 22° 环外坡上的一个小鼓包，都认不出一个环。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "crowded_profiles"
WEDGES = (52.4, 56.0, 60.0, 62.0, 63.8)
FADED = (52.4, 62.0)                 # 加总后认不出环的两族（正文断言，单测核）：18° 无局部极大、23° 只剩小鼓包
NO_MAX, BUMP = 52.4, 62.0
BUMP_MAX = 0.05                      # 23° 小鼓包高出前方谷底的上限（实测 2.7%）
FADED_NOTE = {NO_MAX: "连起伏都没有", BUMP: "只剩一个小鼓包"}
WINDOW = (16.0, 28.0)
PEAK_SEARCH = (15.0, 30.0)
WIDTH, HEIGHT, DPI = 2000, 1150, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def family_profiles(bin_deg: float = S.PROFILE_BIN_DEG) -> tuple[np.ndarray, dict[float, np.ndarray]]:
    """五族各自的径向剖面（绝对单位），``(θ, {楔角: 辐亮度})``。"""
    out = {}
    c = None
    for w in WEDGES:
        c, out[w], _ = F.DualScene(f"zenith/w{w:g}").profile(bin_deg=bin_deg)
    return c, out


def summed(profiles: dict[float, np.ndarray]) -> np.ndarray:
    return np.sum([profiles[w] for w in WEDGES], axis=0)


def sum_peaks(c: np.ndarray, total: np.ndarray) -> dict[float, dict | None]:
    """加总曲线的局部极大归到已知半径（只认 5 族）。"""
    pk = S.detect_peaks(c, total, ratio=0.0, min_deg=PEAK_SEARCH[0], max_deg=PEAK_SEARCH[1])
    return S.assign_peaks(pk, {w: S.KNOWN_RADII[w] for w in WEDGES})


def bump_height(c: np.ndarray, total: np.ndarray, peak_deg: float) -> float:
    """局部极大 ``peak_deg`` 高出它与内侧（小 θ 方向）最近谷底的相对量。"""
    i = int(np.argmin(np.abs(c - peak_deg)))
    j = i
    while j > 0 and total[j - 1] <= total[j]:
        j -= 1
    return float(total[i] / total[j] - 1)


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
        x = r + 0.35 if w == NO_MAX else peaks[w]["peak_deg"]
        y = float(np.interp(x, c, total))
        dy = 0.12 * total[m].max()
        ax.annotate(FADED_NOTE[w], xy=(x, y), xytext=(x - 1.6, y + dy), fontsize=9.5, color=PAL["ink_soft"],
                    ha="center", arrowprops=dict(arrowstyle="-|>", color=PAL["ink_soft"], lw=0.8, mutation_scale=8), **FONT)
    F.theta_axis(ax, *WINDOW, 2)
    ax.set_ylim(0, total[m].max() * 1.15)
    ax.set_yticks([])
    ax.set_ylabel(F.RADIANCE_LABEL)
    ax.legend(loc="upper right", fontsize=9, ncol=1)
    fig.savefig(F.out_png(NAME), dpi=DPI, metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")
    S.write_numbers(NAME, {
        "source": "data/zenith/w*.zip（太阳天顶 dual fisheye，equal_area 取数）；剖面 = _ch9_fig.DualScene.profile（raw / emitted_energy）",
        "bump_23": {"peak_deg": peaks[BUMP]["peak_deg"], "height_over_inner_trough": round(bump_height(c, total, peaks[BUMP]["peak_deg"]), 4)},
        "wedges": list(WEDGES), "window_deg": list(WINDOW),
        "sum_peaks": {f"{w:g}": (None if p is None else round(p["peak_deg"], 3)) for w, p in peaks.items()},
        "theta_deg": [round(float(x), 3) for x in c[m]],
        "families": {f"{w:g}": [round(float(x), 6) for x in prof[w][m]] for w in WEDGES},
        "sum": [round(float(x), 6) for x in total[m]],
    })


if __name__ == "__main__":
    main()
