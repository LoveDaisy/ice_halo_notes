# 产出 ../img/direct_wedges.png（图 2「二十个面两两配对得到的直接楔」）：一条楔角数轴（0°–160°），锥晶二十个面两两配对得到的
# 全部 16 种楔角都落在轴上——
#   99.5° 可透射上限（`2·arcsin(1/n)` 现场算）以左的 9 种：上方一排「卡片」（楔角 / 代表光路 / 晕半径），引线连到轴上的真实位置；
#     卡片按面对类型着色：六棱柱已有的三组（底↔底 / 柱↔柱 / 底↔柱）灰色，锥晶新增的柱↔锥 / 锥↔锥 / 底↔锥三组各一色；
#   上限以右的 7 种：灰底区里的叉号（光在第二个面全反射出不去），99.8° 只差 0.3° 被卡掉，单独点名。
# 楔角与面对类型从 `lumice_integral.geometry.Pyramid` 的面法向现场两两配对算出（楔角 = arccos(−n_a·n_b)），与
# `enumerate_signatures.KNOWN_WEDGES` 互相核对；代表光路读 `data/signature_table.md` 主表「最短代表」列，不手抄正文表格。
# 读者要看出：九个楔从哪些面对来、哪三组是锥晶新增的、上限卡掉了谁。
# 设计偏离 plan 的「一排 9 个楔形示意」：18°–24° 五族楔角挤在 11.4° 内，楔形图元与数轴位置对不上，改用数轴 + 卡片引线（progress DECISION）。
from __future__ import annotations

import itertools
import math
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import _ch9_fig as F
import enumerate_signatures as ES
from lumice_integral.geometry import Pyramid
from lumice_integral.geometry.core import N_ICE

NAME = "direct_wedges"
WIDTH, HEIGHT, DPI = 2400, 1000, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}
A_MAX = 2 * math.degrees(math.asin(1 / N_ICE))     # 可透射楔角上限（99.5°）
X_RANGE = (-4.0, 160.0)

KIND_NAME = {"BB": "底面 ↔ 底面", "PP": "柱面 ↔ 柱面", "BP": "底面 ↔ 柱面",
             "PY": "柱面 ↔ 锥面", "YY": "锥面 ↔ 锥面", "BY": "底面 ↔ 锥面"}
PRISM_KINDS = ("BB", "PP", "BP")                    # 六棱柱已有（灰）
NEW_KINDS = ("PY", "YY", "BY")                      # 锥晶新增（着色）
KIND_COLOR = {"BB": PAL["slate"], "PP": PAL["slate"], "BP": PAL["slate"],
              "PY": PAL["face_4"], "YY": PAL["face_3"], "BY": PAL["face_8"]}


def face_kind(n: int) -> str:
    return "B" if n in (1, 2) else ("P" if 3 <= n <= 8 else "Y")


def pair_wedges(p: Pyramid | None = None) -> dict[float, set[str]]:
    """全部面对的楔角（0.1° 取整）→ 出现过的面对类型集合（"BB"/"PY"/…，字母排序）。"""
    p = p or Pyramid()
    out: dict[float, set[str]] = defaultdict(set)
    for fa, fb in itertools.combinations(p.faces, 2):
        c = -float(np.dot(p.normal(fa), p.normal(fb)))
        A = round(math.degrees(math.acos(max(-1.0, min(1.0, c)))), 1)
        out[A].add("".join(sorted(face_kind(fa.number) + face_kind(fb.number), key="BPY".index)))
    return dict(out)


def transmittable(wedges: dict[float, set[str]]) -> list[float]:
    return sorted(A for A in wedges if A < A_MAX)


def wedge_kind(A: float, kinds: set[str]) -> str:
    """一个楔角的着色类型：0° 三种面对都有（平行面），归「底面 ↔ 底面」（正文表格的典型构成）；其余每个楔角只有一种面对类型。"""
    if A == 0.0:
        return "BB"
    (k,) = kinds
    return k


def representatives() -> dict[float, str]:
    """`signature_table.md` 主表：楔角 → 最短代表光路。"""
    text = (F.DATA / "signature_table.md").read_text()
    main = text.split("## 主表")[1].split("\n## ")[0]
    out = {}
    for line in main.splitlines():
        m = re.match(r"\| ([\d.]+)° \|.*?\| `([\d-]+)` \|", line)
        if m:
            out[float(m.group(1))] = m.group(2)
    return out


def radius_text(A: float) -> str:
    return "太阳原像" if A == 0 else f"{ES.min_deviation_deg(A):.0f}° 晕"


