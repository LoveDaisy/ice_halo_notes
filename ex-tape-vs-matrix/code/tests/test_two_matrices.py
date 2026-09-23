"""番外图 5 `two_matrices` 的机械核验：`3-5` 与 `3-4-5-7` 楔角相同、取向相同 ⇒ 左表同格；Φ 类不同 ⇒ 右表异格；
左表两列 = TM2006 Fig. 12.1 的 α = 60° / 90°（= framework 定理 5 的非零有效楔）；右表是 34 类全表的真子集节选；
画出来的 chip 落在上述格子里，含内反射的 `3-4-5-7` 在左表用虚线 chip。"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

import fig_two_matrices as fig
from halo_notes.draw.tests.test_figures import run_figure
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import FAMILY_NAMES, phi_class, phi_class_table

SCRIPT = "ex-tape-vs-matrix/code/fig_two_matrices.py"
FRAMEWORK = Path(__file__).resolve().parents[3] / "docs" / "framework.md"


def test_same_wedge_and_attitude_put_both_paths_in_one_left_cell():
    hl = fig.highlight_classes()
    w35, w3457 = hl["3-5"]["wedge"], hl["3-4-5-7"]["wedge"]
    assert abs(w35 - 60.0) < 1e-9 and abs(w3457 - 60.0) < 1e-9   # 由 signature.wedge_angle 算出
    cells = fig.left_cells(hl)
    assert cells["3-5"] == cells["3-4-5-7"] == ("片晶", 60.0)      # 左表：同一 (取向类, 楔角) 格
    assert hl["3-5"]["attitude"] in fig.TM_ROWS


def test_different_phi_class_put_the_paths_in_two_right_rows():
    hl = fig.highlight_classes()
    assert hl["3-5"]["class"] != hl["3-4-5-7"]["class"]            # Φ 类不同
    assert hl["3-5"]["row"].id == "A60-12" and hl["3-4-5-7"]["row"].id == "A60-10"   # 源笔记 §6.2 的编号
    assert hl["3-5"]["row"].folds == (12,) and 6 in hl["3-4-5-7"]["row"].folds       # M = e vs M = R_z(+120°)
    assert np.allclose(fig.M_3457, rg.Rz(120.0), atol=1e-12)
    rows, _ = fig.excerpt_rows()
    ids = [r.id for r in rows]
    cells = fig.right_cells(hl)
    assert cells["3-5"][0] != cells["3-4-5-7"][0] and {cells["3-5"][0], cells["3-4-5-7"][0]} <= set(ids)   # 右表：两行
    assert cells["3-5"][1] == cells["3-4-5-7"][1] == "片晶"


def test_left_wedge_columns_match_framework_theorem_5():
    text = FRAMEWORK.read_text()
    m = re.search(r"有效楔只有 \*\*(.+?)\*\*", text)
    assert m, "framework 定理 5 的「有效楔只有」一句找不到了"
    framework_wedges = sorted(float(x) for x in re.findall(r"(\d+)°", m.group(1)))
    assert sorted(FAMILY_NAMES) == framework_wedges == [0.0, 60.0, 90.0]
    # TM2006 Fig. 12.1（p.131）六棱柱两列 α = 60° / 90°：恰是定理 5 的非零有效楔（0° 楔不偏折，不是晕）
    assert fig.TM_WEDGES == [w for w in framework_wedges if w > 0]


def test_right_excerpt_is_a_proper_subset_of_the_34_classes():
    table = phi_class_table(fig.CRYSTAL)
    transmittable = [r for r in table if r.transmittable]
    assert len(transmittable) == 34
    rows, n = fig.excerpt_rows()
    assert n == 34 and len(rows) < 34
    assert all(r in transmittable for r in rows)                   # 节选行都是全表里的真行
    assert {r.wedge_deg for r in rows} == {0.0, 60.0, 90.0}


def test_figure_renders_and_labels_the_excerpt(monkeypatch):
    cap, ns = run_figure(SCRIPT, monkeypatch)
    assert ns["PATHS"] == {} and cap.paths == []
    src = Path(fig.__file__).read_text()
    assert "示意标签" in src and "非计算输出" in src                # plan-review Minor #3：取向类 / 姿态族的语义边界写进图注


def test_drawn_chips_land_in_the_declared_cells(monkeypatch):
    """白盒：记录两张表实际画出的 chip。左表两枚同一行（y 相同）、3-4-5-7 虚线；右表两枚同一列（x 相同）、不同行、都是实线。"""
    import matplotlib.pyplot as plt
    chips = []
    monkeypatch.setattr(fig, "grid_chip", lambda ax, cx, cy, text, color, dashed=False: chips.append((text, cx, cy, dashed)))
    hl = fig.highlight_classes()
    _, ax = plt.subplots()
    fig.left_table(ax, hl)
    left = {t: (x, y, d) for t, x, y, d in chips}
    chips.clear()
    fig.right_table(ax, hl)
    right = {t: (x, y, d) for t, x, y, d in chips}
    plt.close("all")
    assert set(left) == set(right) == {"3-5", "3-4-5-7"}
    assert left["3-5"][1] == left["3-4-5-7"][1] and abs(left["3-5"][0] - left["3-4-5-7"][0]) < fig.L_CELL_W / 2
    assert left["3-4-5-7"][2] and not left["3-5"][2]
    assert right["3-5"][0] == right["3-4-5-7"][0] and abs(right["3-5"][1] - right["3-4-5-7"][1]) >= fig.R_CELL_H * 0.9
    assert not right["3-5"][2] and not right["3-4-5-7"][2]


@pytest.mark.parametrize("path", [([3, 5], np.eye(3), 3, 5), ([3, 4, 7], None, 3, 7)])
def test_counterexample_other_paths_do_not_share_the_cell(path):
    """反证：换成 60° 楔之外的路（3-4 楔 120°、或 M 不同的 3-4-5-7 对照）时，同格 / 异格判据给出相反结论。"""
    faces, M, a, b = path
    if M is None:
        M = rg.path_matrix(faces)                                  # 3-4-7：一次反射，M = S_{n_4}
    cls = phi_class(fig.CRYSTAL, M, a, b)
    hl = fig.highlight_classes()
    if faces == [3, 5]:
        assert cls == hl["3-5"]["class"]                           # 同一条路必须同类（判据不是恒真的 ≠）
    else:
        assert cls != hl["3-5"]["class"] and cls != hl["3-4-5-7"]["class"]
