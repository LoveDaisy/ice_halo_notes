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
    ("08-wedge-times-fold/code/fig_b1_same_class.py", "img/same_class.jpg"),
    ("08-wedge-times-fold/code/fig_b2_unnamed_cell.py", "img/unnamed_cell.jpg"),
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


# ---- ch8 图 B1 / B2（task-write-ch8）：单光路对照 / Φ 类整类过滤器；config 除过滤器、帧中心、曝光外逐字段相同；帧中心机械可复现；拼图由子图拼成 ----

CH8 = "08-wedge-times-fold"


def _ch8_script(name: str):
    return runpy.run_path(str(ROOT / CH8 / "code" / name))


def _strip_filter_view_exposure(cfg: dict) -> dict:
    cfg = _strip_filter_and_view(cfg)
    for r in cfg["render"]:
        r.pop("ev_mode", None)
        r.pop("intensity_factor", None)
    return cfg


def test_ch8_b_figures_configs_differ_only_by_filter_view_and_exposure():
    """B1 两张子图（同一绝对曝光）之间只差过滤器与帧中心；B1 与 B2（片晶）之间再差曝光模式；共同点：片晶 h/a=0.2（Lumice height 0.1）、
    zenith σ=0.5°、Σ=10°、globe fov 30、1400²、经纬网格 30°、max_hits 9。"""
    b1 = {tag: _cfg(f"{CH8}/data/same_class.{tag}.lumice.json") for tag in ("3-5", "3-1-2-5")}
    b2 = _cfg(f"{CH8}/data/unnamed_cell.plate.lumice.json")
    assert len({json.dumps(_strip_filter_and_view(c), sort_keys=True) for c in b1.values()}) == 1
    assert len({json.dumps(_strip_filter_view_exposure(c), sort_keys=True) for c in (*b1.values(), b2)}) == 1
    for r in (c["render"][0] for c in b1.values()):
        assert r["ev_mode"] == "absolute" and r["intensity_factor"] == 0.5                  # 两张图亮度可直接比
    assert b2["render"][0]["ev_mode"] == "relative"
    for cfg in (*b1.values(), b2):
        cr = cfg["crystal"][0]
        assert cr["shape"]["height"] == 0.1 and cr["axis"]["zenith"] == {"type": "gauss", "mean": 0, "std": 0.5} and "roll" not in cr["axis"]
        assert cfg["scene"]["light_source"]["altitude"] == 10 and cfg["scene"]["max_hits"] == 9
        assert cfg["scene"]["scattering"][0]["entries"] == [{"crystal": 1, "proportion": 100, "filter": 1}]
        r = cfg["render"][0]
        assert r["lens"] == {"type": "globe", "fov": 30} and r["resolution"] == [1400, 1400] and r["visible"] == "full"
        assert sorted(g["value"] for g in r["grid"]["elevation"]) == list(range(-60, 90, 30))
        assert sorted(g["value"] for g in r["grid"]["longitude"]) == list(range(0, 360, 30))


def test_ch8_b1_two_single_paths_share_phi_class_center_and_shape():
    """B1：过滤器各是一条单光路（PBD），两条同属 Φ 类 A60-12；帧中心由参考图机械复现且两张一致（太阳）；
    两张子图像素相关 > 0.99（形状相同）、参考图全天能量之比在 0.8–1.2（片晶取向下亮度相当——提纲「暗三个数量级」不成立）。"""
    import sys
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(ROOT / CH8 / "code"))
    import _ch8_sim as S
    mod = _ch8_script("fig_b1_same_class.py")
    centers, energies, grays = {}, {}, {}
    for tag, faces in mod["PATHS"].items():
        sub = _cfg(f"{CH8}/data/same_class.{tag}.lumice.json")
        ref = _cfg(f"{CH8}/data/same_class.ref_{tag}.lumice.json")
        assert sub["filter"] == [{"id": 1, "type": "raypath", "raypath": list(faces), "symmetry": "PBD", "action": "filter_in"}]
        assert S.class_filter_paths(sub["filter"]) == {faces} and S.class_id_of(mod["RATIO"], faces) == "A60-12"
        assert ref["crystal"] == sub["crystal"] and ref["filter"] == sub["filter"]
        assert {**ref["scene"], "ray_num": 0} == {**sub["scene"], "ray_num": 0} and ref["scene"]["ray_num"] == mod["REF_RAY_NUM"]
        r = ref["render"][0]
        assert r["lens"]["type"] == "rectangular" and r["ev_mode"] == "absolute" and r["intensity_factor"] == mod["REF_INTENSITY"]
        image = np.asarray(Image.open(ROOT / CH8 / "data" / "same_class" / f"ref_{tag}" / "img_01.png").convert("RGB"))
        assert image.max() < 255                                                           # 参考图不削顶，能量比才可信
        centers[tag], _ = S.choose_center(image, r)
        assert centers[tag] == mod["center_of"](sub)
        energies[tag] = S.sky_energy(image, r)
        grays[tag] = np.asarray(Image.open(ROOT / CH8 / "img" / f"same_class_{tag}.jpg").convert("L"))
    assert set(centers.values()) == {"sun"}
    assert 0.8 < energies["3-1-2-5"] / energies["3-5"] < 1.2, energies
    assert mod["shape_similarity"](grays["3-5"], grays["3-1-2-5"]) > 0.99


