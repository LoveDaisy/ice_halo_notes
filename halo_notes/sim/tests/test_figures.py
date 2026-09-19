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
    ("08-wedge-times-fold/code/fig_b2_unnamed_cell.py", "img/unnamed_cell.png"),
    ("08-wedge-times-fold/code/fig_cross_section_sensitivity.py", "img/cross_section_sensitivity.png"),
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


# ---- ch8 图 B1 / B2 / 截面敏感性（task-write-ch8 / task-backfill-ch8 / task-revise-ch8）：单光路对照 / Φ 类整类过滤器；三份 B1 config 只差过滤器；
# B1 与 B2 同一 population（片晶 h/a=0.2），太阳高度 B1 10°、B2 系列 0°（各自显式）；B2 三件套各自独立文件、globe 斜视偏移 / 裁切窗口 / 剖面数字机械可复现；
# 截面敏感性：face_distance 交替四档、A60-10 锐边不动能量单调降、A0-02 窄峰摊平 ----

CH8 = "08-wedge-times-fold"
B1_TAGS = ("3-1-5-2-6-7", "3-1-5-6-2-7", "3-1-2-5-6-7")
B2_VARIANTS = ("globe", "rect", "ref_A60-10", "ref_A0-02", "ref_all")


def _ch8_script(name: str):
    return runpy.run_path(str(ROOT / CH8 / "code" / name))


def _ch8_sim():
    import sys
    sys.path.insert(0, str(ROOT / CH8 / "code"))
    import _ch8_sim as S
    return S


def _strip_filter(cfg: dict) -> dict:
    cfg = json.loads(json.dumps(cfg))
    cfg["filter"] = None
    for layer in cfg["scene"]["scattering"]:
        for e in layer["entries"]:
            e.pop("filter", None)
    return cfg


def _no_ray_num(scene: dict) -> dict:
    return {**scene, "ray_num": 0}


def _b2_cfgs() -> dict[str, dict]:
    return {v: _cfg(f"{CH8}/data/unnamed_cell.{v}.lumice.json") for v in B2_VARIANTS}


