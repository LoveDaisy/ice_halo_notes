"""图表语义 token（mapping 新字段 + ``figure_scheme`` resolver）的机械对照。

默认方案钉死 #48 定稿（曲面 S1、地形 T3、太阳金，2026-10-30 作者签核）的 hex 清单：
resolver 或 mapping 单边漂移都会在这里响。
"""

from halo_notes.draw.style import DEFAULT_LIGHT, DEFAULT_MAP
from halo_notes.draw.style.figure import Surface, figure_scheme

# #48 定稿（升格自暂存模块 candidate 的 S1 + T3）：semantic-table.md 的代码侧单源
PINNED = {
    "family": {"random": "#8C96A3", "column": "#4E78BE", "parry": "#2E4B7E",
               "plate": "#E95536", "lowitz": "#F2917C"},
    "sky_glow": {"random": "#D2D6DC", "column": "#3C7DD9", "plate": "#E95536"},
    "sky": {"ink": "#CCCCCC", "ring": "#848897", "guide": "#555555", "night": "#000000"},
    "sun": "#E8A020", "point": "#3C7DD9", "ray_in": "#FC5D53", "ray_out": "#3C7DD9",
    "pair": {"a": "#2F3A4A", "b": "#8778B3"}, "pair_dash": (0, (4.0, 2.6)),
    "ink": "#455775", "guide": "#C9CFD8", "paper": "#FFFFFF",
    "surfaces": {"column": ("#C9DAEF", 0.80, "#6F88AE", 0.0042, "#3E5A86"),
                 "lowitz": ("#F8E4DE", 0.84, "#C79A8E", 0.0042, "#9A6556"),
                 "neutral": ("#E3EEF8", 0.84, "#7D8DA3", 0.0040, "#56677D")},
    "terrain_ramp": ("#F3F4F6", "#A3ABB7", "#2F3A4A"),
    "crystal": ("#D5EFFD", 0.8, "#767B8B"),
    "sphere": ("#D5EFFD", 0.24, "#767B8B"),
}


def test_default_scheme_pins_signed_off_hex():
    """resolver 默认槽逐个钉在 #48 签核 hex 上（改名 / 换值都算漂移）。"""
    f = figure_scheme()
    assert dict(f.family) == PINNED["family"]
    assert dict(f.sky_glow) == PINNED["sky_glow"]
    assert dict(f.sky) == PINNED["sky"]
    assert f.sun == PINNED["sun"] and f.point == PINNED["point"]
    assert f.ray_in == PINNED["ray_in"] and f.ray_out == PINNED["ray_out"]
    assert dict(f.pair) == PINNED["pair"] and f.pair_dash == PINNED["pair_dash"]
    assert f.ink == PINNED["ink"] and f.guide == PINNED["guide"] and f.paper == PINNED["paper"]
    assert f.terrain_ramp == PINNED["terrain_ramp"]
    assert (f.crystal_fill, f.crystal_fill_alpha, f.crystal_edge) == PINNED["crystal"]
    assert (f.sphere_fill, f.sphere_fill_alpha, f.sphere_edge) == PINNED["sphere"]
    assert dict(f.surfaces).keys() == PINNED["surfaces"].keys()
    for key, s in f.surfaces.items():
        assert isinstance(s, Surface)
        assert (s.base, s.ambient, s.mesh, s.mesh_width, s.outline) == PINNED["surfaces"][key]


def test_mapping_color_fields_are_palette_names():
    """mapping 图表语义字段的每个颜色值都必须是配色板里的名字（拼错就地响）。"""
    mappings = (DEFAULT_MAP.family_colors, DEFAULT_MAP.sky_glow_colors,
                DEFAULT_MAP.sky_colors, DEFAULT_MAP.pair_colors)
    for mapping in mappings:
        for name in mapping.values():
            assert name in DEFAULT_LIGHT, name
    bare = (DEFAULT_MAP.sun_color, DEFAULT_MAP.point_color, DEFAULT_MAP.ink_color,
            DEFAULT_MAP.guide_color, DEFAULT_MAP.crystal_edge, DEFAULT_MAP.sphere_edge)
    for name in bare:
        assert name in DEFAULT_LIGHT, name
    assert all(c in DEFAULT_LIGHT for c in DEFAULT_MAP.terrain_ramp)
    assert DEFAULT_MAP.crystal_fill.color in DEFAULT_LIGHT
    assert DEFAULT_MAP.sphere_fill.color in DEFAULT_LIGHT
    for s in DEFAULT_MAP.surface_styles.values():
        for name in (s.base, s.mesh) + ((s.outline,) if s.outline else ()):
            assert name in DEFAULT_LIGHT, name


def test_overrides_are_the_per_chapter_entry():
    """篇内覆盖经 ``**overrides`` 生效，且不影响默认（颜色-语义作用域是篇内，作者裁定）。"""
    f = figure_scheme(sun_color="accent_warm", family_colors={"random": "gold"})
    assert f.sun == DEFAULT_LIGHT["accent_warm"]
    assert dict(f.family) == {"random": DEFAULT_LIGHT["gold"]}
    assert figure_scheme().sun == DEFAULT_LIGHT["gold"]


def test_figure_style_colors_table_fresh():
    """docs/figure-style-colors.md 是 table.py 的生成物：手改或 token 变更后未重新生成都算漂移。"""
    from pathlib import Path

    from halo_notes.draw.style.table import generate

    doc = Path(__file__).resolve().parents[3] / "docs" / "figure-style-colors.md"
    assert doc.is_file(), "docs/figure-style-colors.md 缺失：跑 uv run python -m halo_notes.draw.style.table"
    assert doc.read_text() == generate()


def test_new_fields_have_defaults_and_existing_fields_untouched():
    """新字段全部带默认值；既有字段一个没动（只增不改）。"""
    assert DEFAULT_MAP.sun_color == "gold"
    assert DEFAULT_MAP.point_color == "accent_cool"
    assert DEFAULT_MAP.pair_dash == (0, (4.0, 2.6))
    assert DEFAULT_MAP.terrain_ramp == ("fog", "stone_light", "charcoal")
    assert set(DEFAULT_MAP.family_colors) == {"random", "column", "parry", "plate", "lowitz"}
    assert set(DEFAULT_MAP.surface_styles) == {"column", "lowitz", "neutral"}
    # 既有字段抽查：默认值未被顺手改动
    assert DEFAULT_MAP.ray_incident.color == "accent_warm"
    assert DEFAULT_MAP.ray_incident.linewidth == 1.6
    assert DEFAULT_MAP.face_number_colors is None
    assert DEFAULT_MAP.face_fill is None
