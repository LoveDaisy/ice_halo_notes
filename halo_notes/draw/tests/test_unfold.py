import numpy as np
import pytest

from halo_notes.draw.geometry import HexPrism, unit
from halo_notes.draw.raypath import EventKind, RayEvent, RayPath, SegmentKind, aim, trace
from halo_notes.draw.unfold import corridor_faces, straighten, unfold


def _synthetic_path(reflect_faces):
    """手工拼一条只带事件语义的路径（几何不必物理自洽，只测镜像编排逻辑）。"""
    n = len(reflect_faces)
    pts = np.zeros((n + 4, 3))  # 起点、入射点、n 个反射点、出射点、终点
    pts[:, 0] = np.arange(n + 4)
    kinds = (SegmentKind.INCIDENT,) + (SegmentKind.INTERNAL,) * (n + 1) + (SegmentKind.EXIT,)
    events = [RayEvent(1, 6, EventKind.REFRACT_IN)]
    events += [RayEvent(2 + k, f, EventKind.REFLECT_INTERNAL) for k, f in enumerate(reflect_faces)]
    events.append(RayEvent(n + 2, 3, EventKind.REFRACT_OUT))
    return RayPath(pts, kinds, tuple(events))


def test_unfold_no_reflection_returns_empty():
    assert unfold(HexPrism(1, 1), _synthetic_path([])) == []


def test_unfold_single_reflection_matches_mirrored():
    c = HexPrism(1, 0.8)
    ghosts = unfold(c, _synthetic_path([3]))
    assert len(ghosts) == 1
    assert np.allclose(ghosts[0].vertices, c.mirrored(c.face(3)).vertices)


def test_unfold_cascades_on_previous_ghost():
    c = HexPrism(1, 0.8)
    ghosts = unfold(c, _synthetic_path([1, 5]))
    assert len(ghosts) == 2
    g1 = c.mirrored(c.face(1))
    expected = g1.mirrored(g1.face(5))            # 第二次镜像作用在第一个幽灵上
    wrong = c.mirrored(c.face(5))                 # 而不是作用在原晶体上
    assert np.allclose(ghosts[1].vertices, expected.vertices)
    assert not np.allclose(ghosts[1].vertices, wrong.vertices)
    # 具体数值：先关于顶面 1 镜像（体心 z 抬到 0.8），再关于该幽灵的面 5 镜像（z 不变）
    assert np.isclose(ghosts[1].centroid()[2], 0.8)
    assert np.isclose(wrong.centroid()[2], 0.0)


@pytest.fixture
def two_reflection_path():
    """真实追迹：从面 3 质心斜向下射入（方位 120°、俯角 60°），先在底面 2 反射、
    再在侧面 5 反射，从顶面 1 出射。"""
    c = HexPrism(1, 1.0)
    el, az = np.deg2rad(-60), np.deg2rad(120)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    p = trace(c, aim(c, 3, d), d, ["refract", "reflect", "reflect", "refract"])
    assert [e.face_number for e in p.events] == [3, 2, 5, 1]
    return c, p


def test_two_reflections_straight_ray_threads_ghost_faces(two_reflection_path):
    """共线性：展开后，从入射点沿第一段内部方向的一条直线依次穿过两个幽灵晶体，
    且第一个幽灵的穿出面就是真实路径第二次反射的面。"""
    c, p = two_reflection_path
    ghosts = unfold(c, p)
    assert len(ghosts) == 2
    entry = p.points[1]
    d1 = unit(p.points[2] - p.points[1])
    hit1 = ghosts[0].intersect_ray(entry - d1 * 1e-6, d1)
    assert hit1 is not None
    _, _, t1, f1 = hit1
    assert f1.number == p.events[2].face_number == 5
    exit1 = entry + d1 * t1
    hit2 = ghosts[1].intersect_ray(exit1 + d1 * 1e-6, d1)
    assert hit2 is not None
    _, f2_in, t2, f2 = hit2
    assert f2.number == p.events[3].face_number == 1  # 最后从幽灵 2 的面 1 出射
    # 直线穿过幽灵串的总路程 = 真实折线各内部段长度之和
    inner = sum(np.linalg.norm(p.points[k + 1] - p.points[k]) for k in (1, 2, 3))
    assert np.isclose(t1 + t2 + 1e-6, inner, atol=1e-6)


