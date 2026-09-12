# 产出 ../img/c6_table.png：C6 群表（7×7：表头行 / 列 + 6×6 正文），表头灰底粗斜体，格内 $I$、$R^c_1$…$R^c_5$。
# 重制 1.4 旧图 img/legacy/c6_table.png（800×800）。读者要看出：i 行 j 列 = 先 i 后 j（正文第 39 行：2 行 3 列 =
# $R^c_3$），且每行每列都是全部 6 个元素的一个排列（拉丁方）。格内容由 halo_notes.math.group 算出，脚本内自检。
from pathlib import Path

import matplotlib.pyplot as plt

from group_table import draw_group_table
from halo_notes.math.group import R, elements

OUT = Path(__file__).resolve().parent.parent / "img" / "c6_table.png"
WIDTH, HEIGHT, DPI = 800, 800, 200  # = 旧图分辨率


def main() -> None:
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    rots = elements()[:6]
    table = draw_group_table(ax, rots, fontsize=11, grid_lw=0.6, frame_lw=1.2)
    # 机械核验：正文第 39 行例子 + 拉丁方 + C6 交换（表关于主对角线对称）
    assert table[1][2] == R(3), table[1][2]
    assert all(sorted(r, key=rots.index) == rots for r in table)
    assert all(sorted((row[j] for row in table), key=rots.index) == rots for j in range(6))
    assert all(table[i][j] == table[j][i] for i in range(6) for j in range(6))
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