def test_ch8_b_figures_configs_share_crystal_and_differ_in_sun_altitude():
    """B1 三张子图（同一绝对曝光、同一 rectangular 全天镜头）之间**只差过滤器**；B1 与 B2 全部五份 config 的 crystal 段逐字段相同（片晶 h/a=0.2 =
    Lumice height 0.1、zenith σ=0.5°、无 roll），max_hits 9；太阳高度 **B1 = 10°、B2 系列 = 0°**（task-revise-ch8：两层同现需太阳贴地平线），
    B2 五份之间 scene 段（去掉过滤器、光线数）逐字段相同；B1 子图与 B2 rect 都是 rectangular 5760×2880、absolute；B1 子图带 30° 经纬网格，
    B2 rect 不带（拼版时由坐标轴给参考）；B2 globe 是 globe fov 30、relative、带同一套 30° 网格。"""
    b1m, b2m = _ch8_script("fig_b1_same_class.py"), _ch8_script("fig_b2_unnamed_cell.py")
    b1 = {tag: _cfg(f"{CH8}/data/same_class.{tag}.lumice.json") for tag in B1_TAGS}
    b2 = _b2_cfgs()
    assert tuple(b1m["PATHS"]) == B1_TAGS
    assert len({json.dumps(_strip_filter(c), sort_keys=True) for c in b1.values()}) == 1
    assert len({json.dumps(c["crystal"], sort_keys=True) for c in (*b1.values(), *b2.values())}) == 1
    assert len({json.dumps(_no_ray_num(_strip_filter(c)["scene"]), sort_keys=True) for c in b2.values()}) == 1
    for cfg in (*b1.values(), *b2.values()):
        cr = cfg["crystal"][0]
        assert cr["shape"] == {"height": 0.1} and cr["axis"]["zenith"] == {"type": "gauss", "mean": 0, "std": 0.5} and "roll" not in cr["axis"]
        assert cfg["scene"]["max_hits"] == 9
    for cfg in b1.values():
        assert cfg["scene"]["light_source"]["altitude"] == 10 and cfg["scene"]["scattering"][0]["entries"] == [{"crystal": 1, "proportion": 100, "filter": 1}]
    for v, cfg in b2.items():
        assert cfg["scene"]["light_source"]["altitude"] == 0 == b2m["SUN_ALT"], v
        entries = cfg["scene"]["scattering"][0]["entries"]
        assert entries == ([{"crystal": 1, "proportion": 100}] if v == "ref_all" else [{"crystal": 1, "proportion": 100, "filter": 1}]), v
    rect = b2["rect"]["render"][0]
    b1_grid = b1[B1_TAGS[0]]["render"][0]["grid"]
    for r in (*(c["render"][0] for c in b1.values()), rect):
        assert r["lens"]["type"] == "rectangular" and r["resolution"] == [5760, 2880] == list(b1m["SUB_RESOLUTION"]) == list(b2m["SUB_RESOLUTION"])
        assert r["ev_mode"] == "absolute" and r["visible"] == "full"
    for r in (c["render"][0] for c in b1.values()):
        assert r["grid"] == b1_grid
        assert sorted(g["value"] for g in r["grid"]["elevation"]) == list(range(-60, 90, 30))
        assert sorted(g["value"] for g in r["grid"]["longitude"]) == list(range(0, 360, 30))
    assert "grid" not in rect
    assert b1[B1_TAGS[0]]["render"][0]["intensity_factor"] == b1m["INTENSITY"] and rect["intensity_factor"] == b2m["INTENSITY"]
    globe = b2["globe"]["render"][0]
    assert globe["ev_mode"] == "relative" and globe["lens"] == {"type": "globe", "fov": 30} and globe["grid"] == b1_grid
    for v in ("ref_A60-10", "ref_A0-02", "ref_all"):
        r = b2[v]["render"][0]
        assert r["lens"]["type"] == "rectangular" and r["resolution"] == [1440, 720] and r["ev_mode"] == "absolute" and "grid" not in r
        assert r["intensity_factor"] == b2m["REF_INTENSITY"]                                # 三张参考图同一绝对曝光，剖面曲线可直接比


