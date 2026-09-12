import pytest

from halo_notes.draw.style import (DEFAULT_GEOM, DEFAULT_LIGHT, DEFAULT_MAP, PRESETS, GeomStyle,
                                   LineStyle, Palette, Preset, SemanticStyleMap)


def test_default_preset_has_four_independent_layers():
    p = PRESETS["default"]
    assert isinstance(p, Preset)
    assert isinstance(p.palette, Palette)
    assert isinstance(p.style_map, SemanticStyleMap)
    assert isinstance(p.geom, GeomStyle)


def test_replacing_palette_keeps_other_layers():
    p = PRESETS["default"]
    dark = DEFAULT_LIGHT.with_colors("dark", ink="#FFFFFF", background="#000000")
    q = p.replace(palette=dark)
    assert q.style_map is p.style_map and q.geom is p.geom
    assert q.line_kwargs("edge_visible")["color"] == "#FFFFFF"
    assert p.line_kwargs("edge_visible")["color"] == "#000000"


def test_replacing_style_map_keeps_palette_and_geom():
    p = PRESETS["default"]
    q = p.replace(style_map=DEFAULT_MAP.replace(edge_visible=LineStyle("accent_cool", linewidth=3)))
    assert q.palette is p.palette and q.geom is p.geom
    assert q.line_kwargs("edge_visible") == dict(color="#3C7DD9", linewidth=3, linestyle="-", alpha=1.0)


def test_replacing_geom_keeps_palette_and_map():
    p = PRESETS["default"]
    q = p.replace(geom=DEFAULT_GEOM.replace(cone_rings=7))
    assert q.palette is p.palette and q.style_map is p.style_map
    assert q.geom.cone_rings == 7 and p.geom.cone_rings != 7


def test_unknown_color_name_is_loud():
    p = PRESETS["default"].replace(style_map=DEFAULT_MAP.replace(axis=LineStyle("no_such_color")))
    with pytest.raises(KeyError):
        p.line_kwargs("axis")


def test_layers_are_immutable():
    with pytest.raises(Exception):
        DEFAULT_GEOM.cone_rings = 5  # type: ignore[misc]


def test_hidden_face_number_only_fades_not_shrinks():
    """作者裁定：隐藏面编号与可见编号同字号，只靠 alpha 表达在背面。"""
    from halo_notes.draw.style import DEFAULT_MAP
    assert DEFAULT_MAP.face_number_hidden.fontsize == DEFAULT_MAP.face_number.fontsize
    assert DEFAULT_MAP.face_number_hidden.alpha < DEFAULT_MAP.face_number.alpha


def test_unfold_semantics_resolve_and_differ_from_neighbours():
    """新增三个语义都能解析出色值，且不与最相邻的既有字段巧合同值
    （plan-review Minor 2：防"新字段 = 旧字段复制值"被静默吞掉）。"""
    p = PRESETS["default"]
    ghost = p.line_kwargs("edge_ghost")
    hi, hi_hidden = p.fill_kwargs("face_highlight"), p.fill_kwargs("face_highlight_hidden")
    assert ghost != p.line_kwargs("edge_hidden") and ghost != p.line_kwargs("edge_visible")
    assert hi["facecolor"] == DEFAULT_LIGHT["highlight"]
    assert hi != p.fill_kwargs("face_fill") and hi_hidden != p.fill_kwargs("face_fill_hidden")
    ice = PRESETS["ice_filled"]
    assert ice.fill_kwargs("face_highlight")["facecolor"] != ice.fill_kwargs("face_fill")["facecolor"]


def test_face_highlight_hidden_is_fainter_than_visible():
    assert DEFAULT_MAP.face_highlight_hidden.alpha < DEFAULT_MAP.face_highlight.alpha
    assert DEFAULT_MAP.face_highlight_hidden.color == DEFAULT_MAP.face_highlight.color


def test_face_colors_are_six_distinct_named_colors():
    from halo_notes.draw.style import FACE_COLORS
    assert sorted(FACE_COLORS) == [3, 4, 5, 6, 7, 8]
    values = [DEFAULT_LIGHT[name] for name in FACE_COLORS.values()]
    assert len(set(values)) == 6
    # 不与既有语义色撞色
    for name in ("accent_warm", "accent_cool", "highlight", "slate", "ice"):
        assert DEFAULT_LIGHT[name] not in values


def test_face_number_colors_switch_is_off_by_default_and_changes_output():
    """开关默认关；打开后编号确实按面号取色（不是摆设）。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from halo_notes.draw.geometry2d import CrossSection
    from halo_notes.draw.labels import draw_edge_number
    from halo_notes.draw.style import FACE_COLORS
    assert DEFAULT_MAP.face_number_colors is None
    section = CrossSection(1.0)
    plain = PRESETS["default"]
    colored = plain.replace(style_map=DEFAULT_MAP.replace(face_number_colors=FACE_COLORS))
    fig, ax = plt.subplots()
    p_plain = draw_edge_number(ax, section, section.face(3), plain)
    p_colored = draw_edge_number(ax, section, section.face(3), colored)
    plt.close(fig)
    assert p_plain.get_facecolor() != p_colored.get_facecolor()
    assert matplotlib.colors.to_hex(p_colored.get_facecolor()).upper() == DEFAULT_LIGHT["face_3"]
    assert matplotlib.colors.to_hex(p_plain.get_facecolor()).upper() == DEFAULT_LIGHT["slate"]


def test_new_2d_fields_have_defaults_and_do_not_touch_existing():
    assert DEFAULT_GEOM.arrow2d_length > 0 and DEFAULT_GEOM.edge_number_height > 0
    assert DEFAULT_MAP.ray2d.color == "accent_warm"
    assert DEFAULT_MAP.ray_incident == LineStyle("accent_warm", linewidth=1.6)
    assert DEFAULT_GEOM.cone_length == 0.36


def test_draw_rest_semantics_resolve_and_differ_from_neighbours():
    """task-draw-rest 新增的弧 / 主轴 / 球面语义都能解析出色值；三条弧各不同色、可见与背面版本只差
    透明度或线型（同色减淡惯例），主轴箭头比坐标轴粗。"""
    p = PRESETS["default"]
    arcs = [p.line_kwargs(s)["color"] for s in ("arc_roll", "arc_tilt", "arc_azimuth")]
    assert len(set(arcs)) == 3 and p.line_kwargs("axis")["color"] not in arcs
    assert p.line_kwargs("axis_main")["linewidth"] > p.line_kwargs("axis")["linewidth"]
    for vis, hid in (("sphere_grid", "sphere_grid_hidden"), ("sphere_curve", "sphere_curve_hidden"),
                     ("equator", "equator_hidden")):
        a, b = p.line_kwargs(vis), p.line_kwargs(hid)
        assert a["color"] == b["color"] and a != b
    a, b = p.marker_kwargs("pose_cloud"), p.marker_kwargs("pose_cloud_hidden")
    assert a["color"] == b["color"] and a["alpha"] > b["alpha"]
    assert p.fill_kwargs("cone_surface")["alpha"] < 1.0
    assert p.text_kwargs("arc_label")["fontsize"] == p.text_kwargs("axis_label")["fontsize"]
    geom = p.geom
    assert geom.main_axis_cone_scale > geom.axis_cone_scale
    assert geom.sphere_grid_step_deg == 15.0 and geom.cone_extend > 1.0
