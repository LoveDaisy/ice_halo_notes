"""最小偏向角闭式：已知值与边界。"""

import math

import pytest

from halo_notes.math.wedge import min_deviation_deg


def test_known_radii():
    assert min_deviation_deg(60.0) == pytest.approx(21.8393, abs=1e-4)          # 22° 晕内缘（n = 1.31）
    assert min_deviation_deg(90.0) == pytest.approx(45.7, abs=0.05)             # 46° 晕（Tape 1980 p.5：45.7）
    assert min_deviation_deg(60.0) == pytest.approx(2 * math.degrees(math.asin(1.31 / 2)) - 60.0, abs=1e-12)


def test_edges():
    assert min_deviation_deg(0.0) == 0.0
    assert min_deviation_deg(120.0) == pytest.approx(60.0)                      # n·sin60° > 1：截断到 asin(1)
