# 验证图1/7实际生成配置、原始线性能量、投影与图版出处；本地大数组缺失显式 skip。
from __future__ import annotations

import json
from pathlib import Path
import sys
import subprocess

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sky_fig as F
import fig_column_sky as C
import fig_sky_comparison as S
from check_parhelion import bravais, spherical_distance, unit_from
from halo_notes.sim.fetch import sha256_of
from halo_notes.sim.projection import project_equal_area
from halo_notes.sim.run import config_sha256


@pytest.mark.parametrize("altitude", F.HEIGHTS)
def test_actual_configs_share_one_physics_except_orientation(altitude):
    configs = []
    for family in F.FAMILIES:
        path = F.DATA / f"{F.name(family, altitude)}.lumice.json"
        cfg = json.loads(path.read_text())
        assert cfg == F.build(family, altitude)
        assert len(cfg["crystal"]) == 1
        assert cfg["filter"] == [{"id": 1, "type": "raypath", "raypath": [3, 5],
                                  "symmetry": "PBD", "action": "filter_in"}]
        assert cfg["scene"]["scattering"] == [{"prob": 0, "entries": [{"crystal": 1, "proportion": 100, "filter": 1}]}]
        assert all("filter" not in r for r in cfg["render"])  # render.filter 并非光路过滤
        assert cfg["render"][1]["view"]["elevation"] == altitude
        cfg["crystal"][0].pop("axis")
        configs.append(cfg)
    assert configs[0] == configs[1] == configs[2]


@pytest.mark.local_data
@pytest.mark.parametrize("family", F.FAMILIES)
@pytest.mark.parametrize("altitude", F.HEIGHTS)
def test_linear_scene_energy_edges_and_actual_run(family, altitude):
    folder = F.DATA / F.name(family, altitude)
    energy, cfg, prov = F.load_scene(folder)
    display, _, _ = F.load_scene(folder, 2)
    assert prov["format"] == "npy" and prov["lumice_version"] == F.LUMICE_VERSION
    assert prov["config_sha256"] == config_sha256(F.build(family, altitude))
    assert f"sim_rays={cfg['scene']['ray_num']}" in (folder / "lumice.log").read_text()
    assert f"Lumice {F.LUMICE_VERSION.removeprefix('v')}" in (folder / "lumice.log").read_text()
    assert energy.sum() > 0
    # 原始全天与显示图是同一批光线，显示窗没有悄悄裁掉径向外界。
    assert display.sum() == pytest.approx(energy.sum(), rel=1e-6)
    d, _, dirs = F.angular_data(cfg)
    observed = d[energy > 0].min()
    sun_radius = cfg["scene"]["light_source"]["diameter"] / 2
    pixel_bound = np.sqrt(2) * 180 / cfg["render"][0]["resolution"][0]
    if family == "plate":
        ideal = float(spherical_distance(altitude, bravais(altitude)[1]))
        neighbors = [float(spherical_distance(h, bravais(h)[1]))
                     for h in (altitude - sun_radius, altitude + sun_radius)]
        assert min(neighbors) - sun_radius - pixel_bound <= observed <= ideal + pixel_bound
        elevations = np.degrees(np.arcsin(dirs[..., 2][energy > 0]))
        assert np.max(np.abs(elevations - altitude)) <= sun_radius + pixel_bound
    else:
        ideal = bravais(0)[1]
        assert abs(observed - ideal) <= sun_radius + pixel_bound
    if family == "column":
        # 确认两处实际切点，不把上半图的一处误报为完整图只有一处。
        for elevation in (altitude - bravais(0)[1], altitude + bravais(0)[1]):
            target = unit_from(elevation, 0).reshape(3)
            dot = np.sum(dirs * target, axis=-1)
            near = dot > np.cos(np.radians(sun_radius + pixel_bound + .1))
            assert energy[near].sum() > 0


@pytest.mark.local_data
def test_strict_probe_and_disappearance_control():
    strict = F.DATA / F.name("column", 20, probe=True, strict=True)
    energy, cfg, _ = F.load_scene(strict)
    assert cfg["filter"][0]["symmetry"] == ""
    assert cfg["filter"][0]["raypath"] == [3, 5]
    d, _, _ = F.angular_data(cfg)
    assert energy[d > 48].sum() > 0
    # 只验证本次观测，不将 MC 零命中提升为所有方向没有光的定理。
    assert energy[d > 51].sum() == 0
    energy, cfg, _ = F.load_scene(F.DATA / F.name("plate", 65, probe=True))
    assert cfg["scene"]["light_source"]["altitude"] == 65
    assert energy.sum() == 0 and bravais(65)[1] is None


