# 产出 ../img/panorama_triptych.png（图 6「三档随机取向全景并列」）：棱柱占主导 (h/a, tip_ratio) = (3, 0.25)、参考几何 (1, 0.5)、
# 锥面占主导 (0.3, 0.85) 三档锥晶随机取向全景，横排三联，每张都是**以太阳为中心的等距鱼眼**（半径 ∝ 与太阳的夹角，外圈 = 60°）。
# 数据：已入库的 `data/odd_radius_panorama{_h3_t0.25,,_h0.3_t0.85}/rect/img_01.png`（2×10⁸ 光线、max_hits 4、太阳 20°、D65、各自
# absolute 曝光到盘外最亮像素 ≈ 200/255），用 `_ch9_fig.rect_to_fisheye` 逐像素重投影——**不重渲**。已入库的 `fisheye/` 变体是天顶朝上的
# 等面积鱼眼，与正文「视野中心对准太阳的等距鱼眼」不符，所以不用它（progress DECISION）。
# 每张下方标该档「清晰可见的环」= 各自 numbers.json 的 `detected_radii`（峰 / 局部背景 ≥ 3，`_ch9_sim` 判据），不手填。
# 源图 0.25°/px，输出 0.15°/px（外圈 60° / 半径 400 px），双线性插值有轻微放大；Lumice 渲染不可逐字节复现，本脚本对同一份
# 入库渲染是逐字节可复现的。
# 读者要看出：三档的直接楔一样，点亮的环不一样。
from __future__ import annotations

import json

import matplotlib.pyplot as plt

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES

NAME = "panorama_triptych"
TIERS = (("odd_radius_panorama_h3_t0.25", "棱柱占主导"), ("odd_radius_panorama", "参考几何"),
         ("odd_radius_panorama_h0.3_t0.85", "锥面占主导"))
DISK_PX = 800
MAX_THETA = 60.0
WIDTH, HEIGHT, DPI = 3 * DISK_PX + 4 * 40, DISK_PX + 250, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def tier_numbers(name: str) -> dict:
    return json.loads((F.DATA / f"{name}.numbers.json").read_text())


def visible_halos(name: str) -> list[str]:
    """该档全景里「清晰可见」的环（numbers.json `detected_radii` → 晕名，按半径排）。"""
    d = tier_numbers(name)
    return [d["radii"][w]["halo"] for w in sorted(d["detected_radii"], key=float)]


def panel_image(name: str):
    img, cfg = S.load_product(name, "rect")
    return F.rect_to_fisheye(img, cfg["render"][0], S.sun_direction(S.SUN_ALT), DISK_PX, MAX_THETA,
                             background=tuple(int(F.PAL["background"][k:k + 2], 16) for k in (1, 3, 5)))


def main() -> None:
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    gap = 40 / WIDTH
    w = DISK_PX / WIDTH
    h = DISK_PX / HEIGHT
    for k, (name, label) in enumerate(TIERS):
        x0 = gap + k * (w + gap)
        ax = fig.add_axes([x0, 1 - h - 20 / HEIGHT, w, h])
        ax.imshow(panel_image(name), interpolation="none")
        ax.set_axis_off()
        tier = tuple(tier_numbers(name)["tier"])
        assert tier == tuple(ES.TIERS[[ES.tier_label(t) for t in ES.TIERS].index(ES.tier_label(tier))])
        fig.text(x0 + w / 2, 150 / HEIGHT, label, ha="center", va="center", fontsize=14, color=PAL["ink"], **FONT)
        fig.text(x0 + w / 2, 85 / HEIGHT, "清晰可见：" + "、".join(visible_halos(name)), ha="center", va="center",
                 fontsize=11.5, color=PAL["ink_soft"], **FONT)
    fig.text(0.5, 25 / HEIGHT, f"以太阳为中心的等距鱼眼，圆心到外圈 {MAX_THETA:.0f}°", ha="center", va="center", fontsize=10,
             color=PAL["slate"], **FONT)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
