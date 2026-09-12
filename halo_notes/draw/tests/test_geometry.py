import numpy as np
import pytest

from halo_notes.draw.geometry import HexPrism, rotation


@pytest.fixture
def prism():
    return HexPrism(a=1.0, h=0.8)


def test_face_count_and_numbers(prism):
    assert sorted(f.number for f in prism.faces) == list(range(1, 9))
    assert len(prism.vertices) == 12
    assert len(prism.edges) == 18


def test_normals_are_unit_and_outward(prism):
    body = prism.centroid()
    for f in prism.faces:
        n = prism.normal(f)
        assert np.isclose(np.linalg.norm(n), 1.0)
        assert n @ (prism.centroid(f) - body) > 0


def test_basal_normals(prism):
    assert np.allclose(prism.normal(prism.face(1)), [0, 0, 1])
    assert np.allclose(prism.normal(prism.face(2)), [0, 0, -1])


@pytest.mark.parametrize("i", range(6))
def test_prism_face_azimuth_ccw(prism, i):
    """面 3+i 的外法向方位角 = i*60°（从 +x 起逆时针）。"""
    n = prism.normal(prism.face(3 + i))
    assert np.isclose(n[2], 0.0)
    az = np.rad2deg(np.arctan2(n[1], n[0])) % 360
    assert np.isclose(az, (i * 60) % 360, atol=1e-9)


def test_rotation_about_c_shifts_face_number(prism):
    """绕 c 轴转 60° 后，原面 3 的法向落到面 4 的方位。"""
    rotated = prism.transformed(rotation([0, 0, 1], 60))
    assert np.allclose(rotated.normal(rotated.face(3)), prism.normal(prism.face(4)))
    assert np.allclose(rotated.normal(rotated.face(8)), prism.normal(prism.face(3)))


def test_transformed_keeps_type_and_params(prism):
    r = prism.transformed(rotation([1, 0, 0], 30), translation=[1, 2, 3])
    assert isinstance(r, HexPrism)
    assert (r.a, r.h) == (prism.a, prism.h)
    assert np.allclose(r.centroid(), [1, 2, 3])


def test_intersect_ray_through_prism(prism):
    hit = prism.intersect_ray([-5, 0, 0], [1, 0, 0])
    assert hit is not None
    t_in, f_in, t_out, f_out = hit
    assert f_in.number == 6 and f_out.number == 3  # 从 -x 侧进（面 6），+x 侧出（面 3）
    assert np.isclose(t_in, 5 - np.sqrt(3) / 2) and np.isclose(t_out, 5 + np.sqrt(3) / 2)


def test_intersect_ray_miss(prism):
    assert prism.intersect_ray([-5, 0, 5], [1, 0, 0]) is None


def test_contains(prism):
    assert prism.contains([0, 0, 0])
    assert not prism.contains([0, 0, 1])


def test_rotation_between():
    from halo_notes.draw.geometry import rotation_between
    r = rotation_between([0, 0, 1], [1, 1, 0])
    assert np.allclose(r @ [0, 0, 1], [1, 1, 0] / np.sqrt(2))
    assert np.allclose(rotation_between([0, 0, 1], [0, 0, 1]), np.eye(3))
    r180 = rotation_between([0, 0, 1], [0, 0, -1])
    assert np.allclose(r180 @ [0, 0, 1], [0, 0, -1])
    assert np.allclose(r180 @ r180.T, np.eye(3))


# ---- 镜像（光路展开的幽灵晶体） -------------------------------------------

def test_mirror_reflects_vertices_about_face_plane(prism):
    face = prism.face(3)
    n, p0 = prism.normal(face), prism.face_vertices(face)[0]
    m = prism.mirrored(face)
    for v, mv in zip(prism.vertices, m.vertices):
        assert np.allclose(mv, v - 2 * ((v - p0) @ n) * n)  # 逐点对照镜像公式
    # 面 3 的法向沿 +x、平面 x = √3/2：镜像后顶点 x 坐标关于该平面对称
    assert np.allclose(m.vertices[:, 0], np.sqrt(3) - prism.vertices[:, 0])
    assert np.allclose(m.vertices[:, 1:], prism.vertices[:, 1:])


