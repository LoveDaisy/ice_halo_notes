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


@pytest.mark.local_data
def test_supremum_annotation_preserves_actual_weak_light(monkeypatch, tmp_path):
    from matplotlib.figure import Figure

    energy, cfg, _ = S.obtain('column', C.ALTITUDE, replot=True)
    report, _ = C.evidence()
    captured = []

    def capture(fig, *_args, **_kwargs):
        ax = fig.axes[0]
        captured.append(True)
        expected = S.tone(energy, float(np.quantile(energy[energy > 0], .995)))
        np.testing.assert_array_equal(ax.images[0].get_array(), expected)
        boundary = next(line for line in ax.lines if line.get_gid() == 'grazing-supremum')
        # 等面积显示投影的半径是sin(D/2)，与标注数值独立核对，不使用ring_directions。
        unit = cfg['render'][1]
        center = np.array(F.DISPLAY_RES)/2
        radius = np.linalg.norm(boundary.get_xydata()-center, axis=1)
        reference = project_equal_area([unit_from(C.ALTITUDE+report['optical_supremum_deg'], 0)], unit)[0]
        np.testing.assert_allclose(radius, np.linalg.norm(reference-center), atol=1e-9)
        text = '\n'.join(t.get_text() for t in [*ax.texts, *fig.texts])
        # 「透射趋零、不是最后可见像素」的限定已按 #48 移入正文图 7 图注；图面只留量值标注。
        assert '几何上确界' in text
        assert '最远采样' not in text
        assert ax.get_ylim() == (C.UPPER_VIEW_BOTTOM, 0)

    monkeypatch.setattr(Figure, 'savefig', capture)
    # draw末尾计算PNG哈希；截获保存时给独立临时输出一个最小文件，不动章图。
    output = tmp_path/'capture.png'
    output.write_bytes(b'test-only')
    C.draw(replot=True, output=output)
    assert captured == [True]


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


def _stale_cache(monkeypatch, tmp_path):
    """config/provenance 不一致但 img_02 在场的失效缓存，指向临时 DATA。"""
    monkeypatch.setattr(F, "DATA", tmp_path)
    folder = tmp_path / F.name("column", 20)
    folder.mkdir()
    cfg = F.build("column", 20)
    cfg["scene"]["ray_num"] = 123
    (folder / "config.json").write_text(json.dumps(cfg))
    (folder / "provenance.json").write_text(json.dumps(
        {"config_sha256": "deadbeef", "lumice_version": "v0", "lumice_bin_sha256": "y"}))
    (folder / "img_02.json").write_text(json.dumps(
        {"channels": "XYZ", "normalization": "raw", "sim_ray_num": 123, "emitted_energy": 1.0}))
    np.save(folder / "img_02.npy",
            np.full((*reversed(F.DISPLAY_RES), 3), 1e-9, dtype=np.float32))
    return folder


def _write_valid_cache(folder):
    """模拟 run_scene 的真实行为：渲染后写回与当前 build 一致的完整缓存。"""
    cfg = F.build("column", 20)
    (folder / "config.json").write_text(json.dumps(cfg))
    (folder / "provenance.json").write_text(json.dumps(
        {"config_sha256": F.config_sha256(cfg), "lumice_version": F.LUMICE_VERSION,
         "lumice_bin_sha256": "unused"}))
    (folder / "img_02.json").write_text(json.dumps(
        {"channels": "XYZ", "normalization": "raw",
         "sim_ray_num": cfg["scene"]["ray_num"], "emitted_energy": 1.0}))
    np.save(folder / "img_02.npy",
            np.full((*reversed(F.DISPLAY_RES), 3), 1e-6, dtype=np.float32))


def test_stale_cache_default_mode_rerenders(monkeypatch, tmp_path):
    """评审 Major 回归：失效缓存不得在重渲前阻断默认模式。"""
    folder = _stale_cache(monkeypatch, tmp_path)
    calls = []

    def fake_run(*a, **k):
        calls.append(a)
        _write_valid_cache(folder)  # 与真实 run_scene 一样落盘全新一致产物。
    monkeypatch.setattr(F, "run_scene", fake_run)
    energy, cfg, prov = S.obtain("column", 20)
    assert calls and cfg["scene"]["ray_num"] != 123
    assert energy.sum() > 0 and prov["lumice_version"] == F.LUMICE_VERSION


def test_render_bypasses_stale_cache_without_reading(monkeypatch, tmp_path):
    folder = _stale_cache(monkeypatch, tmp_path)
    assert (folder / "img_02.npy").is_file()
    stale = (folder / "config.json").read_text()
    calls = []

    def fake_run(*a, **k):
        calls.append(a)
        _write_valid_cache(folder)
    monkeypatch.setattr(F, "run_scene", fake_run)
    S.obtain("column", 20, render=True)
    assert calls
    assert (folder / "config.json").read_text() != stale


def test_replot_rejects_stale_cache_with_clear_error(monkeypatch, tmp_path):
    folder = _stale_cache(monkeypatch, tmp_path)
    monkeypatch.setattr(F, "run_scene", lambda *a, **k: pytest.fail("replot must not render"))
    with pytest.raises(FileNotFoundError, match="去掉 --replot"):
        S.obtain("column", 20, replot=True)


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
