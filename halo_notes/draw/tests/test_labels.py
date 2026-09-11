import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.text import Text  # noqa: E402

from halo_notes.draw import PRESETS, Camera, HexPrism, finish, new_figure, render_crystal  # noqa: E402
from halo_notes.draw.labels import (draw_face_number, draw_face_number_flat,  # noqa: E402
                                    draw_face_number_warped, face_label_anchor)
from halo_notes.draw.projection import face_in_plane_basis, face_jacobian  # noqa: E402
from halo_notes.draw.style import DEFAULT_GEOM, FaceNumberStyle  # noqa: E402


def _singular_ratio(J: np.ndarray) -> float:
    s = np.linalg.svd(J, compute_uv=False)
    return s[1] / s[0]


def test_face_basis_is_orthonormal_and_in_plane():
    prism = HexPrism()
    for f in prism.faces:
        u, v = face_in_plane_basis(prism, f)
        n = prism.normal(f)
        assert np.isclose(u @ u, 1) and np.isclose(v @ v, 1) and np.isclose(u @ v, 0)
        assert np.isclose(u @ n, 0) and np.isclose(v @ n, 0)
        assert np.allclose(np.cross(u, v), n)  # 右手系：从外侧看 u 向右、v 向上


def test_prism_face_text_up_is_c_axis():
    prism = HexPrism()
    for k in range(3, 9):
        _, v = face_in_plane_basis(prism, prism.face(k))
        assert np.allclose(v, [0, 0, 1])


def test_jacobian_identity_for_face_on_view():
    """正交、正对面 3（法向 +x）：面内 u=+y→画面 x，v=+z→画面 y，雅可比为单位阵。"""
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0, projection="orthographic")
    assert np.allclose(face_jacobian(prism, prism.face(3), cam), np.eye(2), atol=1e-6)


def test_jacobian_shrinks_with_obliquity():
    """斜看面 3：u 方向被压成 cos(方位角)，且越斜压得越狠。"""
    prism = HexPrism()
    ratios = []
    for az in (30, 60, 80):
        cam = Camera(azimuth=az, elevation=0, projection="orthographic")
        J = face_jacobian(prism, prism.face(3), cam)
        assert np.isclose(_singular_ratio(J), np.cos(np.deg2rad(az)), atol=1e-6)
        ratios.append(_singular_ratio(J))
    assert ratios[0] > ratios[1] > ratios[2]


def test_jacobian_perspective_adds_depth_scale():
    """透视下同一面的雅可比比正交多一层 distance/(distance-depth) 的整体放大。"""
    prism = HexPrism()
    ortho = Camera(azimuth=0, elevation=0, projection="orthographic")
    persp = Camera(azimuth=0, elevation=0, projection="perspective", distance=4)
    depth = prism.centroid(prism.face(3))[0]  # 面 3 质心沿视线 (+x) 的深度
    expected = 4 / (4 - depth)
    Jo, Jp = face_jacobian(prism, prism.face(3), ortho), face_jacobian(prism, prism.face(3), persp)
    assert np.allclose(Jp, expected * Jo, atol=1e-3)
    assert expected > 1


def test_back_face_is_mirrored():
    """从背面看到的面（透过晶体）行列式为负：文字呈镜像，与旧图一致。"""
    prism = HexPrism()
    cam = Camera(azimuth=0, elevation=0)
    assert np.linalg.det(face_jacobian(prism, prism.face(3), cam)) > 0
    assert np.linalg.det(face_jacobian(prism, prism.face(6), cam)) < 0


def test_warped_label_centered_on_anchor_after_finish():
    """贴面字形的中心落在面心投影处，且 finish() 事后改坐标范围仍成立（惰性变换）。"""
    prism = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    fig, ax = new_figure(400, 300, dpi=50)
    patch = draw_face_number_warped(ax, prism, prism.face(4), cam, PRESETS["default"])
    finish(ax, (-3, 3), (-2, 2))
    fig.canvas.draw()
    center_px = patch.get_transform().transform((0, 0))
    anchor_px = ax.transData.transform(face_label_anchor(prism, prism.face(4), cam))
    assert np.allclose(center_px, anchor_px, atol=1e-6)
    plt.close(fig)


def test_flat_label_is_text_at_anchor():
    prism = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    fig, ax = new_figure(400, 300, dpi=50)
    t = draw_face_number_flat(ax, prism, prism.face(4), cam, PRESETS["default"])
    assert isinstance(t, Text) and t.get_text() == "4"
    assert np.allclose(t.get_position(), face_label_anchor(prism, prism.face(4), cam))
    plt.close(fig)


def test_dispatch_follows_geom_face_number_style():
    prism = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    base = PRESETS["default"]
    assert base.geom.face_number_style is FaceNumberStyle.WARPED
    fig, ax = new_figure(400, 300, dpi=50)
    assert isinstance(draw_face_number(ax, prism, prism.face(4), cam, base), PathPatch)
    flat = base.replace(geom=DEFAULT_GEOM.replace(face_number_style=FaceNumberStyle.FLAT))
    assert isinstance(draw_face_number(ax, prism, prism.face(4), cam, flat), Text)
    plt.close(fig)


def test_render_crystal_flat_style_keeps_texts():
    prism = HexPrism(1, 0.8)
    cam = Camera(azimuth=72, elevation=20)
    flat = PRESETS["default"].replace(geom=DEFAULT_GEOM.replace(face_number_style=FaceNumberStyle.FLAT))
    fig, ax = new_figure(400, 300, dpi=50)
    render_crystal(ax, prism, camera=cam, preset=flat, face_numbers=True)
    assert len(ax.texts) == 8 and len(ax.patches) == 0
    plt.close(fig)
