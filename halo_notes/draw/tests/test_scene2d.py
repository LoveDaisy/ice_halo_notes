import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from matplotlib.patches import PathPatch, Polygon  # noqa: E402

from halo_notes.draw import PRESETS, finish  # noqa: E402
from halo_notes.draw.geometry import unit  # noqa: E402
from halo_notes.draw.geometry2d import CrossSection  # noqa: E402
from halo_notes.draw.raypath import Cone  # noqa: E402
from halo_notes.draw.raypath2d import solve_raypath_2d  # noqa: E402
from halo_notes.draw.scene2d import (draw_flip_axis, draw_raypath_2d, draw_rotation_arc, draw_wedge_angle,  # noqa: E402
                                     multi_panel, render_medium, render_section)
from halo_notes.draw.schematic import two_face_medium, wedge_angle  # noqa: E402
from halo_notes.draw.style import DEFAULT_GEOM, DEFAULT_MAP  # noqa: E402
from halo_notes.draw.symmetry import FlipAxis, flip, rotate  # noqa: E402


@pytest.fixture
def ax():
    fig, ax = plt.subplots()
    yield ax
    plt.close(fig)


@pytest.fixture
def section():
    return CrossSection(1.0)


def test_draw_raypath_2d_arrows_are_triangles_along_propagation(ax, section):
    path = solve_raypath_2d(section, [3, 5])
    draw_raypath_2d(ax, path, preset=PRESETS["default"])
    tris = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(tris) == len(path.kinds)          # 每段一个
    for tri, (p0, p1, _) in zip(tris, path.segments()):
        xy = tri.get_xy()[:3]
        assert xy.shape == (3, 2)
        tip, base = xy[0], xy[1:].mean(axis=0)
        assert (tip - base) @ unit(p1 - p0) > 0  # 尖朝传播方向
        # 尖落在该段上
        t = (tip - p0) @ unit(p1 - p0) / np.linalg.norm(p1 - p0)
        assert 0 <= t <= 1
        d = unit(p1 - p0)
        assert np.isclose((tip - p0)[0] * d[1] - (tip - p0)[1] * d[0], 0.0, atol=1e-9)
    # 没有任何 3D 锥体产物
    assert not any(isinstance(obj, Cone) for obj in ax.get_children())
    assert all(len(l.get_xdata()) == 2 for l in ax.lines)   # 折线段，不是锥体的母线 / 纬线


def test_arrow2d_geom_fields_are_consumed(ax, section):
    path = solve_raypath_2d(section, [3, 5])
    big = PRESETS["default"].replace(geom=DEFAULT_GEOM.replace(arrow2d_length=0.5, arrow2d_width=0.4))
    draw_raypath_2d(ax, path, preset=big, arrows=[(0, 0.5)])
    tri = [p for p in ax.patches if isinstance(p, Polygon)][0].get_xy()[:3]
    assert np.isclose(np.linalg.norm(tri[1] - tri[2]), 0.4)
    assert np.isclose(np.linalg.norm(tri[0] - (tri[1] + tri[2]) / 2), 0.5)


def test_internal_semantic_and_markers(ax, section):
    path = solve_raypath_2d(section, [3, 7])
    preset = PRESETS["default"]
    draw_raypath_2d(ax, path, preset=preset, internal="ray_internal", markers=True, arrows=[])
    alphas = [l.get_alpha() for l in ax.lines if len(l.get_xdata()) == 2]
    assert alphas[1] == DEFAULT_MAP.ray_internal.alpha and alphas[0] == 1.0
    dots = [l for l in ax.lines if len(l.get_xdata()) == 1]
    assert len(dots) == 4   # 首、尾、两个事件点


def test_render_section_variants(ax, section):
    preset = PRESETS["ice_filled"]
    render_section(ax, section, preset=preset, face_numbers=True)
    fills = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(fills) == 1 and len(ax.lines) == 6
    assert len([p for p in ax.patches if isinstance(p, PathPatch)]) == 6
    render_section(ax, section.transformed(translation=[-0.3, 0.3]), preset=preset,
                   face_numbers=True, variant="reference")
    assert len([p for p in ax.patches if isinstance(p, Polygon)]) == 1   # 参考幽灵不填充
    ref = ax.lines[6]
    assert matplotlib.colors.to_hex(ref.get_color()).upper() == preset.palette["reference"]
    render_section(ax, section, preset=preset, variant="ghost", edges=(3, 4))
    assert len(ax.lines) == 14 and ax.lines[-1].get_linestyle() == ":"


