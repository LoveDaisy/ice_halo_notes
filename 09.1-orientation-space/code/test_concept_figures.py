"""9.1 新概念图：从独立旋转、体轴约束、Jacobian 与实际绘图对象核验语义。"""
import importlib
import importlib.util

import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.spatial.transform import Rotation
from scipy.stats import kstest

import _orientation_fig as F
import check_orientation_space as C
import fig_axis_angle_ball as A
import fig_rotation_seam as B
import fig_plate_lowitz as L
import fig_euler_sampling as E
import fig_euler_density as D
import fig_sun_rotation as S
import fig_angle_fibers as G
import fig_column_torus as T
from _sun_rotation import solar_orbit, body_sun


def test_antipodes_are_same_rotation_and_actual_crystal():
    rotations = A.boundary_rotations()
    expected = 2*np.outer(A.AXIS, A.AXIS)-np.eye(3)
    for R in rotations:
        np.testing.assert_allclose(R, expected, atol=1e-14)
    fig, axes = plt.subplots(1, 2)
    polys = [F.crystal(ax, R) for ax, R in zip(axes, rotations)]
    np.testing.assert_allclose(polys[0].vertices, polys[1].vertices, atol=1e-14)
    plt.close(fig)


def test_coordinate_jump_does_not_jump_rotation():
    angles = np.linspace(0, 360, 1441)
    Rs = B.orientations(angles)
    coord = B.signed_angle(angles)
    alternative = Rotation.from_rotvec(np.radians(coord)[:, None]*B.AXIS).as_matrix()
    np.testing.assert_allclose(Rs, alternative, atol=1e-14)
    increments = Rotation.from_matrix(Rs[1:] @ Rs[:-1].transpose(0, 2, 1)).magnitude()
    np.testing.assert_allclose(np.degrees(increments), .25, atol=1e-12)
    assert np.max(np.abs(np.diff(coord))) > 359
    np.testing.assert_allclose(Rs[0], Rs[-1], atol=1e-14)
    delta = B.orientations([170, 190])
    np.testing.assert_allclose(np.degrees(Rotation.from_matrix(delta[1]@delta[0].T).magnitude()), 20)


def test_lowitz_surface_parameters_and_plate_circle():
    for phi in np.arange(0, 360, 17):
        for t in np.arange(-180, 180, 23):
            R = L.attitude(phi, t)
            independent = Rotation.from_euler('ZY', [phi, t], degrees=True).as_matrix()
            np.testing.assert_allclose(R, independent, atol=1e-14)
            assert abs(R[2, 1]) < 1e-14
            np.testing.assert_allclose(L.attitude(phi+360, t), R, atol=1e-14)
            np.testing.assert_allclose(L.attitude(phi, t+360), R, atol=1e-14)
            p = L.parameter_point(phi, t)
            np.testing.assert_allclose(T.signed_distance(p), 0, atol=1e-14)
        np.testing.assert_allclose(L.attitude(phi, 0)[:, 2], [0, 0, 1], atol=1e-14)
        # 图中高亮圈的显示高度在管顶；不是把显示角误当物理摆角。
        np.testing.assert_allclose(L.parameter_point(phi, 0)[2], T.MINOR)
    _, points = T.surface_pixels(151)
    image, changed_points = T.surface_pixels(151, ring_color=F.BLUE, meridian_color=F.ORANGE)
    np.testing.assert_array_equal(points, changed_points)
    assert np.isfinite(image).all()


def test_equal_step_grid_and_haar_have_expected_marginals():
    euler, haar = E.samples()
    assert euler.shape == haar.shape == (1440, 3)
    for directions in (euler, haar):
        np.testing.assert_allclose(np.linalg.norm(directions, axis=1), 1, atol=1e-14)
    # 独立 ZYZ 矩阵链；自转任取，不会改变 c 轴。
    angles = [[a, b, 37] for b in np.arange(2.5, 180, 5) for a in np.arange(0, 360, 9)]
    expected = Rotation.from_euler('ZYZ', angles, degrees=True).as_matrix()[:, :, 2]
    np.testing.assert_allclose(euler, expected, atol=1e-14)
    np.testing.assert_allclose(E.bin_fractions(euler), np.full(18, 1/18))
    assert kstest((haar[:, 2]+1)/2, 'uniform').pvalue > .001
    analytic_euler, analytic_haar = E.expected_fractions()
    np.testing.assert_allclose(analytic_euler.sum(), 1)
    np.testing.assert_allclose(analytic_haar.sum(), 1)
    for i in range(18):
        mass = quad(lambda b: np.sin(b)/2, *np.radians(E.EDGES[i:i+2]))[0]
        np.testing.assert_allclose(analytic_haar[i], mass, atol=1e-14)
    assert E.bin_fractions(euler)[0] > E.bin_fractions(haar)[0]*3


def test_density_matches_independent_body_jacobian_and_cap_integral():
    zyz = lambda x: Rotation.from_euler('ZYZ', x).as_matrix()
    for beta in (1, 10, 45, 90, 170, 179):
        J = C.body_jacobian(zyz, [.4, np.radians(beta), -.7])
        np.testing.assert_allclose(D.relative_density(beta), 2/(np.pi*abs(np.linalg.det(J))), rtol=1e-8)
    ratios = []
    for delta in (20, 10, 5, 1, .1):
        e = np.radians(delta)
        haar = quad(lambda b: np.sin(b)/2, 0, e)[0]
        np.testing.assert_allclose(D.cap_ratio(delta), (e/np.pi)/haar, rtol=1e-12)
        ratios.append(D.cap_ratio(delta))
    assert np.all(np.diff(ratios) > 0)
    assert D.relative_density(.0001) > 1e5  # 极点不是被截成一个有限峰。


