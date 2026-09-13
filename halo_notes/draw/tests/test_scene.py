import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from matplotlib.patches import Polygon  # noqa: E402

from halo_notes.draw import (PRESETS, Camera, HexPrism, draw_axes, finish, new_figure,  # noqa: E402
                             render_crystal, rotation, trace)
from halo_notes.draw.labels import face_label_anchor, point_in_polygon  # noqa: E402
from halo_notes.draw.projection import visible_faces  # noqa: E402
from halo_notes.draw.raypath import RayPath, SegmentKind  # noqa: E402
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


def test_ghost_face_numbers_use_two_levels_by_visibility():
    """幽灵晶体的面编号两级：朝向观察者的面用 face_number_ghost（中等灰），背面用
    face_number_hidden（更淡）；两级都比实体的 face_number 淡。"""
    from halo_notes.draw.style import DEFAULT_MAP, TextStyle
    c = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    # 故意把三级 alpha 设成互不相同、且与默认值不同的数，确认确实按语义取值而非碰巧
    preset = PRESETS["default"].replace(style_map=DEFAULT_MAP.replace(
        face_number=TextStyle("slate", alpha=0.9), face_number_ghost=TextStyle("slate", alpha=0.6),
        face_number_hidden=TextStyle("slate", alpha=0.3)))
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, c, camera=cam, preset=preset, face_numbers=True, ghost=True)
    labels = list(ax.patches)  # 默认贴面编号是 PathPatch，且 ghost 无面填充
    assert len(labels) == 8
    vis = {f.number for f in visible_faces(c, cam)}
    for f, patch in zip(c.faces, labels):
        assert patch.get_alpha() == (0.6 if f.number in vis else 0.3)
    assert DEFAULT_MAP.face_number_hidden.alpha < DEFAULT_MAP.face_number_ghost.alpha < DEFAULT_MAP.face_number.alpha
    plt.close(fig)


# ---- 锥体箭头：锥尖朝传播方向、光线穿入锥底 ----------------------------------------

def test_ray_cones_point_along_propagation():
    """每条外部段的锥体：锥尖在下游、锥底在上游——锥体轴向（顶点→底面）与传播方向点积 < 0，
    等价于 issue 原句"锥尖朝传播方向"。"""
    from halo_notes.draw.scene import segment_cone
    from halo_notes.draw.style import DEFAULT_GEOM
    c = HexPrism(1, 1.0)
    p = trace(c, [-5, 0.0, -2.0], [1, 0, 0.5], ["refract", "reflect", "refract"])
    for p0, p1, kind in p.segments():
        if kind is SegmentKind.INTERNAL:
            continue
        cone = segment_cone(p0, p1, kind, DEFAULT_GEOM)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        assert cone.axis @ d < 0                       # 轴指向底面 = 逆传播方向 ⇒ 尖朝传播方向
        assert (cone.apex - cone.base_center) @ d > 0  # 尖在底面的下游
        at = DEFAULT_GEOM.incident_cone_at if kind is SegmentKind.INCIDENT else DEFAULT_GEOM.exit_cone_at
        assert np.allclose(cone.apex, p0 + (p1 - p0) * at)  # cone_at 参数定位的是锥尖


