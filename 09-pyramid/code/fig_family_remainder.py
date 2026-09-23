# 产出 ../img/family_remainder.png（图 4「族外余量全天图及径向剖面」）：参考几何、随机取向、全天减去 9 族（≤ 4 面全部代表的
# `filter_out`）后剩下的光——族外多次反射 + 单面外反射。三块：
#   左：以太阳为中心的**全天**等距鱼眼（圆心 = 太阳，外圈 = 180° = 反日点；半径 ∝ 与太阳的夹角，与右上剖面横轴一一对应），
#       从已入库 `data/odd_radius_remainder/rect/img_01.png` 重投影（`_ch9_fig.rect_to_fisheye`，不重渲）；
#   右上：径向剖面（对数纵轴；按 Lumice 像素语义现算，见 `_ch9_fig` 天空图一节——numbers.json 里的旧剖面多乘了一次 cos(lat)），叠一条
#       「3 × 局部背景」虚线——`_ch9_sim` 的成环判据（峰 / 局部背景 ≥ 3），剖面没有一处局部极大越过它，淡灰竖线 = 八个经典晕半径；
#   右下：同一参考几何下「方向集面积」与「能量」的份额对照——面积来自 `signature_table.md` 汇总行（族内 / 族外面积），能量来自
#       `odd_radius_families.numbers.json` 的 MC 份额（9 族 / 族外 / 单面外反射）。百分数取整进图面。
# 设计偏离 plan（plan：rectangular 原图）：换成太阳中心全天等距鱼眼，理由同图 6，且让天空图半径与剖面横轴同一刻度（progress DECISION）。
# 读者要看出：族外是太阳周围的雾 + 反日侧的弥散，不是环；方向集面积过半，能量却只有一成多。
from __future__ import annotations

import json
import re

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S

NAME = "family_remainder"
WIDTH, HEIGHT, DPI = 2400, 1120, 200
DISK_PX = 1000
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}
PRODUCT = "odd_radius_remainder"
DISPLAY_GAIN = 2.5        # 只作用于左侧天空图的显示（线性亮度 ×2.5，太阳旁的雾仍不削顶）；余量是全天最暗的成分，按原曝光几乎看不见。剖面取数不受影响


def numbers() -> dict:
    return S.read_numbers(PRODUCT)


def profile() -> tuple[np.ndarray, np.ndarray]:
    """径向剖面：按 Lumice 像素语义从入库渲染现算（`_ch9_fig.radiance_profile`，0.25° 桶，与 numbers.json 同分桶）。"""
    img, cfg = S.load_product(PRODUCT, "rect")
    c, r, _ = F.radiance_profile(img, cfg["render"][0], S.sun_direction())
    return c, r


def threshold_curve(centers: np.ndarray, radiance: np.ndarray) -> np.ndarray:
    """每个 θ 处的「成环判据线」= PEAK_RATIO × 局部背景（`_ch9_sim.local_background`，与 detect_peaks 同一口径）。"""
    return np.array([S.PEAK_RATIO * S.local_background(centers, radiance, float(t)) for t in centers])


def shares() -> dict[str, dict[str, float]]:
    """{"area": {"in": %, "off": %}, "energy": {"in": %, "off": %, "single": %}}（参考几何）。"""
    text = (F.DATA / "signature_table.md").read_text()
    row = next(line for line in text.splitlines() if line.startswith("| 面积合计 (sr) 族内 / 族外 |"))
    a_in, a_off = (float(x) for x in re.findall(r"([\d.]+) / ([\d.]+)", row)[0])
    mc = json.loads((F.DATA / "odd_radius_families.numbers.json").read_text())["mc_shares"]
    e_in = sum(v for k, v in mc.items() if k not in ("off", "single"))
    return {"area": {"in": 100 * a_in / (a_in + a_off), "off": 100 * a_off / (a_in + a_off)},
            "energy": {"in": e_in, "off": mc["off"], "single": mc["single"]}}