def test_edge_numbers_follow_frame(ax, section):
    """编号字形朝向锚定在截面自身的 frame：旋转后字形转动、翻转后镜像（雅可比行列式符号）。"""
    preset = PRESETS["default"]

    def glyph_jacobian(poly):
        render_section(ax, poly, preset=preset, face_numbers=(3,))
        patch = [p for p in ax.patches if isinstance(p, PathPatch)][-1]
        tf = patch.get_transform() - ax.transData
        m = tf.get_matrix()[:2, :2]
        return m

    j0 = glyph_jacobian(section)
    j_rot = glyph_jacobian(rotate(section, 1))
    j_flip = glyph_jacobian(flip(section, FlipAxis.face(3)))
    assert np.linalg.det(j0) > 0 and np.allclose(j0 / j0[0, 0], np.eye(2))
    assert np.linalg.det(j_rot) > 0
    assert np.allclose(unit(j_rot[:, 0]), [np.cos(np.pi / 3), np.sin(np.pi / 3)])
    assert np.linalg.det(j_flip) < 0


def test_edge_number_height_is_world_units(ax, section):
    preset = PRESETS["default"]
    render_section(ax, section, preset=preset, face_numbers=(3,))
    patch = [p for p in ax.patches if isinstance(p, PathPatch)][-1]
    bb = patch.get_path().transformed(patch.get_transform() - ax.transData).get_extents()
    assert np.isclose(bb.height, preset.geom.edge_number_height, rtol=0.05)
    # 锚点：边中点向内退 inset
    mid = section.midpoint(section.face(3))
    assert np.isclose((bb.x0 + bb.x1) / 2, mid[0] - preset.geom.edge_number_inset, atol=0.02)


def test_rotation_arc_and_flip_axis_anchor_on_given_centre(ax, section):
    preset = PRESETS["default"]
    c = section.centroid() + [-0.3, 0.3]
    draw_rotation_arc(ax, c, 0.5, -30, 90, preset=preset, spokes=1.0)
    lines = ax.lines
    assert len(lines) == 3   # 两根辐条 + 弧
    for l in lines[:2]:
        assert np.allclose(l.get_xydata()[0], c)
    arc = lines[2].get_xydata()
    assert np.allclose(np.linalg.norm(arc - c, axis=1), 0.5)
    tri = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(tri) == 1
    tip = tri[0].get_xy()[0]
    assert np.allclose(tip, c + 0.5 * np.array([0, 1]))   # 尖在 90° 处
    # 逆时针：弧从 -30° 走到 90°
    assert np.degrees(np.arctan2(*(arc[0] - c)[::-1])) == pytest.approx(-30)
    draw_flip_axis(ax, c, [1, 0], 2.0, preset=preset, arrow_at=1.6, arrow_half=0.3)
    axis_line = ax.lines[3]
    assert np.allclose(axis_line.get_xydata()[0], c - [2, 0])
    tris = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(tris) == 3   # 弧箭头 + 双向箭头两端
    tips = np.array([t.get_xy()[0] for t in tris[1:]])
    assert np.allclose(tips[:, 0], c[0] + 1.6)
    assert set(np.round(tips[:, 1] - c[1], 6)) == {0.3, -0.3}
    draw_flip_axis(ax, c, [1, 1], 2.0, preset=preset)   # 无箭头
    assert len([p for p in ax.patches if isinstance(p, Polygon)]) == 3


def test_wedge_angle_mark_matches_geometry(ax):
    wedge = two_face_medium(entry=([-1.0, 0.0], [-3.0, -4.0]), exit=([3.0, -4.0], [1.0, 0.0]))
    theta = draw_wedge_angle(ax, wedge, preset=PRESETS["default"], radius=1.5)
    assert np.isclose(theta, wedge_angle(wedge))
    arc = [l for l in ax.lines if len(l.get_xdata()) > 2][0].get_xydata()
    apex = np.array([0.0, 2.0])
    assert np.allclose(np.linalg.norm(arc - apex, axis=1), 1.5)
    texts = [t for t in ax.texts]
    assert texts and texts[0].get_text() == r"$\theta$"
    render_medium(ax, wedge, preset=PRESETS["default"], closure="jagged")
    assert any(isinstance(p, Polygon) and len(p.get_xy()) > 10 for p in ax.patches)


