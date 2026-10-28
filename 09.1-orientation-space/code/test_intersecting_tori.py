"""图 3 扩展候选：姿态约束独立于显示环面，切口/遮挡也须核验。"""
import numpy as np
from numpy.polynomial import Polynomial
from scipy.spatial.transform import Rotation

import fig_intersecting_tori as F


def test_display_intersections_are_exactly_two_uncut_circles():
    # 两个母圆方程相减得到唯一半径；再代入得到 ±z，不能凭标签指定交线。
    r = (F.MAJOR[0]**2 - F.MAJOR[1]**2) / (2 * (F.MAJOR[0] - F.MAJOR[1]))
    z = np.sqrt(F.MINOR**2 - (r - F.MAJOR[0])**2)
    np.testing.assert_allclose([r, z], [F.CROSS_R, F.CROSS_Z])
    phi = np.linspace(-np.pi, np.pi, 361)
    for sign in (-1, 1):
        points = F.surface(F.LOWITZ, phi, sign * F.CROSS_ANGLE[F.LOWITZ])
        np.testing.assert_allclose(points, F.surface(F.COLUMN, phi, sign * F.CROSS_ANGLE[F.COLUMN]), atol=1e-12)
        for kind in (F.LOWITZ, F.COLUMN):
            np.testing.assert_allclose(F.torus_distance(kind, points), 0, atol=1e-12)
            assert np.max(F.cut_distance(kind, points)) < -0.05


def test_both_display_surfaces_map_to_same_physical_intersections():
    for sign in (-1, 1):
        for phi in np.linspace(-np.pi, np.pi, 39):
            a = F.attitude(F.LOWITZ, phi, sign * F.CROSS_ANGLE[F.LOWITZ])
            b = F.attitude(F.COLUMN, phi, sign * F.CROSS_ANGLE[F.COLUMN])
            np.testing.assert_allclose(a, b, atol=1e-12)
            # 世界中的两条水平体轴必使第三条竖直；不是显示面的相交判据。
            np.testing.assert_allclose(a[:, 0], [0, 0, -sign], atol=1e-12)
            assert abs(a[2, 1]) < 1e-12 and abs(a[2, 2]) < 1e-12
            np.testing.assert_allclose(a.T @ a, np.eye(3), atol=1e-12)
            assert abs(np.linalg.det(a) - 1) < 1e-12


def test_independent_rotation_samples_have_only_those_two_branches():
    # 不调用显示参数化；SciPy 生成物理族，并对随机非格点采样查体轴约束。
    rng = np.random.default_rng(734)
    angles = np.r_[rng.uniform(-180, 180, 181), -90, 90]
    zeros = []
    for t in angles:
        phi = rng.uniform(0, 360)
        r = Rotation.from_euler('ZY', [phi, t], degrees=True).as_matrix()
        assert abs(r[2, 1]) < 1e-12
        np.testing.assert_allclose(r[2, 2], np.cos(np.radians(t)), atol=1e-12)
        if abs(r[2, 2]) < 1e-12:
            zeros.append(t)
            np.testing.assert_allclose(abs(r[2, 0]), 1, atol=1e-12)
    assert zeros == [-90, 90]
    assert [t for t in zeros if -180 <= t <= 0] == [-90]
    # 从柱晶一侧反查，避免只证明两圈是交集的子集。
    for theta in np.r_[rng.uniform(0, 360, 181), 0, 180]:
        r = Rotation.from_euler('ZYZ', [rng.uniform(0, 360), 90, theta], degrees=True).as_matrix()
        assert abs(r[2, 2]) < 1e-12
        np.testing.assert_allclose(r[2, 1], np.sin(np.radians(theta)), atol=1e-12)
        assert (abs(r[2, 1]) < 1e-12) == (theta in (0, 180))


