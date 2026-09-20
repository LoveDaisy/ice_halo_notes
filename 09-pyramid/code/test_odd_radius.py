"""task-odd-radius-instances 的章节私有测试：`_ch9_sim.py` 的过滤器构造 / top-3 排名 / 判据函数（不跑 Lumice），以及四个
`fig_odd_radius_*.py` 的小光线数冒烟（`slow`，真跑 Lumice 到临时目录）——后者是 `halo_notes/sim/tests/test_figures.py`
里 `test_fig_scripts_run_small` 冒烟模式在 ch9 的章节私有版本（本任务 `halo_notes/` 只读，不并入库级回归测试）。"""

from __future__ import annotations

import json
import re
import runpy
import sys
from pathlib import Path

import numpy as np
import pytest

from halo_notes.sim import config as C
from halo_notes.sim import fetch
from halo_notes.sim.projection import rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch9_sim as S  # noqa: E402
import fig_odd_radius_families as FAM  # noqa: E402
import fig_odd_radius_panorama as PAN  # noqa: E402
import fig_odd_radius_remainder as REM  # noqa: E402
import fig_odd_radius_top3 as TOP  # noqa: E402

DATA = CODE_DIR.parent / "data"

# energy_table.md「族级互证」表 @(1, 0.5) 列的「命中（L≥2，N 条）」= 精确侧 ≤ 4 面代表数（独立于 raypaths csv 的读法）
MC_COVERED_MEMBERS = {0.0: 39, 28.0: 36, 52.4: 27, 56.0: 23, 60.0: 17, 62.0: 16, 63.8: 30, 80.2: 11, 90.0: 8}


# ---- 过滤器构造 ----


def test_family_filters_are_exactly_the_renderable_members():
    """族过滤器的成员 == csv 里该族长度 ≤ MAX_HITS 的全部代表；被略去的只有长度 > MAX_HITS 的；计数与 energy_table.md 一致。"""
    members = S.family_members()
    assert set(members) == set(S.KNOWN_WEDGES)
    assert sum(len(v) for v in members.values()) == 1520
    for wedge in S.KNOWN_WEDGES:
        flts = S.family_filters(wedge)
        assert flts[0]["type"] == "complex" and flts[0]["action"] == "filter_in" and flts[0]["symmetry"] == S.SYMMETRY
        assert all(f["symmetry"] == S.SYMMETRY and f["type"] == "raypath" for f in flts[1:])
        got = S.filter_paths(flts)
        assert got == set(S.renderable_members(wedge))
        omitted = set(members[wedge]) - got
        assert all(len(seq) > S.MAX_HITS for seq in omitted)
        assert len(got) == MC_COVERED_MEMBERS[wedge]
        assert len(flts) <= S.MAX_FILTERS


def test_remainder_filter_is_filter_out_over_union():
    flts = S.remainder_filter()
    top = flts[0]
    assert top["type"] == "complex" and top["action"] == "filter_out" and top["symmetry"] == S.SYMMETRY
    union = {seq for w in S.KNOWN_WEDGES for seq in S.renderable_members(w)}
    assert S.filter_paths(flts) == union
    assert len(union) == sum(MC_COVERED_MEMBERS.values()) == 207
    assert len(flts) == 208 <= S.MAX_FILTERS
    assert all(len(seq) > 1 for seq in union)          # 单面外反射不在并集里 → 留在余量里


def test_complex_over_rejects_more_than_lumice_cap():
    too_many = tuple((3, 15 + i % 6, 2) for i in range(S.MAX_FILTERS))
    with pytest.raises(ValueError, match="超过 Lumice"):
        S._complex_over(too_many, action="filter_in")


def test_single_raypath_filter():
    flts = S.single_raypath_filter((13, 24, 26))
    assert flts == [C.raypath_filter(S.FILTER_ID, [13, 24, 26], S.SYMMETRY)]
    assert S.filter_paths(flts) == {(13, 24, 26)}


# ---- 族外 top-3 与 MC 份额口径 ----