def test_ch8_b2_complex_filter_is_exactly_the_phi_class_members():
    """B2：过滤器段 = 一个 complex（id 1，PBD，OR 全部子过滤器）+ 每条代表一个 raypath 子过滤器；子光路集合 == 枚举器在 h/a=0.2 下
    落入 A60-10 的全部 PBD 代表（59 条，与 signature_table.md「光路条数」表一致）；柱晶参考图（h/a=2）的 37 条也都属于 A60-10。"""
    import sys
    from halo_notes.sim import config as C
    sys.path.insert(0, str(ROOT / CH8 / "code"))
    import _ch8_sim as S
    mod = _ch8_script("fig_b2_unnamed_cell.py")
    for orientation, expected_n in (("plate", 59), ("column", 37)):
        cfg = _cfg(f"{CH8}/data/unnamed_cell.ref_{orientation}.lumice.json")
        top = cfg["filter"][0]
        assert top["id"] == S.FILTER_ID == 1 and top["type"] == "complex" and top["symmetry"] == "PBD"
        subs = {f["id"]: f for f in cfg["filter"][1:]}
        assert C.composition_ids(top) == set(subs) and all(f["type"] == "raypath" and f["symmetry"] == "PBD" for f in subs.values())
        paths = S.class_filter_paths(cfg["filter"])
        ratio = mod["ORIENTATIONS"][orientation]
        assert len(paths) == expected_n and all(S.class_id_of(ratio, p) == "A60-10" for p in paths)
        assert (3, 4, 5, 7) in paths and (3, 5, 6, 7) in paths                             # 最短代表 / Liljequist 幻日主光路
    plate = _cfg(f"{CH8}/data/unnamed_cell.plate.lumice.json")
    assert plate["filter"] == _cfg(f"{CH8}/data/unnamed_cell.ref_plate.lumice.json")["filter"]
    assert S.class_filter_paths(plate["filter"]) == set(S.class_representatives("A60-10", 0.2))     # 重新枚举（约 50 s）


def test_ch8_b2_frame_center_and_spots_are_reproducible_from_the_reference_render():
    """B2 帧中心 = 反日点（参考图 75.5° 球冠占比 argmax）；「渲染成立」的量化锚点：片晶参考图上两个亮斑质心在方位 ±140–165°、
    仰角 ≈ 太阳高度（±3°），两个 5° 圆内装下 > 50% 的全天能量（紧凑、可辨认）；柱晶参考图 5° 圆内 < 10%（弥散，落选）。"""
    import sys
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(ROOT / CH8 / "code"))
    import _ch8_sim as S
    mod = _ch8_script("fig_b2_unnamed_cell.py")
    sub = _cfg(f"{CH8}/data/unnamed_cell.plate.lumice.json")
    assert mod["center_of"](sub) == "anthelic"
    stats = {}
    for orientation in ("plate", "column"):
        ref = _cfg(f"{CH8}/data/unnamed_cell.ref_{orientation}.lumice.json")
        r = ref["render"][0]
        assert r["lens"]["type"] == "rectangular" and r["ev_mode"] == "absolute" and "grid" not in r
        image = np.asarray(Image.open(ROOT / CH8 / "data" / "unnamed_cell" / f"ref_{orientation}" / "img_01.png").convert("RGB"))
        best, fr = S.choose_center(image, r)
        assert best == "anthelic" and fr["anthelic"] > 0.9
        stats[orientation] = mod["spot_stats"](image, r)
    st = stats["plate"]
    assert 140 < st["az_deg"] < 165 and abs(st["el_deg"] - 10) < 3 and st["within_frac"] > 0.5, st
    assert stats["column"]["within_frac"] < 0.1, stats["column"]
    assert {**_cfg(f"{CH8}/data/unnamed_cell.ref_plate.lumice.json")["scene"], "ray_num": 0} == {**sub["scene"], "ray_num": 0}


def test_ch8_b_figures_are_composed_from_the_sub_images():
    import numpy as np
    from PIL import Image
    img = ROOT / CH8 / "img"
    b1, b2 = _ch8_script("fig_b1_same_class.py"), _ch8_script("fig_b2_unnamed_cell.py")
    sky, margin, gap, label = b1["SKY_PX"], b1["MARGIN"], b1["GAP"], b1["LABEL_PX"]
    canvas = np.asarray(Image.open(img / "same_class.jpg").convert("L"), float)
    assert canvas.shape == (b1["HEIGHT"], b1["WIDTH"])
    for i, tag in enumerate(b1["PATHS"]):
        s = np.asarray(Image.open(img / f"same_class_{tag}.jpg").convert("L"), float)
        assert s.shape == (sky, sky)
        x = margin + i * (sky + gap)
        region = canvas[margin + label:margin + label + sky, x:x + sky]
        assert np.abs(region - s).mean() < 2.0 and np.corrcoef(region.ravel(), s.ravel())[0, 1] > 0.95, tag   # 画面大片纯黑，jpg 暗部噪声压低相关（实测 0.97–0.99），均差 < 0.5
    canvas = np.asarray(Image.open(img / "unnamed_cell.jpg").convert("L"), float)
    assert canvas.shape == (b2["HEIGHT"], b2["WIDTH"])
    s = np.asarray(Image.open(img / f"unnamed_cell_{b2['CHOSEN']}.jpg").convert("L"), float)
    region = canvas[b2["MARGIN"] + b2["LABEL_PX"]:b2["MARGIN"] + b2["LABEL_PX"] + sky, b2["MARGIN"]:b2["MARGIN"] + sky]
    assert np.abs(region - s).mean() < 2.0 and np.corrcoef(region.ravel(), s.ravel())[0, 1] > 0.95


def test_ch8_b_figures_provenance_present():
    for name, variants in (("same_class", ("3-5", "3-1-2-5", "ref_3-5", "ref_3-1-2-5")), ("unnamed_cell", ("plate", "ref_plate", "ref_column"))):
        for variant in variants:
            prov = json.loads((ROOT / CH8 / "data" / name / variant / "provenance.json").read_text())
            assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0
            assert prov["config_sha256"] == config_sha256(_cfg(f"{CH8}/data/{name}.{variant}.lumice.json"))
