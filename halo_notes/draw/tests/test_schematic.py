import numpy as np
import pytest

from halo_notes.draw.geometry import unit
from halo_notes.draw.geometry2d import perp2d, reflection2d
from halo_notes.draw.raypath import N_ICE, EventKind, RayPath2D, face_sequence, refract, verify_path
from halo_notes.draw.schematic import (ENTRY_FACE, EXIT_FACE, concentric_projection, jagged_polyline, split_tree,
                                       two_face_medium, wavy_polyline, wedge_angle, wedge_apex)


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


# ---- concentric_projection：同心圆作图 ---------------------------------------------------------

def _cross2(a, b) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


@pytest.mark.parametrize("sun_deg, normal_deg", [(139.1, 0.0), (200.0, 0.0), (75.0, 120.0), (10.0, -35.0)])
def test_concentric_projection_points_are_collinear_along_the_normal(sun_deg, normal_deg):
    s = np.array([np.cos(np.deg2rad(sun_deg)), np.sin(np.deg2rad(sun_deg))])
    nrm = np.array([np.cos(np.deg2rad(normal_deg)), np.sin(np.deg2rad(normal_deg))])
    p = concentric_projection(s, nrm, N_ICE)
    assert np.isclose(np.linalg.norm(p.incident), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(p.reflected), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(p.refracted), N_ICE, atol=1e-12)
    # S、S'、R 三点共线，且直线平行于界面法向
    for q in (p.reflected, p.refracted):
        assert abs(_cross2(q - p.incident, p.normal)) < 1e-12
    # S' 是 S 关于界面（过原点、方向 ⟂ 法向）的镜像：reflection2d 矩阵复算
    assert np.allclose(reflection2d(perp2d(nrm)) @ s, p.reflected, atol=1e-12)
    # Snell：相对法向量的入射角 / 折射角满足 1·sinθ1 = n·sinθ2；折射光的法向分量与入射同号（穿过界面）
    sin1 = abs(_cross2(unit(p.incident), p.normal))
    sin2 = abs(_cross2(unit(p.refracted), p.normal))
    assert abs(sin1 - N_ICE * sin2) < 1e-12
    assert np.sign(p.refracted @ p.normal) == np.sign(p.incident @ p.normal)


def test_concentric_projection_agrees_with_vector_refract_and_is_reversible():
    """与 raypath.refract（向量形式 Snell）同一个结果；从内圆投回外圆恢复原光点（两次折射的可逆性）。"""
    d = unit([-0.8, 0.35])
    n_out = np.array([1.0, 0.0])                          # 面 3 外法向；光从外侧射入（d·n < 0）
    p = concentric_projection(d, n_out, N_ICE)
    assert np.allclose(unit(p.refracted), refract(d, n_out, 1.0, N_ICE), atol=1e-12)
    back = concentric_projection(p.refracted, n_out, 1.0)
    assert np.allclose(back.refracted, d, atol=1e-12)
    # 三维同样成立（切向分量守恒与维数无关）
    p3 = concentric_projection(unit([-0.7, 0.3, 0.2]), [1.0, 0.0, 0.0], N_ICE)
    assert np.isclose(np.linalg.norm(p3.refracted), N_ICE)
    assert np.allclose(np.cross(p3.refracted - p3.incident, p3.normal), 0.0, atol=1e-12)


def test_concentric_projection_counterexamples_fail():
    """反证：半径传成 1/n 或取错根，Snell / 共线断言就应失败；内圆 → 外圆越过临界角时抛全反射。"""
    s = np.array([np.cos(np.deg2rad(139.1)), np.sin(np.deg2rad(139.1))])
    nrm = np.array([1.0, 0.0])
    wrong = concentric_projection(s, nrm, 1.0 / N_ICE)       # 1/n 半径：切向分量 0.65 < 0.76，仍有解但不是冰
    sin1 = abs(_cross2(unit(s), nrm))
    assert abs(sin1 - N_ICE * abs(_cross2(unit(wrong.refracted), nrm))) > 1e-3
    flipped = concentric_projection(s, -nrm, N_ICE)         # 法向取反：根按新法向重选，仍是同一个折射光点
    assert np.allclose(flipped.refracted, concentric_projection(s, nrm, N_ICE).refracted, atol=1e-12)
    grazing_inside = N_ICE * unit([-0.2, 1.0])               # 冰内几乎贴着界面走：投回半径 1 无交点
    with pytest.raises(ValueError, match="total internal reflection"):
        concentric_projection(grazing_inside, nrm, 1.0)