def test_ch8_b1_three_paths_share_phi_class_and_shape():
    """B1：过滤器各是一条单光路（PBD），三条同属 Φ 类 A60-10；参考图（rectangular、absolute、不削顶）机械复现：主对照两条
    （`3-1-5-2-6-7` / `3-1-5-6-2-7`）全天能量之比在 0.9–1.1、窗口内像素相关 > 0.98（同形同亮）；反衬 `3-1-2-5-6-7` 能量比在 0.1–0.3
    （暗约 5 倍）、相关 < 0.95（只亮一段），且幻日环条带上它落在内侧 142°–150° 的能量占比比主对照高 ≥ 0.1；子图 = 参考窗口的 4× 放大。"""
    import numpy as np
    from PIL import Image
    S = _ch8_sim()
    mod = _ch8_script("fig_b1_same_class.py")
    base, contrast = mod["BASE"], "3-1-2-5-6-7"
    energies, windows, inner = {}, {}, {}
    for tag, faces in mod["PATHS"].items():
        sub = _cfg(f"{CH8}/data/same_class.{tag}.lumice.json")
        ref = _cfg(f"{CH8}/data/same_class.ref_{tag}.lumice.json")
        assert sub["filter"] == [{"id": 1, "type": "raypath", "raypath": list(faces), "symmetry": "PBD", "action": "filter_in"}]
        assert S.class_filter_paths(sub["filter"]) == {faces} and S.class_id_of(mod["RATIO"], faces) == "A60-10"
        assert ref["crystal"] == sub["crystal"] and ref["filter"] == sub["filter"]
        assert _no_ray_num(ref["scene"]) == _no_ray_num(sub["scene"]) and ref["scene"]["ray_num"] == mod["REF_RAY_NUM"]
        r = ref["render"][0]
        assert r["lens"]["type"] == "rectangular" and r["ev_mode"] == "absolute" and r["intensity_factor"] == mod["REF_INTENSITY"] and "grid" not in r
        image = np.asarray(Image.open(ROOT / CH8 / "data" / "same_class" / f"ref_{tag}" / "img_01.png").convert("RGB"))
        assert image.max() < 255                                                           # 参考图不削顶，能量比才可信
        energies[tag] = S.sky_energy(image, r)
        windows[tag] = mod["window_luminance"](image, r)
        prof = mod["strip_profile"](image, r)
        inner[tag] = prof[(mod["STRIP_BINS"][:-1] >= 142) & (mod["STRIP_BINS"][:-1] < 150)].sum() / prof.sum()
        rows, cols = S.rectangular_window(sub["render"][0], mod["WINDOW_AZ"], mod["WINDOW_EL"])
        assert (cols.stop - cols.start, rows.stop - rows.start) == (mod["SUB_W"], mod["SUB_H"]) == (960, 480)
        rr, rc = S.rectangular_window(r, mod["WINDOW_AZ"], mod["WINDOW_EL"])
        assert (rows.start, rows.stop, cols.start, cols.stop) == (4 * rr.start, 4 * rr.stop, 4 * rc.start, 4 * rc.stop)
        assert Image.open(ROOT / CH8 / "img" / f"same_class_{tag}.jpg").size == (960, 480)
    other = [t for t in B1_TAGS if t not in (base, contrast)][0]
    assert 0.9 < energies[other] / energies[base] < 1.1, energies
    assert 0.1 < energies[contrast] / energies[base] < 0.3, energies
    assert mod["shape_similarity"](windows[base], windows[other]) > 0.98
    assert mod["shape_similarity"](windows[base], windows[contrast]) < 0.95
    assert inner[contrast] > inner[base] + 0.1 and inner[contrast] > inner[other] + 0.1, inner


def test_ch8_b2_complex_filters_are_exactly_the_phi_class_members():
    """B2：A60-10 参考图 / globe / rect 三份过滤器段相同 = 一个 complex（id 1，PBD，OR 全部子过滤器）+ 每条代表一个 raypath 子过滤器，子光路集合 ==
    枚举器在 h/a=0.2 下落入 A60-10 的全部 PBD 代表（59 条，与 signature_table.md「光路条数」表一致，含 `3-4-5-7` / `3-5-6-7`）；A0-02 参考图同形态、
    108 条（含幻日环主光路 `1-3-2` 与 Liljequist 窄峰光路 `3-5-6-7-3`）；「全部」参考图不带过滤器。"""
    from halo_notes.sim import config as C
    S = _ch8_sim()
    mod = _ch8_script("fig_b2_unnamed_cell.py")
    b2 = _b2_cfgs()
    assert b2["ref_all"]["filter"] == [] and mod["CURVES"] == {"A60-10": "A60-10", "A0-02": "A0-02", "all": None}
    assert b2["globe"]["filter"] == b2["rect"]["filter"] == b2["ref_A60-10"]["filter"]
    for cid, expected_n, must in (("A60-10", 59, {(3, 4, 5, 7), (3, 5, 6, 7)}), ("A0-02", 108, {(1, 3, 2), (3, 5, 6, 7, 3)})):
        cfg = b2[f"ref_{cid}"]
        top = cfg["filter"][0]
        assert top["id"] == S.FILTER_ID == 1 and top["type"] == "complex" and top["symmetry"] == "PBD"
        subs = {f["id"]: f for f in cfg["filter"][1:]}
        assert C.composition_ids(top) == set(subs) and all(f["type"] == "raypath" and f["symmetry"] == "PBD" for f in subs.values())
        paths = S.class_filter_paths(cfg["filter"])
        assert len(paths) == expected_n and must <= paths and all(S.class_id_of(mod["RATIO"], p) == cid for p in paths)
        assert paths == set(S.class_representatives(cid, mod["RATIO"]))                    # 重新枚举（约 50 s，进程内缓存）


