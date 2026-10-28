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
    assert F.project(u)[2] > 0
    # 实际数值极小点左右都不能有更低的值。
    az, _ = F.C.az_el(u)
    neighbors = F.C.dp(F.C.unit_from(h, az + np.array([-0.1, 0.1])))[0]
    assert np.all(neighbors >= d)
    x = F.C.light_point(u)[0]
    assert abs(x[2] - u[2]) < 1e-12


def test_terrain_pixels_and_global_minimum():
    x, y, u, d = F.terrain(301)
    inside = x*x + y*y <= 1
    np.testing.assert_allclose(np.linalg.norm(u[inside], axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(F.project(u)[..., :2], np.stack([x, y], axis=-1), atol=1e-12)
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
    assert F.HEIGHTS[-2] < hc < F.HEIGHTS[-1]
    assert F.latitude_minimum(hc + 0.01) is None
    # 此取景确实包含完整光学域；不能靠背面遮挡隐藏另一块可行方向。
    el, az = np.meshgrid(np.arange(-90, 91, 1), np.arange(0, 360, 1), indexing="ij")
    u = F.C.unit_from_grid(el.ravel(), az.ravel())
    d, _ = F.C.dp(u)
    assert (F.project(u[np.isfinite(d)])[:, 2] > 0).all()


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