def test_straighten_matches_unfolded_geometry(two_reflection_path):
    c, p = two_reflection_path
    s = straighten(p)
    assert s.kinds == (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.EXIT)
    assert [(e.point_index, e.kind) for e in s.events] == [
        (1, EventKind.REFRACT_IN), (2, EventKind.REFRACT_OUT)]
    assert [e.face_number for e in s.events] == [3, 1]
    assert np.allclose(s.points[0], p.points[0]) and np.allclose(s.points[1], p.points[1])
    # 直线终点落在最后一个幽灵晶体的出射面上
    last = unfold(c, p)[-1]
    f = last.face(1)
    assert abs(last.normal(f) @ (s.points[2] - last.face_vertices(f)[0])) < 1e-6
    assert last.contains(s.points[2], eps=1e-6)
    # 出射段：长度不变；方向 = 直线 d1 在最后一个幽灵的出射面上按 Snell 折射的方向
    # （即真实出射方向经两次镜像搬到展开空间），而不是原样照搬真实出射方向
    from halo_notes.draw.raypath import N_ICE, refract
    d1 = unit(p.points[2] - p.points[1])
    out_dir = s.points[3] - s.points[2]
    assert np.isclose(np.linalg.norm(out_dir), np.linalg.norm(p.points[-1] - p.points[-2]))
    assert np.allclose(unit(out_dir), refract(d1, -last.normal(f), N_ICE, 1.0), atol=1e-9)
    assert not np.allclose(unit(out_dir), unit(p.points[-1] - p.points[-2]))


def test_straighten_rejects_path_without_exit():
    c = HexPrism(1, 1)
    p = trace(c, [-0.8, 0.1, 5], [0.2, 0, -1], ["reflect"])
    with pytest.raises(ValueError):
        straighten(p)


def test_unfolded_tail_drops_incident_segment(two_reflection_path):
    from halo_notes.draw.unfold import unfolded_tail
    _, p = two_reflection_path
    s = straighten(p)
    t = unfolded_tail(s)
    assert t.kinds == (SegmentKind.INTERNAL, SegmentKind.EXIT)
    assert np.allclose(t.points, s.points[1:])
    assert [(e.point_index, e.kind) for e in t.events] == [
        (0, EventKind.REFRACT_IN), (1, EventKind.REFRACT_OUT)]


def test_corridor_faces_assigns_faces_to_crystal_and_ghosts(two_reflection_path):
    from halo_notes.draw.unfold import corridor_faces
    c, p = two_reflection_path  # 3-2-5-1
    faces = corridor_faces(p)
    assert faces == [(0, 3), (1, 2), (2, 5), (2, 1)]
    ghosts = unfold(c, p)
    # 反射面在幽灵 k 上与晶体 k-1 的同编号面共面（这就是光线穿入幽灵 k 的那个面）
    chain = [c] + ghosts
    for k, number in faces[1:-1]:
        prev, ghost = chain[k - 1], chain[k]
        a = {tuple(np.round(v, 9)) for v in prev.face_vertices(prev.face(number))}
        b = {tuple(np.round(v, 9)) for v in ghost.face_vertices(ghost.face(number))}
        assert a == b
    assert corridor_faces(_synthetic_path([])) == [(0, 6), (0, 3)]


# ---- Corridor ---------------------------------------------------------------

