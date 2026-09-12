import numpy as np
import pytest

from halo_notes.draw.geometry2d import CrossSection
from halo_notes.draw.raypath import (N_ICE, EventKind, RayPath, RayPath2D, face_sequence, trace,
                                     verify_path)
from halo_notes.draw.raypath2d import _incident_directions_2d, solve_raypath_2d, unfold_2d
from halo_notes.draw.unfold import Corridor


@pytest.fixture
def section():
    return CrossSection(1.0)


def test_raypath2d_shape_and_type():
    p = RayPath2D([[0, 0], [1, 0], [2, 1]], ("incident", "internal"))
    assert p.points.shape == (3, 2) and p.DIM == 2
    assert isinstance(p.transformed(np.eye(2), [1, 1]), RayPath2D)
    with pytest.raises(ValueError):
        RayPath2D([[0, 0], [1, 0]], ())
    # 3D 类保持 (N,3)
    assert RayPath([[0, 0, 0], [1, 0, 0]], ("incident",)).points.shape == (2, 3)


def test_trace_on_section_returns_raypath2d(section):
    path = trace(section, [-4, 0.1], [1, 0], ["refract", "refract"])
    assert isinstance(path, RayPath2D)
    assert face_sequence(path) == [6, 3]
    verify_path(path, lambda ev: section)


def test_incident_directions_are_unit_and_toward_edge():
    n = np.array([1.0, 0.0])
    dirs = _incident_directions_2d(n, np.array([-60.0, 0.0, 60.0]))
    assert np.allclose(np.linalg.norm(dirs, axis=1), 1.0)
    assert np.all(dirs @ n < 0)
    assert np.allclose(dirs[1], [-1, 0])
    assert dirs[2][1] > 0 and dirs[0][1] < 0   # 正负入射角落在法向两侧


@pytest.mark.parametrize("faces", [[3, 5], [4, 6], [3, 7], [5, 3, 7, 5], [3]])
def test_solve_raypath_2d_realises_declared_sequence(section, faces):
    """issue 验收：[3,5] / [4,6] / [3,7]（1.2）与 [5,3,7,5]（3.1，截面转 30° 后）反解成功，
    trace 回放的面序列相等且通过 Snell / 反射定律白盒复核（偏差 < 1e-9）。"""
    body = section.rotated(30) if faces == [5, 3, 7, 5] else section
    path = solve_raypath_2d(body, faces)
    assert isinstance(path, RayPath2D)
    assert face_sequence(path) == faces
    verify_path(path, lambda ev: body, tol=1e-9, min_margin=1e-6)
    kinds = [ev.kind for ev in path.events]
    if len(faces) == 1:
        assert kinds == [EventKind.REFLECT_EXTERNAL]
    else:
        assert kinds[0] is EventKind.REFRACT_IN and kinds[-1] is EventKind.REFRACT_OUT
        assert all(k is EventKind.REFLECT_INTERNAL for k in kinds[1:-1])


def test_solve_raypath_2d_prefers_given_direction(section):
    d = np.array([-1.0, 0.3])
    path = solve_raypath_2d(section, [3, 6], prefer_direction=d)
    assert np.allclose(path.points[1] - path.points[0], d / np.linalg.norm(d) * 1.6)


def test_solve_raypath_2d_rejects_impossible_sequence(section):
    with pytest.raises(ValueError):
        solve_raypath_2d(section, [3, 3])


def test_solve_raypath_2d_rejects_3d_body():
    from halo_notes.draw.geometry import HexPrism
    with pytest.raises(TypeError):
        solve_raypath_2d(HexPrism(1.0, 1.0), [3, 5])


def test_snell_holds_at_entry_with_n_ice(section):
    path = solve_raypath_2d(section, [3, 5])
    ev = path.events[0]
    n = section.normal(section.face(ev.face_number))
    d_in = path.points[1] - path.points[0]
    d_out = path.points[2] - path.points[1]
    d_in, d_out = d_in / np.linalg.norm(d_in), d_out / np.linalg.norm(d_out)
    sin_i = np.sqrt(1 - (n @ d_in) ** 2)
    sin_t = np.sqrt(1 - (n @ d_out) ** 2)
    assert np.isclose(sin_i, N_ICE * sin_t, atol=1e-12)


def test_unfold_2d_cascades_and_mirrors_frame(section):
    body = section.rotated(30)
    path = solve_raypath_2d(body, [5, 3, 7, 5])
    ghosts = unfold_2d(body, path)
    assert len(ghosts) == 2
    # 第一个幽灵关于反射边 3 镜像：该边位置不变、法向反向
    assert np.allclose(ghosts[0].midpoint(ghosts[0].face(3)), body.midpoint(body.face(3)))
    assert np.allclose(ghosts[0].normal(ghosts[0].face(3)), -body.normal(body.face(3)))
    # 第二个幽灵是对第一个幽灵（不是原截面）关于其边 7 的镜像
    assert np.allclose(ghosts[1].midpoint(ghosts[1].face(7)), ghosts[0].midpoint(ghosts[0].face(7)))
    assert np.isclose(np.linalg.det(ghosts[0].frame), -1.0)
    assert np.isclose(np.linalg.det(ghosts[1].frame), 1.0)
    # 展开直线穿过幽灵串，与 3D Corridor 同一份实现
    corridor = Corridor(body, path)
    assert face_sequence(corridor.straight) == [5, 3, 7, 5]
    assert isinstance(corridor.straight, RayPath2D)


def test_unfold_2d_rejects_3d(section):
    from halo_notes.draw.geometry import HexPrism
    with pytest.raises(TypeError):
        unfold_2d(HexPrism(1.0, 1.0), solve_raypath_2d(section, [3, 5]))