def test_top3_out_of_family_grouped_by_pbd_orbit():
    """分组求和口径：`13-24-26`（19.5°）0.300% 居首（plan §2 假设 5 核实过的数字），三条都是 raypaths csv 里的族外代表。"""
    top = S.top_out_of_family(3)
    assert [p.label for p in top] == ["13-24-26", "13-5-26-28", "13-15-26-28"]
    assert top[0].wedge_deg == 19.5 and abs(top[0].energy_pct - 0.3002) < 1e-4
    assert [p.wedge_deg for p in top] == [19.5, 35.2, 60.7]
    off = set(S.off_family_members())
    assert all(p.faces in off for p in top)
    assert abs(top[2].radius_deg - 22.19) < 0.01                      # 60.7° 楔的最小偏向角，离 22° 晕只差 0.35°


def _energy_table_default_column() -> dict[str, float]:
    """energy_table.md 主表的「能量@(1, 0.5)」列 + 汇总表的族外 / 单面外反射两行。"""
    text = (DATA / "energy_table.md").read_text()
    out: dict[str, float] = {}
    for m in re.finditer(r"^\| ([\d.]+)° \| [^|]+ \| ([\d.]+) \|", text, re.M):
        out[f"{float(m.group(1)):g}"] = float(m.group(2))
    out["off"] = float(re.search(r"^\| 族外能量（%）/ 族外 Φ 类数 \| ([\d.]+) /", text, re.M).group(1))
    out["single"] = float(re.search(r"^\| 单面外反射能量（%） \| ([\d.]+) \|", text, re.M).group(1))
    return out


def test_mc_family_shares_match_energy_table():
    """脚本从 rows csv 重算的 MC 份额与 energy_table.md 逐位一致（同一口径，不是抄表）。"""
    got = FAM.mc_family_shares()
    table = _energy_table_default_column()
    assert set(f"{w:g}" for w in S.KNOWN_WEDGES) <= set(table)
    for k, v in table.items():
        assert abs(got[k] - v) < 5e-4, (k, got[k], v)
    assert abs(sum(got[f"{w:g}"] for w in S.KNOWN_WEDGES) - 86.9296) < 5e-3


# ---- 版本门槛 ----


def test_ensure_lumice_version_rejects_override(monkeypatch):
    monkeypatch.setenv("LUMICE_BIN", "/nonexistent/Lumice")
    with pytest.raises(RuntimeError, match="LUMICE_BIN"):
        S.ensure_lumice_version()


def test_ensure_lumice_version_returns_cached_release(monkeypatch, tmp_path):
    monkeypatch.delenv("LUMICE_BIN", raising=False)
    want = fetch.cached_binary("v9.9.9")
    monkeypatch.setattr(fetch, "ensure_lumice", lambda version: want if version == "v9.9.9" else tmp_path / "other")
    assert S.ensure_lumice_version("v9.9.9") == want
    with pytest.raises(RuntimeError, match="不是 release"):
        S.ensure_lumice_version("v8.8.8")


# ---- 通用角度统计：合成剖面 / 合成图 ----


def _synthetic_profile(peaks: dict[float, float], bg: float = 1.0, sigma: float = 0.4):
    centers = np.arange(0.0, 180.0, S.PROFILE_BIN_DEG) + S.PROFILE_BIN_DEG / 2
    prof = np.full_like(centers, bg)
    for at, h in peaks.items():
        prof += h * np.exp(-0.5 * ((centers - at) / sigma) ** 2)
    return centers, prof


def test_peak_over_background_and_detect_peaks_synthetic():
    centers, prof = _synthetic_profile({22.4: 5.0, 35.4: 1.5})
    strong = S.peak_over_background(centers, prof, S.radius_window(S.KNOWN_RADII[60.0]))
    assert abs(strong["peak_deg"] - 22.4) < S.PROFILE_BIN_DEG and strong["is_local_max"] and strong["detected"]
    assert abs(strong["ratio"] - 6.0) < 0.15
    weak = S.peak_over_background(centers, prof, S.radius_window(S.KNOWN_RADII[80.2]))
    assert weak["is_local_max"] and not weak["detected"] and abs(weak["ratio"] - 2.5) < 0.15
    slope = S.peak_over_background(centers, prof, (15.0, 19.0))             # 窗内只有 22.4° 峰的上坡：argmax 在窗边，不是峰
    assert not slope["is_local_max"] and not slope["detected"]
    found = S.detect_peaks(centers, prof)
    assert [round(p["peak_deg"], 2) for p in found] == [22.38]
    assigned = S.assign_peaks(found)
    assert assigned[60.0] is found[0] and all(v is None for w, v in assigned.items() if w != 60.0)
    all_max = S.assign_peaks(S.detect_peaks(centers, prof, ratio=1.0))
    assert all_max[80.2] is not None and abs(all_max[80.2]["peak_deg"] - 35.4) < S.PROFILE_BIN_DEG


