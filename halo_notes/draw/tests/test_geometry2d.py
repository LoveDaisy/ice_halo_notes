import numpy as np
import pytest

from halo_notes.draw.geometry import Face, HexPrism, rotation
from halo_notes.draw.geometry2d import CrossSection, Polygon2D, reflection2d, rotation2d


@pytest.fixture
def section():
    return CrossSection(1.0)


def test_edge_numbers_are_prism_faces(section):
    assert sorted(f.number for f in section.faces) == [3, 4, 5, 6, 7, 8]
    assert section.vertices.shape == (6, 2)
    assert len(section.edges) == 6


@pytest.mark.parametrize("number", [3, 4, 5, 6, 7, 8])
def test_edge_normal_equals_prism_side_normal_xy(section, number):
    """截面边 k 的外法向 == HexPrism 侧面 k 外法向的 xy 分量（方向重合，不只是方位角相等）。"""
    prism = HexPrism(1.0, 1.0)
    n3 = prism.normal(prism.face(number))
    n2 = section.normal(section.face(number))
    assert np.isclose(np.linalg.norm(n2), 1.0)
    assert np.allclose(n2, n3[:2], atol=1e-12)
    # 外向：法向与"中心 → 边中点"同向
    assert n2 @ (section.midpoint(section.face(number)) - section.centroid()) > 0


@pytest.mark.parametrize("number, lo, hi", [
    (3, -10, 10),      # 右
    (4, 50, 70),       # 右上
    (5, 110, 130),     # 左上
    (6, 170, 190),     # 左
    (7, 230, 250),     # 左下
    (8, 290, 310),     # 右下
])
def test_calibration_against_old_figure_1_2(section, number, lo, hi):
    """旧图 1.2 校准点：从 +c 看（x 右 y 上）3 右、4 右上、5 左上、6 左、7 左下、8 右下，逆时针。
    视向取反时六个编号整体镜像，这里会红。"""
    m = section.midpoint(section.face(number)) - section.centroid()
    az = np.rad2deg(np.arctan2(m[1], m[0])) % 360
    assert lo <= az <= hi


def test_edges_are_counterclockwise(section):
    """相邻编号的边中点方位角递增 60°（逆时针）。"""
    def az(number):
        m = section.midpoint(section.face(number))
        return np.rad2deg(np.arctan2(m[1], m[0])) % 360
    for k in range(3, 8):
        assert np.isclose((az(k + 1) - az(k)) % 360, 60.0, atol=1e-9)


def test_derivation_follows_prism_pose():
    """编号是从棱柱几何抽出来的：棱柱绕 c 轴转 60° 后，截面上边 3 落到原边 4 的位置。"""
    turned = CrossSection(prism=HexPrism(1.0, 1.0).transformed(rotation([0, 0, 1], 60)))
    base = CrossSection(1.0)
    assert np.allclose(turned.normal(turned.face(3)), base.normal(base.face(4)))


def test_intersect_ray_and_contains(section):
    hit = section.intersect_ray([-5, 0], [1, 0])
    assert hit is not None
    t_in, f_in, t_out, f_out = hit
    assert f_in.number == 6 and f_out.number == 3
    assert np.isclose(t_in, 5 - np.sqrt(3) / 2) and np.isclose(t_out, 5 + np.sqrt(3) / 2)
    assert section.intersect_ray([-5, 3], [1, 0]) is None
    assert section.contains([0, 0]) and not section.contains([2, 0])


def test_edge_margin_and_distance(section):
    e3 = section.face(3)
    mid = section.midpoint(e3)
    assert np.isclose(section.face_distance(e3, mid), 0.0)
    assert np.isclose(section.face_margin(e3, mid), 0.5)          # 边长 1，中点到两端 0.5
    assert section.face_margin(e3, mid + [0, 0.7]) < 0             # 越过端点
    assert np.isclose(section.face_distance(e3, [1.5, 0]), 1.5 - np.sqrt(3) / 2)


def test_square_polygon_margin_and_normals():
    square = Polygon2D([[0, 0], [1, 0], [1, 1], [0, 1]],
                       [Face(k, (k - 1, k % 4)) for k in range(1, 5)])
    assert np.allclose(square.normal(square.face(1)), [0, -1])
    assert np.allclose(square.normal(square.face(2)), [1, 0])
    assert np.isclose(square.face_margin(square.face(1), [0.25, 0]), 0.25)
    assert square.contains([0.5, 0.5])


def test_transformed_keeps_type_and_frame(section):
    r = rotation2d(60)
    turned = section.transformed(r, translation=[1, 2])
    assert isinstance(turned, CrossSection) and turned.a == section.a
    assert np.allclose(turned.centroid(), [1, 2])
    assert np.allclose(turned.frame, r)
    assert np.allclose(turned.normal(turned.face(3)), section.normal(section.face(4)))


def test_rotated_about_own_centre(section):
    moved = section.transformed(translation=[3, 0]).rotated(90)
    assert np.allclose(moved.centroid(), [3, 0])
    assert np.isclose(np.linalg.det(moved.frame), 1.0)


def test_mirrored_flips_frame_and_keeps_outward_normals(section):
    ghost = section.mirrored(section.face(3))
    assert np.isclose(np.linalg.det(ghost.frame), -1.0)
    assert np.allclose(ghost.centroid(), [np.sqrt(3), 0])
    for f in ghost.faces:
        assert ghost.normal(f) @ (ghost.midpoint(f) - ghost.centroid()) > 0
    # 镜像面在幽灵上法向反向、位置不变
    assert np.allclose(ghost.normal(ghost.face(3)), -section.normal(section.face(3)))
    assert np.allclose(ghost.midpoint(ghost.face(3)), section.midpoint(section.face(3)))


def test_reflection2d_is_involution_with_negative_det():
    m = reflection2d([1, 1])
    assert np.isclose(np.linalg.det(m), -1.0)
    assert np.allclose(m @ m, np.eye(2))
    assert np.allclose(m @ [1, 0], [0, 1])


def test_transformed_with_reflection_keeps_outward_normals(section):
    """行列式 −1 的变换会把顶点环翻成顺时针：各边顶点顺序须同步反转，否则六个外法向整体朝内。"""
    m = reflection2d([1, 0])
    flipped = section.transformed(m)
    for f in flipped.faces:
        assert flipped.normal(f) @ (flipped.midpoint(f) - flipped.centroid()) > 0
    assert np.allclose(flipped.normal(flipped.face(4)), section.normal(section.face(8)))
    assert np.isclose(np.linalg.det(flipped.frame), -1.0)
