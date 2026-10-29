"""图 5：真实天球大圆和水平投影角的独立几何证据。"""
import numpy as np
import pytest

import fig_parhelion_rulers as R


@pytest.mark.parametrize('height', [0.0, 20.0, 40.0, 60.0])
def test_two_angles_from_vectors_and_horizontal_projection(height):
    data = R.ruler_geometry(height)
    a, b = data.directions
    dot_angle = np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b))
    flat = data.projections[:, :2].copy()
    flat /= np.linalg.norm(flat, axis=1, keepdims=True)
    horizontal_angle = np.degrees(np.arccos(np.clip(flat[0] @ flat[1], -1, 1)))
    assert dot_angle == pytest.approx(data.distance, abs=1e-10)
    assert horizontal_angle == pytest.approx(data.azimuth, abs=1e-10)
    assert np.allclose(data.directions[:, 2], np.sin(np.radians(height)))
    assert np.allclose(data.projections[:, 2], 0.0)
    h = np.radians(height)
    assert a @ b == pytest.approx(np.sin(h)**2 + np.cos(h)**2 * np.cos(np.radians(horizontal_angle)))
    if height:
        assert dot_angle < horizontal_angle
    else:
        assert dot_angle == pytest.approx(horizontal_angle)


def test_great_circle_is_not_latitude_arc():
    data = R.ruler_geometry()
    a, b = data.directions
    normal = np.cross(a, b)
    assert np.allclose(np.linalg.norm(data.great_circle, axis=1), 1.0)
    assert np.allclose(data.great_circle @ normal, 0.0, atol=1e-15)
    assert np.allclose(data.great_circle[[0, -1]], data.directions)
    assert data.great_circle[len(data.great_circle)//2, 2] > a[2]
    assert data.distance == pytest.approx(27.63, abs=0.005)
    assert data.azimuth == pytest.approx(36.32, abs=0.005)


@pytest.mark.parametrize('height', [0.0, 20.25, 40.0, 60.0])
def test_meridians_pass_through_zenith_targets_and_equator(height):
    data = R.ruler_geometry(height)
    north = np.array([0., 0., 1.])
    for direction, foot, meridian in zip(data.directions, data.projections, data.meridians):
        assert np.allclose(np.linalg.norm(meridian, axis=1), 1.0)
        assert np.allclose(meridian @ np.cross(north, direction), 0.0, atol=1e-15)
        assert np.allclose(meridian[0], north)
        assert np.allclose(meridian[-1], foot)
        assert np.min(np.linalg.norm(meridian - direction, axis=1)) < 1e-14
        assert np.linalg.norm(foot) == pytest.approx(1.0)
        assert np.allclose(foot[:2] * np.cos(np.radians(height)), direction[:2])
        assert np.all(np.diff(meridian[:, 2]) <= 0)
    assert np.allclose(data.horizontal_arc[[0, -1]], data.projections)
    assert np.allclose(np.linalg.norm(data.horizontal_arc, axis=1), 1.0)
    assert np.allclose(data.horizontal_arc[:, 2], 0.0)
    assert np.allclose(np.linalg.norm(data.equator, axis=1), 1.0)
    assert np.allclose(data.equator[:, 2], 0.0)
    assert np.allclose(np.linalg.norm(data.latitude, axis=1), 1.0)
    assert np.allclose(data.latitude[:, 2], np.sin(np.radians(height)))


def test_drawn_spherical_rulers_and_meridians_use_scene_points():
    fig, data = R.make_figure()
    try:
        axes = {ax.get_label(): ax for ax in fig.axes}
        lines = {line.get_gid(): line for ax in fig.axes for line in ax.lines if line.get_gid()}
        assert set(axes) == {'celestial-sphere'}
        assert set(lines) == {'sky-great-circle', 'equatorial-azimuth-arc',
                              'meridian-0', 'meridian-1'}
        assert np.allclose(lines['sky-great-circle'].get_xydata(),
                           R.CAMERA.project_xy(data.great_circle))
        assert np.allclose(lines['equatorial-azimuth-arc'].get_xydata(),
                           R.CAMERA.project_xy(data.horizontal_arc))
        for i in (0, 1):
            assert np.allclose(lines[f'meridian-{i}'].get_xydata(),
                               R.CAMERA.project_xy(data.meridians[i]))
        texts = [t.get_text() for t in fig.texts + axes['celestial-sphere'].texts]
        assert not any('cos' in t or 'sin' in t for t in texts)
    finally:
        R.plt.close(fig)


def test_actual_generated_rulers_have_correct_spherical_lengths():
    # 从实际线图元反投到单位球，不以返回的 data 自证画出的线正确。
    fig, _ = R.make_figure()
    try:
        camera = R.CAMERA
        lines = {line.get_gid(): line for line in fig.axes[0].lines if line.get_gid()}
        for gid, expected in [('sky-great-circle', 27.63), ('equatorial-azimuth-arc', 36.32)]:
            xy = lines[gid].get_xydata()
            image = xy[:, :1] * camera.right + xy[:, 1:] * camera.cam_up
            rays = image - camera.position
            rays /= np.linalg.norm(rays, axis=1, keepdims=True)
            b = rays @ camera.position
            travel = -b - np.sqrt(b*b - (camera.position @ camera.position - 1))
            points = camera.position + travel[:, None] * rays
            angles = np.arctan2(np.linalg.norm(np.cross(points[:-1], points[1:]), axis=1),
                                np.sum(points[:-1] * points[1:], axis=1))
            assert np.degrees(angles.sum()) == pytest.approx(expected, abs=0.005)
            assert np.allclose(points @ np.cross(points[0], points[-1]), 0., atol=2e-14)
    finally:
        R.plt.close(fig)


def test_perspective_sphere_silhouette_and_depth_scaling():
    rim = R.sphere_outline()
    assert np.allclose(np.linalg.norm(rim, axis=1), 1.0)
    assert np.allclose(rim @ R.CAMERA.position, 1.0)
    x = R.CAMERA.right * 0.2
    near = R.CAMERA.project_xy(x + 0.5 * R.CAMERA.view_dir)[0]
    far = R.CAMERA.project_xy(x - 0.5 * R.CAMERA.view_dir)[0]
    ratio = np.linalg.norm(near) / np.linalg.norm(far)
    assert ratio == pytest.approx((R.CAMERA.distance + 0.5) / (R.CAMERA.distance - 0.5))
    data = R.ruler_geometry()
    # 斜视角不是原来正对两点的角平分线；两个目标具有不同深度。
    assert abs(np.diff(data.directions @ R.CAMERA.view_dir)[0]) > 0.1
    assert np.all(R.Sphere().facing(data.great_circle, R.CAMERA))
    assert np.all(R.Sphere().facing(data.horizontal_arc, R.CAMERA))


@pytest.mark.parametrize('height', [-1, R.C.critical_height(), 65])
def test_no_synthetic_geometry_outside_transmitting_domain(height):
    with pytest.raises(ValueError):
        R.ruler_geometry(height)
    if height >= R.C.critical_height():
        _, distance, delta = R.curve_data([height])
        assert np.isnan(distance[0]) and np.isnan(delta[0])