def test_ch8_b2_globe_offset_window_and_profile_numbers_are_reproducible():
    """B2 三件套的机械锚点：globe 帧中心在幻日环高度上、方位偏离反日点 GLOBE_OFFSET_DEG=10°（作者：不正对；25° 时远侧亮斑压球缘，
    2026-09-19 试渲 10/15/25 后收到 10°）；rect 裁切窗口
    方位 120°–180°、仰角 −10°…+20° → 960×480；A60-10 参考图两个亮斑质心方位 ±140–165°、仰角 ≈ 0°、5° 圆内 > 50% 全天能量；
    剖面（±1.5° 条带、0.5° 桶，`S.azimuth_profile`）特征：A60-10 锐边（内侧半高）141–144°、峰值 148–153°、外缘（10% 峰值）159–164°、
    锐边宽度（10%→半高）< 1.5°；A0-02 窄峰 152–156°、FWHM < 8°、峰位在 A60-10 锐边外侧 ≥ 8°；`far_side_profile.csv` == 从参考图重算的三条曲线。"""
    import csv
    import numpy as np
    from PIL import Image
    S = _ch8_sim()
    mod = _ch8_script("fig_b2_unnamed_cell.py")
    b2 = _b2_cfgs()
    assert abs(mod["globe_offset_of"](b2["globe"]) - mod["GLOBE_OFFSET_DEG"]) < 1e-6 and mod["GLOBE_OFFSET_DEG"] == 10.0
    rows, cols = S.rectangular_window(b2["rect"]["render"][0], mod["WINDOW_AZ"], mod["WINDOW_EL"])
    assert (mod["WINDOW_AZ"], mod["WINDOW_EL"]) == ((120.0, 180.0), (-10.0, 20.0))
    assert (cols.stop - cols.start, rows.stop - rows.start) == (mod["SUB_W"], mod["SUB_H"]) == (960, 480)
    hists, features = {}, {}
    for name in mod["CURVES"]:
        r = b2[f"ref_{name}"]["render"][0]
        image = np.asarray(Image.open(ROOT / CH8 / "data" / "unnamed_cell" / f"ref_{name}" / "img_01.png").convert("RGB"))
        assert S.strip_max(image, r, mod["SUN_ALT"], half_deg=mod["PROFILE_HALF_DEG"], az_range=mod["FEATURE_WINDOW"]) < 255, name
        centers, hists[name] = mod["profile"](image, r)
        features[name] = S.profile_features(centers, hists[name])
        if name == "A60-10":
            st = mod["spot_stats"](image, r)
            assert 140 < st["az_deg"] < 165 and abs(st["el_deg"]) < 3 and st["within_frac"] > 0.5, st
    a, b = features["A60-10"], features["A0-02"]
    assert 141 < a["edge_az"] < 144 and 148 < a["peak_az"] < 153 and 159 < a["outer_az"] < 164 and a["edge_width_deg"] < 1.5, a
    assert 152 < b["peak_az"] < 156 and b["fwhm_deg"] < 8 and b["peak_az"] - a["edge_az"] >= 8, b
    assert abs(features["all"]["peak_az"] - b["peak_az"]) <= 1                             # 全部光路的峰就是 Liljequist 窄峰
    with (ROOT / CH8 / "data" / "far_side_profile.csv").open() as f:
        table = list(csv.DictReader(f))
    assert [row["az_deg"] for row in table] == [f"{c:.2f}" for c in centers]
    for name, h in hists.items():
        assert np.allclose([float(row[name]) for row in table], h, atol=2e-6), name
    assert (ROOT / CH8 / "data" / "far_side_profile_numbers.txt").read_text().count("\n") >= 8


