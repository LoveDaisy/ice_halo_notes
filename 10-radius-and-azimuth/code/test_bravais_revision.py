"""图 4 正穿/斜穿：直接核验成图使用的几何，不以标题或预填角度作证。"""
import matplotlib.pyplot as plt
import numpy as np
import pytest

import fig_bravais_prism as F


@pytest.fixture(scope="module")
def comparison():
    fig, scenes = F.make_figure()
    fig.canvas.draw()
    yield fig, scenes
    plt.close(fig)


def line_by_gid(ax, gid):
    return next(line for line in ax.lines if line.get_gid() == gid)


@pytest.mark.parametrize("index,height", [(0, 0.0), (1, 40.0)])
def test_two_drawn_cases_are_real_same_wedge_paths(comparison, index, height):
    fig, scenes = comparison
    scene = scenes[index]
    crystal, path = scene.crystal, scene.path
    directions = np.diff(path.points, axis=0)
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    k = directions * np.array([1.0, F.optics.N, 1.0])[:, None]
    np.testing.assert_allclose(k[:, 2], -np.sin(np.radians(height)), atol=2e-9)
    assert [event.face_number for event in path.events] == [3, 5]
    assert not path.sketch
    normals = [crystal.normal(crystal.face(number)) for number in (3, 5)]
    # 两侧面的外法向夹角是 120°，相应透射楔角是 60°。
    assert normals[0] @ normals[1] == pytest.approx(-0.5)
    for i, event in enumerate(path.events):
        normal = normals[i]
        vertices = crystal.face_vertices(crystal.face(event.face_number))
        point = path.points[event.point_index]
        assert abs((point - vertices[0]) @ normal) < 2e-9
        edges = np.roll(vertices, -1, axis=0) - vertices
        inward = np.cross(normal, edges)
        assert np.min(np.sum(inward * (point - vertices), axis=1)) > 1e-4
        np.testing.assert_allclose(np.cross(k[i + 1] - k[i], normal), 0, atol=2e-9)
    # 凸体半空间保证画出的冰内段并未穿出其他面。
    for face in crystal.faces:
        signed = (path.points[1:3] - crystal.face_vertices(face)[0]) @ crystal.normal(face)
        assert max(signed) < 2e-9
    # LI 的方向传递不调用用于绘图的有限晶体追迹器。
    np.testing.assert_allclose(-directions[-1], F.optics.light_point(-directions[0])[0], atol=2e-9)
    axes = {ax.get_label(): ax for ax in fig.axes}
    # 俯视光路按系列约定分两色画（入射 + 冰内红、出射蓝），两段首尾相接即完整光路。
    section = axes[f"horizontal-section-{index}"]
    actual = np.vstack([line_by_gid(section, "projected-ray").get_xydata(),
                        line_by_gid(section, "projected-ray-exit").get_xydata()[1:]])
    np.testing.assert_allclose(actual, path.points[:, :2] @ F.SECTION_BASIS.T, atol=2e-9)
    # 标出的两条楔面边确实落在入射面 3 与出射面 5 上，延长线夹角 60°。
    edges = [line.get_xydata() for line in section.lines if line.get_gid() == "wedge-face"]
    assert len(edges) == 2
    for edge, number in zip(edges, (3, 5)):
        normal = crystal.normal(crystal.face(number))
        offset = crystal.face_vertices(crystal.face(number))[0] @ normal
        world = edge @ F.SECTION_BASIS  # 纸面基正交，逆即转置
        np.testing.assert_allclose(world @ normal[:2], offset, atol=1e-9)
    d = [e[1] - e[0] for e in edges]
    cos = abs(d[0] @ d[1]) / np.prod(np.linalg.norm(d, axis=1))
    assert np.degrees(np.arccos(cos)) == pytest.approx(60)
    expected = F.CAMERA.project_xy(path.points[1:3])
    assert any(line.get_xydata().shape == expected.shape and np.allclose(line.get_xydata(), expected)
               for line in axes[f"prism-3d-{index}"].lines)


def test_drawn_angle_arcs_match_independent_horizontal_snell(comparison):
    fig, scenes = comparison
    axes = {ax.get_label(): ax for ax in fig.axes}
    measured = []
    for i, scene in enumerate(scenes):
        height = np.degrees(np.arcsin(scene.sun[2]))
        xy = scene.path.points[:, :2] @ F.SECTION_BASIS.T
        arc = line_by_gid(axes[f"horizontal-section-{i}"], "horizontal-deviation-arc").get_xydata()
        arc_vectors = arc - xy[2]
        np.testing.assert_allclose(np.linalg.norm(arc_vectors, axis=1), 0.72, atol=2e-9)
        ends = arc_vectors[[0, -1]] / 0.72
        expected_ends = np.array([xy[1] - xy[0], xy[3] - xy[2]])
        expected_ends /= np.linalg.norm(expected_ends, axis=1, keepdims=True)
        np.testing.assert_allclose(ends, expected_ends, atol=2e-9)
        angle = np.degrees(np.arctan2(abs(np.linalg.det(ends)), ends[0] @ ends[1]))
        n_eff = np.sqrt(F.optics.N ** 2 - np.sin(np.radians(height)) ** 2) / np.cos(np.radians(height))
        expected_angle = 2 * np.degrees(np.arcsin(n_eff / 2)) - 60
        assert angle == pytest.approx(expected_angle, abs=1e-6)
        measured.append(angle)
    assert measured[1] > measured[0]
    np.testing.assert_allclose(scenes[0].crystal.vertices, scenes[1].crystal.vertices, atol=2e-9)


def test_single_interface_component_diagram_uses_k_not_unit_d(comparison):
    fig, scenes = comparison
    ax = next(ax for ax in fig.axes if ax.get_label() == "wavevector-components")
    lines = [line for line in ax.lines if line.get_gid() == "wavevector"]
    assert len(lines) == 2
    k = scenes[1].wavevectors[:2]
    vectors = np.array([line.get_xydata()[1] - line.get_xydata()[0] for line in lines])
    np.testing.assert_allclose(vectors, np.column_stack([np.linalg.norm(k[:, :2], axis=1), k[:, 2]]), atol=2e-9)
    assert vectors[0, 1] == pytest.approx(vectors[1, 1], abs=2e-9)
    assert vectors[1, 0] > vectors[0, 0]
    assert abs(vectors[1, 1] - scenes[1].directions[1, 2]) > 0.1


def test_perspective_and_same_image_scale():
    assert F.CAMERA.projection == "perspective"
    near, far = F.CAMERA.project_xy([F.CAMERA.right + F.CAMERA.view_dir,
                                    F.CAMERA.right - F.CAMERA.view_dir])
    assert near[0] / far[0] == pytest.approx((F.CAMERA.distance + 1) / (F.CAMERA.distance - 1))
    assert np.linalg.det(F.SECTION_BASIS) == pytest.approx(1)
    np.testing.assert_allclose(F.SECTION_BASIS @ F.SECTION_BASIS.T, np.eye(2), atol=1e-14)