def test_plate_disjoint_and_d6_identification_is_not_raw_equality():
    for phi in np.linspace(0, 2 * np.pi, 29):
        plate = F.attitude(F.LOWITZ, phi, 0)
        minus = F.attitude(F.LOWITZ, phi, -F.CROSS_ANGLE[F.LOWITZ])
        plus = F.attitude(F.LOWITZ, phi + np.pi, F.CROSS_ANGLE[F.LOWITZ])
        np.testing.assert_allclose(plate[:, 2], [0, 0, 1], atol=1e-12)
        assert np.linalg.norm(minus - plus) > 2
        np.testing.assert_allclose(minus @ np.diag([-1, -1, 1]), plus, atol=1e-12)
        assert F.N.C.d6_index(minus.T @ plus) is not None
        assert F.N.C.d6_index(plate.T @ minus) is None
    for kind in (F.LOWITZ, F.COLUMN):
        for angle in np.linspace(-np.pi, np.pi, 21):
            np.testing.assert_allclose(F.attitude(kind, 0, angle), F.attitude(kind, 2*np.pi, angle), atol=1e-12)
            np.testing.assert_allclose(F.attitude(kind, 0, angle), F.attitude(kind, 0, angle+2*np.pi), atol=1e-12)


def test_visible_hit_points_are_retained_surfaces_and_correct_families():
    image, xyz, kinds = F.surface_pixels(301)
    assert np.isfinite(image).all() and 0 <= image.min() <= image.max() <= 1
    for kind in (F.LOWITZ, F.COLUMN):
        points = xyz[kinds == kind]
        assert len(points) > 1000
        assert np.max(np.abs(F.torus_distance(kind, points))) < 2e-5
        assert np.max(F.cut_distance(kind, points)) < 2e-5
        for point in points[::197]:
            phi, angle = F.parameters(kind, point)
            r = F.attitude(kind, phi, angle)
            assert abs(r[2, 1 if kind == F.LOWITZ else 2]) < 1e-12
    # 实际可见像素必须包含上下两条强调圈，不能只算出了却被完全遮住。
    for sign in (-1, 1):
        distance = np.hypot(np.hypot(xyz[:, 0], xyz[:, 1]) - F.CROSS_R,
                            xyz[:, 2] - sign * F.CROSS_Z)
        assert np.count_nonzero(distance < 0.025) > 80


def analytic_depth(origin, kind):
    """独立四次多项式求所有射线/完整环面交点，再滤掉切口。"""
    x, y, z = [Polynomial([a, -b]) for a, b in zip(origin, F.EYE)]
    q = x*x + y*y + z*z + F.MAJOR[kind]**2 - F.MINOR**2
    roots = (q*q - 4 * F.MAJOR[kind]**2 * (x*x + y*y)).roots()
    roots = sorted(root.real for root in roots if abs(root.imag) < 1e-8 and root.real >= 0)
    return next((d for d in roots if F.cut_distance(kind, origin - d * F.EYE) <= 0), np.inf)


def test_ray_marching_matches_independent_all_root_occlusion():
    rng = np.random.default_rng(369)
    xy = rng.uniform([-3.6, -2.0], [3.6, 2.0], (96, 2))
    origins = xy[:, :1] * F.RIGHT + xy[:, 1:] * F.UP + 8 * F.EYE
    for kind in (F.LOWITZ, F.COLUMN):
        actual = F.trace(origins, kind)
        expected = np.array([analytic_depth(o, kind) for o in origins])
        np.testing.assert_array_equal(np.isfinite(actual), np.isfinite(expected))
        keep = np.isfinite(expected)
        np.testing.assert_allclose(actual[keep], expected[keep], atol=0.001, rtol=0)


def test_leader_targets_are_visible_not_hidden_backside():
    for kind, phi, angle, *_ in F.LEADERS:
        p = F.surface(kind, phi, angle)
        depth = 8 - F.project(p)[2]
        origin = p + depth * F.EYE
        nearest = min(analytic_depth(origin, k) for k in (F.LOWITZ, F.COLUMN))
        np.testing.assert_allclose(nearest, depth, atol=1e-7)
