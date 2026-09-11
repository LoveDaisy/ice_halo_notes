import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from halo_notes.draw import (PRESETS, Camera, HexPrism, draw_axes, finish, new_figure,  # noqa: E402
                             render_crystal, trace)
from halo_notes.draw.labels import face_label_anchor, point_in_polygon  # noqa: E402
from halo_notes.draw.projection import visible_faces  # noqa: E402
from halo_notes.draw.raypath import SegmentKind  # noqa: E402
from halo_notes.draw.scene import (Z_CONE_FILL, Z_CONE_OUTLINE, Z_EXTERNAL, Z_HIDDEN_FILL,  # noqa: E402
                                   Z_HIDDEN_LABEL, Z_INTERNAL, Z_VISIBLE_EDGE, Z_VISIBLE_FILL,
                                   Z_VISIBLE_LABEL)


def test_face_label_anchor_inside_projected_polygon():
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    for f in visible_faces(c, cam):
        poly = cam.project_xy(c.face_vertices(f))
        assert point_in_polygon(face_label_anchor(c, f, cam), poly)


def test_render_crystal_smoke():
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=PRESETS["default"], face_numbers=True)
    assert len(ax.lines) == 18  # 每条边一条线
    assert len(ax.patches) == 8  # 默认贴面编号是 PathPatch，不是 Text
    assert len(ax.texts) == 0
    plt.close(fig)


def test_face_number_zorder_matches_visibility():
    """贴面编号（PathPatch）的 zorder 由 render_crystal 对返回 artist 统一
    ``.set_zorder()``，与 draw_face_number 内部返回 Text 还是 PathPatch 无关；
    这里直接核验该外部机制在默认（贴面）样式下确实生效（code-review round 1
    Major 意见：切到 PathPatch 后未见对应回归测试）。"""
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=PRESETS["default"], face_numbers=True)
    visible_numbers = {f.number for f in visible_faces(c, cam)}
    assert len(ax.patches) == len(c.faces)  # 默认预设无面填充，全部是编号 patch
    for f, patch in zip(c.faces, ax.patches):
        expected = Z_VISIBLE_LABEL if f.number in visible_numbers else Z_HIDDEN_LABEL
        assert patch.get_zorder() == expected
    plt.close(fig)


def test_render_crystal_with_raypath_and_axes():
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    fig, ax = new_figure(400, 300, dpi=50)
    p = trace(c, [-3, -1.2, 0.3], [1, 0.35, -0.1], ["refract", "refract"])
    render_crystal(ax, c, [p], camera=cam, preset=PRESETS["ice_filled"])
    draw_axes(ax, camera=cam, preset=PRESETS["default"], occluder=c)
    finish(ax, (-3, 3), (-2, 2))
    # patch 来源：可见面填充 + 每段外部光线一个锥体遮挡衬底 + x/y/z 三个实心轴箭头
    n_ray_cone_fills = sum(k is not SegmentKind.INTERNAL for k in p.kinds)
    assert n_ray_cone_fills == 2  # 入射 + 出射
    n_axis_arrows = 3
    assert len(ax.patches) == len(visible_faces(c, cam)) + n_ray_cone_fills + n_axis_arrows
    assert len(ax.lines) > 18
    assert [t.get_text() for t in ax.texts] == ["$x$", "$y$", "$z$"]
    plt.close(fig)


def test_hidden_edges_can_be_suppressed():
    from halo_notes.draw.style import DEFAULT_GEOM, HiddenEdgeMode
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["default"].replace(geom=DEFAULT_GEOM.replace(hidden_edges=HiddenEdgeMode.HIDE))
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset)
    assert 0 < len(ax.lines) < 18
    plt.close(fig)


def test_new_figure_pixel_size_exact(tmp_path):
    from PIL import Image
    fig, _ = new_figure(1956, 1279, dpi=200)
    out = tmp_path / "f.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)
    assert Image.open(out).size == (1956, 1279)


def test_swapping_preset_does_not_change_geometry_of_output():
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    data = []
    for name in ("default", "ice_filled"):
        fig, ax = new_figure(400, 300, dpi=50)
        render_crystal(ax, c, camera=cam, preset=PRESETS[name])
        data.append(np.vstack([ln.get_xydata() for ln in ax.lines]))
        plt.close(fig)
    assert np.allclose(data[0], data[1])


