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


# task-math-depend-on-lumice-integral 迁移前（main 8e8a74b，本仓 halo_notes.math.reflection_group.pbd_orbit）跑出的
# phi_class_filters("A60-10", 0.2) 代表序列，按返回顺序（子过滤器 id 2, 3, … 依此分配）；B2 config 只锁集合，这里连顺序一起锁。
A60_10_RATIO_02_MAIN = tuple(tuple(map(int, s.split("-"))) for s in (
    "3-4-5-7", "3-5-6-7", "3-1-2-5-6-7", "3-1-4-5-2-7", "3-1-5-2-6-7", "3-1-5-6-2-7",
    "3-4-1-5-2-7", "3-4-5-1-2-7", "3-4-5-7-4-7", "3-5-7-3-5-7", "3-5-8-6-4-7", "3-6-3-5-6-7",
    "3-6-4-8-5-7", "3-1-2-1-5-2-6-7", "3-1-2-1-5-6-2-7", "3-1-2-4-5-1-2-7", "3-1-2-5-1-2-6-7", "3-1-2-5-1-6-2-7",
    "3-1-2-5-6-1-2-7", "3-1-4-2-5-1-2-7", "3-1-4-5-2-1-2-7", "3-1-4-5-7-2-4-7", "3-1-4-5-7-4-2-7", "3-1-5-7-2-3-5-7",
    "3-1-5-7-3-2-5-7", "3-1-5-7-3-5-2-7", "3-1-5-8-2-6-4-7", "3-1-5-8-6-2-4-7", "3-1-5-8-6-4-2-7", "3-1-6-2-3-5-6-7",
    "3-1-6-3-2-5-6-7", "3-1-6-3-5-2-6-7", "3-1-6-3-5-6-2-7", "3-1-6-4-2-8-5-7", "3-1-6-4-8-2-5-7", "3-1-6-4-8-5-2-7",
    "3-4-1-2-5-1-2-7", "3-4-1-5-2-1-2-7", "3-4-1-5-7-2-4-7", "3-4-1-5-7-4-2-7", "3-4-5-1-7-2-4-7", "3-4-5-1-7-4-2-7",
    "3-4-5-7-1-4-2-7", "3-4-5-7-3-4-5-7", "3-5-1-7-3-2-5-7", "3-5-1-7-3-5-2-7", "3-5-1-8-2-6-4-7", "3-5-1-8-6-2-4-7",
    "3-5-1-8-6-4-2-7", "3-5-6-7-3-5-6-7", "3-5-7-1-3-5-2-7", "3-5-8-1-6-4-2-7", "3-6-1-3-2-5-6-7", "3-6-1-3-5-2-6-7",
    "3-6-1-3-5-6-2-7", "3-6-1-4-8-2-5-7", "3-6-1-4-8-5-2-7", "3-6-4-1-8-2-5-7", "3-6-4-1-8-5-2-7",
))


def test_phi_class_filters_matches_main():
    """``phi_class_filters`` 走 ``rg.pbd_orbit``（已迁 lumice_integral.symmetry）去重的枚举分支——确定性图的 ``--replot`` 重跑覆盖不到它；
    迁移后返回值须与迁移前逐项相等（含顺序与 id）。枚举约 50 s，与 halo_notes/sim/tests/test_figures.py 的 B2 用例共享进程内缓存。"""
    filters = S.phi_class_filters("A60-10", 0.2)
    assert [tuple(f["raypath"]) for f in filters[1:]] == list(A60_10_RATIO_02_MAIN)
    assert [f["id"] for f in filters] == list(range(S.FILTER_ID, S.FILTER_ID + 1 + len(A60_10_RATIO_02_MAIN)))
    assert filters[0]["type"] == "complex" and all(f["type"] == "raypath" and f["symmetry"] == "PBD" for f in filters[1:])