def test_ray_line_enters_cone_base_to_its_centre():
    """锥底朝观察者时，光线画到锥底中心为止（压在锥体衬底之上），而不是在轮廓处被截断；
    锥尖之后再继续。"""
    from matplotlib.colors import to_rgba
    from halo_notes.draw import draw_raypath
    from halo_notes.draw.scene import Z_CONE_ENTRY, segment_cone
    from halo_notes.draw.style import DEFAULT_GEOM
    preset = PRESETS["default"]
    d = np.array([1.0, 0.0, 0.0])
    p = RayPath(np.array([[-3.0, 0, 0], [-1.0, 0, 0]]), (SegmentKind.INCIDENT,))
    cam = Camera(azimuth=150, elevation=10)   # 观察者在光线上游一侧偏后：锥底朝向观察者
    cone = segment_cone(p.points[0], p.points[1], SegmentKind.INCIDENT, DEFAULT_GEOM)
    assert cone.axis @ cam.view_vector(cone.base_center)[0] > 0
    fig, ax = new_figure(400, 300, dpi=50)
    draw_raypath(ax, p, camera=cam, preset=preset)
    color = to_rgba(preset.line_kwargs("ray_incident")["color"])
    entry = [ln for ln in ax.lines if ln.get_zorder() == Z_CONE_ENTRY and len(ln.get_xydata()) > 2]
    assert len(entry) == 1
    ends = entry[0].get_xydata()[[0, -1]]
    assert np.allclose(ends[0], cam.project_xy(p.points[0])[0])
    assert np.allclose(ends[1], cam.project_xy(cone.base_center)[0])  # 终点 = 锥底中心
    assert Z_CONE_ENTRY > Z_CONE_FILL
    tail = [ln for ln in ax.lines if ln.get_zorder() == Z_EXTERNAL and len(ln.get_xydata()) > 2]
    assert len(tail) == 1 and np.allclose(tail[0].get_xydata()[0], cam.project_xy(cone.apex)[0])
    assert all(to_rgba(ln.get_color()) == color for ln in entry + tail)
    # 锥底背对观察者：没有 Z_CONE_ENTRY 的线，上游一截按 Z_EXTERNAL（被锥体衬底在轮廓处遮住）
    cam2 = Camera(azimuth=-30, elevation=10)
    assert cone.axis @ cam2.view_vector(cone.base_center)[0] < 0
    fig2, ax2 = new_figure(400, 300, dpi=50)
    draw_raypath(ax2, p, camera=cam2, preset=preset)
    assert not [ln for ln in ax2.lines if ln.get_zorder() == Z_CONE_ENTRY]
    plt.close(fig)
    plt.close(fig2)


def test_render_corridor_highlights_corridor_faces_on_the_right_bodies():
    """光走廊：入射面高亮在真实晶体上、反射面在对应幽灵上、出射面在最后一个幽灵上；
    幽灵一律线框，真实晶体按 ghost_crystal 决定。"""
    from matplotlib.colors import to_rgba
    from halo_notes.draw import render_corridor
    from halo_notes.draw.unfold import corridor_faces
    c = HexPrism(1, 1.0)
    cam = Camera(azimuth=72, elevation=20)
    preset = PRESETS["ice_filled"]  # 有默认面填充，便于区分"真实晶体按默认画"与"幽灵不填充"
    p = trace(c, [-5, 0.0, -2.0], [1, 0, 0.5], ["refract", "reflect", "refract"])  # 6-1-3
    assert corridor_faces(p) == [(0, 6), (1, 1), (1, 3)]
    hi = to_rgba(preset.fill_kwargs("face_highlight")["facecolor"])
    for ghost_crystal in (True, False):
        fig, ax = new_figure(400, 300, dpi=50)
        chain = render_corridor(ax, c, p, camera=cam, preset=preset, ghost_crystal=ghost_crystal)
        assert len(chain) == 2 and np.allclose(chain[1].vertices, c.mirrored(c.face(1)).vertices)
        fills = _fills(ax)
        hi_patches = [pt for pt in fills if pt.get_facecolor()[:3] == hi[:3]]
        assert len(hi_patches) == 3  # 6 / 1 / 3 三个走廊面
        # 反射面 1 与晶体顶面共面：从这个视角晶体的面 1 可见、幽灵的面 1 背对，应归到晶体并按"可见"画
        vis_alpha = preset.fill_kwargs("face_highlight")["alpha"]
        assert sum(pt.get_facecolor()[3] == vis_alpha for pt in hi_patches) >= 1
        n_default = len(fills) - len(hi_patches)
        vis_numbers = {f.number for f in visible_faces(c, cam)}
        expected = 0 if ghost_crystal else len(vis_numbers - {6, 1})  # 6 / 1 被高亮顶掉
        assert n_default == expected
        plt.close(fig)


