"""config.py 单测：断言序列化后的字段值（不是"builder 没抛异常"）。"""

from __future__ import annotations

import json

import pytest

from halo_notes.sim import config as C


def _minimal(**kw):
    plate = C.prism_crystal(1, 0.5, axis=C.plate_axis(1.0))
    sc = C.scene(C.sun(25), 1000, [C.entry(1)])
    r = C.render_unit(1, C.lens("fisheye_equal_area", fov=180), [100, 100])
    return C.build_config([plate], kw.get("filters", []), sc, [r])


def test_four_sections_and_json_roundtrip():
    cfg = _minimal()
    assert set(cfg) == {"crystal", "filter", "scene", "render"}
    assert json.loads(json.dumps(cfg)) == cfg


def test_duplicate_ids_rejected():
    c1 = C.prism_crystal(1, 0.5)
    c2 = C.prism_crystal(1, 2.0)
    sc = C.scene(C.sun(25), 1000, [C.entry(1)])
    with pytest.raises(ValueError, match="crystal 段 id 重复"):
        C.build_config([c1, c2], [], sc, [C.render_unit(1, C.lens("linear", fov=40), [10, 10])])


def test_dangling_references_rejected():
    sc = C.scene(C.sun(25), 1000, [C.entry(7)])
    with pytest.raises(ValueError, match="不存在的 crystal id 7"):
        C.build_config([C.prism_crystal(1, 0.5)], [], sc, [C.render_unit(1, C.lens("linear", fov=40), [10, 10])])
    sc = C.scene(C.sun(25), 1000, [C.entry(1, filter=3)])
    with pytest.raises(ValueError, match="不存在的 filter id 3"):
        C.build_config([C.prism_crystal(1, 0.5)], [], sc, [C.render_unit(1, C.lens("linear", fov=40), [10, 10])])


def test_ray_num_is_total_integer():
    sc = C.scene(C.sun(25), 4_000_000, [C.entry(1)])
    assert sc["ray_num"] == 4_000_000 and type(sc["ray_num"]) is int
    assert sc["scattering"][0]["prob"] == 0  # doc: prob 必填
    assert C.scene(C.sun(25), "infinite", [C.entry(1)])["ray_num"] == "infinite"
    with pytest.raises(TypeError):
        C.scene(C.sun(25), 1e6, [C.entry(1)])  # 浮点不接受
    with pytest.raises(TypeError):
        C.scene(C.sun(25), "1000000", [C.entry(1)])


def test_plate_and_column_axis_means():
    p = C.prism_crystal(1, 0.3, axis=C.plate_axis(0.8))
    assert p["axis"]["zenith"] == {"type": "gauss", "mean": 0, "std": 0.8}
    assert "roll" not in p["axis"] and "azimuth" not in p["axis"]  # 省略 = 均匀
    c = C.prism_crystal(2, 2.0, axis=C.column_axis(0.3))
    assert c["axis"]["zenith"]["mean"] == 90
    pa = C.parry_axis(0.3, 1.0)
    assert pa["zenith"]["mean"] == 90 and pa["roll"]["type"] == "gauss"
    assert C.random_axis()["zenith"] == {"type": "uniform", "mean": 90, "std": 180}


def test_fixed_orientation_omits_axis_entirely():
    assert "axis" not in C.prism_crystal(1, 1.0)
    with pytest.raises(ValueError, match="zenith"):
        C.prism_crystal(1, 1.0, axis={"roll": 0})


def test_raypath_filter_symmetry_serialized():
    f = C.raypath_filter(1, [3, 5], "P")
    cfg = _minimal(filters=[f])
    assert cfg["filter"][0]["raypath"] == [3, 5]
    assert cfg["filter"][0]["symmetry"] == "P"
    assert C.raypath_filter(2, [1, 3])["symmetry"] == ""
    with pytest.raises(ValueError):
        C.raypath_filter(3, [3, 5], "PBX")


def test_lens_fov_rules():
    assert C.lens("dual_fisheye_equal_area") == {"type": "dual_fisheye_equal_area", "fov": 180}
    assert C.lens("globe")["fov"] == 30
    assert C.lens("linear", f=14) == {"type": "linear", "f": 14}
    with pytest.raises(ValueError, match="fov"):
        C.lens("fisheye_equal_area")
    with pytest.raises(ValueError):
        C.lens("pinhole", fov=40)


def test_render_unit_fields_and_extra_override():
    r = C.render_unit(
        1, C.lens("globe"), [1600, 1600], view={"azimuth": 0, "elevation": 20}, visible="full",
        background=[1, 1, 1], ev_mode="absolute", intensity_factor=2.0,
        grid=C.grid(horizon=True, elevation=[C.grid_line(30, opacity=0.3)]), filter_ids=[2], extra={"front": True},
    )
    assert r["ev_mode"] == "absolute" and r["intensity_factor"] == 2.0 and r["visible"] == "full"
    assert r["grid"]["horizon"] is True and r["grid"]["elevation"][0] == {"value": 30, "opacity": 0.3}
    assert r["filter"] == [2] and r["front"] is True
    with pytest.raises(ValueError):
        C.render_unit(1, C.lens("globe"), [10, 10], visible="front")
    with pytest.raises(ValueError):
        C.render_unit(1, C.lens("globe"), [10, 10], ev_mode="auto")


def test_spectrum_forms():
    assert C.sun(20)["spectrum"] == "D65"
    s = C.sun(20, spectrum=C.LEGACY_SPECTRUM)["spectrum"]
    assert [w["wavelength"] for w in s] == [420, 460, 500, 540, 580, 620]


def test_complex_filter_composition_and_reference_checks():
    """复合过滤器：composition 顶层 = OR、子列表 = AND；symmetry 写在复合过滤器上；build_config 拒绝悬空 / 嵌套复合引用。"""
    f = C.complex_filter(1, [2, [3, 4], 5], "PBD")
    assert f == {"id": 1, "type": "complex", "composition": [2, [3, 4], 5], "symmetry": "PBD", "action": "filter_in"}
    assert C.composition_ids(f) == {2, 3, 4, 5} and C.composition_ids(C.none_filter(9)) == set()
    with pytest.raises(ValueError):
        C.complex_filter(1, [], "PBD")
    with pytest.raises(ValueError):
        C.complex_filter(1, [2], "PX")
    subs = [C.raypath_filter(i, [1, 3, 2], "PBD") for i in (2, 3)]
    sc = C.scene(C.sun(10), 1000, [C.entry(1, filter=1)])
    render = C.render_unit(1, C.lens("rectangular"), [200, 100])
    cfg = C.build_config([C.prism_crystal(1)], [C.complex_filter(1, [2, 3], "PBD")] + subs, sc, [render])
    assert cfg["filter"][0]["composition"] == [2, 3]
    with pytest.raises(ValueError, match="不存在"):
        C.build_config([C.prism_crystal(1)], [C.complex_filter(1, [2, 7], "PBD")] + subs, sc, [render])
    with pytest.raises(ValueError, match="非复合"):
        C.build_config([C.prism_crystal(1)], [C.complex_filter(1, [2, 4], "PBD"), C.complex_filter(4, [3], "PBD")] + subs,
                       sc, [render])
