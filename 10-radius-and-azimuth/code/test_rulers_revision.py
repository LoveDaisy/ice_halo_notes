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


def test_drawn_spherical_and_projected_rulers_use_scene_points():
    fig, data = R.make_figure()
    try:
        axes = {ax.get_label(): ax for ax in fig.axes}
        lines = {line.get_gid(): line for ax in fig.axes for line in ax.lines if line.get_gid()}
        assert set(axes) == {'celestial-sphere', 'horizontal-view'}
        assert np.allclose(lines['sky-great-circle'].get_xydata(),
                           R.CAMERA.project_xy(data.great_circle))
        assert np.allclose(lines['central-distance-arc'].get_xydata(),
                           R.CAMERA.project_xy(data.great_circle * 0.58))
        assert np.allclose(lines['top-view-azimuth-arc'].get_xydata(),
                           (data.horizontal_arc * 0.46)[:, [1, 0]])
        for i in (0, 1):
            assert np.allclose(lines[f'direction-{i}'].get_xydata(),
                               R.CAMERA.project_xy([[0, 0, 0], data.directions[i]]))
            assert np.allclose(lines[f'drop-{i}'].get_xydata(),
                               R.CAMERA.project_xy([data.directions[i], data.projections[i]]))
            assert np.allclose(lines[f'top-view-projection-{i}'].get_xydata(),
                               [[0, 0], data.projections[i, [1, 0]]])
    finally:
        R.plt.close(fig)


def test_perspective_sphere_silhouette_and_depth_scaling():
    rim = R.sphere_outline()
    assert np.allclose(np.linalg.norm(rim, axis=1), 1.0)
    assert np.allclose(rim @ R.CAMERA.position, 1.0)
    x = R.CAMERA.right * 0.2
    near = R.CAMERA.project_xy(x + 0.5 * R.CAMERA.view_dir)[0]
    far = R.CAMERA.project_xy(x - 0.5 * R.CAMERA.view_dir)[0]
    assert np.linalg.norm(near) > np.linalg.norm(far)


@pytest.mark.parametrize('height', [-1, R.C.critical_height(), 65])
def test_no_synthetic_geometry_outside_transmitting_domain(height):
    with pytest.raises(ValueError):
        R.ruler_geometry(height)
    if height >= R.C.critical_height():
        _, distance, delta = R.curve_data([height])
        assert np.isnan(distance[0]) and np.isnan(delta[0])
