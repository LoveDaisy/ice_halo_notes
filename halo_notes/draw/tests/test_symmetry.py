import numpy as np
import pytest

from halo_notes.draw.geometry2d import CrossSection
from halo_notes.draw.symmetry import FlipAxis, face_permutation, flip, rotate


@pytest.fixture
def section():
    return CrossSection(1.0)


def _wrap(k: int) -> int:
    """侧面编号 3–8 循环。"""
    return (k - 3) % 6 + 3


@pytest.mark.parametrize("k", range(6))
def test_rotate_moves_edge_j_to_where_j_plus_k_was(section, k):
    """rotate(k) 后边 j 的法向 == 原边 j+k 的法向（编号跟着晶体转到新位置）。"""
    turned = rotate(section, k)
    for j in range(3, 9):
        assert np.allclose(turned.normal(turned.face(j)),
                           section.normal(section.face(_wrap(j + k))), atol=1e-12)
    assert np.allclose(turned.centroid(), section.centroid(), atol=1e-12)
    # 字形变换：旋转矩阵，行列式 +1（保持手性，只是转动）
    assert np.isclose(np.linalg.det(turned.frame), 1.0)
    assert np.allclose(turned.frame @ [1, 0], [np.cos(np.deg2rad(60 * k)), np.sin(np.deg2rad(60 * k))])


def test_rotate_permutation_is_shift_by_k(section):
    perm = face_permutation(section, rotate(section, 1))
    # 原来编号 k 的位置现在站着 k-1（k+1 转到 k+2 的位置 ⇔ 站到 k 位置上的是 k-1）
    assert perm == {k: _wrap(k - 1) for k in range(3, 9)}


@pytest.mark.parametrize("k", [3, 4, 5])
def test_flip_about_face_axis_keeps_that_edge(section, k):
    flipped = flip(section, FlipAxis.face(k))
    assert np.allclose(flipped.normal(flipped.face(k)), section.normal(section.face(k)), atol=1e-12)
    assert np.allclose(flipped.midpoint(flipped.face(k)), section.midpoint(section.face(k)), atol=1e-12)
    # 对面也不动；其余成对互换
    opposite = _wrap(k + 3)
    assert np.allclose(flipped.normal(flipped.face(opposite)), section.normal(section.face(opposite)))
    perm = face_permutation(section, flipped)
    assert perm[k] == k and perm[opposite] == opposite
    assert perm[_wrap(k + 1)] == _wrap(k - 1) and perm[_wrap(k - 1)] == _wrap(k + 1)
    assert np.isclose(np.linalg.det(flipped.frame), -1.0)   # 字形镜像


@pytest.mark.parametrize("k", [3, 4, 5])
def test_flip_about_vertex_axis_keeps_that_vertex(section, k):
    j = _wrap(k + 1)
    flipped = flip(section, FlipAxis.vertex(k, j))
    v = section.vertex_between(k, j)
    # 该顶点仍是两条边的公共顶点且位置不变；两条边互换
    assert np.allclose(flipped.vertex_between(k, j), v, atol=1e-12)
    perm = face_permutation(section, flipped)
    assert perm[k] == j and perm[j] == k
    assert np.isclose(np.linalg.det(flipped.frame), -1.0)


def test_flip_is_involution(section):
    axis = FlipAxis.vertex(3, 4)
    back = flip(flip(section, axis), axis)
    assert np.allclose(back.vertices, section.vertices, atol=1e-12)
    assert np.allclose(back.frame, np.eye(2))


def test_figure_1_2_consistency_chain(section):
    """旧图 1.2 的自洽检查：翻转轴过 3|4 与 6|7 之间的顶点（$F^d_{3,4}$）。
    该翻转把面 3↔4、5↔8、6↔7 互换：同一条光线，晶体翻转后原本读作 4-6 的光路读作 3-7；
    而绕 c 轴转 60° 把 3-5 变成 4-6。所以 3-5 ⟺ 4-6 ⟺ 3-7。"""
    perm_flip = face_permutation(section, flip(section, FlipAxis.vertex(3, 4)))
    assert perm_flip == {3: 4, 4: 3, 5: 8, 8: 5, 6: 7, 7: 6}
    # 光路 "4-6"：光线穿过原来 4、6 所在的位置；翻转后站在那两个位置上的编号
    assert [perm_flip[4], perm_flip[6]] == [3, 7]
    perm_rot = face_permutation(section, rotate(section, 1))
    # 光线不动、晶体左转 60°：原来 4、6 位置上现在站着 3、5，即 3-5 光路转过来读作 4-6
    assert [perm_rot[4], perm_rot[6]] == [3, 5]


def test_axis_labels_and_direction(section):
    assert FlipAxis.face(3).label == "$F^f_{3}$"
    assert FlipAxis.vertex(3, 4).label == "$F^d_{3,4}$"
    assert np.allclose(FlipAxis.face(3).direction(section), [1, 0])
    d = FlipAxis.vertex(3, 4).direction(section)
    assert np.isclose(np.degrees(np.arctan2(d[1], d[0])), 30.0)
