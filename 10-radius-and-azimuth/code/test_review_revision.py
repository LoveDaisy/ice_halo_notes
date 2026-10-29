"""图2/3c/3d/7的本轮生成路径：临界闭包不当透射、带宽与实际图元。"""
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pytest

import _terrain_layers as L
import fig_plate_terrain as T
import fig_solar_circle as S
import fig_column_sky as K


def test_critical_contact_is_double_grazing_limit():
    u = T.critical_contact()
    n1 = T.C.CRYSTAL.normal(T.C.CRYSTAL.face(3))
    n2 = T.C.CRYSTAL.normal(T.C.CRYSTAL.face(5))
    assert np.linalg.norm(u) == pytest.approx(1)
    assert u @ n1 == pytest.approx(0, abs=1e-12)
    assert np.degrees(np.arcsin(u[2])) == pytest.approx(T.C.critical_height())
    # 独立用界面波矢切向连续构造掠入、掠出极限，不靠phi接受边界点。
    internal = -u - np.sqrt(T.C.N**2-1)*n1
    outgoing = internal - (internal @ n2)*n2
    assert np.linalg.norm(internal) == pytest.approx(T.C.N)
    assert np.linalg.norm(outgoing) == pytest.approx(1)
    assert outgoing @ n2 == pytest.approx(0, abs=1e-12)
    distances = []
    incidence_cosines = []
    for epsilon in (1e-2, 1e-4, 1e-6):
        h = T.C.critical_height()-epsilon
        ne, _ = T.C.bravais(h)
        azimuth = -np.degrees(np.arcsin(ne/2))
        near = T.C.unit_from(h, azimuth)
        distances.append(np.linalg.norm(near-u))
        incidence_cosines.append(near @ n1)
        assert np.isfinite(T.C.dp(near)[0]).all()
    assert np.all(np.diff(distances) < 0)
    assert np.all(np.diff(incidence_cosines) < 0)
    # Fresnel无偏振反射率在掠入时趋1，故不能把空心点声称为唯一亮点。
    ci = np.array(incidence_cosines)
    ct = np.sqrt(1-(1-ci*ci)/T.C.N**2)
    reflection = (((ci-T.C.N*ct)/(ci+T.C.N*ct))**2
                  + ((T.C.N*ci-ct)/(T.C.N*ci+ct))**2)/2
    assert np.all(np.diff(reflection) > 0) and reflection[-1] > .995
    assert T.latitude_minimum(T.C.critical_height()+.01) is None


def test_critical_marker_is_hollow_and_at_actual_contact(monkeypatch, tmp_path):
    captured = []

    def capture(fig, *args, **kwargs):
        ax = fig.axes[0]
        point = next(p for p in ax.collections if p.get_gid() == 'critical-closure-contact')
        captured.append(point.get_offsets().copy())
        assert not np.allclose(point.get_facecolors(), point.get_edgecolors())
        assert any(line.get_gid() == f'latitude-{T.C.critical_height():g}' for line in ax.lines)

    monkeypatch.setattr(Figure, 'savefig', capture)
    T.main(out=tmp_path/'ignored.png')
    np.testing.assert_allclose(captured[0][0], T.project(T.critical_contact())[:2], atol=1e-12)


def test_band_overlays_follow_horizontal_axis_constraint():
    fig = L.make_column_figure()
    try:
        for name, h, size in [('column-terrain', L.COLUMN_HEIGHT, 801),
                              *[(f'band-{h:g}', h, 301) for h in L.BAND_HEIGHTS]]:
            ax = next(ax for ax in fig.axes if ax.get_label() == name)
            image = next(im for im in ax.images if im.get_gid() == 'column-accessible-band')
            u = T.base_terrain(size)[2]
            # c为水平单位向量，s·c范围[-cos h,cos h]。直接取球面z分量，不调用accessible。
            expected = (np.abs(u[..., 2]) <= np.cos(np.radians(h))+1e-12)
            np.testing.assert_array_equal(image.get_array()[..., 3] > 0, expected)
            assert np.max(image.get_array()[..., 3]) < .5
            boundaries = [line for line in ax.lines if line.get_gid() == 'column-band-boundary']
            assert len(boundaries) == 2
            for line, latitude in zip(boundaries, (h-90, 90-h)):
                units = T.C.unit_from(latitude, np.linspace(0, 360, 1441))
                mask = T.sphere_visible(units)
                np.testing.assert_allclose(line.get_xydata()[mask], T.project(units)[mask, :2])
        assert L.COLUMN_HEIGHT > T.C.critical_height()
    finally:
        plt.close(fig)


def test_solar_four_frames_and_angle_arcs_are_actual_directions():
    fig, (_, sun, _, points) = S.make_figure()
    try:
        assert len(fig.axes) == 4  # 不留一个重复的天空整圆
        for ax, point in zip(fig.axes, points):
            arcs = [p for p in ax.patches if p.get_gid() == 'angular-distance']
            assert len(arcs) == 1
            actual = arcs[0]._path_original.vertices
            # 独立的球面插值弧，不调用angle_arc构造期望值。
            angle = np.arccos(sun @ point)
            t = np.linspace(0, 1, 81)
            u = (np.sin((1-t)*angle)[:, None]*sun + np.sin(t*angle)[:, None]*point)/np.sin(angle)
            np.testing.assert_allclose(actual, S.CAMERA.project_xy(1.35*u), atol=1e-12)
            assert any(p.get_gid() == 'solar-axis-rotation' for p in ax.patches)
        assert all(ax.get_label().startswith('attitude-') for ax in fig.axes)
    finally:
        plt.close(fig)


def test_sky_supremum_is_grazing_not_farthest_pixel():
    hc = T.C.critical_height()
    # 两侧面夹60°，掠入掠出时横向转120°；完整角距可由n直接消去h求出。
    expected = np.degrees(np.arccos((3-T.C.N*T.C.N)/2))
    assert K.spherical_distance(hc, 120) == pytest.approx(expected, abs=1e-12)
    assert expected == pytest.approx(50.062, abs=.001)
    assert np.sin(np.radians(hc)) < np.cos(np.radians(K.ALTITUDE))
    # 此太阳高度的柱晶可取带确实能逼近该极限；不是任意h均达同一上界。
    for epsilon in (1e-2, 1e-4):
        h = hc-epsilon
        _, delta = T.C.bravais(h)
        assert K.spherical_distance(h, delta) < expected