def test_ch8_b1_figure_is_composed_from_the_sub_images():
    import numpy as np
    from PIL import Image
    img = ROOT / CH8 / "img"
    b1 = _ch8_script("fig_b1_same_class.py")
    w, h, margin, gap, label = b1["SUB_W"], b1["SUB_H"], b1["MARGIN"], b1["GAP"], b1["LABEL_PX"]
    canvas = np.asarray(Image.open(img / "same_class.jpg").convert("L"), float)
    assert canvas.shape == (b1["HEIGHT"], b1["WIDTH"]) and tuple(b1["PATHS"]) == B1_TAGS
    for i, tag in enumerate(b1["PATHS"]):                                                # 三张子图上下叠放，各带一行标签
        s = np.asarray(Image.open(img / f"same_class_{tag}.jpg").convert("L"), float)
        assert s.shape == (h, w)
        y = margin + i * (h + label + gap)
        region = canvas[y + label:y + label + h, margin:margin + w]
        assert np.abs(region - s).mean() < 2.0 and np.corrcoef(region.ravel(), s.ravel())[0, 1] > 0.95, tag   # 画面大片纯黑，jpg 暗部噪声压低相关，均差 < 0.5


def test_ch8_b2_composite_figure_and_rect_without_grid():
    """B2 拼版（图 6）：正式图只有一张 `unnamed_cell.png`（2100×1050：左 globe 反相定位 + 右上 rect 局部 + 右下方位剖面），旧的三张
    分立文件不再存在；rect 渲染 config 不带 Lumice 网格（拼版时由坐标轴给参考，网格线会压在骑地平线的亮斑上），globe 仍带 30° 网格；
    `crop_sub` 从 rect 原图裁出的窗口仍是 960×480；`--replot` 只从 data/ 重画不跑 Lumice。"""
    import numpy as np
    from PIL import Image
    mod = _ch8_script("fig_b2_unnamed_cell.py")
    img, data = ROOT / CH8 / "img", ROOT / CH8 / "data" / "unnamed_cell"
    for old in ("unnamed_cell_globe.jpg", "unnamed_cell_rect.jpg", "far_side_profile.png"):
        assert not (img / old).exists(), old
    composite = Image.open(img / "unnamed_cell.png")
    assert composite.size == (2100, 1050)
    b2 = _b2_cfgs()
    assert "grid" not in b2["rect"]["render"][0] and "grid" in b2["globe"]["render"][0]
    full = Image.open(data / "rect" / "img_01.png").convert("RGB")
    crop = mod["crop_sub"](full, b2["rect"]["render"][0])
    assert crop.size == (960, 480)
    assert np.asarray(Image.open(data / "globe" / "img_01.png").convert("L")).shape == (1400, 1400)
    assert (img / "cross_section_sensitivity.png").exists()
    assert set(mod["STEPS"]) == {"refs", "globe", "rect", "compose"}


