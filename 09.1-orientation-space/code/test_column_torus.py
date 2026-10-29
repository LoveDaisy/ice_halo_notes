"""候选图 2a：参数环面必须对应真实柱晶姿态，不能以漂亮形状代替族约束。"""
import numpy as np
import pytest

import fig_column_torus as F


def test_periods_and_column_constraint():
    for psi in (0, 37, 183, 359):
        for theta in (0, 62, 180, 311):
            r = F.attitude(psi, theta)
            assert abs(r[2, 2]) < 1e-12
            np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)
            for p, t in ((psi + 360, theta), (psi, theta + 360)):
                np.testing.assert_allclose(F.attitude(p, t), r, atol=1e-12)
                np.testing.assert_allclose(F.torus(p, t), F.torus(psi, theta), atol=1e-12)
            # 各自走半圈不是同一个带面号姿态，排除把周期自由度压成单向线段。
            assert np.linalg.norm(r - F.attitude(psi + 180, theta)) > 1
            assert np.linalg.norm(r - F.attitude(psi, theta + 180)) > 1


def test_parry_circle_locks_upward_side_face():
    for psi in np.linspace(0, 360, 73):
        r = F.attitude(psi, F.PARRY_THETA)
        np.testing.assert_allclose(r[:, 0], [0, 0, 1], atol=1e-12)
        assert abs(r[2, 2]) < 1e-12
        assert abs(F.torus(psi, F.PARRY_THETA)[2] - F.MINOR) < 1e-12
        assert np.linalg.norm(F.attitude(psi, F.PARRY_THETA + 30)[:, 0] - [0, 0, 1]) > 0.1


def test_visible_surface_is_on_torus_and_faces_camera():
    image, xyz = F.surface_pixels(width=201)
    assert np.isfinite(image).all() and image.min() >= 0 and image.max() <= 1
    assert len(xyz) > 1000
    # 代数环面方程是一条不同于射线步进距离函数的几何核验链。
    x, y, z = xyz.T
    residual = (x*x + y*y + z*z + F.MAJOR**2 - F.MINOR**2)**2 - 4 * F.MAJOR**2 * (x*x + y*y)
    assert np.max(np.abs(residual)) < 0.002
    radial = np.hypot(x, y)
    normals = np.column_stack([x * (1 - F.MAJOR / radial),
                               y * (1 - F.MAJOR / radial), z]) / F.MINOR
    toward = F.CAMERA.position - xyz
    toward /= np.linalg.norm(toward, axis=1, keepdims=True)
    assert np.einsum('ij,ij->i', normals, toward).min() > -1e-6
    # 每个命中点沿自己的相机射线前移一小段应在外部，防止误取背面表面。
    assert F.signed_distance(xyz + 0.002 * toward).min() > 0


def test_inverse_projection_and_depth_scaling():
    from halo_notes.draw.projection import Camera

    # 非默认滚转相机，防止 helper 暗中使用全局 EYE/RIGHT。
    camera = Camera(azimuth=23, elevation=41, distance=9, roll=17)
    xy = np.array([[-2.1, 0.6], [0, 0], [1.2, -0.7]])
    origins, directions = F.camera_rays(xy, camera)
    np.testing.assert_allclose(origins, np.broadcast_to(camera.position, origins.shape))
    np.testing.assert_allclose(np.linalg.norm(directions, axis=1), 1)
    assert np.linalg.norm(directions[0] - directions[-1]) > 0.3
    for distance in (3, 6, 12):
        points = origins + distance * directions
        np.testing.assert_allclose(camera.project_xy(points), xy, atol=1e-12)
    near = camera.to_world(1, 0, 3)
    far = camera.to_world(1, 0, -3)
    np.testing.assert_allclose(camera.project_xy([near, far])[:, 0], [1.5, 0.75])
    assert F.CAMERA.projection == 'perspective'


def test_raster_hit_projects_to_its_own_pixel_center():
    width = 161
    image, xyz = F.surface_pixels(width)
    height = image.shape[0]
    left, right, bottom, top = F.EXTENT
    row, col = np.where(np.any(image != 1, axis=-1))
    expected = np.column_stack([left + (col + 0.5) * (right-left)/width,
                                bottom + (row + 0.5) * (top-bottom)/height])
    np.testing.assert_allclose(F.CAMERA.project_xy(xyz), expected, atol=1e-12)


def test_single_torus_trace_matches_independent_quartic_nearest_root():
    from numpy.polynomial import Polynomial

    rng = np.random.default_rng(351)
    xy = rng.uniform([-3.6, -2.1], [3.6, 2.1], (140, 2))
    origins, directions = F.camera_rays(xy)
    expected = []
    for origin, direction in zip(origins, directions):
        x, y, z = [Polynomial([a, b]) for a, b in zip(origin, direction)]
        q = x*x + y*y + z*z + F.MAJOR**2 - F.MINOR**2
        roots = (q*q - 4*F.MAJOR**2*(x*x+y*y)).roots()
        forward = [r.real for r in roots if abs(r.imag) < 1e-8 and r.real > 0]
        expected.append(min(forward, default=np.inf))
    expected = np.array(expected)
    actual = F.trace(origins, directions)
    np.testing.assert_array_equal(np.isfinite(actual), np.isfinite(expected))
    hit = np.isfinite(expected)
    np.testing.assert_allclose(actual[hit], expected[hit], atol=0.001, rtol=0)
    # 同一视线上的前后两面不能都被可见性测试放行。
    points = origins[hit] + expected[hit, None] * directions[hit]
    assert F.line_visibility(points).all()
    assert not F.line_visibility(points + 0.1*directions[hit]).any()


@pytest.mark.parametrize("finish", ["lowitz", "neutral"])
def test_surface_finishes_keep_geometry(finish):
    # 曲面着色只换颜色（候选方案的 surfaces 槽），命中像素与语义圈位置不变。
    original, points = F.surface_pixels(width=201)
    variant, other = F.surface_pixels(width=201, finish=finish)
    np.testing.assert_array_equal(points, other)
    np.testing.assert_array_equal(np.all(original == 1, axis=-1), np.all(variant == 1, axis=-1))
    assert np.mean(np.abs(original - variant)) > 0.01
    assert np.isfinite(variant).all() and 0 <= variant.min() <= variant.max() <= 1
