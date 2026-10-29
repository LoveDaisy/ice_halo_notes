"""图6正/斜穿与实际天空图元；用切向守恒和柱晶映射的折叠反证曲线。"""
import matplotlib.pyplot as plt
import numpy as np
import pytest

import fig_tangent_direction as F


@pytest.fixture(scope="module")
def scene():
    return F.build_scene()


def rotation_z(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def test_three_real_paths_conserve_axial_wavevector_and_snell(scene):
    for beta, path_scene, radius in zip(scene.obliquities, scene.examples, scene.radii):
        r = path_scene.rotation
        np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)
        assert np.linalg.det(r) == pytest.approx(1)
        c_axis = r[:, 2]
        assert abs(c_axis[2]) < 1e-12
        assert c_axis @ scene.sun == pytest.approx(np.sin(np.radians(beta)))
        path = path_scene.path
        assert not path.sketch
        assert [event.face_number for event in path.events] == [3, 5]
        directions = np.diff(path.points, axis=0)
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        wavevectors = directions * np.array([1, F.optics.N, 1])[:, None]
        np.testing.assert_allclose(wavevectors @ c_axis, -np.sin(np.radians(beta)), atol=1e-12)
        for index, event in enumerate(path.events):
            face = path_scene.crystal.face(event.face_number)
            normal = path_scene.crystal.normal(face)
            np.testing.assert_allclose(np.cross(wavevectors[index + 1] - wavevectors[index], normal),
                                       0, atol=1e-12)
            q = path.points[event.point_index]
            vertices = path_scene.crystal.face_vertices(face)
            inward = np.cross(normal, np.roll(vertices, -1, axis=0) - vertices)
            assert np.min(np.sum(inward * (q - vertices), axis=1)) > 1e-4
        for face in path_scene.crystal.faces:
            normal = path_scene.crystal.normal(face)
            samples = path.points[1] + np.linspace(0, 1, 21)[:, None] * (path.points[2] - path.points[1])
            assert np.max((samples - path_scene.crystal.face_vertices(face)[0]) @ normal) < 1e-12
        # 图中有限晶体的追迹与另一条 LI 方向映射链路独立对照。
        np.testing.assert_allclose(path_scene.light_point, F.sky_point(r, scene.sun), atol=1e-12)
        body_wave = wavevectors @ r
        index_eff = np.linalg.norm(body_wave[1, :2]) / np.linalg.norm(body_wave[0, :2])
        n_eff, delta = F.optics.bravais(beta)
        assert index_eff == pytest.approx(n_eff, abs=1e-12)
        assert radius == pytest.approx(F.optics.spherical_distance(beta, delta), abs=1e-6)
    assert np.all(np.diff(scene.radii) > 0)
    np.testing.assert_allclose(scene.radii, [21.83929991, 27.62897990, 36.42648178], atol=1e-7)
    assert 0 < np.degrees(np.arcsin(scene.lower.light_point[2])) < F.SUN_HEIGHT


@pytest.mark.parametrize("branch", [-1, 1])
@pytest.mark.parametrize("beta", [-55.0, -40.0, 0.0, 40.0, 55.0])
def test_transverse_minimum_is_non_degenerate_column_fold(beta, branch):
    """固定轴下极小不自动保证聚焦：直接检验2D姿态→2D天空秩一与法向二阶项。"""
    sun = F.optics.unit_from(F.SUN_HEIGHT, 0)
    r = F.minimum_pose(beta, F.SUN_HEIGHT, branch)

    def image(yaw, spin):
        return F.sky_point(rotation_z(yaw) @ r @ rotation_z(spin), sun)

    eps = 1e-4
    x = image(0, 0)
    yaw_derivative = (image(eps, 0) - image(-eps, 0)) / (2 * eps)
    spin_derivative = (image(0, eps) - image(0, -eps)) / (2 * eps)
    spin_second = (image(0, eps) - 2 * x + image(0, -eps)) / eps**2
    assert np.linalg.norm(spin_derivative) < 2e-6
    assert np.linalg.norm(yaw_derivative) > 0.05
    normal_second = x @ np.cross(yaw_derivative, spin_second)
    assert abs(normal_second) > 0.05
    # 过同一临界姿态两侧，映射有向面积变号，而不是仅一阶导数偶然小。
    determinants = []
    for spin in (-1e-3, 1e-3):
        yaw_diff = (image(eps, spin) - image(-eps, spin)) / (2 * eps)
        spin_diff = (image(0, spin + eps) - image(0, spin - eps)) / (2 * eps)
        determinants.append(image(0, spin) @ np.cross(yaw_diff, spin_diff))
    assert determinants[0] * determinants[1] < 0