def main() -> None:
    wedges = pair_wedges()
    ok = transmittable(wedges)
    assert tuple(ok) == ES.KNOWN_WEDGES, ok
    reps = representatives()
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    ax = fig.add_axes([0.03, 0.14, 0.94, 0.84])
    ax.set_xlim(*X_RANGE)
    ax.set_ylim(-0.55, 1.0)
    ax.set_axis_off()
    ink, soft = PAL["ink_soft"], PAL["slate"]
    # 数轴
    ax.plot([0, X_RANGE[1]], [0, 0], color=ink, lw=1.2, zorder=2)
    for t in range(0, 161, 20):
        ax.plot([t, t], [0, -0.025], color=ink, lw=1.0)
        ax.text(t, -0.06, F.deg(t), ha="center", va="top", fontsize=10.5, color=ink, **FONT)
    ax.text(X_RANGE[1], -0.17, "楔角", ha="right", va="top", fontsize=11, color=ink, **FONT)
    # 不可透射区
    ax.axvspan(A_MAX, X_RANGE[1], ymin=0.0, ymax=1.0, color=PAL["medium"], alpha=0.35, lw=0, zorder=0)
    ax.plot([A_MAX, A_MAX], [0.0, 0.97], color=ink, lw=1.2, ls=(0, (5, 3)), zorder=3)
    ax.text(A_MAX + 1.5, 0.92, f"可透射上限 {A_MAX:.1f}°", ha="left", va="center", fontsize=12, color=ink, **FONT)
    ax.text(A_MAX + 1.5, 0.84, "楔角再大，光在第二个面全反射，出不去", ha="left", va="center", fontsize=10.5, color=ink, **FONT)
    blocked = sorted(A for A in wedges if A >= A_MAX)
    for A in blocked:
        ax.plot(A, 0, marker="x", ms=8, mew=1.8, color=KIND_COLOR[next(iter(wedges[A]))] if A != 120.0 else soft, zorder=4)
        if A == blocked[0]:
            continue                                   # 最近的一个单独点名（见下），不再竖排标注
        ax.text(A, 0.05, F.deg(A, 1 if A % 1 else 0), ha="center", va="bottom", fontsize=9.5, color=soft, rotation=90, **FONT)
    near = blocked[0]
    ax.annotate(f"{F.deg(near, 1)}（{KIND_NAME[next(iter(wedges[near]))]}）\n只差 {near - A_MAX:.1f}° 被卡掉",
                xy=(near, -0.02), xytext=(near + 6, -0.33), fontsize=10, color=ink, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=ink, lw=0.8), **FONT)
    # 可透射的 9 种：卡片 + 引线
    n = len(ok)
    card_x = np.linspace(4, A_MAX - 8, n)
    card_y, card_w, card_h = 0.52, 8.6, 0.36
    for A, cx in zip(ok, card_x):
        kind = wedge_kind(A, wedges[A])
        color = KIND_COLOR[kind]
        new = kind in NEW_KINDS
        ax.add_patch(FancyBboxPatch((cx - card_w / 2, card_y - card_h / 2), card_w, card_h,
                                    boxstyle="round,pad=0.0,rounding_size=1.2", mutation_aspect=0.04,
                                    facecolor=color if new else "white", edgecolor=color, lw=1.4, alpha=0.95, zorder=5))
        tc = "white" if new else ink
        ax.text(cx, card_y + 0.105, F.deg(A, 1 if A % 1 else 0), ha="center", va="center", fontsize=13, fontweight="bold",
                color=tc, zorder=6, **FONT)
        ax.text(cx, card_y - 0.005, reps[A], ha="center", va="center", fontsize=10, color=tc, zorder=6, family="Menlo")
        ax.text(cx, card_y - 0.1, radius_text(A), ha="center", va="center", fontsize=10.5 if A else 9.5, color=tc, zorder=6, **FONT)
        ax.plot([cx, A], [card_y - card_h / 2, 0.0], color=color, lw=1.1, zorder=3)
        ax.plot(A, 0, marker="o", ms=6.5, color=color, zorder=6, mec="white", mew=0.8)
    # 图例
    x = 0.06
    for k in PRISM_KINDS[:1] + NEW_KINDS:
        label = "六棱柱已有（底↔底 / 柱↔柱 / 底↔柱）" if k == "BB" else f"锥晶新增：{KIND_NAME[k]}"
        fig.text(x, 0.05, "■ " + label, ha="left", va="center", fontsize=11, color=KIND_COLOR[k], **FONT)
        x += 0.25 if k == "BB" else 0.19
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
