# 产出 ../img/closure_growth.png（图 3「反射矩阵闭包随字长的增长」）：六棱柱（8 面）与锥晶（20 面）的镜面反射矩阵闭包元素数随字长
# 0–8 的累计增长，纵轴对数。数据直接调 `check_pyramid.mirror_group_growth`（定理 6 核验脚本的同一函数，不另写数组）：
# 六棱柱在字长 3 封顶于 12；锥晶字长 6 为 47244（= `KNOWN_PYRAMID_GROWTH_6`），字长 7、8 仍以每级约 5 倍增长。
# 正文断言的范围是字长 0–6，字长 7、8 用浅底标「继续往后算两级」。跑一次约 20 s（字长 8 的闭包有 118 万个矩阵）。
# 读者要看出：一条封顶在 12、一条一路上升且没有减速。
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

import _ch9_fig as F
import check_pyramid as CP

NAME = "closure_growth"
WIDTH, HEIGHT, DPI = 1800, 1100, 200
MAX_LEN = 8
TEXT_LEN = 6                        # 正文断言覆盖的字长
PAL = F.PAL
COLORS = {False: PAL["slate"], True: PAL["face_3"]}
LABELS = {False: "六棱柱（8 个面）", True: "锥晶（20 个面）"}


def growth_data(max_len: int = MAX_LEN) -> dict[bool, list[int]]:
    return {pyr: CP.mirror_group_growth(pyr, max_len) for pyr in (False, True)}


def main() -> None:
    F.apply_style()
    data = growth_data()
    assert data[True][: TEXT_LEN + 1] == CP.KNOWN_PYRAMID_GROWTH_6
    fig, ax = plt.subplots(figsize=((WIDTH + 0.5) / DPI, (HEIGHT + 0.5) / DPI), dpi=DPI)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.95, bottom=0.13)
    x = np.arange(MAX_LEN + 1)
    ax.axvspan(TEXT_LEN + 0.5, MAX_LEN + 0.5, color=PAL["medium"], alpha=0.3, lw=0)
    ax.text(TEXT_LEN + 1.5, 1.5, "继续往后算两级", ha="center", va="bottom", fontsize=10.5, color=PAL["ink_soft"])
    for pyr in (False, True):
        y = data[pyr]
        ax.plot(x, y, color=COLORS[pyr], lw=2.2, marker="o", ms=5.5, label=LABELS[pyr], zorder=3)
    ax.annotate("封顶于 12", xy=(4, 12), xytext=(4.3, 3.2), fontsize=11, color=COLORS[False],
                arrowprops=dict(arrowstyle="-", color=COLORS[False], lw=0.8))
    for k in (TEXT_LEN, MAX_LEN):
        v = data[True][k]
        ax.annotate(f"{v:,}", xy=(k, v), xytext=(k - 0.25, v * 2.2), ha="right", fontsize=10.5, color=COLORS[True])
    ax.set_yscale("log")
    ax.set_xlim(-0.3, MAX_LEN + 0.5)
    ax.set_ylim(0.8, 1e7)
    ax.set_xticks(x)
    ax.yaxis.set_major_locator(FixedLocator([1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="y", color=PAL["ink_faint"], lw=0.6, alpha=0.7)
    ax.set_xlabel("字长（至多几次镜面反射相乘）")
    ax.set_ylabel("闭包里不同矩阵的个数（对数）")
    ax.legend(loc="upper left")
    fig.savefig(F.out_png(NAME), dpi=DPI, metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}")


if __name__ == "__main__":
    main()
