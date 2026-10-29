"""候选图 3c：实际着色场与最低点对 Bravais 闭式独立核验。"""
import numpy as np
import pytest

import fig_plate_terrain as F


def closed_minimum(h):
    h = np.radians(h)
    n_eff = np.sqrt(F.C.N**2 - np.sin(h)**2) / np.cos(h)
    if n_eff >= 2:
        return None
    delta = 2 * np.arcsin(n_eff / 2) - np.pi / 3
    return np.degrees(np.arccos(np.sin(h)**2 + np.cos(h)**2 * np.cos(delta)))


@pytest.mark.parametrize("h", F.HEIGHTS)
def test_displayed_minima_against_bravais(h):
    result = F.latitude_minimum(h)
    expected = closed_minimum(h)
    if expected is None:
        assert result is None
        return
    u, d = result
    assert abs(d - expected) < 1e-6
    assert abs(u[2] - np.sin(np.radians(h))) < 1e-12
    assert F.sphere_visible(u)
    # 实际数值极小点左右都不能有更低的值。
    az, _ = F.C.az_el(u)
    neighbors = F.C.dp(F.C.unit_from(h, az + np.array([-0.1, 0.1])))[0]
    assert np.all(neighbors >= d)
    x = F.C.light_point(u)[0]
    assert abs(x[2] - u[2]) < 1e-12


