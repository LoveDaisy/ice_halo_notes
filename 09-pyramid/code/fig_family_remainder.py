# 产出 ../img/family_remainder.png（图 4「族外余量全天图及径向剖面」）+ ../data/family_remainder.numbers.json：参考几何、随机取向，
# 全天减去 9 族（≤ 4 面全部代表的 `filter_out`）后剩下的光——族外多次反射 + 单面外反射。返工 R1：太阳放天顶重渲（`render_zenith.py` 的
# panorama / remainder 两景，10⁹ 光线），不再从已入库 rectangular 重投影。
#   左栏三行，每行一张 dual fisheye 等距全天图（左盘圆心 = 太阳、右盘圆心 = 反日点，两盘盘沿都是与太阳成 90° 的那一圈）：
#     (a) 全天总晕图；(b) 族外余量，**与 (a) 同一绝对亮度标尺**；(c) 族外余量提亮 REMAINDER_GAIN 倍（倍数写在图上）；
#   右上：径向剖面（dual_fisheye_equal_area 取数），全景与余量画在**同一绝对纵轴**上（对数）；淡灰竖线 = 八个经典晕半径。
#     成环判据（`_ch9_sim` 的「峰 / 局部背景 ≥ 3」）是实现细节，返工 R2 起不画进图（作者：图上亮度差已说明问题），只留在单测里；
#   右下：同一参考几何下「方向集面积」与「能量」的份额对照——面积来自 `signature_table.md` 汇总行（族内 / 族外面积），能量来自
#     `odd_radius_families.numbers.json` 的 MC 份额（9 族 / 族外 / 单面外反射）。百分数取整进图面。
# 渲染侧的余量能量份额（余量 / 全景像素能量）另记 numbers.json，与 MC 份额互证。
# 读者要看出：同一亮度标尺下族外几乎看不见；提亮之后能看出几道暗弧，但没有一处过得了可辨阈值；方向集面积过半，能量却只有一成多。
from __future__ import annotations

import json
import re

import matplotlib.pyplot as plt
import numpy as np

import _ch9_fig as F
import _ch9_sim as S

NAME = "family_remainder"
WIDTH, HEIGHT, DPI = 2400, 2000, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}
REMAINDER_GAIN = 40.0      # (c) 的显示增益（线性亮度乘数）：余量最亮处约为全景最亮处的 1/45，×40 才看得清；只作用于 (c) 的显示
WHITE_HEADROOM = 1.3


def scenes() -> dict[str, F.DualScene]:
    return {"total": F.DualScene("zenith/panorama"), "remainder": F.DualScene("zenith/remainder")}


def profiles() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """全景与余量的径向剖面（绝对单位：每单位发射能量每 sr），右上栏画的就是它们，不做归一化。"""
    out = {}
    for k, sc in scenes().items():
        c, r, _ = sc.profile()
        out[k] = (c, r)
    return out


def shares() -> dict[str, dict[str, float]]:
    """{"area": {"in": %, "off": %}, "energy": {"in": %, "off": %, "single": %}}（参考几何）。"""
    text = (F.DATA / "signature_table.md").read_text()
    row = next(line for line in text.splitlines() if line.startswith("| 面积合计 (sr) 族内 / 族外 |"))
    a_in, a_off = (float(x) for x in re.findall(r"([\d.]+) / ([\d.]+)", row)[0])
    mc = json.loads((F.DATA / "odd_radius_families.numbers.json").read_text())["mc_shares"]
    e_in = sum(v for k, v in mc.items() if k not in ("off", "single"))
    return {"area": {"in": 100 * a_in / (a_in + a_off), "off": 100 * a_off / (a_in + a_off)},
            "energy": {"in": e_in, "off": mc["off"], "single": mc["single"]}}


def numbers(prof: dict, sc: dict) -> dict:
    c, r = prof["remainder"]
    e = {k: v.total_energy()["equal_area"] for k, v in sc.items()}
    return {"remainder_peaks": S.detect_peaks(c, r), "render_energy_share_pct": 100 * e["remainder"] / e["total"],
            "mc_off_plus_single_pct": shares()["energy"]["off"] + shares()["energy"]["single"],
            "remainder_gain": REMAINDER_GAIN, "total_energy": e}


def draw_dual(fig, rect, scene: F.DualScene, white: float, gain: float, title: str) -> None:
    x, y, w, h = rect
    dw = w / 2
    for k, (hemi, center) in enumerate((("sun", "太阳"), ("anti", "反日点"))):
        ax = fig.add_axes([x + k * dw, y, dw, h])
        rad, _ = F.disc_radiance(scene, hemi, 90.0)
        F.show_disc(ax, F.tone(rad, white, gain=gain), 90.0, rings=(30.0, 60.0), ring_labels=False, center=center)
    fig.text(x + 0.005, y + h + 0.004, title, ha="left", va="bottom", fontsize=12, color=PAL["ink"], **FONT)


def draw_profile(ax, prof: dict) -> None:
    F.mark_radii(ax, sorted(S.KNOWN_RADII.values()))
    c, tot = prof["total"]
    _, rem = prof["remainder"]
    m = c >= 1.0
    ax.plot(c[m], tot[m], color=PAL["slate"], lw=1.2, label="(a) 全天总晕", gid="profile:total")
    ax.plot(c[m], rem[m], color=F.SUM_COLOR, lw=1.5, label="(b) 族外余量", gid="profile:remainder")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    ax.yaxis.set_minor_formatter(plt.NullFormatter())
    F.theta_axis(ax, 0, 180, 30)
    ax.set_ylabel("平均亮度（对数，两条同一标尺）")
    ax.text(0.99, 0.02, "淡灰竖线：八个经典晕半径", transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=PAL["slate"],
            **FONT)
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


def build():
    """画整张图（不落盘）：返回 ``(fig, numbers)``——单测据此检查画上去的剖面就是绝对单位的原剖面、且同图共用纵轴。"""
    F.apply_style()
    sc = scenes()
    prof = profiles()
    nums = numbers(prof, sc)
    c, tot = prof["total"]
    white = WHITE_HEADROOM * float(tot[c >= 2].max())
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    h, w = 0.285, 0.285 * 2 * HEIGHT / WIDTH
    rows = [("(a) 全天总晕", sc["total"], 1.0), ("(b) 族外余量：与 (a) 同一亮度标尺", sc["remainder"], 1.0),
            (f"(c) 族外余量：提亮 {REMAINDER_GAIN:g} 倍", sc["remainder"], REMAINDER_GAIN)]
    for i, (title, s, gain) in enumerate(rows):
        draw_dual(fig, (0.01, 1 - (i + 1) * 0.325 + 0.01, w, h), s, white, gain, title)
    fig.text(0.012, 0.012, "每行两个圆：左圆心是太阳、右圆心是反日点，两圆边缘都是与太阳成 90° 的那一圈；虚线圈为 30° / 60°",
             ha="left", va="bottom", fontsize=9.5, color=PAL["slate"], **FONT)
    draw_profile(fig.add_axes([0.02 + w + 0.07, 0.42, 1 - w - 0.11, 0.53]), prof)
    draw_shares(fig.add_axes([0.02 + w + 0.14, 0.08, 1 - w - 0.18, 0.2]))
    return fig, nums


def main() -> None:
    fig, nums = build()
    S.write_numbers(NAME, nums)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}  {nums}")


if __name__ == "__main__":
    main()
