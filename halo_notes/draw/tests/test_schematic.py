import numpy as np
import pytest

from halo_notes.draw.geometry import unit
from halo_notes.draw.raypath import N_ICE, EventKind, RayPath2D, face_sequence, refract, verify_path
from halo_notes.draw.schematic import (ENTRY_FACE, EXIT_FACE, jagged_polyline, split_tree, two_face_medium,
                                       wavy_polyline, wedge_angle, wedge_apex)


@pytest.fixture
def plate():
    """6.2 的平板：上界面略向右上倾、下界面略向右下倾（两界面不平行）。"""
    return two_face_medium(entry=([-2.0, 1.0], [2.0, 1.3]), exit=([2.0, -1.3], [-2.0, -1.0]))


def test_two_face_medium_is_ccw_with_numbered_interfaces(plate):
    assert sorted(f.number for f in plate.faces) == [1, 2, 3, 4]
    assert plate.normal(plate.face(ENTRY_FACE))[1] > 0      # 上界面外法向朝上
    assert plate.normal(plate.face(EXIT_FACE))[1] < 0       # 下界面外法向朝下
    for f in plate.faces:
        assert plate.normal(f) @ (plate.midpoint(f) - plate.centroid()) > 0
    # 顶点给成顺时针也能自动整理，且编号语义不变
    cw = two_face_medium(entry=([2.0, 1.3], [-2.0, 1.0]), exit=([-2.0, -1.0], [2.0, -1.3]))
    assert cw.normal(cw.face(ENTRY_FACE))[1] > 0


def test_wedge_angle_and_apex():
    wedge = two_face_medium(entry=([-1.0, 0.0], [-3.0, -4.0]), exit=([3.0, -4.0], [1.0, 0.0]))
    theta = wedge_angle(wedge)
    expected = 2 * np.degrees(np.arctan2(2.0, 4.0))   # 两条边各偏离竖直 atan(2/4)
    assert np.isclose(theta, expected)
    apex = wedge_apex(wedge)
    assert np.allclose(apex, [0.0, 2.0])
    assert np.isclose(wedge_angle(two_face_medium(entry=([-1, 1], [1, 1]), exit=([1, -1], [-1, -1]))), 0.0)
    with pytest.raises(ValueError):
        wedge_apex(two_face_medium(entry=([-1, 1], [1, 1]), exit=([1, -1], [-1, -1])))


def test_split_tree_obeys_reflection_and_snell(plate):
    """6.2 分支角度单测：反射角 == 入射角、折射满足 Snell（n=1.31），不是手画的角度。"""
    d = unit([1.0, -1.2])
    tree = split_tree(plate, np.array([-1.0, 1.0]) - d * 3, d, inside_length=1.0)
    for branch in tree.branches():
        assert isinstance(branch, RayPath2D)
        verify_path(branch, lambda ev: plate, n_ice=N_ICE, tol=1e-9, min_margin=1e-6)
    assert face_sequence(tree.transmitted) == [ENTRY_FACE, EXIT_FACE]
    assert face_sequence(tree.reflected_outside) == [ENTRY_FACE]
    assert face_sequence(tree.reflected_inside) == [ENTRY_FACE, EXIT_FACE]
    assert [ev.kind for ev in tree.reflected_inside.events] == [EventKind.REFRACT_IN, EventKind.REFLECT_INTERNAL]

    n1 = plate.normal(plate.face(ENTRY_FACE))
    d_in = unit(tree.transmitted.points[1] - tree.transmitted.points[0])
    d_ref = unit(tree.reflected_outside.points[2] - tree.reflected_outside.points[1])
    assert np.isclose(-(n1 @ d_in), n1 @ d_ref)                       # 反射角 == 入射角
    d_t = unit(tree.transmitted.points[2] - tree.transmitted.points[1])
    assert np.allclose(d_t, refract(d_in, n1, 1.0, N_ICE))            # Snell
    sin_i, sin_t = np.sqrt(1 - (n1 @ d_in) ** 2), np.sqrt(1 - (n1 @ d_t) ** 2)
    assert np.isclose(sin_i, N_ICE * sin_t)
    # 内反射支从穿透支的入射点出发、沿同一内部方向（同一条光线的分支）
    assert np.allclose(tree.reflected_inside.points[:2], tree.transmitted.points[1:3])
    n2 = plate.normal(plate.face(EXIT_FACE))
    d_back = unit(tree.reflected_inside.points[2] - tree.reflected_inside.points[1])
    assert np.isclose(n2 @ d_t, -(n2 @ d_back))


def test_split_tree_rejects_ray_missing_interface_1(plate):
    with pytest.raises(ValueError):
        split_tree(plate, [0.0, -5.0], [0.0, 1.0])   # 从下界面进


def test_decorative_polylines_keep_endpoints_and_are_deterministic():
    a, b = np.array([0.0, 0.0]), np.array([4.0, 1.0])
    j1, j2 = jagged_polyline(a, b, seed=3), jagged_polyline(a, b, seed=3)
    assert np.allclose(j1, j2)
    assert np.allclose(j1[0], a) and np.allclose(j1[-1], b)
    assert not np.allclose(j1, jagged_polyline(a, b, seed=4))
    w = wavy_polyline(a, b)
    assert np.allclose(w[0], a) and np.allclose(w[-1], b)
    # 偏移垂直于 a→b
    d = unit(b - a)
    along = (w - a) @ d
    assert np.all(np.diff(along) > 0)