def test_frame_fits_points_with_aspect_and_margin():
    from halo_notes.draw import frame
    cam = Camera(azimuth=0, elevation=0, projection="orthographic")  # 画面 x = 世界 -y… 取正交便于验算
    pts = np.array([[0, -2.0, -1.0], [0, 2.0, 1.0]])
    (x0, x1), (y0, y1) = frame(cam, [pts], 400, 200, margin=0.1)
    xy = cam.project_xy(pts)
    assert np.isclose((x1 - x0) / (y1 - y0), 2.0)                         # 宽高比 = 图片宽高比
    assert x0 <= xy[:, 0].min() and x1 >= xy[:, 0].max()                  # 包住所有点
    assert y0 <= xy[:, 1].min() and y1 >= xy[:, 1].max()
    assert np.isclose(y1 - y0, np.ptp(xy[:, 1]) * 1.2)                    # 竖向是瓶颈：留 10% 边


# ---- 3D 旋转弧 / 主轴箭头（task-draw-rest Step 1） ----------------------------------------

@pytest.mark.parametrize("axis,radius,start,angle", [
    ((0, 0, 1), 0.6, (1, 0, 0), 60.0),
    ((0, 1, 0), 1.3, (0, 0, 1), 90.0),
    ((1, 1, 1), 0.4, (0, 0, 1), 200.0),
    ((0, 0, 1), 0.5, (1, 2, 3), -45.0),   # 起始方向带沿轴分量、负角反向
])
def test_rotation_arc_points_lie_on_circle_about_axis(axis, radius, start, angle):
    from halo_notes.draw.scene import rotation_arc_points
    from halo_notes.draw.geometry import unit
    center = np.array([0.2, -0.1, 0.3])
    pts = rotation_arc_points(axis, center, radius, start, angle, samples=33)
    k = unit(axis)
    rel = pts - center
    # 弧上每点到轴的距离恒为半径，且全部落在过 center 垂直于轴的平面内
    assert np.allclose(np.linalg.norm(rel - (rel @ k)[:, None] * k, axis=1), radius, atol=1e-12)
    assert np.allclose(rel @ k, 0.0, atol=1e-12)
    # 张角 = angle_deg（用向量差范数而不是 arccos，避免小角度失真），转向符合右手（负角反向）
    a, b = unit(rel[0]), unit(rel[-1])
    expected = unit(np.cos(np.deg2rad(angle)) * a + np.sin(np.deg2rad(angle)) * np.cross(k, a))
    assert np.linalg.norm(b - expected) < 1e-12
    # 起点 = start 去掉沿轴分量后的方向
    s = np.asarray(start, float)
    assert np.linalg.norm(a - unit(s - (s @ k) * k)) < 1e-12


def test_draw_rotation_arc_3d_arrow_points_along_rotation():
    from halo_notes.draw import draw_rotation_arc_3d
    from halo_notes.draw.geometry import unit
    cam = Camera(azimuth=45, elevation=20)
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    pts, cone = draw_rotation_arc_3d(ax, (0, 0, 1), 0.6, (1, 0, 0), 120.0, camera=cam, preset=preset,
                                     semantic="arc_roll", label=r"$\theta$")
    tangent = unit(pts[-1] - pts[-2])
    assert np.allclose(cone.apex, pts[-1])                 # 锥尖在弧末端
    assert cone.axis @ tangent < -0.99                     # 锥体轴指向弧的来路 ⇒ 锥尖朝旋转方向
    assert len(ax.patches) == 1 and len(ax.lines) == 1     # 实心锥 + 一段弧线
    assert [t.get_text() for t in ax.texts] == [r"$\theta$"]
    # 反向：负角的箭头掉头
    pts2, cone2 = draw_rotation_arc_3d(ax, (0, 0, 1), 0.6, (1, 0, 0), -120.0, camera=cam, preset=preset,
                                       semantic="arc_roll")
    tangent2 = unit(pts2[-1] - pts2[-2])
    assert cone2.axis @ tangent2 < -0.99 and np.cross(tangent2, [0, 0, 1])[2] == 0
    assert (np.cross(pts2[-1], tangent2) @ [0, 0, 1]) < 0 < (np.cross(pts[-1], tangent) @ [0, 0, 1])  # 顺 / 逆时针
    plt.close(fig)


