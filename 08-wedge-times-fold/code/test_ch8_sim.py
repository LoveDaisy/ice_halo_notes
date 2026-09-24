"""`_ch8_sim` 像素能量语义的章节私有测试（task-pixel-energy-semantics）：合成 rectangular 图，不跑 Lumice。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from halo_notes.sim.projection import rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_sim as S  # noqa: E402

RENDER = {"lens": {"type": "rectangular"}, "resolution": [360, 180], "view": {"azimuth": 0, "elevation": 0, "roll": 0}}


def _patch_image(lat_deg: float, az_deg: float = 0.0, *, half_deg: float = 2.0, value: int = 200) -> np.ndarray:
    """黑底图上 (lat, az) 周围 ±half_deg 的一块方形像素点亮为同一码值（同样多的像素 = 同样多的像素能量，与纬度无关）。"""
    dirs, _ = rectangular_pixel_directions(RENDER)
    lat = np.degrees(np.arcsin(np.clip(dirs[..., 2], -1, 1)))
    az = np.degrees(np.arctan2(dirs[..., 1], dirs[..., 0]))
    img = np.zeros(lat.shape + (3,), np.uint8)
    img[(np.abs(lat - lat_deg) <= half_deg) & (np.abs(az - az_deg) <= half_deg)] = value
    return img


def test_sky_energy_is_pixel_sum_independent_of_latitude():
    low, high = _patch_image(0.0), _patch_image(70.0)
    assert (low > 0).sum() == (high > 0).sum() > 0
    assert S.sky_energy(low, RENDER) == pytest.approx(S.sky_energy(high, RENDER))   # 修正前（× cos lat）两者差 ~3 倍
    assert S.sky_energy(low, RENDER) == pytest.approx(float(S.pixel_energy(low).sum()))


def test_cap_energy_fractions_do_not_reweight_by_latitude():
    img = _patch_image(0.0, 0.0) | _patch_image(70.0, 90.0)                          # 两块像素能量相等的亮斑
    cands = {"eq": np.array([1.0, 0.0, 0.0]),
             "hi": np.array([0.0, np.cos(np.radians(70)), np.sin(np.radians(70))])}
    fr = S.cap_energy_fractions(img, RENDER, cands, cap_deg=5.0)
    assert fr["eq"] == pytest.approx(0.5, abs=0.02) and fr["hi"] == pytest.approx(0.5, abs=0.02)