def test_solar_orbit_preserves_body_sun_and_sky_radius():
    rotations, sun, us = S.scene_data(np.linspace(0, 360, 37))
    np.testing.assert_allclose(us, np.broadcast_to(S.INITIAL.T@sun, us.shape), atol=1e-14)
    # 每个体轴与太阳的夹角不变，独立逐列点积，不调用 body_sun。
    for R in rotations:
        for i in range(3):
            np.testing.assert_allclose(R[:, i]@sun, S.INITIAL[:, i]@sun, atol=1e-14)
    # 为 ch10 复用的等距不变量；此处不声称这一任意方向是已求解的物理出射光。
    body_direction = np.array([.2, -.5, .7])
    body_direction /= np.linalg.norm(body_direction)
    sky = rotations @ body_direction
    np.testing.assert_allclose(sky @ sun, np.full(len(sky), sky[0]@sun), atol=1e-14)
    assert np.linalg.norm(sky[9]-sky[0]) > .3
    np.testing.assert_allclose(rotations[0], rotations[-1], atol=1e-14)


def test_solar_orbit_action_is_world_left_multiplication_for_other_inputs():
    R = Rotation.from_euler('XYZ', [12, -39, 78], degrees=True).as_matrix()
    rotations, s = solar_orbit(R, [3, -4, 2], [0, 45, 190])
    for angle, actual in zip([0, 45, 190], rotations):
        a = np.radians(angle)
        # Rodrigues 逐列旋转，独立于 SciPy rotvec 实现与矩阵乘法方向。
        expected = np.stack([v*np.cos(a)+np.cross(s, v)*np.sin(a)+s*(s@v)*(1-np.cos(a))
                             for v in R.T], axis=1)
        np.testing.assert_allclose(actual, expected, atol=1e-14)
    np.testing.assert_allclose(body_sun(rotations, s), np.tile(R.T@s, (3, 1)), atol=1e-14)


@pytest.mark.parametrize('radius', [5., 1.])
def test_fiber_reference_winding_is_relative_to_smooth_local_section(radius):
    phi, u, shortest, local, phase = G.reference_loop(radius_deg=radius)
    s = np.array([0., 0., 1.])
    for matrices in (shortest, local):
        np.testing.assert_allclose(np.einsum('nij,nj->ni', matrices, u), np.tile(s, (len(u), 1)), atol=1e-10)
        np.testing.assert_allclose(np.linalg.det(matrices), 1, atol=1e-10)
    for i in range(0, len(u), 90):
        expected, _ = Rotation.align_vectors([s], [u[i]])
        np.testing.assert_allclose(shortest[i], expected.as_matrix(), atol=1e-10)
    relative = shortest @ local.transpose(0, 2, 1)
    z = relative[:, 0, 0] + 1j*relative[:, 1, 0]
    winding = np.sum(np.angle(z[1:]/z[:-1]))/(2*np.pi)
    np.testing.assert_allclose(winding, 2, atol=1e-10)
    np.testing.assert_allclose(phase-phase[0], 2*phi, atol=1e-10)
    # 局部截面相邻姿态平滑，最短截面不能在南极取同一个极限。
    assert np.max(np.linalg.norm(np.diff(local, axis=0), axis=(1, 2))) < .002
    assert np.linalg.norm(shortest[0]-shortest[180]) > 2


def test_clock_mark_uses_computed_relative_phase():
    _, _, _, _, phase = G.reference_loop()
    fig, ax = plt.subplots()
    G.clock(ax, [0, 0], phase[90]-phase[0])
    mark = np.asarray(ax.collections[0].get_offsets())[0]
    np.testing.assert_allclose(mark, [-.19, 0], atol=1e-12)
    plt.close(fig)


def test_compare_manifest_binds_every_required_number_to_exact_images(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    import sys
    from types import ModuleType
    from PIL import Image

    # 全仓多个章节都有 make_compare.py；即使同名模块已加载，也只读当前章。
    monkeypatch.setitem(sys.modules, 'make_compare', ModuleType('foreign_compare'))
    spec = importlib.util.spec_from_file_location('orientation_compare', Path(__file__).with_name('make_compare.py'))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    monkeypatch.setattr(M, 'CHAPTER', tmp_path)
    (tmp_path/'img').mkdir()
    for _, name, _ in M.FIGURES:
        Image.new('RGB', (24, 16), 'white').save(tmp_path/f'img/{name}.png')
    out = tmp_path/'compare.png'
    M.main(out)
    record = json.loads(out.with_suffix('.json').read_text())
    assert [row['figure'] for row in record['figures']] == ['1a', '1b', '2a', '2b', '3', '4a', '4b', '5a', '5b']
    assert record['compare_sha256'] == M.digest(out)
    assert record['optional_pending'] == ['4c']
    for row in record['figures']:
        assert row['sha256'] == M.digest(tmp_path/row['image'])
    assert not plt.get_fignums()


NEW_FIGURES = ('axis_angle_ball', 'rotation_seam', 'plate_lowitz', 'euler_sampling',
               'euler_density', 'sun_rotation', 'angle_fibers')


@pytest.mark.parametrize('name', NEW_FIGURES)
def test_each_figure_renders_only_into_requested_location(name, tmp_path):
    path = tmp_path / f'{name}.png'
    importlib.import_module(f'fig_{name}').main(path)
    from PIL import Image
    with Image.open(path) as image:
        assert image.width >= 2000 and image.height >= 1200
    assert not plt.get_fignums()