def test_axis_arrow_and_axes_share_one_arrow_implementation(monkeypatch):
    """a56：主轴箭头与坐标轴箭头不能是两份实现——两者都必须经过 scene._draw_single_arrow。"""
    import halo_notes.draw.scene as scene
    from halo_notes.draw import draw_axis_arrow
    calls = []
    real = scene._draw_single_arrow

    def spy(ax, origin, direction, length, **kw):
        calls.append((np.asarray(direction, float), length, kw["semantic"], kw["cone_scale"], kw["negative"]))
        return real(ax, origin, direction, length, **kw)

    monkeypatch.setattr(scene, "_draw_single_arrow", spy)
    cam = Camera(azimuth=45, elevation=20)
    preset = PRESETS["default"]
    fig, ax = new_figure(400, 300, dpi=50)
    draw_axes(ax, camera=cam, preset=preset, length=1.5)
    cone = draw_axis_arrow(ax, (0, 0, 0), (0, 0, 1), 2.0, camera=cam, preset=preset)
    assert len(calls) == 4
    assert [c[2] for c in calls] == ["axis"] * 3 + ["axis_main"]
    assert [c[3] for c in calls] == [preset.geom.axis_cone_scale] * 3 + [preset.geom.main_axis_cone_scale]
    assert [c[4] for c in calls] == [True] * 3 + [False]
    assert np.allclose(cone.apex, [0, 0, 2.0]) and np.allclose(cone.axis, [0, 0, -1])
    plt.close(fig)


# ---- ch7：半透明镜面平面 ----------------------------------------------------------------------

def test_mirror_plane_quad_is_parallel_to_face_and_scaled():
    from halo_notes.draw.scene import mirror_plane_quad
    crystal = HexPrism(1.0, 2.0)
    face = crystal.face(3)
    n = crystal.normal(face)
    for through_center in (True, False):
        quad = mirror_plane_quad(crystal, 3, scale=1.5, through_center=through_center)
        assert quad.shape == (4, 3)
        center = crystal.centroid() if through_center else crystal.centroid(face)
        assert np.allclose(quad.mean(axis=0), center)
        assert np.abs((quad - center) @ n).max() < 1e-12                    # 四点共面、法向 == 面法向
        qn = np.cross(quad[1] - quad[0], quad[3] - quad[0])
        assert np.abs(np.abs(qn @ n) - np.linalg.norm(qn)).max() < 1e-12   # 矩形法向 ∥ 面法向
    # 边长 = 面跨度 × scale：面 3 是 1×2 的矩形（a=1 边长 1、h=2）
    quad = mirror_plane_quad(crystal, 3, scale=1.5, through_center=False)
    lengths = sorted(np.linalg.norm(quad[(i + 1) % 4] - quad[i]) for i in range(4))
    assert np.allclose(lengths, [1.5, 1.5, 3.0, 3.0])


