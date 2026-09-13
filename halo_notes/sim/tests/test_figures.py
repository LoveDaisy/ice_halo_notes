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


# ---- ch7 图 6a/6b（task-draw-ch7-figs）：三份子图 config 只差过滤器与帧中心；复合过滤器 == 矩阵类代表集合；帧中心机械可复现；拼图由子图像素拼成 ----


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
    """R2-3：三张子图 `globe` 球面外视、fov 30、1400²，除 filter 与 render.view（帧中心）外三份 config 逐字段相同；
    帧中心是候选之一（太阳 / 反日点 / 侧向），view 按 globe 语义 = (az + 180°, −el)；网格：仰角 / 方位每 30° 一条 + 地平线。"""
    import numpy as np
    from halo_notes.sim.projection import frame_center
    cfgs = {k: _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json") for k in (2, 11, 3)}
    stripped = [json.dumps(_strip_filter_and_view(c), sort_keys=True) for c in cfgs.values()]
    assert len(set(stripped)) == 1
    mod = _ch7_script()
    for k, cfg in cfgs.items():
        assert cfg["scene"]["scattering"][0]["entries"] == [{"crystal": 1, "proportion": 100, "filter": 1}]
        assert cfg["scene"]["light_source"]["altitude"] == 10
        r = cfg["render"][0]
        assert r["lens"] == {"type": "globe", "fov": 30} and r["resolution"] == [1400, 1400] and r["visible"] == "full"
        assert cfg["crystal"][0]["axis"]["zenith"]["mean"] == 90 and "roll" not in cfg["crystal"][0]["axis"]   # 柱晶，roll 均匀
        assert cfg["scene"]["ray_num"] == mod["RAY_NUM"]
        name = mod["center_of"](cfg)
        assert np.linalg.norm(frame_center(r) - mod["CANDIDATES"][name]) < 1e-6
        assert r["view"] == {"azimuth": {"sun": 180, "anthelic": 0, "side": 270}[name], "elevation": -10}
        grid = r["grid"]
        assert sorted(g["value"] for g in grid["elevation"]) == list(range(-60, 90, 30))
        assert sorted(g["value"] for g in grid["longitude"]) == list(range(0, 360, 30))
        assert grid["label"] is False


def test_halo_columns_frame_center_is_reproducible_from_the_reference_render():
    """R2-3 帧中心机械选取：对落盘的全天 rectangular 参考图（同一 sim）重算各候选中心 75.5° 球冠内能量占比，argmax 必须等于
    落盘 config 里的帧中心；参考图 config 与子图 config 除 render / ray_num 外相同；#3 反日点、#2 太阳（占比 > 0.8），
    #11 幻日环装不下整圈、按判据落在侧向。"""
    import numpy as np
    from PIL import Image
    mod = _ch7_script()
    for k in (2, 11, 3):
        ref = _cfg(f"{CH7}/data/halo_columns.ref_{k}.lumice.json")
        sub = _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json")
        for section in ("crystal", "filter"):
            assert ref[section] == sub[section], (k, section)
        assert {**ref["scene"], "ray_num": 0} == {**sub["scene"], "ray_num": 0} and ref["scene"]["ray_num"] == mod["REF_RAY_NUM"]
        r = ref["render"][0]
        assert r["lens"]["type"] == "rectangular" and r["ev_mode"] == "absolute" and "grid" not in r
        image = np.asarray(Image.open(ROOT / CH7 / "data" / "halo_columns" / f"ref_{k}" / "img_01.png").convert("RGB"))
        best, fractions = mod["choose_center"](image, r)
        assert best == mod["center_of"](sub), (k, fractions)
        assert set(fractions) == set(mod["CANDIDATES"]) and all(0 <= v <= 1 for v in fractions.values())
    assert mod["center_of"](_cfg(f"{CH7}/data/halo_columns.col_3.lumice.json")) == "anthelic"
    assert mod["center_of"](_cfg(f"{CH7}/data/halo_columns.col_2.lumice.json")) == "sun"
    assert mod["center_of"](_cfg(f"{CH7}/data/halo_columns.col_11.lumice.json")) == "side"


def test_halo_columns_complex_filters_are_exactly_the_class_representatives():
    """R2-1 (c)：每张子图的过滤器段 = 一个 complex（id 1，PBD，OR 全部子过滤器）+ 各代表一个 raypath 子过滤器；复合引用的
    子光路集合 == `reflection_group` 该类的 PBD 代表集合；每条子光路的镜面积 ∈ 目标共轭类且折射抵消。"""
    import sys
    from halo_notes.math import reflection_group as rg
    from halo_notes.sim import config as C
    sys.path.insert(0, str(ROOT / CH7 / "code"))
    import _ch7_sim as S
    for k in (2, 11, 3):
        cfg = _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json")
        flts = cfg["filter"]
        top = flts[0]
        assert top["id"] == S.FILTER_ID == 1 and top["type"] == "complex" and top["symmetry"] == "PBD"
        subs = {f["id"]: f for f in flts[1:]}
        assert C.composition_ids(top) == set(subs) and all(isinstance(c, int) for c in top["composition"])
        assert all(f["type"] == "raypath" and f["symmetry"] == "PBD" for f in subs.values())
        paths = S.class_filter_paths(flts)
        assert paths == set(S.class_representatives(k)) == set(rg.representatives_under_pbd(rg.raypaths_of_class(k)))
        cls = set(rg.class_of(k))
        for seq in paths:
            assert rg.identify(rg.path_matrix(seq)).number in cls and rg.refraction_cancels(seq) and len(seq) <= S.MAX_LEN
        for old in rg.by_number(k).representative_paths:                                  # ch3 的典型光路都被某个代表的轨道覆盖
            assert any(old in rg.pbd_orbit(s) for s in paths), (k, old)
    assert len(S.class_representatives(3)) == 36 and len(S.class_representatives(2)) == 88 and len(S.class_representatives(11)) == 22


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
            assert np.abs(region - subs[k]).mean() < 6.0, (name, k)      # 同一批像素（有损压缩残差；#2 满幅噪点 3.5）
            assert np.corrcoef(region.ravel(), subs[k].ravel())[0, 1] > 0.98, (name, k)
    assert (img / "halo_col_2.jpg").stat().st_size > 0 and mod["FIGURES"]["halos_2_vs_11"][0] == mod["FIGURES"]["halos_3_vs_2"][1] == 2


def test_halo_columns_provenance_present():
    for k in (2, 11, 3):
        for variant in (f"col_{k}", f"ref_{k}"):
            d = ROOT / CH7 / "data" / "halo_columns" / variant
            prov = json.loads((d / "provenance.json").read_text())
            assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0
            assert prov["config_sha256"] == config_sha256(_cfg(f"{CH7}/data/halo_columns.{variant}.lumice.json"))


# ---- ch7 7.5 底图（R1-1 / R2-3）：与图 6 同一份仿真、只换 render 段；globe，帧中心 = 该行参考点与样本质心的角平分方向 ----


def test_pose_to_sky_backdrops_share_the_halo_columns_simulation():
    """crystal / filter / scene 三段与 halo_columns.col_<k> 逐字段相同；render：globe、fov 30、1000×1000、网格与图 6 相同、
    view == `_pose_to_sky.backdrop_view(k)`。"""
    import sys
    sys.path.insert(0, str(ROOT / CH7 / "code"))
    import _pose_to_sky as P
    for k in (3, 2):
        back = _cfg(f"{CH7}/data/pose_to_sky_backdrop.col_{k}.lumice.json")
        base = _cfg(f"{CH7}/data/halo_columns.col_{k}.lumice.json")
        for section in ("crystal", "filter", "scene"):
            assert back[section] == base[section], (k, section)
        r, r0 = back["render"][0], base["render"][0]
        assert r["lens"] == {"type": "globe", "fov": 30} and r["resolution"] == [1000, 1000]
        assert r["grid"] == r0["grid"] and r["visible"] == "full"
        assert r["view"] == P.backdrop_view(k)
        prov = json.loads((ROOT / CH7 / "data" / "pose_to_sky_backdrop" / f"col_{k}" / "provenance.json").read_text())
        assert prov["config_sha256"] == config_sha256(back) and prov["lumice_version"] == "v4.5.1"
