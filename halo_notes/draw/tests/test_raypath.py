import numpy as np
import pytest

from halo_notes.draw.geometry import HexPrism
from halo_notes.draw.projection import Camera
from halo_notes.draw.raypath import (Cone, EventKind, RayPath, SegmentKind, convex_hull_2d,
                                     reflect, refract, trace)


def test_reflect_and_refract_basic():
    n = np.array([0, 0, 1.0])
    d = np.array([np.sin(0.5), 0, -np.cos(0.5)])
    r = reflect(d, n)
    assert np.allclose(r, [np.sin(0.5), 0, np.cos(0.5)])
    t = refract(d, n, 1.0, 1.31)
    assert np.isclose(np.linalg.norm(t), 1.0)
    assert np.isclose(np.sin(np.arccos(-t[2])) * 1.31, np.sin(0.5))  # Snell


def test_refract_raises_on_tir():
    with pytest.raises(ValueError):
        refract(np.array([np.sin(1.2), 0, -np.cos(1.2)]), np.array([0, 0, 1.0]), 1.31, 1.0)


def test_trace_refract_through():
    c = HexPrism(1, 1)
    p = trace(c, [-5, 0.1, 0.2], [1, 0, 0], ["refract", "refract"], tail=1, head=1)
    assert p.kinds == (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.EXIT)
    assert [e.kind for e in p.events] == [EventKind.REFRACT_IN, EventKind.REFRACT_OUT]
    assert [e.face_number for e in p.events] == [6, 3]
    # 平行平面对射：出射方向平行于入射方向
    d_in = p.points[1] - p.points[0]
    d_out = p.points[-1] - p.points[-2]
    assert np.allclose(np.cross(d_in, d_out), 0, atol=1e-9)
    assert np.isclose(np.linalg.norm(d_out), 1)  # head 长度


def test_trace_external_reflection():
    c = HexPrism(1, 1)
    p = trace(c, [-0.8, 0.1, 5], [0.2, 0, -1], ["reflect"])
    assert p.kinds == (SegmentKind.INCIDENT, SegmentKind.EXIT)
    assert p.events[0].kind is EventKind.REFLECT_EXTERNAL and p.events[0].face_number == 1
    assert p.points[-1][2] > p.points[1][2]  # 反射后向上


def test_trace_internal_reflection_stays_inside():
    c = HexPrism(1, 1)
    p = trace(c, [-5, 0.0, -2.0], [1, 0, 0.5], ["refract", "reflect", "refract"])
    assert [(e.face_number, e.kind) for e in p.events] == [
        (6, EventKind.REFRACT_IN), (1, EventKind.REFLECT_INTERNAL), (3, EventKind.REFRACT_OUT)]
    for i in (1, 2, 3):
        assert c.contains(p.points[i], eps=1e-6)


def test_trace_refuses_impossible_refraction():
    """要求在本应全反射的面上折射 → 报错而不是画出非物理光路。"""
    c = HexPrism(1, 1)
    with pytest.raises(ValueError, match="total internal reflection"):
        trace(c, [-5, 0.0, -2.2], [1, 0, 0.5], ["refract", "reflect", "refract"])


def test_trace_errors():
    c = HexPrism(1, 1)
    with pytest.raises(ValueError):
        trace(c, [-5, 0, 5], [1, 0, 0], ["refract"])  # 不相交
    with pytest.raises(ValueError):
        trace(c, [-5, 0, 0], [1, 0, 0], ["refract"])  # 序列在体内结束
    with pytest.raises(ValueError):
        trace(c, [-5, 0, 0], [1, 0, 0], [])


def test_raypath_length_check():
    with pytest.raises(ValueError):
        RayPath(np.zeros((3, 3)), (SegmentKind.INCIDENT,))