def test_assign_peaks_takes_nearest_radius_below():
    """峰在最小偏向角外侧：24.4° 归 63.8° 族（R 23.82），不归 62° 族（R 22.86）；9.4° 归 28° 族。"""
    pk = lambda at: {"peak_deg": at, "ratio": 9.0}  # noqa: E731
    out = S.assign_peaks([pk(24.4), pk(9.4)])
    assert out[63.8]["peak_deg"] == 24.4 and out[62.0] is None and out[28.0]["peak_deg"] == 9.4


def test_local_background_excludes_ring_zones():
    """非峰窗口的中位数：20° 环旁边 22°/24° 两环再亮也不该抬高背景。"""
    centers, prof = _synthetic_profile({20.4: 8.0, 22.4: 12.0, 24.4: 15.0}, bg=1.0, sigma=0.5)
    assert abs(S.local_background(centers, prof, 20.4) - 1.0) < 0.05
    naive = S.local_background(centers, prof, 20.4, zones=())
    assert naive > 1.0                                                     # 不剔环带时中位数被邻环抬高


def _synthetic_sky(paint) -> tuple[np.ndarray, dict]:
    """黑底 rectangular 图；``paint(theta, az)`` 返回要点亮的像素掩模（theta = 与太阳夹角，az = 绕太阳方位）。"""
    render = S.rect_render(1.0)
    dirs, _ = rectangular_pixel_directions(render)
    sun = S.sun_direction()
    theta = np.degrees(np.arccos(np.clip(dirs @ sun, -1, 1)))
    az = S._azimuth_about(dirs.reshape(-1, 3), sun).reshape(theta.shape)
    img = np.zeros(theta.shape + (3,), np.uint8)
    img[paint(theta, az)] = 200
    return img, render


def test_arc_or_spot_synthetic_full_ring_vs_sector():
    r = 22.4
    full, render = _synthetic_sky(lambda th, az: (th >= r) & (th <= r + 1.0))
    out = S.arc_or_spot(full, render, S.sun_direction(), r)
    assert out["verdict"] == "arc" and out["coverage"] > 0.95 and out["radial_is_local_max"]
    sector, _ = _synthetic_sky(lambda th, az: (th >= r) & (th <= r + 1.0) & (az >= 100) & (az <= 118))
    out = S.arc_or_spot(sector, render, S.sun_direction(), r)
    assert out["verdict"] == "spot" and abs(out["coverage"] - 18 / 360) < 0.03


def test_exposure_stats_and_total_energy_per_i():
    img, render = _synthetic_sky(lambda th, az: th <= 0.5)
    img[..., :] = np.where(img > 0, 255, 20)                   # 盘内削顶、盘外均匀暗
    st = S.exposure_stats(img, render)
    assert st["sat_disk"] > 0 and st["sat_out"] == 0 and st["max_out"] == 20 and st["intensity"] == 1.0
    with pytest.raises(ValueError, match="没有 dim"):
        S.total_energy_per_i(st)
    dim = dict(st, sat_disk=0, energy_disk_per_i=3.0)
    assert S.total_energy_per_i(st, dim) == pytest.approx(st["energy_out_per_i"] + 3.0)
    bad = dict(st, sat_out=1)
    with pytest.raises(ValueError, match="bright 曝光盘外"):
        S.total_energy_per_i(bad, dim)


def test_energy_quantiles_and_observed_peak():
    centers, prof = _synthetic_profile({120.0: 4.0}, bg=0.0, sigma=3.0)
    e = prof * np.sin(np.radians(centers))
    q = S.energy_quantiles(centers, e)
    assert abs(q["q50"] - 120.0) < 1.0 and q["q10"] < 118 < 122 < q["q90"]


