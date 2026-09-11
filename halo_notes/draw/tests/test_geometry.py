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