@pytest.mark.parametrize("ratio, faces", [(0.8, [1, 3, 2]), (2.0, [3, 1, 5, 7, 4]), (2.0, [1, 2, 3, 5, 1])])
def test_corridor_straight_threads_every_corridor_face_interior(ratio, faces):
    from halo_notes.draw.raypath import EventKind, face_sequence, solve_raypath
    from halo_notes.draw.unfold import Corridor
    c = HexPrism(1.0, ratio)
    path = solve_raypath(c, faces)
    co = Corridor(c, path)
    s = co.straight
    assert len(co.chain) == len(faces) - 1 and co.faces == corridor_faces(path)
    assert face_sequence(s) == faces
    # 入射段与折线的真实入射段完全一致（含折射折点）
    assert np.allclose(s.points[:2], path.points[:2])
    # 直线段共线：入射点之后、出射点之前的所有点都在同一条直线上
    d = unit(s.points[2] - s.points[1])
    for q in s.points[2:-1]:
        assert np.allclose(np.cross(q - s.points[1], d), 0, atol=1e-9)
    # 每个事件点落在其所属多面体的该编号面上，且在面内部（不擦边）
    for ev in s.events:
        body = co.polyhedron_for_event(ev, s)
        f = body.face(ev.face_number)
        q = s.points[ev.point_index]
        assert abs(body.face_distance(f, q)) < 1e-6
        assert body.face_margin(f, q) > 1e-3
    kinds = [ev.kind for ev in s.events]
    assert kinds[0] is EventKind.REFRACT_IN and kinds[-1] is EventKind.REFRACT_OUT
    assert all(k is EventKind.PASS_THROUGH for k in kinds[1:-1])
    # 与 straighten() 的独立结果一致：终点、出射段
    st = straighten(path)
    assert np.allclose(s.points[-2:], st.points[-2:])


def test_corridor_polyhedron_for_event_indexes_chain_by_corridor_faces():
    from halo_notes.draw.raypath import solve_raypath
    from halo_notes.draw.unfold import Corridor
    c = HexPrism(1.0, 2.0)
    co = Corridor(c, solve_raypath(c, [3, 1, 5, 7, 4]))
    bodies = [co.polyhedron_for_event(ev, co.straight) for ev in co.straight.events]
    assert [co.chain.index(b) for b in bodies] == [0, 1, 2, 3, 3]
    # 折线的事件全部在真实晶体上
    assert all(co.polyhedron_for_event(ev, co.path) is c for ev in co.path.events)
    with pytest.raises(ValueError):
        co.polyhedron_for_event(co.straight.events[0], straighten(co.path))


def test_corridor_rejects_centroid_line_masquerading_as_ray():
    """三面质心连线（旧 2.7 / 2.8 的画法）声称走 1-3-2：几何上它确实依次穿过三个面的内部，
    但在面 1 没有折射折点（入射方向 = 内部方向，违反 Snell）——Corridor 构造必须报错而不是画出来。"""
    from halo_notes.draw.unfold import Corridor
    c = HexPrism(1.0, 0.8)
    ghost = c.mirrored(c.face(3))
    pts = np.array([c.centroid(c.face(1)), c.centroid(c.face(3)), ghost.centroid(ghost.face(2))])
    d = unit(pts[1] - pts[0])
    fake = RayPath(np.vstack([pts[0] - d, pts, pts[2] + d]),
                   (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.INTERNAL, SegmentKind.EXIT),
                   (RayEvent(1, 1, EventKind.REFRACT_IN), RayEvent(2, 3, EventKind.REFLECT_INTERNAL),
                    RayEvent(3, 2, EventKind.REFRACT_OUT)))
    with pytest.raises(ValueError, match="refraction"):
        Corridor(c, fake)


def test_raypath_sketch_flag_survives_transform_and_straighten():
    c = HexPrism(1.0, 0.8)
    from halo_notes.draw.raypath import solve_raypath
    p = solve_raypath(c, [1, 3, 2])
    assert p.sketch is False
    q = RayPath(p.points, p.kinds, p.events, sketch=True)
    assert q.transformed(translation=(1, 0, 0)).sketch is True
    assert straighten(q).sketch is True
