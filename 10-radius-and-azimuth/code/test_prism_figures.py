"""图 4/6：核验实际绘图光路、姿态、投影及 Matplotlib 图元，不以图注自证。"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

import fig_bravais_prism as bravais
import fig_tangent_direction as tangent


TOL = 2e-9


def assert_physical_path(scene):
    """不调用追迹器的 refract/verify_path：直接检查界面切向守恒与凸体半空间。"""
    path, crystal = scene.path, scene.crystal
    assert not path.sketch
    assert [event.face_number for event in path.events] == [3, 5]
    segments = np.diff(path.points, axis=0)
    directions = segments / np.linalg.norm(segments, axis=1, keepdims=True)
    k = directions * np.array([1.0, bravais.optics.N, 1.0])[:, None]
    np.testing.assert_allclose(scene.wavevectors, k, atol=TOL)
    np.testing.assert_allclose(directions[0], -scene.sun, atol=TOL)
    np.testing.assert_allclose(scene.light_point, -directions[-1], atol=TOL)
    for i, event in enumerate(path.events):
        face = crystal.face(event.face_number)
        normal = crystal.normal(face)
        q = path.points[event.point_index]
        vertices = crystal.face_vertices(face)
        assert abs((q - vertices[0]) @ normal) < TOL
        # 事件点严格在面多边形内，不仅仅在无限延伸的平面上。
        inward = np.cross(normal, np.roll(vertices, -1, axis=0) - vertices)
        assert np.min(np.sum(inward * (q - vertices), axis=1)) > 1e-4
        residual = np.cross(k[i + 1] - k[i], normal)
        np.testing.assert_allclose(residual, 0, atol=TOL)
        assert directions[i] @ normal < 0 if i == 0 else directions[i + 1] @ normal > 0
    # 内部整段必须在有限晶体内；凸性 + 各个半空间保证不是假穿越。
    samples = path.points[1] + np.linspace(0, 1, 51)[:, None] * (path.points[2] - path.points[1])
    for face in crystal.faces:
        signed = (samples - crystal.face_vertices(face)[0]) @ crystal.normal(face)
        assert np.max(signed) < TOL
    return directions, k


@pytest.mark.parametrize("height", [0.0, 20.0, bravais.SUN_HEIGHT])
def test_bravais_tangent_conservation_and_same_sky_height(height):
    scene = bravais.build_scene(height)
    directions, k = assert_physical_path(scene)
    np.testing.assert_allclose(k[:, 2], -np.sin(np.radians(height)), atol=TOL)
    # 守恒的是 n*d_z；冰内单位方向的竖直分量并不等于空气中的值。
    if height:
        assert abs(directions[1, 2] - directions[0, 2]) > 0.07
    sky_height = np.degrees(np.arctan2(scene.light_point[2], np.linalg.norm(scene.light_point[:2])))
    assert sky_height == pytest.approx(height, abs=1e-9)
    n_eff = np.linalg.norm(k[1, :2]) / np.linalg.norm(k[0, :2])
    expected_index, expected_azimuth = bravais.optics.bravais(height)
    assert n_eff == pytest.approx(expected_index, abs=TOL)
    assert n_eff >= bravais.optics.N - TOL
    # 再独立在水平截面核验 Snell：sin(alpha)=n' sin(beta)，出射面反向亦然。
    xy_directions = directions[:, :2] / np.linalg.norm(directions[:, :2], axis=1, keepdims=True)
    for i, face_number in enumerate((3, 5)):
        normal = scene.crystal.normal(scene.crystal.face(face_number))[:2]
        normal /= np.linalg.norm(normal)
        tangent_direction = np.array([-normal[1], normal[0]])
        indices = [1.0, n_eff, 1.0]
        assert indices[i] * (xy_directions[i] @ tangent_direction) == pytest.approx(
            indices[i + 1] * (xy_directions[i + 1] @ tangent_direction), abs=TOL
        )
    actual_azimuth = np.degrees(np.arccos(np.clip(xy_directions[0] @ xy_directions[-1], -1, 1)))
    assert actual_azimuth == pytest.approx(expected_azimuth, abs=1e-6)
    # 同一入射方向经 LI 的 phi（而非绘图追迹）得到同一光点。
    np.testing.assert_allclose(scene.light_point, bravais.optics.light_point(scene.sun)[0], atol=TOL)


def test_column_real_attitudes_and_independent_sky_directions():
    data = tangent.build_scene()
    expected_radius = 2 * np.degrees(np.arcsin(bravais.optics.N / 2)) - 60
    for sign, scene in ((1, data.upper), (-1, data.lower)):
        directions, _ = assert_physical_path(scene)
        r = scene.rotation
        np.testing.assert_allclose(r.T @ r, np.eye(3), atol=TOL)
        assert np.linalg.det(r) == pytest.approx(1)
        c_axis = r[:, 2]
        assert abs(c_axis[2]) < TOL  # 水平柱晶
        assert abs(c_axis @ data.sun) < TOL  # 垂直太阳方位
        np.testing.assert_allclose(scene.path.points @ c_axis, 0, atol=TOL)
        np.testing.assert_allclose(directions @ c_axis, 0, atol=TOL)
        # 唯一光学函数的独立链路，实际 R，不用声明的“上 / 下”标签。
        optical_point = r @ bravais.optics.light_point(r.T @ data.sun)[0]
        np.testing.assert_allclose(scene.light_point, optical_point, atol=TOL)
        x = scene.light_point
        distance = np.degrees(np.arctan2(np.linalg.norm(np.cross(x, data.sun)), x @ data.sun))
        azimuth = np.degrees(np.arctan2(x[1], x[0]))
        elevation = np.degrees(np.arctan2(x[2], np.hypot(x[0], x[1])))
        assert distance == pytest.approx(expected_radius, abs=1e-6)
        assert azimuth == pytest.approx(0, abs=1e-7)
        assert elevation == pytest.approx(tangent.SUN_HEIGHT + sign * expected_radius, abs=1e-6)
    # 此取景的下切点确实在地平线下，不应把它画为可见亮弧。
    assert data.lower.light_point[2] < 0 < data.upper.light_point[2]
    np.testing.assert_allclose(data.circle @ data.sun, np.cos(np.radians(expected_radius)), atol=TOL)


def by_gid(ax, gid):
    return next(line for line in ax.lines if line.get_gid() == gid)


def assert_drawn_internal_ray(ax, scene, camera):
    projected = camera.project_xy(scene.path.points[1:3])
    assert any(np.asarray(line.get_xydata()).shape == projected.shape
               and np.allclose(line.get_xydata(), projected, atol=TOL) for line in ax.lines)
    # 实际多边形顶点也必须来自同一透视相机，而非一套正射数据加上透视射线。
    for face in scene.crystal.faces:
        projected = camera.project_xy(scene.crystal.face_vertices(face))
        candidates = [patch.get_xy()[:-1] for patch in ax.patches if hasattr(patch, "get_xy")]
        if any(p.shape == projected.shape and np.allclose(p, projected, atol=TOL) for p in candidates):
            return
    pytest.fail("No crystal face used the physical perspective camera")


def test_figure4_artists_are_the_verified_path(caplog):
    fig, scene = bravais.make_figure()
    try:
        fig.canvas.draw()
        axes = {ax.get_label(): ax for ax in fig.axes}
        actual = by_gid(axes["horizontal-section"], "projected-ray").get_xydata()
        expected = scene.path.points[:, :2] @ bravais.SECTION_BASIS.T
        np.testing.assert_allclose(actual, expected, atol=TOL)
        assert_drawn_internal_ray(axes["prism-3d"], scene, bravais.CAMERA)
        vectors = [line.get_xydata() for line in axes["wavevector-components"].lines
                   if line.get_gid() == "wavevector"]
        assert len(vectors) == 3
        for vector, k in zip(vectors, scene.wavevectors):
            np.testing.assert_allclose(vector[1] - vector[0], [np.linalg.norm(k[:2]), k[2]], atol=TOL)
        assert "does not have a glyph" not in caplog.text
    finally:
        plt.close(fig)


def test_figure6_artists_are_actual_sky_points_not_arcs(caplog):
    fig, data = tangent.make_figure()
    try:
        fig.canvas.draw()
        axes = {ax.get_label(): ax for ax in fig.axes}
        sky = axes["sky-directions"]
        assert_drawn_internal_ray(axes["upper-prism"], data.upper, tangent.CAMERA)
        assert_drawn_internal_ray(axes["lower-prism"], data.lower, tangent.CAMERA)
        for gid, scene in (("upper-tangent", data.upper), ("lower-tangent", data.lower)):
            point = by_gid(sky, gid)
            assert point.get_linestyle() == "None"
            assert len(point.get_xydata()) == 1
            az, el = np.radians(point.get_xydata()[0])
            x = [np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)]
            np.testing.assert_allclose(x, scene.light_point, atol=TOL)
        lower = by_gid(sky, "lower-tangent")
        assert lower.get_markerfacecolor() == tangent.PAPER
        # 屏幕圆线的每个点反算回单位球；不拿纸面欧氏距离当角距离。
        az, el = np.radians(by_gid(sky, "angular-distance-circle").get_xydata()).T
        vectors = np.column_stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        np.testing.assert_allclose(vectors, data.circle, atol=TOL)
        np.testing.assert_allclose(vectors @ data.sun, np.cos(np.radians(data.radius)), atol=TOL)
        assert "does not have a glyph" not in caplog.text
    finally:
        plt.close(fig)


@pytest.mark.parametrize("camera", [bravais.CAMERA, tangent.CAMERA])
def test_camera_really_has_depth_scaling(camera):
    assert camera.projection == "perspective"
    near = camera.right + camera.view_dir
    far = camera.right - camera.view_dir
    near_xy, far_xy = camera.project_xy([near, far])
    assert near_xy[0] / far_xy[0] == pytest.approx((camera.distance + 1) / (camera.distance - 1))
    assert near_xy[0] > far_xy[0]
    # 从同一个相机点出发的视线投影到同一点，和正射相机失败模式不同。
    point = np.array([0.2, 0.3, 0.4])
    farther = camera.position + 1.3 * (point - camera.position)
    np.testing.assert_allclose(camera.project_xy(point), camera.project_xy(farther), atol=TOL)
