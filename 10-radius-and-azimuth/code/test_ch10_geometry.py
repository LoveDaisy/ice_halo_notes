"""ch10 实际绘图数据：四张底图一致、等角距轨迹与两把尺的独立核验。"""
import numpy as np
import pytest
from matplotlib.figure import Figure
from lumice_integral.symmetry.attitude import column_attitude

import _terrain_layers as L
import fig_plate_terrain as T
import fig_solar_circle as S
import fig_parhelion_rulers as R


def test_four_figures_render_identical_scalar_fields(monkeypatch, tmp_path):
    rendered = []

    def capture(fig, *_args, **_kwargs):
        image = fig.axes[0].images[0]
        rendered.append((image.get_array().copy(), image.get_extent(), image.norm.vmin,
                         image.norm.vmax, image.cmap(np.linspace(0, 1, 32))))

    monkeypatch.setattr(Figure, 'savefig', capture)
    import fig_terrain_domain as A
    import fig_random_terrain as B
    import fig_column_terrain as D
    for module in (A, B, T, D):
        module.main(out=tmp_path / 'ignored.png')
    assert len(rendered) == 4
    for data in rendered[1:]:
        np.testing.assert_array_equal(data[0].mask, rendered[0][0].mask)
        np.testing.assert_array_equal(data[0].data, rendered[0][0].data)
        np.testing.assert_array_equal(data[1], rendered[0][1])
        assert data[2:4] == rendered[0][2:4]
        np.testing.assert_array_equal(data[4], rendered[0][4])
    assert not T.base_terrain()[3].flags.writeable


def test_column_band_against_rotated_horizontal_crystals():
    sun = T.C.unit_from(L.COLUMN_HEIGHT, 0.)
    rotations = np.array([column_attitude(p, t) for p in np.arange(0, 360, 10)
                          for t in np.arange(0, 360, 10)])
    np.testing.assert_allclose(rotations[:, 2, 2], 0, atol=1e-12)
    us = np.einsum('nji,j->ni', rotations, sun)
    assert L.accessible(us, 'column').all()
    # 边界必须紧：不是把整球误画成柱晶的带。
    assert abs(np.max(us[:, 2]) - np.cos(np.radians(L.COLUMN_HEIGHT))) < 1e-12
    assert not L.accessible(np.array([[0., 0., 1.], [0., 0., -1.]]), 'column').any()
    equator = T.C.unit_from(0, np.arange(360))
    assert L.accessible(equator, 'column').all()
    u, d = T.latitude_minimum(0)
    assert L.accessible(u, 'column')
    expected = np.degrees(2*np.arcsin(T.C.N/2)) - 60
    assert abs(d-expected) < 1e-7


def test_solar_circle_independent_rodrigues_and_snell():
    angles = np.array([0., 17., 90., 181., 287., 360.])
    rotations, sun, us, points = S.scene_data(angles)
    np.testing.assert_allclose(us, np.broadcast_to(us[0], us.shape), atol=1e-12)
    assert np.isfinite(points).all()
    np.testing.assert_allclose(np.linalg.norm(points, axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(points @ sun, np.full(len(angles), points[0] @ sun), atol=1e-12)
    # 不调用 solar_orbit：逐项用向量 Rodrigues 公式验证真实生成的光点。
    a = np.radians(angles)[:, None]
    expected = (points[0]*np.cos(a) + np.cross(sun, points[0])*np.sin(a)
                + sun*(sun @ points[0])*(1-np.cos(a)))
    np.testing.assert_allclose(points, expected, atol=1e-12)
    assert np.linalg.norm(points[0]-points[2]) > .4
    np.testing.assert_allclose(rotations[0], rotations[-1], atol=1e-12)
    xy = S.sky_xy(points, sun)
    radius = np.degrees(np.arccos(points[0] @ sun))
    np.testing.assert_allclose(np.linalg.norm(xy, axis=1), radius, atol=1e-10)
    np.testing.assert_allclose(S.sky_xy(sun[None], sun), 0, atol=1e-10)
    assert S.ORBIT.__file__.endswith('09.1-orientation-space/code/_sun_rotation.py')
    assert S.CAMERA.projection == 'perspective'


def test_rulers_against_phi_minimum_and_critical():
    hc = R.C.critical_height()
    h, distance, delta = R.curve_data([0., 20., 40., 55., 60., hc, hc+.01, 65.])
    for i in range(5):
        u, expected = T.latitude_minimum(h[i])
        assert abs(distance[i] - expected) < 1e-6
        x = T.C.light_point(u)[0]
        az_u, _ = T.C.az_el(u)
        az_x, _ = T.C.az_el(x)
        actual_delta = abs((az_x-az_u+180) % 360 - 180)
        assert abs(delta[i]-actual_delta) < 1e-6
    assert np.isnan(distance[5:]).all() and np.isnan(delta[5:]).all()
    assert abs(distance[0]-delta[0]) < 1e-10
    assert np.all(delta[1:5] > distance[1:5])
    assert abs(R.C.bravais(hc)[0]-2.) < 1e-12
    assert T.latitude_minimum(hc+.01) is None


def test_rulers_geometry_rejects_critical_and_supercritical():
    for height in (R.C.critical_height(), R.C.critical_height()+.01, 65.):
        with pytest.raises(ValueError, match='critical'):
            R.ruler_geometry(height)
    # 单幅球面图只展示有效域内的方向，数值仍由同一物理接口产生。
    fig, data = R.make_figure()
    try:
        assert {ax.get_label() for ax in fig.axes} == {'celestial-sphere'}
        for text in fig.texts:
            assert 'nan' not in text.get_text()
        assert data.height < R.C.critical_height()
    finally:
        T.plt.close(fig)