def test_mirror_keeps_outward_normals(prism):
    """镜像翻转手性；若不反转顶点环，所有法向都会朝内——这是本方法的核心正确性门槛。"""
    for number in (1, 3, 6):
        m = prism.mirrored(prism.face(number))
        body = m.centroid()
        for f in m.faces:
            n = m.normal(f)
            assert np.isclose(np.linalg.norm(n), 1.0)
            assert n @ (m.centroid(f) - body) > 0


def test_mirror_preserves_face_numbers_and_type(prism):
    m = prism.mirrored(prism.face(5))
    assert {f.number for f in m.faces} == {f.number for f in prism.faces}
    assert isinstance(m, HexPrism) and (m.a, m.h) == (prism.a, prism.h)
    assert len(m.edges) == 18


def test_mirror_is_involution(prism):
    m = prism.mirrored(prism.face(4))
    back = m.mirrored(m.face(4))  # 用镜像晶体上同编号的面（平面位置相同）再镜像一次
    assert np.allclose(back.vertices, prism.vertices)
    assert all(bf.vertex_ids == f.vertex_ids for bf, f in zip(back.faces, prism.faces))


def test_mirror_shares_the_mirror_plane(prism):
    """镜像面本身留在原位：镜像晶体上同编号面的顶点集合与原面重合，法向反向。"""
    face = prism.face(3)
    m = prism.mirrored(face)
    orig = {tuple(np.round(p, 9)) for p in prism.face_vertices(face)}
    mirr = {tuple(np.round(p, 9)) for p in m.face_vertices(m.face(3))}
    assert orig == mirr
    assert np.allclose(m.normal(m.face(3)), -prism.normal(face))


def test_mirror_face_intersect_ray_still_works(prism):
    m = prism.mirrored(prism.face(3))  # 体心移到 x = √3
    hit = m.intersect_ray([-5, 0, 0], [1, 0, 0])
    assert hit is not None
    t_in, f_in, t_out, f_out = hit
    assert f_in.number == 3 and f_out.number == 6  # 镜像后 3 在 -x 侧、6 在 +x 侧
    assert np.isclose(t_in, 5 + np.sqrt(3) / 2) and np.isclose(t_out, 5 + 3 * np.sqrt(3) / 2)
    assert m.contains([np.sqrt(3), 0, 0]) and not m.contains([0, 0, 0])


def test_face_margin_and_distance():
    c = HexPrism(1.0, 1.0)
    top = c.face(1)
    assert np.isclose(c.face_distance(top, [0, 0, 0.5]), 0.0)
    assert np.isclose(c.face_distance(top, [0, 0, 0.7]), 0.2)
    # 质心到最近棱边的距离 = 内切圆半径 √3/2
    assert np.isclose(c.face_margin(top, [0, 0, 0.5]), np.sqrt(3) / 2)
    assert np.isclose(c.face_margin(top, [np.sqrt(3) / 2, 0, 0.5]), 0.0)   # 恰在棱边上
    assert c.face_margin(top, [1.2, 0, 0.5]) < 0                            # 面外
    # 侧面 3（法向 +x）：上下棱边由 z 决定
    side = c.face(3)
    assert np.isclose(c.face_margin(side, [np.sqrt(3) / 2, 0, 0.0]), 0.5)
    assert np.isclose(c.face_margin(side, [np.sqrt(3) / 2, 0, 0.4]), 0.1)


def test_intersect_ray_vectorised_matches_reference_cases():
    c = HexPrism(1.0, 1.0)
    hit = c.intersect_ray([-5, 0, 0], [1, 0, 0])
    assert hit is not None
    t_in, f_in, t_out, f_out = hit
    assert (f_in.number, f_out.number) == (6, 3)
    assert np.isclose(t_in, 5 - np.sqrt(3) / 2) and np.isclose(t_out, 5 + np.sqrt(3) / 2)
    assert c.intersect_ray([-5, 0, 5], [1, 0, 0]) is None        # 与顶面平行且在外侧
    inside = c.intersect_ray([0, 0, 0], [0, 0, 1])
    assert inside is not None and inside[0] < 0 and inside[3].number == 1