def test_ray_cone_fill_sits_between_lines_and_outline():
    """光线锥体的背景色衬底压在光线 / 晶体线之上、锥体轮廓与纬线之下。"""
    from matplotlib.colors import to_rgba
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    p = trace(c, [-3, -1.2, 0.3], [1, 0.35, -0.1], ["refract", "refract"])
    render_crystal(ax, c, [p], camera=cam, preset=preset)
    bg = to_rgba(preset.palette["background"])
    fills = [pt for pt in ax.patches if pt.get_facecolor() == bg]
    assert len(fills) == 2
    ray_color = to_rgba(preset.line_kwargs("ray_incident")["color"])
    outline = [ln for ln in ax.lines if ln.get_zorder() == Z_CONE_OUTLINE]
    assert outline and all(to_rgba(ln.get_color()) in
                           (ray_color, to_rgba(preset.line_kwargs("ray_exit")["color"]))
                           for ln in outline)
    for pt in fills:
        assert pt.get_zorder() == Z_CONE_FILL
        assert pt.get_zorder() > max(Z_EXTERNAL, Z_VISIBLE_EDGE, Z_INTERNAL)
        assert pt.get_zorder() < Z_CONE_OUTLINE
    plt.close(fig)


def test_axes_arrows_are_solid_and_scaled():
    """轴箭头：三个实心 patch、无纬线弧，尺寸按 axis_cone_scale 缩小。"""
    from halo_notes.draw.style import DEFAULT_GEOM
    cam = Camera(azimuth=72, elevation=20)
    sizes = {}
    for scale in (0.6, 0.3):
        preset = PRESETS["default"].replace(geom=DEFAULT_GEOM.replace(axis_cone_scale=scale))
        fig, ax = new_figure(400, 300, dpi=50)
        draw_axes(ax, camera=cam, preset=preset)
        assert len(ax.patches) == 3
        assert len(ax.lines) == 3  # 只有三根轴线本身（无遮挡体时各一条），没有纬线弧
        sizes[scale] = max(np.ptp(pt.get_xy(), axis=0).max() for pt in ax.patches)
        plt.close(fig)
    assert sizes[0.3] < sizes[0.6]  # 配置确实接入：改 scale 箭头随之缩放


# ---- 高亮 / 幽灵（光路展开） --------------------------------------------------

def _fills(ax):
    """面填充 patch（排除贴面编号 PathPatch）。"""
    from matplotlib.patches import Polygon
    return [p for p in ax.patches if isinstance(p, Polygon)]


def test_render_crystal_highlight_face_uses_highlight_style():
    from matplotlib.colors import to_rgba
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)  # 顶面 1 可见、底面 2 不可见
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset, highlight=(1, 2))
    fills = _fills(ax)
    assert len(fills) == 2  # 默认预设无面填充，只有两个高亮面
    hi = preset.fill_kwargs("face_highlight")
    hi_hidden = preset.fill_kwargs("face_highlight_hidden")
    colors = sorted((p.get_facecolor(), p.get_zorder()) for p in fills)
    assert (to_rgba(hi["facecolor"], hi["alpha"]), Z_VISIBLE_FILL) in colors
    assert (to_rgba(hi_hidden["facecolor"], hi_hidden["alpha"]), Z_HIDDEN_FILL) in colors
    plt.close(fig)


def test_render_crystal_ghost_mode_forces_no_default_fill_and_uses_edge_ghost():
    from matplotlib.colors import to_rgba
    from halo_notes.draw.style import DEFAULT_GEOM, HiddenEdgeMode
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    # ice_filled 本身有 face_fill；再把 hidden_edges 设成 HIDE——两者都应被 ghost 覆盖
    preset = PRESETS["ice_filled"].replace(geom=DEFAULT_GEOM.replace(hidden_edges=HiddenEdgeMode.HIDE))
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset, ghost=True)
    assert _fills(ax) == []
    assert len(ax.lines) == 18
    kw = preset.line_kwargs("edge_ghost")
    for ln in ax.lines:
        assert to_rgba(ln.get_color(), ln.get_alpha()) == to_rgba(kw["color"], kw["alpha"])
        assert ln.get_linewidth() == kw["linewidth"]
    plt.close(fig)


def test_render_crystal_highlight_and_ghost_together():
    from matplotlib.colors import to_rgba
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["ice_filled"]
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset, ghost=True, highlight=(3,))
    fills = _fills(ax)
    assert len(fills) == 1  # 只有高亮面被填充，ghost 的"不填充"不压过 highlight
    vis = visible_faces(c, cam)
    sem = "face_highlight" if c.face(3) in vis else "face_highlight_hidden"
    kw = preset.fill_kwargs(sem)
    assert fills[0].get_facecolor() == to_rgba(kw["facecolor"], kw["alpha"])
    plt.close(fig)