def test_multi_panel_grid_and_shared_scale():
    fig, axes = multi_panel(2, 3, 600, 400, dpi=100, preset=PRESETS["default"],
                            titles=[f"$R^c_{k}$" for k in range(6)])
    assert len(axes) == 2 and all(len(row) == 3 for row in axes)
    assert fig.get_size_inches()[0] * 100 == pytest.approx(600, abs=1)
    for row in axes:
        for a in row:
            finish(a, (-2, 2), (-2, 2))
    boxes = [a.get_position().bounds for row in axes for a in row]
    assert len({round(b[2], 6) for b in boxes}) == 1 and len({round(b[3], 6) for b in boxes}) == 1
    assert all(a.get_xlim() == (-2, 2) for row in axes for a in row)
    assert [t.get_text() for row in axes for a in row for t in a.texts] == [f"$R^c_{k}$" for k in range(6)]
    plt.close(fig)


# ---- ch7 新增图元：翻转标记 / 跨 axes 引线 ----------------------------------------------------

def test_draw_flip_marker_draws_bar_and_double_arrow(ax):
    from halo_notes.draw.scene2d import draw_flip_marker
    preset = PRESETS["default"]
    draw_flip_marker(ax, (0.5, -0.25), preset=preset, size=0.6)
    lines = ax.lines
    assert len(lines) == 2
    bar = [l for l in lines if np.ptp(l.get_ydata()) == 0][0]          # 水平线：长 = size、过中心
    shaft = [l for l in lines if np.ptp(l.get_xdata()) == 0][0]        # 竖直杆：过中心
    assert np.isclose(np.ptp(bar.get_xdata()), 0.6) and np.allclose(np.mean(bar.get_xdata()), 0.5)
    assert np.allclose(bar.get_ydata(), -0.25) and np.allclose(shaft.get_xdata(), 0.5)
    tris = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(tris) == 2
    tips = sorted(t.get_xy()[0][1] for t in tris)
    assert np.isclose(tips[0], -0.25 - 0.36) and np.isclose(tips[1], -0.25 + 0.36)   # 两头尖在 ±size·0.6
    kw = preset.line_kwargs("flip_marker")
    assert all(l.get_color() == kw["color"] for l in lines)
    with pytest.raises(ValueError):
        draw_flip_marker(ax, (0, 0), preset=preset, size=0.1)


def test_draw_connector_keeps_data_coordinates_of_both_axes():
    from matplotlib.patches import ConnectionPatch

    from halo_notes.draw.scene2d import draw_connector
    fig = plt.figure()
    ax_a, ax_b = fig.add_axes([0, 0, 0.5, 1]), fig.add_axes([0.5, 0, 0.5, 1])
    ax_a.set_xlim(0, 10), ax_a.set_ylim(0, 10), ax_b.set_xlim(-1, 1), ax_b.set_ylim(-1, 1)
    preset = PRESETS["default"]
    patch = draw_connector(ax_a, (2.0, 3.0), ax_b, (0.5, -0.5), preset=preset)
    assert isinstance(patch, ConnectionPatch) and patch in ax_b.get_children()
    assert tuple(patch.xy1) == (2.0, 3.0) and tuple(patch.xy2) == (0.5, -0.5)
    assert patch.coords1 == "data" and patch.coords2 == "data" and patch.axesA is ax_a
    # 端点在 figure 像素坐标里确实落到两个 axes 各自的数据点上
    fig.canvas.draw()
    a_px = ax_a.transData.transform((2.0, 3.0))
    b_px = ax_b.transData.transform((0.5, -0.5))
    verts = patch.get_path().transformed(patch.get_transform()).vertices
    assert np.allclose(verts[0], a_px, atol=1e-6) and np.allclose(verts[-1], b_px, atol=1e-6)
    kw = preset.line_kwargs("connector")
    assert patch.get_edgecolor()[:3] == pytest.approx(matplotlib.colors.to_rgb(kw["color"]))
    # 起点在 ax_a 视野之外（如出射光末端在面板取景之外）也照画：ConnectionPatch 默认会整条不画
    outside = draw_connector(ax_a, (-5.0, 3.0), ax_b, (0.0, 0.0), preset=preset)
    assert outside.get_annotation_clip() is False and outside._check_xy(fig.canvas.get_renderer())
    plt.close(fig)