def test_cone_ring_geometry():
    cone = Cone.along([0, 0, 0], [1, 0, 0], length=2.0, radius=0.5, rings=4, samples=36)
    assert len(cone.ring_points(1.0)) == 37
    rim = cone.ring_points(1.0)
    assert np.allclose(rim[:, 0], 2.0)
    assert np.allclose(np.linalg.norm(rim[:, 1:], axis=1), 0.5)
    assert np.allclose(np.linalg.norm(cone.ring_points(0.5)[:, 1:], axis=1), 0.25)
    n = cone.surface_normals(1.0)
    assert np.allclose(np.linalg.norm(n, axis=1), 1.0)
    assert np.all(n[:, 0] < 0)  # 锥面外法向向顶点一侧倾斜


def test_cone_wireframe_changes_with_camera():
    """锥体是真 3D 投影：换视角后投影点集不同（不是固定贴图）。"""
    cone = Cone.along([0, 0, 0], [1, 0, 0], length=1.0, radius=0.3, rings=3)
    a = np.vstack(cone.wireframe(Camera(azimuth=90, elevation=0)))
    b = np.vstack(cone.wireframe(Camera(azimuth=60, elevation=30)))
    assert a.shape != b.shape or not np.allclose(a, b)


def test_cone_wireframe_ring_count_side_view():
    """侧视：每圈纬线只有朝向观察者的半弧可见，加两条轮廓母线。"""
    cone = Cone.along([0, 0, 0], [1, 0, 0], length=1.0, radius=0.3, rings=3)
    pieces = cone.wireframe(Camera(azimuth=90, elevation=0))
    assert len(pieces) == 2 + 3


def test_cone_base_facing_viewer_full_rim():
    cone = Cone.along([0, 0, 0], [1, 0, 0], length=1.0, radius=0.3, rings=2)
    pieces = cone.wireframe(Camera(azimuth=0, elevation=0))  # 从底面正对着看
    lengths = sorted(len(p) for p in pieces)
    assert lengths[-1] == cone.samples + 1  # 底面圆整圈
    assert len(cone.outline(Camera(azimuth=0, elevation=0))) >= 8


def test_convex_hull():
    pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0.5, 0.5], [0.2, 0.7]])
    hull = convex_hull_2d(pts)
    assert len(hull) == 4


def test_parallel_origins_are_offset_perpendicular_to_direction():
    from halo_notes.draw.raypath import parallel_origins
    anchor, d = np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 0.2])
    offs = [-0.4, 0.0, 0.4, 0.8]
    pts = parallel_origins(anchor, d, offs)
    assert pts.shape == (4, 3)
    rel = pts - anchor
    assert np.allclose(rel @ d, 0)                                   # 严格垂直于传播方向
    assert np.allclose(np.linalg.norm(rel, axis=1), np.abs(offs))    # 偏移量即距离
    assert np.allclose(pts[1], anchor)


def test_parallel_origins_respects_explicit_perp():
    from halo_notes.draw.raypath import parallel_origins
    d = np.array([1.0, 0.0, 0.0])
    auto = parallel_origins([0, 0, 0], d, [1.0])[0]
    explicit = parallel_origins([0, 0, 0], d, [1.0], perp=[0.0, 0.0, 1.0])[0]
    assert np.allclose(explicit, [0, 0, 1])
    assert not np.allclose(auto, explicit)
    # 非严格垂直的 perp 先被投影：沿 direction 的分量被剔除
    skew = parallel_origins([0, 0, 0], d, [1.0], perp=[0.5, 0.0, 1.0])[0]
    assert np.allclose(skew, [0, 0, 1])


def test_perp_basis_is_orthonormal_right_handed():
    from halo_notes.draw.geometry import perp_basis, unit
    for v in ([1, 0, 0], [0, 0, 1], [0.3, -0.2, 0.9], [1, 1, 0]):
        u, w = perp_basis(v)
        a = unit(v)
        assert np.isclose(u @ a, 0) and np.isclose(w @ a, 0) and np.isclose(u @ w, 0)
        assert np.isclose(np.linalg.norm(u), 1) and np.isclose(np.linalg.norm(w), 1)
        assert np.allclose(np.cross(u, w), a)
