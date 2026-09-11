import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from halo_notes.draw import (PRESETS, Camera, HexPrism, draw_axes, finish, new_figure,  # noqa: E402
                             render_crystal, trace)
from halo_notes.draw.labels import face_label_anchor, point_in_polygon  # noqa: E402
from halo_notes.draw.projection import visible_faces  # noqa: E402
from halo_notes.draw.raypath import SegmentKind  # noqa: E402
from halo_notes.draw.scene import (Z_CONE_FILL, Z_CONE_OUTLINE, Z_EXTERNAL, Z_INTERNAL,  # noqa: E402
                                   Z_VISIBLE_EDGE)


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
    assert len(ax.texts) == 8
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
