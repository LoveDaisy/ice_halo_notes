"""径向剖切：切口只删除面片，交圈完整、切边与遮挡独立核验。"""
import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial import Polynomial
import pytest

import fig_intersecting_tori as F
import fig_tori_section as S


def test_default_is_author_selected_staggered(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(S, 'draw_scene', lambda ax, variant, width: seen.append(variant))
    S.main(tmp_path / 'default.png')
    assert S.DEFAULT_VARIANT == 'staggered'
    assert seen == ['staggered']


def inside_sector(kind, points, variant):
    # 角度区间判据独立于渲染所用半空间距离。
    azimuth = np.arctan2(points[..., 1], points[..., 0])
    relative = (azimuth - F.AZ + np.pi) % (2 * np.pi) - np.pi
    start, end = np.radians(S.CUTS[variant][kind])
    return (relative > start + 1e-10) & (relative < end - 1e-10)


def analytic_depth(origin, kind, variant):
    # 全四次根解独立于 sphere tracing；不调用被测的切口函数。
    x, y, z = [Polynomial([a, -b]) for a, b in zip(origin, F.EYE)]
    q = x*x + y*y + z*z + F.MAJOR[kind]**2 - F.MINOR**2
    roots = (q*q - 4 * F.MAJOR[kind]**2 * (x*x + y*y)).roots()
    roots = sorted(r.real for r in roots if abs(r.imag) < 1e-8 and r.real >= 0)
    return next((d for d in roots if not inside_sector(kind, origin - d*F.EYE, variant)), np.inf)


@pytest.mark.parametrize('variant', S.CUTS)
def test_cuts_match_angular_sectors_and_edges_are_real_mother_circles(variant):
    rng = np.random.default_rng(486)
    for kind in (F.LOWITZ, F.COLUMN):
        points = F.surface(kind, rng.uniform(-np.pi, np.pi, 1000), rng.uniform(-np.pi, np.pi, 1000))
        np.testing.assert_array_equal(S.cutter_for(variant)(kind, points) > 0,
                                      inside_sector(kind, points, variant))
        for phi in S.cut_angles(kind, variant):
            edge = F.surface(kind, phi, np.linspace(-np.pi, np.pi, 91))
            np.testing.assert_allclose(S.cutter_for(variant)(kind, edge), 0, atol=1e-14)
            radial = np.hypot(edge[:, 0], edge[:, 1])
            np.testing.assert_allclose((radial-F.MAJOR[kind])**2 + edge[:, 2]**2, F.MINOR**2)
            np.testing.assert_allclose(edge @ [-np.sin(phi), np.cos(phi), 0], 0, atol=1e-14)


def test_intersection_curves_are_complete_and_same_attitudes_on_both_surfaces():
    for sign in (-1, 1):
        points = S.circle_points(sign)
        np.testing.assert_allclose(points[0], points[-1], atol=1e-12)
        phi = np.unwrap(np.arctan2(points[:, 1], points[:, 0]))
        np.testing.assert_allclose(phi[-1] - phi[0], 2 * np.pi)
        for kind in (F.LOWITZ, F.COLUMN):
            np.testing.assert_allclose(F.torus_distance(kind, points), 0, atol=1e-12)
        for point in points[::79]:
            rotations = [F.attitude(kind, *F.parameters(kind, point)) for kind in (F.LOWITZ, F.COLUMN)]
            np.testing.assert_allclose(*rotations, atol=1e-12)
            assert abs(rotations[0][2, 1]) < 1e-12
            assert abs(rotations[0][2, 2]) < 1e-12


@pytest.mark.parametrize('variant', S.CUTS)
def test_new_cut_ray_hits_match_all_roots_without_phantom_caps(variant):
    rng = np.random.default_rng(749)
    xy = rng.uniform([-3.6, -1.9], [3.6, 1.9], (160, 2))
    origins = xy[:, :1] * F.RIGHT + xy[:, 1:] * F.UP + 8 * F.EYE
    for kind in (F.LOWITZ, F.COLUMN):
        expected = np.array([analytic_depth(o, kind, variant) for o in origins])
        actual = F.trace(origins, kind, S.cutter_for(variant))
        np.testing.assert_array_equal(np.isfinite(actual), np.isfinite(expected))
        keep = np.isfinite(expected)
        np.testing.assert_allclose(actual[keep], expected[keep], rtol=0, atol=0.001)
        points = origins[keep] - actual[keep, None] * F.EYE
        assert np.max(np.abs(F.torus_distance(kind, points))) < 2e-5


@pytest.mark.parametrize('variant', S.CUTS)
def test_visible_curve_masks_match_independent_occlusion_and_retain_both_rings(variant):
    cutter = S.cutter_for(variant)
    for sign in (-1, 1):
        points = S.circle_points(sign)
        depth = 8 - F.project(points)[:, 2]
        origins = points + depth[:, None] * F.EYE
        nearest = np.array([min(analytic_depth(o, kind, variant) for kind in (F.LOWITZ, F.COLUMN))
                            for o in origins])
        expected = depth <= nearest + 0.002
        actual = S.line_visibility(points, cutter)
        np.testing.assert_array_equal(actual, expected)
        removed = inside_sector(F.LOWITZ, points, variant) & inside_sector(F.COLUMN, points, variant)
        assert np.count_nonzero(actual & removed) > 20
        assert np.count_nonzero(actual & ~removed) > 20
        if sign == -1:
            assert np.count_nonzero(~actual) > 0


@pytest.mark.parametrize('variant', S.CUTS)
def test_cut_edge_visibility_matches_independent_all_roots(variant):
    for kind in (F.LOWITZ, F.COLUMN):
        for phi in S.cut_angles(kind, variant):
            points = F.surface(kind, phi, np.linspace(-np.pi, np.pi, 181))
            depth = 8 - F.project(points)[:, 2]
            origins = points + depth[:, None] * F.EYE
            nearest = np.array([min(analytic_depth(o, k, variant) for k in (F.LOWITZ, F.COLUMN))
                                for o in origins])
            np.testing.assert_array_equal(S.line_visibility(points, S.cutter_for(variant)),
                                          depth <= nearest + 0.002)


@pytest.mark.parametrize('variant', S.CUTS)
def test_surface_pixels_stay_on_retained_faces_and_in_their_physical_families(variant):
    image, xyz, kinds = F.surface_pixels(241, S.cutter_for(variant))
    assert np.isfinite(image).all() and 0 <= image.min() <= image.max() <= 1
    for kind in (F.LOWITZ, F.COLUMN):
        points = xyz[kinds == kind]
        assert len(points) > 500
        assert np.max(np.abs(F.torus_distance(kind, points))) < 2e-5
        assert np.max(S.cutter_for(variant)(kind, points)) < 2e-5
        for point in points[::101]:
            rotation = F.attitude(kind, *F.parameters(kind, point))
            assert abs(rotation[2, 1 if kind == F.LOWITZ else 2]) < 1e-12


def test_section_inset_uses_actual_surface_circles_and_intersections():
    fig, ax = plt.subplots()
    S.draw_section(ax)
    for kind, line in enumerate(ax.lines):
        r, z = line.get_data()
        np.testing.assert_allclose((r-F.MAJOR[kind])**2 + z**2, F.MINOR**2)
    for collection, sign in zip(ax.collections, (1, -1)):
        point = np.asarray(collection.get_offsets())[0]
        np.testing.assert_allclose(point, [F.CROSS_R, sign * F.CROSS_Z])
        for major in F.MAJOR:
            np.testing.assert_allclose((point[0]-major)**2 + point[1]**2, F.MINOR**2)
    plt.close(fig)
