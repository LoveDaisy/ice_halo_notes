"""楔角光路的闭式量：最小偏向角（晕半径）。

全仓唯一权威实现——ch9 的族半径（``09-pyramid/code/enumerate_signatures.py``）、ch10 的 22° 晕内缘闭式对照
（``10-radius-and-azimuth/code/check_parhelion.py``）、ch12 与 LI 临界值的交叉核对（``12-sharp-edges/code/check_focusing.py``）
都调这里，不另抄公式。（``08.1-tape-vs-matrix/code/tape_halo_function.py`` 的 ``min_deviation_tk`` 按 Tape 的参数化另写，
是番外里「两条独立链路对照」的一侧，有意不合并。）
"""

import math

from lumice_integral.geometry.core import N_ICE


def min_deviation_deg(wedge_deg: float, n: float = N_ICE) -> float:
    """楔角 → 最小偏向角（晕半径）：$2\\arcsin(n\\sin(A/2)) - A$。0° 给 0；$n\\sin(A/2)>1$（不可透射）时按 1 截断。"""
    s = n * math.sin(math.radians(wedge_deg / 2))
    return 2 * math.degrees(math.asin(min(1.0, s))) - wedge_deg
