"""局部坐标必须忠实表示实际姿态族；整环与半环不能混为一谈。"""
import numpy as np

import fig_parry_neighborhood as F


def test_local_families_and_shared_parry_circle():
    for phi in (0, 37, 180, 359):
        for a in (-23, 0, 23):
            for b in (-23, 0, 23):
                r = F.local_attitude(phi, a, b)
                # 独立体轴约束，而非只对照参数标签。
                assert (abs(r[2, 2]) < 1e-12) == (a == 0)
                assert (abs(r[2, 1]) < 1e-12) == (b == 0)
                np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)
                if a == b == 0:
                    np.testing.assert_allclose(r[:, 0], [0, 0, 1], atol=1e-12)
                if a == 0:
                    np.testing.assert_allclose(r, F.C.column_attitude(phi + 180, 180 + b), atol=1e-12)
                if b == 0:
                    np.testing.assert_allclose(r, F.lowitz_attitude(phi, a - 90), atol=1e-12)
        np.testing.assert_allclose(F.local_attitude(phi + 360, 12, 18),
                                   F.local_attitude(phi, 12, 18), atol=1e-12)
        np.testing.assert_allclose(F.local_model(phi + 360, 12, 18),
                                   F.local_model(phi, 12, 18), atol=1e-12)


def test_local_chart_is_nonsingular_but_does_not_reach_plate():
    limit = np.degrees(F.WIDTH)
    assert limit < 90
    for phi in (0, 83, 270):
        for a in (-limit, 0, limit):
            for b in (-limit, 0, limit):
                j = F.C.body_jacobian(
                    lambda x: F.local_attitude(*np.degrees(x)), np.radians([phi, a, b])
                )
                assert np.linalg.matrix_rank(j, tol=1e-6) == 3
                assert abs(np.linalg.det(j)) > 0.8
                assert abs(F.local_attitude(phi, a, b)[2, 2]) < 0.5


def test_full_lowitz_two_circles_and_half_one_circle():
    t = np.arange(-180, 180, 0.5)
    for phi in (0, 37, 183):
        r = np.stack([F.lowitz_attitude(phi, angle) for angle in t])
        intersections = t[np.abs(r[:, 2, 2]) < 1e-12]
        np.testing.assert_array_equal(intersections, [-90, 90])
        np.testing.assert_array_equal(intersections[(intersections >= -180) & (intersections <= 0)], [-90])
        np.testing.assert_allclose(F.lowitz_attitude(phi, 0)[:, 2], [0, 0, 1], atol=1e-12)
        np.testing.assert_allclose(F.lowitz_attitude(phi, -180), F.lowitz_attitude(phi, 180), atol=1e-12)
        # 原始两交圈不是同一圈；右乘群元素后才属于同一物理族。
        a = F.lowitz_attitude(phi, -90)
        b = F.lowitz_attitude(phi + 180, 90)
        assert np.linalg.norm(a - b) > 2
        assert F.C.d6_index(a.T @ b) is not None
        assert F.C.d6_index(F.lowitz_attitude(phi, 0).T @ a) is None


def test_rendered_surfaces_match_the_local_coordinate_chart():
    image, xyz, is_column = F.neighborhood_pixels(301)
    assert np.isfinite(image).all() and 0 <= image.min() <= image.max() <= 1
    radial = np.linalg.norm(xyz[:, :2], axis=1)
    np.testing.assert_allclose(radial[is_column], F.RADIUS, atol=1e-12)
    np.testing.assert_allclose(xyz[~is_column, 2], 0, atol=1e-12)
    assert np.max(np.abs(xyz[is_column, 2])) <= F.WIDTH + 1e-12
    assert np.max(np.abs(radial[~is_column] - F.RADIUS)) <= F.WIDTH + 1e-12
    assert is_column.sum() > 1000 and (~is_column).sum() > 1000
    # 从实际成图的命中点反解参数，再检查世界坐标中的体轴条件。
    for point, column in zip(xyz[::277], is_column[::277]):
        phi = np.degrees(np.arctan2(point[1], point[0]))
        a = np.degrees(np.linalg.norm(point[:2]) - F.RADIUS)
        b = np.degrees(point[2])
        r = F.local_attitude(phi, a, b)
        assert abs(r[2, 2 if column else 1]) < 1e-12
