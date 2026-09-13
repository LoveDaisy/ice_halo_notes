"""逐图单测：读各章落盘的 ``data/<name>.lumice.json``（不重新调用 builder）钉住验收标准要求的语义断言；
``slow`` 标记的测试真跑一遍图脚本（小光线数、临时目录），核验出图 + provenance。"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

from halo_notes.sim.run import config_sha256

ROOT = Path(__file__).resolve().parents[3]
CH0, CH1, CH2, CH6 = "00-introduction", "01-symmetry", "02-raypath-enumeration", "06-monte-carlo-vs-integration"
CH7 = "07-reflection-group"


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


def test_compare_two_methods_bands_monochrome():
    """条带单波长（硬切边靠它，D65 色散会抹掉）；全天 globe 图仍 D65。"""
    bands = sorted((ROOT / CH6 / "data").glob("compare_two_methods.band*.lumice.json"))
    assert len(bands) >= 2
    for b in bands:
        spec = json.loads(b.read_text())["scene"]["light_source"]["spectrum"]
        assert isinstance(spec, list) and len(spec) == 1, f"{b.name}: 条带应为单波长，得到 {spec!r}"
    globe = json.loads((ROOT / CH6 / "data" / "compare_two_methods.lumice.json").read_text())
    assert globe["scene"]["light_source"]["spectrum"] == "D65"
    assert _cfg(f"{CH6}/data/compare_two_methods.lumice.json")["scene"]["light_source"]["diameter"] == 0


def test_all_halos_and_dual_fisheye_are_full_sky():
    for path in (f"{CH0}/data/all_halos.lumice.json", f"{CH6}/data/dual_fisheye.lumice.json"):
        r = _cfg(path)["render"][0]
        assert r["lens"]["type"] == "dual_fisheye_equal_area" and r["visible"] == "full"


def test_provenance_sidecars_present():
    for d in (f"{CH0}/data/all_halos", f"{CH1}/data/halos_3-5", f"{CH2}/data/rp1-3_plt0.5_s25_i2_note", f"{CH6}/data/dual_fisheye"):
        prov = json.loads((ROOT / d / "provenance.json").read_text())
        assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0 and prov["config_sha256"]
        assert prov["config_sha256"] == config_sha256(_cfg(f"{d}/config.json"))


@pytest.mark.slow
@pytest.mark.parametrize("script,out_name", [
    (f"{CH1}/code/fig_halos_3_5.py", "img/halos_3-5.jpg"),
    (f"{CH2}/code/fig_rp1_3_note.py", "img/rp1-3_plt0.5_s25_i2_note.png"),
    (f"{CH6}/code/fig_compare_two_methods.py", "img/compare_two_methods.jpg"),
    (f"{CH7}/code/fig_halos_columns.py", "img/halos_3_vs_2.jpg"),
    (f"{CH7}/code/sim_pose_to_sky_backdrop.py", "data/pose_to_sky_backdrop/col_2/img_01.png"),
])
def test_fig_scripts_run_small(tmp_path, script, out_name):
    mod = runpy.run_path(str(ROOT / script))
    out = mod["main"](["--ray-num", "200000", "--out", str(tmp_path)])
    if isinstance(out, dict):   # ch7 图 6 一个脚本出两张 / 7.5 底图脚本出两张
        out = out.get("halos_3_vs_2") or out[2]
    assert out == tmp_path / out_name and out.exists()
    assert any((tmp_path / "data").rglob("provenance.json"))


# ---- ch7 图 6a/6b（task-draw-ch7-figs）：三份子图 config 只差过滤器与视场中心；代表光路 ↔ 权威表矩阵；拼图由子图像素拼成 ----


def _ch7_script():
    return runpy.run_path(str(ROOT / CH7 / "code" / "fig_halos_columns.py"))


def _strip_filter_and_view(cfg: dict) -> dict:
    cfg = json.loads(json.dumps(cfg))
    cfg["filter"] = None
    for layer in cfg["scene"]["scattering"]:
        for e in layer["entries"]:
            e.pop("filter", None)
    for r in cfg["render"]:
        r.pop("view", None)
    return cfg


def test_halo_columns_configs_differ_only_by_filter_and_view():
    """R1-5：每张子图以自己那种晕的中心为视场中心（#2 / #11 太阳、#3 反日点 = 太阳方位 + 180°、同一仰角 Σ），
    除 filter 与 render.view 外三份 config 逐字段相同；镜头 fisheye_equal_area、fov ≥ 320°（幻日环整圈：离太阳最远 180° − 2Σ）；
    网格：仰角 / 方位每 30° 一条 + 地平线（仰角 0）。"""
    cfgs = {k: _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json") for k in (2, 11, 3)}
    stripped = [json.dumps(_strip_filter_and_view(c), sort_keys=True) for c in cfgs.values()]
    assert len(set(stripped)) == 1
    mod = _ch7_script()
    sun = cfgs[2]["scene"]["light_source"]
    for k, cfg in cfgs.items():
        assert len(cfg["filter"]) == 1
        assert cfg["filter"][0]["raypath"] == mod["PATHS"][k] and cfg["filter"][0]["symmetry"] == "PBD"
        assert cfg["scene"]["scattering"][0]["entries"] == [{"crystal": 1, "proportion": 100, "filter": 1}]
        assert cfg["scene"]["light_source"]["altitude"] == 10 and cfg["render"][0]["lens"]["type"] == "fisheye_equal_area"
        assert cfg["crystal"][0]["axis"]["zenith"]["mean"] == 90 and "roll" not in cfg["crystal"][0]["axis"]   # 柱晶，roll 均匀
        assert cfg["scene"]["ray_num"] == mod["RAY_NUM"]
        view = cfg["render"][0]["view"]
        expect_az = sun["azimuth"] if k in (2, 11) else (sun["azimuth"] + 180) % 360
        assert view["azimuth"] == expect_az and view["elevation"] == sun["altitude"], k
        assert cfg["render"][0]["lens"]["fov"] >= 2 * (180 - 2 * sun["altitude"])
        grid = cfg["render"][0]["grid"]
        assert sorted(g["value"] for g in grid["elevation"]) == list(range(-60, 90, 30))
        assert sorted(g["value"] for g in grid["longitude"]) == list(range(0, 360, 30))
    assert mod["VIEW_CENTERS"] == {2: "sun", 11: "sun", 3: "anthelic"}


def test_halo_columns_paths_realise_their_matrices_and_pbd_covers_the_class():
    """每个代表光路的内反射面镜面矩阵连乘 == 权威表目标矩阵；D6 全部像（P/D）+ 上下互换（B）的矩阵集合 == 目标所在共轭类。"""
    from halo_notes.math import group as D6
    from halo_notes.math import reflection_group as rg
    mod = _ch7_script()
    for k, path in mod["PATHS"].items():
        assert tuple(path) in rg.by_number(k).representative_paths
        assert (rg.path_matrix(path) - rg.MATRICES[k]).__abs__().max() < 1e-12
        cls = next(c for c in rg.conjugacy_classes() if k in c)
        images = set()
        for g in D6.elements():
            img = D6.apply_path(g, path)
            images.add(rg.identify(rg.path_matrix(img)).number)
            images.add(rg.identify(rg.path_matrix([{1: 2, 2: 1}.get(f, f) for f in img])).number)
        assert images == set(cls), (k, images)


def test_halo_columns_figures_are_composed_from_the_sub_images():
    """6a = col_2 | col_11、6b = col_3 | col_2：成图对应区域的像素与子图一致（jpg 重压缩容差），且 6a/6b 共用同一 halo_col_2.jpg。"""
    import numpy as np
    from PIL import Image
    mod = _ch7_script()
    img = ROOT / CH7 / "img"
    sky, margin, gap, label = mod["SKY_PX"], mod["MARGIN"], mod["GAP"], mod["LABEL_PX"]
    subs = {k: np.asarray(Image.open(img / f"halo_col_{k}.jpg").convert("L"), float) for k in (2, 11, 3)}
    assert all(s.shape == (sky, sky) for s in subs.values())
    for name, (a, b) in mod["FIGURES"].items():
        canvas = np.asarray(Image.open(img / f"{name}.jpg").convert("L"), float)
        assert canvas.shape == (mod["HEIGHT"], mod["WIDTH"])
        for i, k in enumerate((a, b)):
            x = margin + i * (sky + gap)
            region = canvas[margin + label:margin + label + sky, x:x + sky]
            assert np.abs(region - subs[k]).mean() < 3.0, (name, k)      # 同一批像素（有损压缩残差）
    assert (img / "halo_col_2.jpg").stat().st_size > 0 and mod["FIGURES"]["halos_2_vs_11"][0] == mod["FIGURES"]["halos_3_vs_2"][1] == 2


def test_halo_columns_provenance_present():
    for k in (2, 11, 3):
        d = ROOT / CH7 / "data" / "halo_columns" / f"col_{k}"
        prov = json.loads((d / "provenance.json").read_text())
        assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0
        assert prov["config_sha256"] == config_sha256(_cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json"))


# ---- ch7 7.5 底图（R1-1）：与图 6 同一份仿真、只换 render 段；视场中心 = 该行晕心 ----


def test_pose_to_sky_backdrops_share_the_halo_columns_simulation():
    """crystal / filter / scene 三段与 halo_columns.col_<k> 逐字段相同；render：fisheye_equal_area、1000×1000、
    #3 反日点为中心（太阳方位 + 180°、仰角 Σ）、#2 太阳为中心，网格与图 6 相同。"""
    for k in (3, 2):
        back = _cfg(f"{CH7}/data/pose_to_sky_backdrop.col_{k}.lumice.json")
        base = _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json")
        for section in ("crystal", "filter", "scene"):
            assert back[section] == base[section], (k, section)
        r, r0 = back["render"][0], base["render"][0]
        assert r["lens"]["type"] == "fisheye_equal_area" and r["resolution"] == [1000, 1000]
        assert r["grid"] == r0["grid"] and r["visible"] == "full"
        sun = back["scene"]["light_source"]
        expect_az = (sun["azimuth"] + 180) % 360 if k == 3 else sun["azimuth"]
        assert r["view"] == {"azimuth": expect_az, "elevation": sun["altitude"]}
        prov = json.loads((ROOT / CH7 / "data" / "pose_to_sky_backdrop" / f"col_{k}" / "provenance.json").read_text())
        assert prov["config_sha256"] == config_sha256(back) and prov["lumice_version"] == "v4.5.1"
