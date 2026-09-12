import numpy as np
import pytest

from halo_notes.draw.geometry import HexPrism
from halo_notes.draw.projection import (Camera, depth_sorted_faces, edge_visible,
                                        face_visible, point_on_visible_face,
                                        visible_faces)


def test_orthographic_projection_known_view():
    """从 +x 看（方位 0°、仰角 0°）：画面 x = 世界 y，画面 y = 世界 z。"""
    cam = Camera(azimuth=0, elevation=0, projection="orthographic")
    xy, depth = cam.project([[1, 2, 3]])
    assert np.allclose(xy[0], [2, 3])
    assert np.isclose(depth[0], 1)


def test_orthographic_projection_from_top():
    cam = Camera(azimuth=0, elevation=80, projection="orthographic")
    xy, _ = cam.project([[1, 0, 0]])
    assert np.allclose(xy[0], [0, -np.sin(np.deg2rad(80))])  # 俯视时 +x 在画面下方（up=z）
    with pytest.raises(ValueError):
        Camera(azimuth=0, elevation=90)


def test_perspective_scales_with_depth():
    cam = Camera(azimuth=0, elevation=0, projection="perspective", distance=10)
    near, _ = cam.project([[2, 1, 0]])
    far, _ = cam.project([[-2, 1, 0]])
    assert near[0, 0] > 1 > far[0, 0]


def test_from_direction_roundtrip():
    cam = Camera.from_direction([1, 1, 1])
    assert np.allclose(cam.view_dir, np.ones(3) / np.sqrt(3))


def test_grazing_face_is_hidden():
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0)
    assert not face_visible(prism, prism.face(1), cam)
    assert not face_visible(prism, prism.face(2), cam)


def test_face_visibility_front_and_back():
    """红测：正对面 3（+x）时面 3 可见、面 6（-x）不可见；掉头看则反之。"""
    prism = HexPrism()
    front = Camera(azimuth=0, elevation=0)
    assert face_visible(prism, prism.face(3), front)
    assert not face_visible(prism, prism.face(6), front)
    back = Camera(azimuth=180, elevation=0)
    assert not face_visible(prism, prism.face(3), back)
    assert face_visible(prism, prism.face(6), back)


def test_visible_faces_from_above_include_top_only():
    prism = HexPrism()
    cam = Camera(azimuth=45, elevation=30)
    nums = {f.number for f in visible_faces(prism, cam)}
    assert 1 in nums and 2 not in nums
    assert nums & {3, 4, 5, 6, 7, 8} == {3, 4, 5}  # 方位 45° → 法向 0°/60°/120° 的侧面朝向观察者


def test_perspective_visibility_uses_camera_position():
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0, projection="perspective", distance=3)
    assert face_visible(prism, prism.face(3), cam)
    assert not face_visible(prism, prism.face(6), cam)


def test_edge_visible_if_any_adjacent_face_visible():
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0)
    # 面 3 与面 1 的公共边（顶环 0-1）可见；面 6 与面 2 的公共边（底环 9-10）不可见
    assert edge_visible(prism, (0, 1), cam)
    assert not edge_visible(prism, (9, 10), cam)


def test_depth_sorted_faces_far_to_near():
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0)
    order = [f.number for f in depth_sorted_faces(prism, cam)]
    assert order.index(6) < order.index(3)


def test_point_on_visible_face():
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0)
    assert point_on_visible_face(prism, [np.sqrt(3) / 2, 0, 0], cam) is True
    assert point_on_visible_face(prism, [-np.sqrt(3) / 2, 0, 0], cam) is False
    assert point_on_visible_face(prism, [0, 0, 0], cam) is None


def test_default_projection_is_perspective():
    assert Camera().projection == "perspective"


def test_projection_mode_flips_visibility_of_grazing_face():
    """红绿对照：同一方位/仰角下，正交与近距透视对同一面给出相反的可见性。

    仰角 5°、距离 3 时透视相机高度 z = 3·sin5° ≈ 0.26 低于顶面（z = 0.4），
    从顶面质心看相机在其下方 → 顶面 1 不可见；正交视线常向量仍有 +z 分量 → 可见。
    """
    prism = HexPrism(1, 0.8)
    ortho = Camera(azimuth=0, elevation=5, projection="orthographic")
    persp = Camera(azimuth=0, elevation=5, projection="perspective", distance=3)
    assert persp.position[2] < prism.centroid(prism.face(1))[2]
    assert face_visible(prism, prism.face(1), ortho)
    assert not face_visible(prism, prism.face(1), persp)
    assert face_visible(prism, prism.face(1), ortho) != face_visible(prism, prism.face(1), persp)


def test_solve_camera_distance_hits_target_fov():
    """给定点集与目标视场，求得的 distance 使实际水平视场落在目标 ±1° 内。"""
    from halo_notes.draw.projection import horizontal_fov, solve_camera_distance
    pts = [HexPrism(1.0, 1.9).vertices + [4.3, 0, 0], HexPrism(1.0, 3.2).vertices,
           HexPrism(1.0, 1.7).vertices - [4.3, 0, 0]]
    for target in (28.0, 15.0, 45.0):
        d = solve_camera_distance(pts, azimuth=60, elevation=24, target_fov_deg=target)
        cam = Camera(azimuth=60, elevation=24, distance=d)
        assert abs(horizontal_fov(cam, np.vstack(pts)) - target) < 1.0
        assert not any(cam.project(np.vstack(pts))[1] >= d)   # 没有点跑到相机后方
    # 4.1 的教训：默认 8 是广角，28 是中长焦；求出的 distance 单调随目标视场变小而变大
    d28 = solve_camera_distance(pts, azimuth=60, elevation=24, target_fov_deg=28)
    d15 = solve_camera_distance(pts, azimuth=60, elevation=24, target_fov_deg=15)
    assert d15 > d28 > 8


def test_solve_camera_distance_reports_unreachable_fov_clearly():
    from halo_notes.draw.projection import horizontal_fov, solve_camera_distance
    pts = [HexPrism(1.0, 1.0).vertices]
    with pytest.raises(ValueError, match="no solution"):
        solve_camera_distance(pts, azimuth=30, elevation=20, target_fov_deg=170)
    with pytest.raises(ValueError):
        horizontal_fov(Camera(projection="orthographic"), pts[0])
