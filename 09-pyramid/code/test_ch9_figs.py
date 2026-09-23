"""task-draw-ch9-figs：ch9 十一张正文插图的机械核验——**唯一权威位置**（每图一条语义断言，fig 脚本不再内联重复判据）。
被检量都由对应 `fig_*.py` / `_ch9_fig.py` 里的纯函数给出，这里只 import 调用、断言正文图题的语义；图面美观不在此列（owner 签核）。
不跑 Lumice：图 4/5/6/8/9 只读已入库渲染，图 11 读已入库的 `data/plate_arcs*` 产物。"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import check_pyramid as CP  # noqa: E402
import enumerate_signatures as ES  # noqa: E402
import fig_closure_growth as G3  # noqa: E402
import fig_corridor_1_3 as G7  # noqa: E402
import fig_direct_wedges as G2  # noqa: E402
import fig_pyramid_faces as G1  # noqa: E402
from lumice_integral.geometry import pyramid_face_angle  # noqa: E402

ALL_FACES = {1, 2, *range(3, 9), *range(13, 19), *range(23, 29)}


# ---- 图 1：二十个面的编号 ----


def test_fig1_two_views_label_all_twenty_faces():
    up, lo = set(G1.labelled_faces("upper")), set(G1.labelled_faces("lower"))
    assert up | lo == ALL_FACES and len(ALL_FACES) == 20


def test_fig1_face_angle_is_geometry_not_parameter():
    """标注的角度从法向现场算出、等于闭式 arctan((2/√3)c/a)，且与截顶比例 / 柱段高无关。"""
    ang = G1.face_angle_deg()
    assert ang == pytest.approx(pyramid_face_angle(), abs=1e-9)
    assert round(ang, 1) == 62.0
    for h, t in ((0.3, 0.85), (3.0, 0.25)):
        assert G1.face_angle_deg(G1.Pyramid(a=1.0, h=h, tip_ratio=t)) == pytest.approx(ang, abs=1e-9)


# ---- 图 2：九个直接楔 ----


def test_fig2_nine_transmittable_wedges_and_colouring():
    wedges = G2.pair_wedges()
    ok = G2.transmittable(wedges)
    assert tuple(ok) == ES.KNOWN_WEDGES
    assert ok == CP.transmittable_wedges(True)                      # 定理 7 核验脚本的独立实现（法向手写）一致
    assert G2.A_MAX == pytest.approx(2 * math.degrees(math.asin(1 / 1.31)))
    kinds = {A: G2.wedge_kind(A, wedges[A]) for A in ok}
    gray = {A for A, k in kinds.items() if k in G2.PRISM_KINDS}
    assert gray == {0.0, 60.0, 90.0} == set(CP.transmittable_wedges(False))   # 灰色 = 六棱柱已有
    assert {kinds[A] for A in ok if A not in gray} == set(G2.NEW_KINDS)       # 新增三组都出现
    blocked = sorted(A for A in wedges if A >= G2.A_MAX)
    assert blocked[0] == 99.8 and wedges[99.8] == {"YY"}            # 上限刚好卡掉的是一个锥↔锥楔
    assert set(G2.representatives()) == set(ES.KNOWN_WEDGES)


# ---- 图 3：闭包增长 ----


def test_fig3_prism_caps_at_12_pyramid_keeps_growing():
    data = G3.growth_data(max_len=7)
    assert data[False][3:] == [12] * 5
    assert data[True][:7] == CP.KNOWN_PYRAMID_GROWTH_6
    ratios = [b / a for a, b in zip(data[True][3:], data[True][4:])]
    assert all(r > 4 for r in ratios)                                # 字长 4…7 每级仍 ×4 以上，未见减速


# ---- 图 7：`1-3` 走廊 ----


def test_fig7_corridor_open_then_closed():
    assert G7.corridor_area_sr(G7.TIPS[0]) > 0
    assert G7.corridor_area_sr(G7.TIPS[1]) == 0
    hits = {t: {face for _, _, face in G7.trace_fan(t)} for t in G7.TIPS}
    assert 3 in hits[G7.TIPS[0]] and hits[G7.TIPS[1]] == {13}      # 截面示意与三维结论同向
    assert G7.first_length_90(G7.TIPS[0]) == 2 and G7.first_length_90(G7.TIPS[1]) == 5