def test_fold_samples_have_finite_crystal_corridors():
    for branch in (-1, 1):
        for beta in np.linspace(-55, 55, 23):
            r = F.minimum_pose(float(beta), F.SUN_HEIGHT, branch)
            physical = F.traced_scene(F.minimum_sun_direction(float(beta)), r)
            assert not physical.path.sketch
            assert [event.face_number for event in physical.path.events] == [3, 5]
            np.testing.assert_allclose(physical.light_point, F.sky_point(r, physical.sun), atol=1e-12)


def test_equal_distance_projection_has_true_radial_scale(scene):
    for radius in [0, *scene.radii, 50]:
        points = F.distance_circle(scene.sun, radius)
        xy = F.sky_projection(points, scene.sun)
        np.testing.assert_allclose(np.linalg.norm(xy, axis=1), radius, atol=2e-12)
    np.testing.assert_allclose(F.sky_projection(scene.sun, scene.sun), [0, 0], atol=1e-12)
    np.testing.assert_allclose(F.sky_projection(scene.upper.light_point, scene.sun),
                               [0, scene.radius], atol=1e-7)
    np.testing.assert_allclose(F.sky_projection(scene.lower.light_point, scene.sun),
                               [0, -scene.radius], atol=1e-7)


def test_actual_artists_share_physical_path_and_fold(scene, caplog):
    fig, data = F.make_figure()
    try:
        fig.canvas.draw()
        axes = {ax.get_label(): ax for ax in fig.axes}
        sky = axes["sky-directions"]
        by_gid = {line.get_gid(): line for line in sky.lines}
        for tag, physical in zip("ABC", data.examples):
            np.testing.assert_allclose(by_gid[f"example-{tag}"].get_xydata(),
                                       F.sky_projection(physical.light_point, data.sun)[None, :], atol=1e-12)
            ax = axes[f"prism-{tag}"]
            internal_ray = F.CAMERA.project_xy(physical.path.points[1:3])
            assert any(line.get_xydata().shape == internal_ray.shape
                       and np.allclose(line.get_xydata(), internal_ray, atol=1e-12) for line in ax.lines)
            section = next(line for line in axes[f"section-{tag}"].lines
                           if line.get_gid() == "transverse-ray")
            np.testing.assert_allclose(section.get_xydata(),
                                       (physical.path.points @ physical.rotation)[:, :2], atol=1e-12)
        for name, points, branch in zip(("upper", "lower"), data.folds, (-1, 1)):
            # 画出的整条线来自逐点光学映射，而不是三点样条或手填轮廓。
            np.testing.assert_allclose(by_gid[f"{name}-fold"].get_xydata(),
                                       F.sky_projection(points, data.sun), atol=1e-12)
            for index in range(0, len(points), 20):
                r = F.minimum_pose(float(data.fold_beta[index]), F.SUN_HEIGHT, branch)
                np.testing.assert_allclose(points[index], F.sky_point(r, data.sun), atol=1e-12)
        np.testing.assert_allclose(np.linalg.norm(by_gid["angular-distance-circle"].get_xydata(), axis=1),
                                   data.radius, atol=1e-12)
        assert F.CAMERA.projection == "perspective"
        assert "does not have a glyph" not in caplog.text
    finally:
        plt.close(fig)
