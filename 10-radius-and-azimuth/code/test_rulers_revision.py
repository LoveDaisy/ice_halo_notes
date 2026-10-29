"""图 5：真实天球大圆和水平投影角的独立几何证据。"""
from matplotlib.patches import ArrowStyle
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
                              'equatorial-angle-arc', 'equatorial-radius-0',
                              'equatorial-radius-1', 'meridian-0', 'meridian-1',
                              'central-radius-0', 'central-radius-1', 'central-angle-arc'}
        assert np.allclose(lines['sky-great-circle'].get_xydata(),
                           R.CAMERA.project_xy(data.great_circle))
        assert np.allclose(lines['equatorial-azimuth-arc'].get_xydata(),
                           R.CAMERA.project_xy(data.horizontal_arc))
        assert np.allclose(lines['equatorial-angle-arc'].get_xydata(),
                           R.CAMERA.project_xy(0.56 * data.horizontal_arc))
        for i in (0, 1):
            assert np.allclose(lines[f'equatorial-radius-{i}'].get_xydata(),
                               R.CAMERA.project_xy([np.zeros(3), data.projections[i]]))
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


@pytest.mark.parametrize('height', [0.0, 20.0, 40.0, 60.0])
def test_drawn_central_angle_lies_between_radii_in_their_plane(height):
    # 从实际二维图元沿相机射线反投到两目标张成的平面，独立核定半径和夹角。
    fig, data = R.make_figure(height)
    try:
        ax = fig.axes[0]
        lines = {line.get_gid(): line for line in ax.lines if line.get_gid()}
        camera = R.CAMERA
        normal = np.cross(*data.directions)

        def to_plane(xy):
            xy = np.asarray(xy).reshape(-1, 2)
            image = xy[:, :1] * camera.right + xy[:, 1:] * camera.cam_up
            rays = image - camera.position
            travel = -(camera.position @ normal) / (rays @ normal)
            return camera.position + travel[:, None] * rays

        radii = np.stack([to_plane(lines[f'central-radius-{i}'].get_xydata())
                          for i in (0, 1)])
        assert np.allclose(radii[:, 0], 0.0, atol=1e-14)
        assert np.allclose(radii[:, 1], data.directions)
        arc = to_plane(lines['central-angle-arc'].get_xydata())
        lengths = np.linalg.norm(arc, axis=1)
        assert 0 < lengths[0] < 1
        assert np.allclose(lengths, lengths[0], atol=1e-14)
        assert np.allclose(arc[[0, -1]], lengths[0] * radii[:, 1])
        unit = arc / lengths[:, None]
        angles = np.arctan2(np.linalg.norm(np.cross(unit[:-1], unit[1:]), axis=1),
                            np.sum(unit[:-1] * unit[1:], axis=1))
        expected = np.arctan2(np.linalg.norm(normal), np.prod(data.directions, axis=0).sum())
        assert np.sum(angles) == pytest.approx(expected, abs=1e-12)
        if height == 40:
            assert np.degrees(np.sum(angles)) == pytest.approx(27.63, abs=0.005)
            assert np.degrees(np.sum(angles)) != pytest.approx(36.32, abs=0.005)
        tips = {a.get_gid(): a for a in ax.texts if a.get_gid()}
        assert set(tips) == {'central-angle-tip-0', 'central-angle-tip-1',
                             'equatorial-angle-tip-0', 'equatorial-angle-tip-1'}
        for i, index in enumerate((0, -1)):
            tip = tips[f'central-angle-tip-{i}']
            assert np.allclose(to_plane(tip.xy)[0], arc[index])
            assert np.allclose(to_plane(tip.xyann)[0], arc[9 if i == 0 else -10])
            assert isinstance(tip.arrow_patch.get_arrowstyle(), ArrowStyle.CurveFilledB)
        assert lines['sky-great-circle'].get_linewidth() < lines['central-angle-arc'].get_linewidth()
    finally:
        R.plt.close(fig)


@pytest.mark.parametrize('height', [0.0, 20.0, 40.0, 60.0])
def test_equatorial_angle_has_two_radii_and_centered_double_arrow(height):
    fig, data = R.make_figure(height)
    try:
        ax = fig.axes[0]
        camera = R.CAMERA
        lines = {line.get_gid(): line for line in ax.lines if line.get_gid()}

        def to_equator(xy):
            xy = np.asarray(xy).reshape(-1, 2)
            image = xy[:, :1] * camera.right + xy[:, 1:] * camera.cam_up
            rays = image - camera.position
            travel = -camera.position[2] / rays[:, 2]
            return camera.position + travel[:, None] * rays

        radii = np.stack([to_equator(lines[f'equatorial-radius-{i}'].get_xydata())
                          for i in (0, 1)])
        np.testing.assert_allclose(radii[:, 0], 0.0, atol=1e-14)
        np.testing.assert_allclose(radii[:, 1], data.projections, atol=1e-14)
        arc = to_equator(lines['equatorial-angle-arc'].get_xydata())
        lengths = np.linalg.norm(arc, axis=1)
        assert 0 < lengths[0] < 1
        np.testing.assert_allclose(lengths, lengths[0], atol=1e-14)
        np.testing.assert_allclose(arc[[0, -1]], lengths[0] * radii[:, 1], atol=1e-14)
        unit = arc / lengths[:, None]
        angles = np.arctan2(np.linalg.norm(np.cross(unit[:-1], unit[1:]), axis=1),
                            np.sum(unit[:-1] * unit[1:], axis=1))
        np.testing.assert_allclose(np.degrees(angles.sum()), data.azimuth, atol=1e-10)
        if height == 40:
            assert np.degrees(angles.sum()) == pytest.approx(36.32, abs=0.005)
            assert np.degrees(angles.sum()) != pytest.approx(data.distance)
        tips = {a.get_gid(): a for a in ax.texts if a.get_gid()}
        for i, index in enumerate((0, -1)):
            tip = tips[f'equatorial-angle-tip-{i}']
            np.testing.assert_allclose(to_equator(tip.xy)[0], arc[index], atol=1e-14)
            np.testing.assert_allclose(to_equator(tip.xyann)[0],
                                       arc[9 if i == 0 else -10], atol=1e-14)
            assert isinstance(tip.arrow_patch.get_arrowstyle(), ArrowStyle.CurveFilledB)
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
