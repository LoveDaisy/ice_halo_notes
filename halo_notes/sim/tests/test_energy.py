"""``halo_notes.sim.energy``：sRGB 解码数值、能量 / 辐亮度语义（Lumice 像素已含立体角，不再乘 cos(lat)）。"""

from __future__ import annotations

import numpy as np

from halo_notes.sim.energy import linear_luminance, pixel_energy, pixel_radiance
from halo_notes.sim.projection import rectangular_pixel_directions

RENDER = {"lens": {"type": "rectangular", "fov": 180}, "resolution": [720, 360], "view": {"azimuth": 0, "elevation": 0}}


def _srgb_encode(lin: np.ndarray) -> np.ndarray:
    a = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)
    return np.round(np.clip(a, 0, 1) * 255.0).astype(np.uint8)


def test_linear_luminance_known_values():
    """0 → 0、255 → 每通道 1（三通道和 3）；解码阈值 0.04045（8-bit 10 / 11 两侧）分别走线性段 / 幂律段。"""
    img = np.array([[[0, 0, 0], [255, 255, 255], [10, 0, 0], [11, 0, 0]]], np.uint8)
    L = linear_luminance(img)
    assert L.shape == (1, 4)
    assert L[0, 0] == 0.0 and np.isclose(L[0, 1], 3.0)
    assert np.isclose(L[0, 2], 10 / 255 / 12.92)                          # 10/255 = 0.0392 ≤ 0.04045：线性段
    assert np.isclose(L[0, 3], ((11 / 255 + 0.055) / 1.055) ** 2.4)       # 11/255 = 0.0431 > 0.04045：幂律段


def test_linear_luminance_grayscale_is_per_pixel():
    g = np.array([[0, 128], [255, 11]], np.uint8)
    rgb = np.repeat(g[..., None], 3, axis=-1)
    assert linear_luminance(g).shape == (2, 2)
    assert np.allclose(3 * linear_luminance(g), linear_luminance(rgb))


def test_pixel_energy_is_linear_luminance():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (7, 9, 3), dtype=np.uint8)
    assert np.array_equal(pixel_energy(img), linear_luminance(img))


def test_uniform_sky_radiance_and_cap_energy_fraction():
    """辐亮度均匀的天空在 Lumice rectangular 图上的像素值 = c·cos(lat)：:func:`pixel_radiance` 处处还原 c；天顶 60° 球冠内的
    :func:`pixel_energy` 占比 = 真实立体角占比 (1 − cos 60°)/2 = 0.25。反证：再乘一次 cos(lat) 得到的占比明显偏离 0.25。"""
    dirs, w = rectangular_pixel_directions(RENDER)
    c = 0.3
    img = _srgb_encode(np.repeat((c * w)[..., None], 3, axis=-1) / 3)     # 三通道各 1/3，和 = c·cos(lat)
    E = pixel_energy(img)
    mid = w > 0.2                                                         # 两极 cos→0 处 8-bit 量化相对误差大，只在中纬度比辐亮度
    assert np.allclose(pixel_radiance(E, w)[mid], c, rtol=0.03)
    assert np.isclose(pixel_radiance(np.array([2.0]), np.array([0.5]))[0], 4.0)
    cap = dirs[..., 2] > np.cos(np.radians(60))
    assert abs(E[cap].sum() / E.sum() - 0.25) < 0.005
    Ew = E * w
    assert abs(Ew[cap].sum() / Ew.sum() - 0.25) > 0.05                   # 多乘 cos(lat) 的旧口径：天顶附近被低估