# ---- 脚本 config 的语义 ----


def test_panorama_configs_share_crystal_and_scene():
    rect, fish = PAN.build_rect(0.2, 1000), PAN.build_fisheye(1000)
    assert rect["crystal"] == fish["crystal"] and rect["scene"] == fish["scene"] and rect["filter"] == fish["filter"] == []
    assert rect["scene"]["max_hits"] == S.MAX_HITS == 4 and rect["scene"]["light_source"]["altitude"] == 20.0
    assert rect["crystal"][0]["type"] == "pyramid" and rect["crystal"][0]["shape"]["prism_h"] == 0.5
    assert rect["crystal"][0]["axis"] == C.random_axis()
    assert rect["render"][0]["ev_mode"] == "absolute" and rect["render"][0]["lens"]["type"] == "rectangular"
    assert fish["render"][0]["lens"]["type"] == "fisheye_equal_area" and fish["render"][0]["view"] == {"elevation": 90}


def test_family_and_remainder_configs():
    cfg = FAM.build(63.8)(0.2, 1000)
    assert S.filter_paths(cfg["filter"]) == set(S.renderable_members(63.8))
    assert cfg["scene"]["scattering"][0]["entries"][0]["filter"] == S.FILTER_ID
    assert cfg["scene"] == dict(PAN.build_rect(0.2, 1000)["scene"], scattering=cfg["scene"]["scattering"])   # 除过滤器挂载外同一场景
    rem = REM.build(0.2, 1000)
    assert rem["filter"][0]["action"] == "filter_out" and len(rem["filter"]) == 208
    top = TOP.build(S.top_out_of_family(1)[0])(0.2, 1000)
    assert top["filter"] == S.single_raypath_filter((13, 24, 26))


# ---- 冒烟：真跑四个脚本（小光线数、临时目录、依赖顺序：全景在前） ----


@pytest.mark.slow
def test_odd_radius_scripts_run_small(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMICE_BIN", raising=False)
    order = [
        ("fig_odd_radius_panorama.py", "odd_radius_panorama"),
        ("fig_odd_radius_families.py", "odd_radius_families"),
        ("fig_odd_radius_remainder.py", "odd_radius_remainder"),
        ("fig_odd_radius_top3.py", "odd_radius_top3"),
    ]
    for script, name in order:
        mod = runpy.run_path(str(CODE_DIR / script))
        out = mod["main"](["--ray-num", "200000", "--out", str(tmp_path)])
        assert out == tmp_path / "data" / f"{name}.numbers.json" and out.exists()
        numbers = json.loads(out.read_text())
        assert numbers["max_hits"] == 4
        for prov in (tmp_path / "data" / name).rglob("provenance.json"):
            assert json.loads(prov.read_text())["lumice_version"] == fetch.LUMICE_VERSION
    assert (tmp_path / "data" / "odd_radius_panorama" / "rect_dim" / "img_01.png").exists()
    assert (tmp_path / "data" / "odd_radius_families" / "w0_dim" / "img_01.png").exists()
    assert len(list((tmp_path / "data" / "odd_radius_families").iterdir())) == 10          # 9 族 + w0_dim
    # --replot：不跑 Lumice，只重算；取数逐族重现（曝光探针的 probe_* / rounds 字段只在真跑时有，不比）
    def shares(path: Path) -> dict:
        n = json.loads(path.read_text())
        return {k: (f["energy_per_i"], f["share_render_pct"], f["rel_dev"], f.get("ring")) for k, f in n["families"].items()}
    before = shares(tmp_path / "data" / "odd_radius_families.numbers.json")
    mod = runpy.run_path(str(CODE_DIR / "fig_odd_radius_families.py"))
    monkeypatch.setattr(S, "ensure_lumice_version", lambda *a, **k: pytest.fail("--replot 不该碰版本门槛 / Lumice"))
    mod["main"](["--replot", "--out", str(tmp_path)])
    assert shares(tmp_path / "data" / "odd_radius_families.numbers.json") == before
