"""逐图单测：读各章落盘的 ``data/<name>.lumice.json``（不重新调用 builder）钉住验收标准要求的语义断言；
``slow`` 标记的测试真跑一遍图脚本（小光线数、临时目录），核验出图 + provenance。"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CH0, CH1, CH2, CH6 = "00-introduction", "01-symmetry", "02-raypath-enumeration", "06-monte-carlo-vs-integration"


def _cfg(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_halos_3_5_symmetry_is_P_only():
    """1.5：只开 P 对称不开 D 对称——幻日只出一侧。"""
    cfg = _cfg(f"{CH1}/data/halos_3-5.lumice.json")
    assert len(cfg["filter"]) == 1
    assert cfg["filter"][0]["raypath"] == [3, 5]
    assert cfg["filter"][0]["symmetry"] == "P"
    # 四个 population 都接了这条过滤器
    assert all(e.get("filter") == cfg["filter"][0]["id"] for e in cfg["scene"]["scattering"][0]["entries"])


def test_rp1_3_filter():
    """2.1：只剩片晶 1-3 光路。"""
    cfg = _cfg(f"{CH2}/data/rp1-3_plt0.5_s25_i2_note.lumice.json")
    assert [f["raypath"] for f in cfg["filter"]] == [[1, 3]]
    assert cfg["crystal"][0]["shape"]["height"] == 0.5
    assert cfg["scene"]["light_source"]["altitude"] == 25


def test_compare_two_methods_bands_share_exposure():
    """6.5：三条 Lumice 条带同一 ev_mode="absolute" + 同一 intensity_factor，否则亮度不可比。"""
    bands = sorted((ROOT / CH6 / "data").glob("compare_two_methods.band*.lumice.json"))
    assert len(bands) >= 2, "至少 1e7 / 1e8 两条"
    renders = [json.loads(b.read_text())["render"][0] for b in bands]
    assert {r["ev_mode"] for r in renders} == {"absolute"}
    assert len({r["intensity_factor"] for r in renders}) == 1
    assert len({json.dumps(r["lens"], sort_keys=True) for r in renders}) == 1  # 同镜头 / 视场 / 分辨率
    assert len({tuple(r["resolution"]) for r in renders}) == 1
    ray_nums = [json.loads(b.read_text())["scene"]["ray_num"] for b in bands]
    assert ray_nums == sorted(ray_nums) and all(isinstance(n, int) for n in ray_nums)


def test_compare_two_methods_uses_point_source():
    """6.5：旧图（globe + 三条带）都是严格点光源（旧 template.json diameter 0.0），切边才锐利；chore-figures-followup D。"""
    bands = sorted((ROOT / CH6 / "data").glob("compare_two_methods.band*.lumice.json"))
    assert len(bands) >= 2
    for b in bands:
        assert json.loads(b.read_text())["scene"]["light_source"]["diameter"] == 0
    assert _cfg(f"{CH6}/data/compare_two_methods.lumice.json")["scene"]["light_source"]["diameter"] == 0


def test_all_halos_and_dual_fisheye_are_full_sky():
    for path in (f"{CH0}/data/all_halos.lumice.json", f"{CH6}/data/dual_fisheye.lumice.json"):
        r = _cfg(path)["render"][0]
        assert r["lens"]["type"] == "dual_fisheye_equal_area" and r["visible"] == "full"


def test_provenance_sidecars_present():
    for d in (f"{CH0}/data/all_halos", f"{CH1}/data/halos_3-5", f"{CH2}/data/rp1-3_plt0.5_s25_i2_note", f"{CH6}/data/dual_fisheye"):
        prov = json.loads((ROOT / d / "provenance.json").read_text())
        assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0 and prov["config_sha256"]
        assert prov["config_sha256"] == __import__("halo_notes.sim.run", fromlist=["config_sha256"]).config_sha256(_cfg(f"{d}/config.json"))


@pytest.mark.slow
@pytest.mark.parametrize("script,out_name", [
    (f"{CH1}/code/fig_halos_3_5.py", "img/halos_3-5.jpg"),
    (f"{CH2}/code/fig_rp1_3_note.py", "img/rp1-3_plt0.5_s25_i2_note.png"),
    (f"{CH6}/code/fig_compare_two_methods.py", "img/compare_two_methods.jpg"),
])
def test_fig_scripts_run_small(tmp_path, script, out_name):
    mod = runpy.run_path(str(ROOT / script))
    out = mod["main"](["--ray-num", "200000", "--out", str(tmp_path)])
    assert out == tmp_path / out_name and out.exists()
    assert any((tmp_path / "data").rglob("provenance.json"))
