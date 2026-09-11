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