def draw_disk(ax) -> None:
    img, cfg = S.load_product(PRODUCT, "rect")
    bg = tuple(int(PAL["background"][k:k + 2], 16) for k in (1, 3, 5))
    ax.imshow(F.rect_to_fisheye(img, cfg["render"][0], S.sun_direction(), DISK_PX, 180.0, background=bg, gain=DISPLAY_GAIN),
              interpolation="none", extent=(-180, 180, -180, 180))
    t = np.linspace(0, 2 * np.pi, 361)
    for r in (45, 90, 135):
        ax.plot(r * np.cos(t), r * np.sin(t), color="white", lw=0.5, alpha=0.25, ls=(0, (3, 3)))
        ax.text(r * np.cos(np.radians(-40)), r * np.sin(np.radians(-40)), F.deg(r), color="white", alpha=0.6, fontsize=8.5,
                ha="left", va="top", **FONT)
    ax.text(0, -198, "外圈 180° = 反日点", ha="center", va="top", fontsize=10, color=PAL["ink_soft"], **FONT)
    ax.text(0, 9, "太阳", ha="center", va="bottom", fontsize=9, color="white", alpha=0.8, **FONT)
    ax.set_xlim(-185, 185)
    ax.set_ylim(-215, 185)
    ax.set_axis_off()


def draw_profile(ax) -> None:
    c, r = profile()
    thr = threshold_curve(c, r)
    F.mark_radii(ax, sorted(S.KNOWN_RADII.values()))
    ax.plot(c, r, color=F.SUM_COLOR, lw=1.4, label="族外余量的径向剖面")
    ax.plot(c, thr, color=PAL["face_3"], lw=1.0, ls=(0, (4, 3)), label="3 × 局部背景（成环判据）")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 2.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    F.theta_axis(ax, 0, 180, 30)
    ax.set_ylabel("平均亮度（对数）")
    ax.text(4, 0.03, "太阳周围的雾", fontsize=10.5, color=PAL["ink_soft"], **FONT)
    ax.text(125, 0.026, "反日侧的弥散", fontsize=10.5, color=PAL["ink_soft"], **FONT)
    ax.text(21.8, 0.0115, "淡灰竖线：八个经典晕半径", fontsize=9, color=PAL["slate"], **FONT)
    ax.legend(loc="upper right", fontsize=9.5)


def draw_shares(ax) -> None:
    s = shares()
    rows = [("方向集面积", [("族内", s["area"]["in"], PAL["face_4"]), ("族外", s["area"]["off"], PAL["face_3"])]),
            ("实际能量", [("经典 9 族", s["energy"]["in"], PAL["face_4"]), ("族外", s["energy"]["off"], PAL["face_3"]),
                          ("单面外反射", s["energy"]["single"], PAL["slate"])])]
    for y, (name, parts) in zip((1, 0), rows):
        x, small = 0.0, 0
        for label, v, color in parts:
            ax.barh(y, v, left=x, height=0.62, color=color, edgecolor="white", lw=1.0)
            txt = f"{label} {v:.0f}%"
            if v > 14:
                ax.text(x + v / 2, y, txt, ha="center", va="center", fontsize=10, color="white", **FONT)
            else:                                           # 窄段：标在条下方、右端对齐该段末尾，逐段往下错开
                ax.text(x + v, y - 0.5 - 0.34 * small, txt, ha="right", va="center", fontsize=9, color=color, **FONT)
                small += 1
            x += v
        ax.text(-1.5, y, name, ha="right", va="center", fontsize=10.5, color=PAL["ink"], **FONT)
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.1, 1.6)
    ax.set_axis_off()


def main() -> None:
    F.apply_style()
    c, r = profile()
    assert S.detect_peaks(c, r) == [] and numbers()["peaks"] == []
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    draw_disk(fig.add_axes([0.0, 0.0, 0.46, 1.0]))
    draw_profile(fig.add_axes([0.54, 0.39, 0.44, 0.56]))
    draw_shares(fig.add_axes([0.62, 0.03, 0.36, 0.2]))
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
