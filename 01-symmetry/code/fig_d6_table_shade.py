# 产出 ../img/d6_table_shade.png：D6 群表（13×13），左上 6×6 的 C6 子群块淡红底 + 粗黑框，其余白底；行列顺序 = 旧表：
# I, R1–R5, F^f_3, F^d_{3,4}, F^f_4, F^d_{4,5}, F^f_5, F^d_{5,6}。重制 1.7 旧图 img/legacy/d6_table_shade.png（1486×1486）。
# 读者要看出：左上角是 C6 子群（正文第 71 行）；翻转 × 翻转 = 旋转（右下块全是 R）；F^f_3 行 F^d_{4,5} 列 = R^c_3。
from pathlib import Path

import matplotlib.pyplot as plt

from group_table import draw_group_table
from halo_notes.math.group import Fd, Ff, R, elements

OUT = Path(__file__).resolve().parent.parent / "img" / "d6_table_shade.png"
WIDTH, HEIGHT, DPI = 1486, 1486, 200  # = 旧图分辨率


def main() -> None:
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    elems = elements()
    table = draw_group_table(ax, elems, fontsize=11.5, grid_lw=0.6, frame_lw=1.2, block=6, block_lw=2.4)
    # 机械核验：右下 6×6 全是旋转；左上 6×6 封闭于 C6；正文第 71 行那一格；拉丁方
    assert all(not g.flip for row in table[6:] for g in row[6:])
    assert all(not g.flip for row in table[:6] for g in row[:6])
    assert table[elems.index(Ff(3))][elems.index(Fd(4))] == R(3)
    assert all(sorted(r, key=elems.index) == elems for r in table)
    assert all(sorted((row[j] for row in table), key=elems.index) == elems for j in range(12))
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