@pytest.mark.local_data
def test_column_rings_and_uncropped_upper_tail():
    report, cfg = C.evidence()
    saved = json.loads((F.DATA / "column_sky_evidence.json").read_text())
    for key in report:
        assert saved[key] == report[key]
    assert report["beyond_optical_bound_pixels"] == 0
    assert report["split_gap_nonzero_pixels"] == 0
    assert 48 < report["upper_outermost_pixel_deg"] < report["optical_supremum_deg"] + .3
    # 只凭太阳水平线上方切图会丢掉真实的上切弧尾；当前视窗完整保留这个反例。
    outer = project_equal_area([report["upper_outermost_direction"]], cfg["render"][1])[0]
    assert F.DISPLAY_RES[1] / 2 < outer[1] < C.UPPER_VIEW_BOTTOM
    for row in report["rings_upper"]:
        hist = np.array(row["bin_Y_per_emitted_energy"])
        if row["radius_deg"] in (25, 30, 40):
            left, right = row["peak_pa_left_right_deg"]
            assert left < 0 < right
            assert np.count_nonzero(hist) > 2  # 实际亮段，不把两个亮峰冒充仅有两点光。
            assert np.count_nonzero(hist) < len(hist)  # 甚至没有点亮整个上半圆；不限制任意覆盖比例。
    assert saved["figure_sha256"] == sha256_of(F.IMG / "column_sky.png")


def test_angle_circle_projection_uses_true_spherical_distance():
    cfg = F.build("column", 20)
    sun = unit_from(20, 0).reshape(3)
    for radius in C.RADII:
        dirs = C.ring_directions(radius, np.arange(-110, 111, 2))
        distances = np.degrees(np.arccos(np.sum(dirs * sun, axis=-1)))
        assert np.allclose(distances, radius, atol=1e-9)
        uv = project_equal_area(dirs, cfg["render"][1])
        radii = np.linalg.norm(uv - np.array(F.DISPLAY_RES) / 2, axis=1)
        assert np.ptp(radii) < 1e-9


@pytest.mark.local_data
def test_comparison_manifest_matches_current_raw_and_figure():
    manifest = json.loads((F.DATA / "sky_comparison.json").read_text())
    assert manifest["figure_sha256"] == sha256_of(F.IMG / "sky_comparison.png")
    assert manifest["colors"] == S.COLORS
    assert manifest["strength_per_family"] == S.STRENGTH
    assert manifest["softening"] == S.SOFTENING
    assert len(manifest["scenes"]) == len(F.FAMILIES) * len(F.HEIGHTS)
    for key, row in manifest["scenes"].items():
        folder = F.DATA / key
        assert row["display_raw_sha256"] == sha256_of(folder / "img_02.npy")
        assert row["measurements"] == F.measure_scene(folder)
    assert np.array_equal(S.tone(np.zeros((2, 2)), 1), np.zeros((2, 2)))
    assert np.all(np.diff(S.tone(np.geomspace(1e-12, 1, 50), 1)) > 0)


@pytest.mark.local_data
def test_replot_does_not_render_or_require_binary(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("replot must not render or download a binary")
    monkeypatch.setattr(F, "run_scene", forbidden)
    monkeypatch.setattr(F, "release_binary", forbidden)
    energy, _, _ = S.obtain("column", 20, replot=True)
    assert energy.sum() > 0


@pytest.mark.local_data
@pytest.mark.parametrize("script,stem,default_meta", [
    ("fig_sky_comparison.py", "sky_comparison", "sky_comparison.json"),
    ("fig_column_sky.py", "column_sky", "column_sky_evidence.json"),
])
def test_cli_output_isolated_from_other_cwd(tmp_path, script, stem, default_meta):
    F.load_scene(F.DATA / F.name("column", 20), 2)  # 本地数据缺失时按仓规则显式skip。
    protected = [F.IMG / f"{stem}.png", F.DATA / default_meta]
    before = [(p.stat().st_mtime_ns, sha256_of(p)) for p in protected]
    out = tmp_path / "isolated" / f"{stem}.png"
    result = subprocess.run([sys.executable, str(Path(__file__).with_name(script)),
                             "--replot", "--output", str(out)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert sorted(p.name for p in out.parent.iterdir()) == [f"{stem}.json", f"{stem}.png"]
    metadata = json.loads(out.with_suffix(".json").read_text())
    assert metadata["figure_sha256"] == sha256_of(out)
    assert sha256_of(out) == before[0][1]  # 改输出位置不改变画面。
    assert [(p.stat().st_mtime_ns, sha256_of(p)) for p in protected] == before
