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


# ---- solve_raypath：按面序列反解 --------------------------------------------

@pytest.mark.parametrize("ratio, faces", [
    (0.8, [1, 3, 2]), (2.0, [3, 1, 5, 7, 4]), (2.0, [1, 2, 3, 5, 1]), (3.2, [4, 1]), (1.7, [3, 1, 5]),
    (1.9, [1]),  # 单个面 = 外反射（4.1）
])
def test_solve_raypath_replays_to_same_face_sequence(ratio, faces):
    from halo_notes.draw.raypath import events_for_faces, face_sequence, solve_raypath
    c = HexPrism(1.0, ratio)
    p = solve_raypath(c, faces)
    assert face_sequence(p) == faces
    # 用 trace 从同一起点 / 方向回放：面序列全等、坐标逐点一致
    replay = trace(c, p.points[0], p.points[1] - p.points[0], events_for_faces(faces))
    assert face_sequence(replay) == faces
    assert np.allclose(replay.points, p.points)
    # 每个事件点都在所声明的面内部（不擦边）
    for ev in p.events:
        f = c.face(ev.face_number)
        assert abs(c.face_distance(f, p.points[ev.point_index])) < 1e-6
        assert c.face_margin(f, p.points[ev.point_index]) > 1e-3


def test_solve_raypath_rejects_geometrically_impossible_sequence():
    """片晶 1-3-1：从顶面进、竖直侧面反射不改变竖直分量，回不到顶面。"""
    from halo_notes.draw.raypath import solve_raypath
    with pytest.raises(ValueError, match=r"\[1, 3, 1\]"):
        solve_raypath(HexPrism(1.0, 0.2), [1, 3, 1])


def test_solve_raypath_honours_preference_exactly_when_feasible():
    """迁移旧脚本：偏好的入射点 / 方向本身就能走出该面序列时原样返回（构图零漂移）。"""
    from halo_notes.draw.raypath import aim, solve_raypath
    c = HexPrism(1.0, 0.8)
    el, az = np.deg2rad(-25), np.deg2rad(-40)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    point = c.centroid(c.face(1)) + np.array([0.5, 0.3, 0])
    old = trace(c, aim(c, 1, d, offset=(0.5, 0.3, 0)), d, ["refract", "reflect", "refract"])
    new = solve_raypath(c, [1, 3, 2], prefer_point=point, prefer_direction=d)
    assert np.allclose(new.points, old.points)


def test_solve_raypath_preference_picks_nearest_candidate_when_infeasible():
    """偏好方向本身走不出该序列时，在可行候选里取方向最接近的那条（而不是随便一条）。"""
    from halo_notes.draw.raypath import solve_raypath
    c = HexPrism(1.0, 0.8)
    wish = np.array([0.3, 0.0, -1.0])  # 近乎垂直射向顶面：只会 1-2 直穿，走不出 1-3-2
    p = solve_raypath(c, [1, 3, 2], prefer_direction=wish)
    free = solve_raypath(c, [1, 3, 2])
    d_p = p.points[1] - p.points[0]
    d_free = free.points[1] - free.points[0]
    cos = lambda a, b: a @ b / np.linalg.norm(a) / np.linalg.norm(b)  # noqa: E731
    assert cos(d_p, wish) >= cos(d_free, wish)


def test_events_for_faces():
    from halo_notes.draw.raypath import events_for_faces
    assert events_for_faces([1]) == ["reflect"]
    assert events_for_faces([4, 1]) == ["refract", "refract"]
    assert events_for_faces([3, 1, 5, 7, 4]) == ["refract", "reflect", "reflect", "reflect", "refract"]
    with pytest.raises(ValueError):
        events_for_faces([])


def test_verify_path_accepts_traced_and_rejects_bent_wrong():
    from halo_notes.draw.raypath import verify_path
    c = HexPrism(1.0, 1.0)
    p = trace(c, [-5, 0.0, -2.0], [1, 0, 0.5], ["refract", "reflect", "refract"])  # 6-1-3
    verify_path(p, lambda ev: c)  # 不抛
    # 把内反射点之后的方向改掉（仍在晶体内）：反射定律被破坏
    pts = p.points.copy()
    pts[3] = pts[3] + np.array([0.0, 0.2, 0.0])
    bad = RayPath(pts, p.kinds, p.events)
    with pytest.raises(ValueError, match="reflection"):
        verify_path(bad, lambda ev: c)
    # 事件点不在面上
    pts2 = p.points.copy()
    pts2[1] = pts2[1] + np.array([0.1, 0, 0])
    with pytest.raises(ValueError, match="off the face plane"):
        verify_path(RayPath(pts2, p.kinds, p.events), lambda ev: c)