# ---- 文字注释 ----------------------------------------------------------------

def test_annotate_places_text_at_projected_point_plus_offset():
    from halo_notes.draw import annotate
    from halo_notes.draw.scene import Z_TEXT
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    anchor, off = [0.3, -0.2, 0.5], (0.7, -0.4)
    t = annotate(ax, "全反射路径", anchor, off, camera=cam, preset=preset)
    assert list(ax.texts) == [t]
    assert np.allclose(t.get_position(), cam.project_xy(anchor)[0] + off)
    assert t.get_zorder() == Z_TEXT and len(ax.lines) == 0
    plt.close(fig)


def test_annotate_uses_annotation_semantic_style_and_optional_arrow():
    from matplotlib.colors import to_rgba
    from halo_notes.draw import annotate
    from halo_notes.draw.style import DEFAULT_MAP, TextStyle
    cam = Camera(azimuth=72, elevation=20)
    # 故意用与默认不同的注释样式，确认确实从 annotation 语义取值（不是用默认字体）
    preset = PRESETS["default"].replace(
        style_map=DEFAULT_MAP.replace(annotation=TextStyle("accent_cool", fontsize=9, alpha=0.6)))
    fig, ax = new_figure(400, 300, dpi=50)
    t = annotate(ax, "x", [0, 0, 0], (0.5, 0.5), camera=cam, preset=preset, arrow=True)
    kw = preset.text_kwargs("annotation")
    assert to_rgba(t.get_color()) == to_rgba(kw["color"]) and t.get_fontsize() == 9
    assert t.get_alpha() == 0.6
    assert len(ax.lines) == 1  # arrow=True：文字到锚点一条连线
    xy = ax.lines[0].get_xydata()
    assert np.allclose(xy[0], t.get_position()) and np.allclose(xy[1], cam.project_xy([0, 0, 0])[0])
    plt.close(fig)


def test_draw_raypath_mono_semantic_colours_everything_alike():
    """``semantic=`` 单色模式：所有线段、锥体线、圆点都用该语义的颜色（展开直线 / 折线用）。"""
    from matplotlib.colors import to_rgba
    from halo_notes.draw import draw_raypath
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["default"]
    p = trace(c, [-3, -1.2, 0.3], [1, 0.35, -0.1], ["refract", "reflect", "refract"])
    fig, ax = new_figure(400, 300, dpi=50)
    draw_raypath(ax, p, c, camera=cam, preset=preset, semantic="ray_folded")
    kw = preset.line_kwargs("ray_folded")
    assert ax.lines and all(to_rgba(ln.get_color()) == to_rgba(kw["color"]) for ln in ax.lines)
    lines = [ln for ln in ax.lines if len(ln.get_xydata()) > 1]
    assert all(ln.get_linestyle() == ":" for ln in lines if ln.get_zorder() != Z_CONE_OUTLINE)
    assert len(ax.patches) == 2  # 入射 / 出射两个锥体的遮挡衬底仍在
    default_incident = to_rgba(preset.line_kwargs("ray_incident")["color"])
    assert to_rgba(kw["color"]) == default_incident  # 同色不同线型：确认下一条断言不是靠颜色蒙混
    fig2, ax2 = new_figure(400, 300, dpi=50)
    draw_raypath(ax2, p, c, camera=cam, preset=preset, semantic="ray_unfolded")
    blue = to_rgba(preset.line_kwargs("ray_unfolded")["color"])
    assert all(to_rgba(ln.get_color()) == blue for ln in ax2.lines)
    plt.close(fig)
    plt.close(fig2)


def test_ghost_face_numbers_all_use_hidden_style():
    """幽灵晶体的面编号全部用 face_number_hidden（淡）样式，可见面也不例外。"""
    from matplotlib.colors import to_rgba
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset, face_numbers=True, ghost=True)
    hidden_alpha = preset.text_kwargs("face_number_hidden")["alpha"]
    labels = [p for p in ax.patches]  # 默认贴面编号是 PathPatch，且 ghost 无面填充
    assert len(labels) == 8
    assert all(p.get_alpha() == hidden_alpha for p in labels)
    plt.close(fig)