def test_draw_highlight_plane_redraws_only_edges_in_front_of_the_plane():
    """平面穿过晶体中心、与面 3 平行（法向 +x）：从 +x 侧看，位于 x>0 一侧的边（含面 3 的 4 条边）在平面之上再描一遍，
    x<0 一侧的边只在平面之下；从 −x 侧看则相反；平面 patch 在所有晶体线之上。"""
    from halo_notes.draw.scene import Z_PLANE, Z_PLANE_FRONT, Z_VISIBLE_EDGE, draw_highlight_plane
    crystal = HexPrism(1.0, 2.0)
    preset = PRESETS["default"]
    for az, sign in ((20.0, +1), (200.0, -1)):
        fig, ax = new_figure(300, 300, dpi=50)
        cam = Camera(azimuth=az, elevation=25, distance=12)
        render_crystal(ax, crystal, camera=cam, preset=preset, highlight=[3])
        n_before = len(ax.lines)
        quad = draw_highlight_plane(ax, crystal, 3, camera=cam, preset=preset, scale=1.3)
        assert np.allclose(quad.mean(axis=0), 0.0)
        planes = [p for p in ax.patches if isinstance(p, Polygon) and p.get_zorder() == Z_PLANE]
        assert len(planes) == 1
        assert planes[0].get_alpha() == preset.style_map.mirror_plane.alpha
        front = [l for l in ax.lines[n_before:] if l.get_zorder() == Z_PLANE_FRONT]
        outline = [l for l in ax.lines[n_before:] if l.get_zorder() == Z_PLANE]
        assert len(outline) == 1 and len(outline[0].get_xdata()) == 5
        # 平面 x=0 把六棱柱切成两半：完全在观察者一侧的边整条重描，完全在另一侧的边不描
        drawn = set()
        for l in front:
            xy = np.column_stack([l.get_xdata(), l.get_ydata()])
            for e in crystal.edges:
                p = cam.project_xy(crystal.vertices[list(e)])
                if np.allclose(xy[0], p[0], atol=1e-6) and np.allclose(xy[-1], p[1], atol=1e-6):
                    drawn.add(e)
        # 完全在前方的边整条重描；跨平面的边（这里没有）会只描前半
        wholly_front = {e for e in crystal.edges if (sign * crystal.vertices[list(e)][:, 0]).min() > 1e-9}
        assert wholly_front <= drawn
        wholly_back = {e for e in crystal.edges if (sign * crystal.vertices[list(e)][:, 0]).max() < -1e-9}
        assert not (wholly_back & drawn) and wholly_back
        assert Z_PLANE > Z_VISIBLE_EDGE
        plt.close(fig)


def test_draw_highlight_plane_splits_an_edge_crossing_the_plane():
    """用一个真正跨越平面的边核验切段：立方体的 4 条棱与面 1 的法向平行，穿过晶体中心的平面把它们各切成两截，
    只有观察者一侧的半截被重描。"""
    from halo_notes.draw.geometry import Face, Polyhedron
    from halo_notes.draw.scene import Z_PLANE_FRONT, draw_highlight_plane
    v = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
    cube = Polyhedron(v, [Face(1, (1, 5, 7, 3)), Face(2, (0, 2, 6, 4)), Face(3, (4, 6, 7, 5)),
                          Face(4, (0, 1, 3, 2)), Face(5, (2, 3, 7, 6)), Face(6, (0, 4, 5, 1))])
    n = cube.normal(cube.face(1))
    assert np.allclose(n, [0, 0, 1])
    fig, ax = new_figure(300, 300, dpi=50)
    cam = Camera(azimuth=30.0, elevation=35.0, distance=12)
    preset = PRESETS["default"]
    render_crystal(ax, cube, camera=cam, preset=preset)
    n_before = len(ax.lines)
    draw_highlight_plane(ax, cube, 1, camera=cam, preset=preset, samples=101)
    front = [l for l in ax.lines[n_before:] if l.get_zorder() == Z_PLANE_FRONT]
    crossing = [e for e in cube.edges if np.prod(cube.vertices[list(e)] @ n) < -1e-9]
    assert len(crossing) == 4
    partial = 0
    for l in front:
        xy = np.column_stack([l.get_xdata(), l.get_ydata()])
        for e in crossing:
            a, b = cube.vertices[list(e)]
            top, bottom = (a, b) if a[2] > b[2] else (b, a)      # 观察者在 z>0 一侧：只描上半截
            p_top, p_mid = cam.project_xy(top)[0], cam.project_xy((top + bottom) / 2)[0]
            ends = {tuple(np.round(xy[0], 6)), tuple(np.round(xy[-1], 6))}
            if tuple(np.round(p_top, 6)) in ends and any(np.allclose(q, p_mid, atol=0.05) for q in (xy[0], xy[-1])):
                partial += 1
    assert partial == 4
    plt.close(fig)
