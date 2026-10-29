"""图表语义 token（mapping 新字段 + ``figure_scheme`` resolver）的机械对照。

逐槽等值断言在 candidate.py 删除前直接对照暂存模块（S1+T3 默认），删除后由钉死
hex 的断言接棒，防 resolver 与 mapping 两处漂移。
"""

from halo_notes.draw.style import DEFAULT_LIGHT, DEFAULT_MAP
from halo_notes.draw.style.figure import Surface, figure_scheme


def test_resolver_matches_candidate_default():
    """resolver 各槽与 #48 定稿方案（candidate 默认 S1 + T3）逐槽相等。"""
    from halo_notes.draw.style.candidate import scheme as candidate_scheme

    c = candidate_scheme()
    f = figure_scheme()
    assert dict(f.family) == dict(c.family)
    assert dict(f.sky_glow) == dict(c.sky_glow)
    assert dict(f.sky) == dict(c.sky)
    assert f.sun == c.sun and f.point == c.point
    assert f.ray_in == c.ray_in and f.ray_out == c.ray_out
    assert dict(f.pair) == dict(c.pair) and f.pair_dash == c.pair_dash
    assert f.ink == c.ink and f.guide == c.guide and f.paper == c.paper
    assert f.terrain_ramp == c.terrain_ramp
    assert (f.crystal_fill, f.crystal_fill_alpha, f.crystal_edge) == (
        c.crystal_fill, c.crystal_fill_alpha, c.crystal_edge)
    assert (f.sphere_fill, f.sphere_fill_alpha, f.sphere_edge) == (
        c.sphere_fill, c.sphere_fill_alpha, c.sphere_edge)
    assert dict(f.surfaces).keys() == dict(c.surfaces).keys()
    for key, a in f.surfaces.items():
        b = c.surfaces[key]
        assert isinstance(a, Surface)
        assert (a.base, a.ambient, a.mesh, a.mesh_width, a.outline) == (
            b.base, b.ambient, b.mesh, b.mesh_width, b.outline)


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