def test_ch8_cross_section_sensitivity_configs_and_trends():
    """截面敏感性（图 7）：4 档 d × 2 类 = 8 份 config，crystal 只差 `face_distance == [1, d, 1, d, 1, d]`（其余与 B2 片晶相同），太阳 0°、
    过滤器 == 各类全部代表（与 B2 参考图同一过滤器段）、同一绝对曝光；summary.csv（从参考图重算核对）里的现象方向：A60-10 锐边位置四档
    全在 141–144°（纹丝不动，极差 < 1.5°）、条带能量随 d 单调下降；A0-02 d=1 是 FWHM < 8° 的窄峰，d ≥ 1.2 起 FWHM 至少翻倍（摊平），
    条带总能量 d=1.2 起高于 d=1（反升）。"""
    import csv
    import numpy as np
    from PIL import Image
    S = _ch8_sim()
    mod = _ch8_script("fig_cross_section_sensitivity.py")
    b2 = _b2_cfgs()
    assert mod["DS"] == (1.0, 1.2, 1.4, 1.8) and mod["CLASSES"] == ("A60-10", "A0-02") and mod["SUN_ALT"] == 0.0
    with (ROOT / CH8 / "data" / "cross_section_sensitivity_summary.csv").open() as f:
        summary = {(float(r["d"]), r["class"]): {k: float(v) for k, v in r.items() if k not in ("d", "class")} for r in csv.DictReader(f)}
    assert set(summary) == {(d, c) for d in mod["DS"] for c in mod["CLASSES"]}
    for d in mod["DS"]:
        for cid in mod["CLASSES"]:
            v = mod["variant"](d, cid)
            cfg = _cfg(f"{CH8}/data/cross_section.{v}.lumice.json")
            cr = cfg["crystal"][0]
            assert cr["shape"]["face_distance"] == [1, d, 1, d, 1, d] and {**cr["shape"], "face_distance": None} == {"height": 0.1, "face_distance": None}
            assert {**cr, "shape": None} == {**b2["rect"]["crystal"][0], "shape": None}
            assert cfg["filter"] == b2[f"ref_{cid}"]["filter"] and _no_ray_num(cfg["scene"]) == _no_ray_num(b2[f"ref_{cid}"]["scene"])
            assert cfg["render"][0] == b2[f"ref_{cid}"]["render"][0]
            image = np.asarray(Image.open(ROOT / CH8 / "data" / "cross_section" / v / "img_01.png").convert("RGB"))
            assert S.strip_max(image, cfg["render"][0], mod["SUN_ALT"], half_deg=mod["PROFILE_HALF_DEG"], az_range=S.FEATURE_WINDOW) < 255, (d, cid)
            centers, hist = S.azimuth_profile(image, cfg["render"][0], mod["SUN_ALT"], half_deg=mod["PROFILE_HALF_DEG"], bin_deg=mod["PROFILE_BIN_DEG"])
            fe = S.profile_features(centers, hist)
            assert all(abs(fe[k] - summary[(d, cid)][k]) < 1e-3 for k in ("energy", "peak_az", "edge_az", "fwhm_deg")), (d, cid)
    a = [summary[(d, "A60-10")] for d in mod["DS"]]
    assert all(141 < x["edge_az"] < 144 for x in a) and max(x["edge_az"] for x in a) - min(x["edge_az"] for x in a) < 1.5, a
    assert all(x["energy"] > y["energy"] for x, y in zip(a, a[1:])), [x["energy"] for x in a]
    b = [summary[(d, "A0-02")] for d in mod["DS"]]
    assert b[0]["fwhm_deg"] < 8 and all(x["fwhm_deg"] > 2 * b[0]["fwhm_deg"] for x in b[1:]), [x["fwhm_deg"] for x in b]
    assert all(x["energy"] > b[0]["energy"] for x in b[1:]), [x["energy"] for x in b]


def test_ch8_figures_provenance_present():
    cs = _ch8_script("fig_cross_section_sensitivity.py")
    cs_variants = tuple(cs["variant"](d, c) for d in cs["DS"] for c in cs["CLASSES"])
    for name, variants in (("same_class", (*B1_TAGS, *(f"ref_{t}" for t in B1_TAGS))), ("unnamed_cell", B2_VARIANTS), ("cross_section", cs_variants)):
        for variant in variants:
            prov = json.loads((ROOT / CH8 / "data" / name / variant / "provenance.json").read_text())
            assert prov["lumice_version"] == "v4.5.1" and prov["wall_clock_s"] > 0
            assert prov["config_sha256"] == config_sha256(_cfg(f"{CH8}/data/{name}.{variant}.lumice.json"))