def test_terrain_pixels_and_global_minimum():
    x, y, u, d = F.terrain(301)
    radius = F.CAMERA.distance / np.sqrt(F.CAMERA.distance**2 - 1)
    inside = x*x + y*y <= radius**2
    np.testing.assert_allclose(np.linalg.norm(u[inside], axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(F.project(u[inside])[..., :2],
                               np.stack([x[inside], y[inside]], axis=-1), atol=1e-12)
    assert np.isnan(u[~inside]).all()
    # 独立几何检验：每个像素的世界像平面点、命中点、相机位置共线；
    # 近交点在像平面之前，射线方向随像素变化，不是正射后二维缩放。
    plane = x[..., None] * F.CAMERA.right + y[..., None] * F.CAMERA.cam_up
    to_hit = u[inside] - F.CAMERA.position
    to_plane = plane[inside] - F.CAMERA.position
    np.testing.assert_allclose(np.cross(to_hit, to_plane), 0, atol=1e-12)
    fraction = np.linalg.norm(to_hit, axis=1) / np.linalg.norm(to_plane, axis=1)
    assert np.all((fraction > 0) & (fraction < 1))
    assert np.ptp(to_hit @ F.CAMERA.right) > 1
    assert F.sphere_visible(u[inside]).all()
    # 每个着色像素确实取自同一 Φ 的定义域，不向域外补色。
    expected, light = F.C.dp(u[inside])
    np.testing.assert_allclose(d[inside], expected, equal_nan=True)
    assert np.isnan(d[~inside]).all()
    assert 0.1 < np.isfinite(d).mean() < 0.7
    lower = np.degrees(2 * np.arcsin(F.C.N / 2)) - 60
    assert lower - 1e-9 <= np.nanmin(d) < lower + 0.02
    # 独立 Snell 不变量：两界面都包含 c 轴，k_z 入/出必须一致。
    ok = np.isfinite(expected)
    np.testing.assert_allclose(light[ok, 2], u[inside][ok, 2], atol=1e-12)


def test_above_critical_latitude_empty_and_domain_visible():
    hc = np.degrees(np.arcsin(np.sqrt((4 - F.C.N**2) / 3)))
    assert F.HEIGHTS[-2] == pytest.approx(hc)
    assert hc < F.HEIGHTS[-1]
    assert F.latitude_minimum(hc + 0.01) is None
    # 此取景确实包含完整光学域；不能靠背面遮挡隐藏另一块可行方向。
    el, az = np.meshgrid(np.arange(-90, 91, 1), np.arange(0, 360, 1), indexing="ij")
    u = F.C.unit_from_grid(el.ravel(), az.ravel())
    d, _ = F.C.dp(u)
    assert F.sphere_visible(u[np.isfinite(d)]).all()


@pytest.mark.parametrize("distance,roll", [(3.0, 23.0), (8.0, 0.0)])
def test_inverse_projection_from_known_surface_points(distance, roll):
    camera = F.Camera(azimuth=137, elevation=-21, distance=distance, roll=roll)
    # 先构造已知球面点；独立用直线与原点像平面相交，不调用被测 project。
    depths = np.array([0.4, 0.6, 0.9, 1.0])
    angles = np.array([0.1, 1.7, 3.8, 0.0])
    ring = (np.cos(angles)[:, None] * camera.right
            + np.sin(angles)[:, None] * camera.cam_up)
    expected = (depths[:, None] * camera.view_dir
                + np.sqrt(1 - depths**2)[:, None] * ring)
    rays = expected - camera.position
    t = -(camera.position @ camera.view_dir) / (rays @ camera.view_dir)
    plane = camera.position + t[:, None] * rays
    xy = np.column_stack([plane @ camera.right, plane @ camera.cam_up])
    np.testing.assert_allclose(F.sphere_hit(*xy.T, camera), expected, atol=1e-12)
    np.testing.assert_allclose(F.project(expected, camera)[:, :2], xy, atol=1e-12)


def test_depth_scaling_is_camera_perspective():
    camera = F.CAMERA
    assert isinstance(camera, F.Camera)
    assert camera.projection == "perspective"
    # 两段同长横杆，仅深度不同；比例必须来自各自到相机的距离。
    depths = np.array([-0.6, 0.6])
    bars = (depths[:, None, None] * camera.view_dir
            + np.array([-0.3, 0.3])[None, :, None] * camera.right)
    q = F.project(bars)
    widths = q[:, 1, 0] - q[:, 0, 0]
    expected = 0.6 * camera.distance / (camera.distance - depths)
    np.testing.assert_allclose(widths, expected, atol=1e-12)
    assert widths[1] / widths[0] > 1.15
    np.testing.assert_allclose(q[..., 2], np.broadcast_to(depths[:, None], (2, 2)))


def test_occlusion_selects_near_root_and_masks_curves():
    camera = F.CAMERA
    near, far = [], []
    # np.roots 独立求二次多项式的两根；两点同像素，但远交点必须遮挡。
    for x, y in [(0.0, 0.0), (0.4, -0.3), (0.8, 0.2)]:
        ray = x * camera.right + y * camera.cam_up - camera.position
        roots = np.sort(np.roots([ray @ ray, 2 * ray @ camera.position,
                                  camera.position @ camera.position - 1]))
        hits = camera.position + roots[:, None] * ray
        np.testing.assert_allclose(F.sphere_hit(x, y), hits[0], atol=1e-12)
        np.testing.assert_allclose(F.project(hits)[:, :2], [[x, y], [x, y]], atol=1e-12)
        near.append(hits[0])
        far.append(hits[1])
    assert F.sphere_visible(near).all()
    assert not F.sphere_visible(far).any()
    # 正射的前半球边缘在透视下已被遮住：仅看 depth 符号会误画。
    z = 0.5 / camera.distance
    hidden_front = z * camera.view_dir + np.sqrt(1 - z*z) * camera.right
    assert F.project(hidden_front)[2] > 0
    assert not F.sphere_visible(hidden_front)
    points = np.vstack([near[1], far[1], hidden_front, near[2]])
    fig, ax = F.plt.subplots()
    try:
        line, = F.visible_curve(ax, points)
        xy = line.get_xydata()
        assert np.isnan(xy[[1, 2]]).all()
        np.testing.assert_allclose(xy[[0, 3]], [[0.4, -0.3], [0.8, 0.2]], atol=1e-12)
    finally:
        F.plt.close(fig)


def test_silhouette_rays_are_tangent_and_match_raster_boundary():
    camera = F.CAMERA
    rim = F.silhouette()
    np.testing.assert_allclose(np.linalg.norm(rim, axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(np.sum(rim * (camera.position - rim), axis=1),
                               0, atol=1e-12)
    xy = F.project(rim)[:, :2]
    radius = camera.distance / np.sqrt(camera.distance**2 - 1)
    np.testing.assert_allclose(np.linalg.norm(xy, axis=1), radius, atol=1e-12)
    np.testing.assert_allclose(F.sphere_hit(*xy.T), rim, atol=2e-7)
    assert np.isfinite(F.sphere_hit(*(xy * 0.999).T)).all()
    assert np.isnan(F.sphere_hit(*(xy * 1.001).T)).all()
    x, y, _, _ = F.terrain(101)
    # imshow 的 extent 是像素外边缘；contour 使用相同像素中心，不能差半格。
    step = x[0, 1] - x[0, 0]
    np.testing.assert_allclose([x[0, 0] - step/2, y[-1, 0] + step/2],
                               [-radius, radius], atol=1e-12)


@pytest.mark.parametrize("style", F.RAMPS)
def test_distance_ramps_monotonically_darken(style):
    rgb = F.distance_cmap(style)(np.linspace(0, 1, 256))[:, :3]
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055)**2.4)
    luminance = linear @ np.array([0.2126, 0.7152, 0.0722])
    assert np.all(np.diff(luminance) < 0)
    assert luminance[0] - luminance[-1] > 0.5
    if style != "original":
        with pytest.raises(ValueError, match="输出路径"):
            F.main(style)
