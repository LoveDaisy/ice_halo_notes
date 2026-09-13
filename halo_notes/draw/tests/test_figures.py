"""逐图语义单测：跑每个 fig 脚本，抓它实际画出的每条 ``RayPath`` / ``RayPath2D``，白盒复核"画的是不是声明的那条光路"。
3D 图与 2D 截面图走同一条判据（``verify_path`` / ``locate_body`` 与维数无关；2D 多边形实现了同一套面协议）。

每条画出的光路必须二选一：
- 面序列 ∈ 该图声明的 ``PATHS``，且每个事件点落在**本图已渲染的某个多面体**的该编号面内部、
  方向变化满足对应定律（Snell / 反射 / 穿越不变；:func:`raypath.verify_path`）；
  事件在折线端点上（如 ``unfolded_tail`` 去掉入射段后的展开直线）时，必须接续本图另一条
  完整光路在同一点、同一面的同一事件（同一条光线的两种画法）
- 或显式 ``sketch=True``（手画示意线）

事件所属多面体按几何定位（事件点在哪个已渲染多面体的该编号面上），不借用 ``draw_raypath``
调用点传入的 crystal / 遮挡体参数——旧审计脚本正是用错这个参数得出 2.6 "面 3 处 111°" 的假阳性。
渲染输出被 monkeypatch 掉（``Figure.savefig`` 与 ``PillowWriter.finish`` 空操作），不会覆盖 ``img/``
里的正式图与 gif；``grab_frame`` 保持真实执行，动画脚本跑满整条逐帧路径。没有光路的图（``PATHS = {}``）
必须至少渲染了一个多面体或一个球面图元（``cap.spheres``）。
"""

from __future__ import annotations

import contextlib
import io
import runpy
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation  # noqa: E402
import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import halo_notes.draw as draw  # noqa: E402
import halo_notes.draw.scene as scene  # noqa: E402
import halo_notes.draw.scene2d as scene2d  # noqa: E402
import halo_notes.draw.sphere as sphere  # noqa: E402
from halo_notes.draw.geometry import Polyhedron, unit  # noqa: E402
from halo_notes.draw.raypath import EventKind, RayEvent, RayPath, face_sequence, verify_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CH1, CH2, CH3 = "01-symmetry/code", "02-raypath-enumeration/code", "03-parallel-raypaths/code"
CH4, CH5, CH6 = "04-render-equation/code", "05-rotation-3d/code", "06-monte-carlo-vs-integration/code"
CH7 = "07-reflection-group/code"

# 图 → 脚本；每个脚本头部自己声明 ``PATHS = {名字: 面序列}``，测试从脚本命名空间读取，不另存一份映射
#（没有光路的图声明空字典：测试断言它确实一条光路都没画）
FIGURES = {
    "1.2": f"{CH1}/fig_raypath_symmetry.py",
    "1.3": f"{CH1}/fig_c6.py",
    "1.6": f"{CH1}/fig_d6_f.py",
    "2.2": f"{CH2}/fig_tricker_arc_raypath.py",
    "2.3": f"{CH2}/fig_geo_validation.py",
    "2.4": f"{CH2}/fig_expand_rp132.py",
    "2.5": f"{CH2}/fig_light_corridor_rp132_00.py",
    "2.6": f"{CH2}/fig_light_corridor_rp31574.py",
    "2.7": f"{CH2}/fig_light_corridor_rp132_01.py",
    "2.8": f"{CH2}/fig_light_corridor_rp132_02_note.py",
    "2.9": f"{CH2}/fig_light_corridor_rp132_03.py",
    "3.1": f"{CH3}/fig_ch3_wedge_path.py",
    "3.2": f"{CH3}/fig_tricker_arc_raypath_expand.py",
    "3.4": f"{CH3}/fig_rotation_steps.py",
    "3.5": f"{CH3}/fig_tricker_arc_plot.py",
    "3.6": f"{CH3}/fig_tricker_arc_cone_plot.py",
    "4.1": f"{CH4}/fig_ch4_raypath_all.py",
    "5.1": f"{CH5}/fig_ch5_interp.py",
    "6.1": f"{CH6}/fig_crystal_pose.py",
    "6.2": f"{CH6}/fig_trace.py",
    "7.1": f"{CH7}/fig_four_mirrors.py",
    "7.2": f"{CH7}/fig_two_mirrors_120.py",
    "7.3": f"{CH7}/fig_grid_6x2.py",
    "7.4": f"{CH7}/fig_conjugate_rot90.py",
    "7.5": f"{CH7}/fig_pose_to_sky.py",
    "7.5g": f"{CH7}/fig_pose_to_sky_gif.py",
}


SPHERE_RENDERERS = ("graticule", "render_point_cloud", "render_curve", "render_great_circle", "render_cone")


class Capture:
    """spy：记录本图渲染的所有多面体、画出的所有光路，以及调用过的球面图元（函数名）。"""

    def __init__(self):
        self.bodies: list[Polyhedron] = []
        self.paths: list[tuple[RayPath, str | None]] = []
        self.spheres: list[str] = []
        self.sphere_calls: list[tuple[str, tuple, dict]] = []           # (函数名, 位置参数, 关键字参数)
        self.cameras: list[object] = []                                   # 每次 render_crystal 传入的相机
        self.arcs: list[tuple[object, np.ndarray, float, str]] = []      # (ax, 轴, 张角, 语义)
        self.arrows: list[tuple[object, np.ndarray, np.ndarray]] = []    # (ax, 起点, 方向)
        self.planes: list[tuple[object, Polyhedron, int, np.ndarray]] = []   # (ax, 晶体, 面号, 平面四顶点)：draw_highlight_plane
        self.flip_axes: list[tuple[object, np.ndarray, np.ndarray]] = []     # (ax, 过点, 方向)：scene2d.draw_flip_axis
        self.arcs2d: list[tuple[object, np.ndarray, float, float]] = []      # (ax, 圆心, 起角, 止角)：scene2d.draw_rotation_arc
        self.flip_markers: list[tuple[object, np.ndarray]] = []               # (ax, 中心)：scene2d.draw_flip_marker
        self.connectors: list[object] = []                                    # scene2d.draw_connector 返回的 ConnectionPatch
        self.axes2d: list[object] = []                                        # 每次 render_section 画在哪个 ax（与 bodies 同序，仅 2D）
        self.gif_frames: list[tuple[int, int]] = []                           # PillowWriter.grab_frame 逐帧的帧尺寸


def install_spies(cap: Capture, monkeypatch) -> None:
    """把 3D / 2D / 球面渲染入口换成记录到 ``cap`` 的 spy，并让 savefig / gif 落盘变成空操作。"""
    real_render, real_draw = scene.render_crystal, scene.draw_raypath

    def spy_render(ax, crystal, raypaths=None, **kw):
        cap.bodies.append(crystal)
        cap.cameras.append(kw.get("camera"))
        return real_render(ax, crystal, raypaths, **kw)

    def spy_draw(ax, path, crystal=None, **kw):
        cap.paths.append((path, kw.get("semantic")))
        return real_draw(ax, path, crystal, **kw)

    real_render2d, real_draw2d = scene2d.render_section, scene2d.draw_raypath_2d

    def spy_render2d(ax, poly, raypaths=None, **kw):
        cap.bodies.append(poly)
        cap.axes2d.append(ax)
        return real_render2d(ax, poly, raypaths, **kw)

    def spy_draw2d(ax, path, **kw):
        sem = kw.get("semantic")
        cap.paths.append((path, sem if isinstance(sem, str) else None))
        return real_draw2d(ax, path, **kw)

    for mod in (scene, draw):
        monkeypatch.setattr(mod, "render_crystal", spy_render)
        monkeypatch.setattr(mod, "draw_raypath", spy_draw)
    for mod in (scene2d, draw):
        monkeypatch.setattr(mod, "render_section", spy_render2d)
        monkeypatch.setattr(mod, "draw_raypath_2d", spy_draw2d)
    real_arc, real_arrow = scene.draw_rotation_arc_3d, scene.draw_axis_arrow

    def spy_arc(ax, axis, radius, start_dir, angle_deg, **kw):
        cap.arcs.append((ax, unit(axis), float(angle_deg), kw["semantic"]))
        return real_arc(ax, axis, radius, start_dir, angle_deg, **kw)

    def spy_arrow(ax, origin, direction, length, **kw):
        cap.arrows.append((ax, np.asarray(origin, float), unit(direction)))
        return real_arrow(ax, origin, direction, length, **kw)

    for mod in (scene, draw):
        monkeypatch.setattr(mod, "draw_rotation_arc_3d", spy_arc)
        monkeypatch.setattr(mod, "draw_axis_arrow", spy_arrow)
    real_plane = scene.draw_highlight_plane

    def spy_plane(ax, crystal, face_number, **kw):
        quad = real_plane(ax, crystal, face_number, **kw)
        cap.planes.append((ax, crystal, int(face_number), quad))
        return quad

    real_flip_axis, real_arc2d = scene2d.draw_flip_axis, scene2d.draw_rotation_arc
    real_flip_marker, real_connector = scene2d.draw_flip_marker, scene2d.draw_connector

    def spy_flip_axis(ax, point, direction, half_length, **kw):
        cap.flip_axes.append((ax, np.asarray(point, float), unit(direction)))
        return real_flip_axis(ax, point, direction, half_length, **kw)

    def spy_arc2d(ax, center, radius, start_deg, end_deg, **kw):
        cap.arcs2d.append((ax, np.asarray(center, float), float(start_deg), float(end_deg)))
        return real_arc2d(ax, center, radius, start_deg, end_deg, **kw)

    def spy_flip_marker(ax, point, **kw):
        cap.flip_markers.append((ax, np.asarray(point, float)))
        return real_flip_marker(ax, point, **kw)

    def spy_connector(ax_a, xy_a, ax_b, xy_b, **kw):
        patch = real_connector(ax_a, xy_a, ax_b, xy_b, **kw)
        cap.connectors.append(patch)
        return patch

    for mod in (scene, draw):
        monkeypatch.setattr(mod, "draw_highlight_plane", spy_plane)
    for mod in (scene2d, draw):
        monkeypatch.setattr(mod, "draw_flip_axis", spy_flip_axis)
        monkeypatch.setattr(mod, "draw_rotation_arc", spy_arc2d)
        monkeypatch.setattr(mod, "draw_flip_marker", spy_flip_marker)
        monkeypatch.setattr(mod, "draw_connector", spy_connector)
    for name in SPHERE_RENDERERS:
        real = getattr(sphere, name)

        def spy_sphere(*a, _name=name, _real=real, **kw):
            cap.spheres.append(_name)
            cap.sphere_calls.append((_name, a, kw))
            return _real(*a, **kw)

        for mod in (sphere, draw):
            monkeypatch.setattr(mod, name, spy_sphere)
    # savefig 只在目标是文件路径时空操作；写进内存缓冲（PillowWriter.grab_frame 逐帧抓画布）照常执行
    real_savefig = matplotlib.figure.Figure.savefig

    def savefig_unless_file(self, fname, *a, **k):
        if isinstance(fname, (str, Path)):
            return None
        return real_savefig(self, fname, *a, **k)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", savefig_unless_file)
    monkeypatch.setattr(matplotlib.animation.PillowWriter, "finish", lambda self: None)
    real_grab = matplotlib.animation.PillowWriter.grab_frame

    def spy_grab(self, **kw):
        real_grab(self, **kw)
        cap.gif_frames.append(tuple(self.frame_size))

    monkeypatch.setattr(matplotlib.animation.PillowWriter, "grab_frame", spy_grab)


def run_figure(script: str, monkeypatch) -> tuple[Capture, dict]:
    cap = Capture()
    install_spies(cap, monkeypatch)
    path = ROOT / script
    monkeypatch.syspath_prepend(str(path.parent))
    for helper in ("_light_corridor_rp132", "_tricker_arc", "_pose_to_sky"):   # 章内共享 helper 每图重新导入，拿到本次的 spy
        sys.modules.pop(helper, None)
    with contextlib.redirect_stdout(io.StringIO()):
        ns = runpy.run_path(str(path), run_name="__main__")
    plt.close("all")
    return cap, ns


def test_spies_capture_sphere_renderers_and_swallow_gif_output(monkeypatch, tmp_path):
    """既有图脚本既不画球面也不产 gif，触发不到这两个 patch——用最小 stub 直接验证它们生效。"""
    cap = Capture()
    install_spies(cap, monkeypatch)
    fig, ax = draw.new_figure(100, 100, dpi=50)
    cam = draw.Camera(azimuth=30, elevation=20)
    s = draw.Sphere()
    draw.graticule(ax, s, camera=cam, preset=draw.PRESETS["default"], lat_step=45, lon_step=90, samples=19)
    sphere.render_point_cloud(ax, s, [[0, 0, 1]], camera=cam, preset=draw.PRESETS["default"])
    assert cap.spheres == ["graticule", "render_point_cloud"]
    out = tmp_path / "x.gif"
    w = matplotlib.animation.PillowWriter(fps=10)
    with w.saving(fig, str(out), 50):
        w.grab_frame()
    assert len(w._frames) == 1       # 帧确实抓到了（savefig 写内存缓冲照常）
    assert not out.exists()          # finish 被空操作掉：文件没落盘
    fig.savefig(tmp_path / "x.png")
    assert not (tmp_path / "x.png").exists()
    plt.close(fig)


def _on_face(body: Polyhedron, number: int, point) -> bool:
    if number not in {f.number for f in body.faces}:
        return False
    f = body.face(number)
    return abs(body.face_distance(f, point)) < 1e-6 and body.face_margin(f, point) > 0


def locate_body(bodies: list[Polyhedron], path: RayPath, ev: RayEvent) -> Polyhedron:
    """事件发生在本图哪个多面体上：事件点在其该编号面内部；反射面在晶体 k-1 与幽灵 k 上共面
    （法向相反），按事件种类用入射方向与外法向的符号区分"进入的是哪一个"。"""
    q = path.points[ev.point_index]
    hits = [b for b in bodies if _on_face(b, ev.face_number, q)]
    if not hits:
        raise AssertionError(f"event {ev.kind.value} on face {ev.face_number} at {np.round(q, 3)} "
                             f"is not on that face of any rendered body")
    if len(hits) == 1 or ev.point_index == 0:
        return hits[0]
    d_in = unit(q - path.points[ev.point_index - 1])
    want_entering = ev.kind in (EventKind.REFRACT_IN, EventKind.REFLECT_EXTERNAL)
    want_leaving = ev.kind in (EventKind.REFRACT_OUT, EventKind.REFLECT_INTERNAL)
    for b in hits:
        s = b.normal(b.face(ev.face_number)) @ d_in
        if (want_entering and s < 0) or (want_leaving and s > 0) or ev.kind is EventKind.PASS_THROUGH:
            return b
    return hits[0]


def continues_a_full_path(path: RayPath, ev: RayEvent, others: list[RayPath]) -> bool:
    """端点上的事件：本图另一条完整光路在同一点、同一面有同种事件，且之后的方向一致。"""
    q = path.points[ev.point_index]
    d = unit(path.points[ev.point_index + 1] - q)
    for other in others:
        if other is path or other.sketch:
            continue
        for oev in other.events:
            i = oev.point_index
            if (oev.kind is ev.kind and oev.face_number == ev.face_number and 0 < i < len(other.points) - 1
                    and np.allclose(other.points[i], q, atol=1e-9)
                    and np.allclose(unit(other.points[i + 1] - other.points[i]), d, atol=1e-9)):
                return True
    return False


@pytest.mark.parametrize("fig", sorted(FIGURES))
def test_every_drawn_raypath_is_the_declared_light_path(fig, monkeypatch):
    script = FIGURES[fig]
    cap, ns = run_figure(script, monkeypatch)
    assert "PATHS" in ns, f"{fig}: script must declare PATHS = {{name: [faces…]}} at module level"
    expected = {k: list(v) for k, v in ns["PATHS"].items()}
    if not expected:
        assert not cap.paths, f"{fig}: PATHS is empty but {len(cap.paths)} RayPath(s) were drawn"
        assert cap.bodies or cap.spheres, f"{fig}: nothing rendered (no polyhedron, no sphere primitive)"
        return
    assert cap.paths, f"{fig}: no RayPath drawn"
    all_paths = [p for p, _ in cap.paths]
    problems: list[str] = []
    for path, semantic in cap.paths:
        tag = f"{fig} [{semantic or '-'}] faces={face_sequence(path)}"
        if path.sketch:
            continue
        if not path.events:
            problems.append(f"{tag}: hand-drawn polyline without events and not marked sketch=True")
            continue
        if face_sequence(path) not in expected.values():
            problems.append(f"{tag}: face sequence not among declared PATHS {list(expected.values())}")
            continue
        # 一条光路的全部事件都落在同一个多面体上时（动画逐帧渲染了几十枚姿态相近的晶体，相邻帧的同号面几乎重合），
        # 就按整条光路定位那个多面体；否则（展开幽灵链）逐事件按几何定位
        whole = [b for b in cap.bodies if all(_on_face(b, ev.face_number, path.points[ev.point_index]) for ev in path.events)]
        # 来回扫描的动画会把同一姿态渲染两次（两枚一模一样的晶体）：候选多于一个时逐个试，有一个通过即可
        candidates = [(lambda ev, b=b: b) for b in whole] or [lambda ev: locate_body(cap.bodies, path, ev)]
        errors = []
        for body_of in candidates:
            try:
                verify_path(path, body_of, tol=1e-9, min_margin=1e-6)
                break
            except (ValueError, AssertionError) as e:
                errors.append(str(e))
        else:
            problems.append(f"{tag}: {errors[0]}")
            continue
        for ev in path.events:
            if ev.point_index in (0, len(path.points) - 1) and not continues_a_full_path(path, ev, all_paths):
                problems.append(f"{tag}: endpoint event {ev.kind.value}@{ev.face_number} does not "
                                f"continue a full traced path drawn in this figure")
    assert not problems, "\n".join(problems)


# ---- 逐图语义单测（task-draw-rest：无光路的图，按 issue「机械核验」列另行断言） ----------------------

def _same_direction(a, b, tol=1e-9) -> bool:
    return np.linalg.norm(unit(a) - unit(b)) < tol


def test_3_4_rotation_steps_follow_the_text(monkeypatch):
    """R₁ = R_z(θ)、R₂ = R_y(90°)·R₁、R₃ = R_z(α)·R₂，且与正文第 75 行起的显式矩阵逐项一致；
    三帧各画的弧：帧 1 绕 z 标 θ，帧 2 绕 y 标 90° + 绕 c 轴标 θ，帧 3 绕 z 标 α + 绕 c 轴标 θ；主轴箭头沿 R₃ 的 c 轴；
    三帧共用同一相机实例。"""
    cap, ns = run_figure(FIGURES["3.4"], monkeypatch)
    R1, R2, R3 = ns["ROTATIONS"]
    th, al = np.deg2rad(ns["THETA_DEG"]), np.deg2rad(ns["ALPHA_DEG"])
    Rz = lambda a: draw.rotation((0, 0, 1), np.rad2deg(a))  # noqa: E731
    assert np.abs(R1 - Rz(th)).max() < 1e-9
    assert np.abs(R2 - draw.rotation((0, 1, 0), 90.0) @ R1).max() < 1e-9
    assert np.abs(R3 - Rz(al) @ R2).max() < 1e-9
    text_R = np.array([[-np.sin(al) * np.sin(th), -np.sin(al) * np.cos(th), np.cos(al)],
                       [np.cos(al) * np.sin(th), np.cos(al) * np.cos(th), np.sin(al)],
                       [-np.cos(th), np.sin(th), 0.0]])
    assert np.abs(R3 - text_R).max() < 1e-9
    # 三帧晶体 = 标准晶体经 R₁ / R₂ / R₃（按渲染顺序）
    base = ns["CRYSTAL"]
    assert len(cap.bodies) == 3
    for body, R in zip(cap.bodies, (R1, R2, R3)):
        assert np.allclose(body.vertices, base.vertices @ R.T)
    # 弧按帧归组（同一 ax 上的弧属于同一帧）
    frames = {}
    for ax, axis, angle, sem in cap.arcs:
        frames.setdefault(id(ax), []).append((axis, angle, sem))
    assert len(frames) == 3
    f1, f2, f3 = [frames[id(ax)] for ax in dict.fromkeys(ax for ax, *_ in cap.arcs)]
    z, y = np.array([0, 0, 1.0]), np.array([0, 1.0, 0])

    def has(frame, axis, angle, sem):
        return any(_same_direction(a, axis) and np.isclose(g, angle) and s == sem for a, g, s in frame)

    theta, alpha = ns["THETA_DEG"], ns["ALPHA_DEG"]
    assert len(f1) == 1 and has(f1, z, theta, "arc_roll")
    assert len(f2) == 2 and has(f2, y, 90.0, "arc_tilt") and has(f2, R2[:, 2], theta, "arc_roll")
    assert len(f3) == 3 and has(f3, y, 90.0, "arc_tilt") and has(f3, z, alpha, "arc_azimuth") \
        and has(f3, R3[:, 2], theta, "arc_roll")
    assert _same_direction(R2[:, 2], [1, 0, 0])                      # 帧 2 的 c 轴横到 x
    assert len(cap.arrows) == 1 and _same_direction(cap.arrows[0][2], R3[:, 2])
    assert np.allclose(cap.arrows[0][1], 0)
    assert ns["THETA_DEG"] > 0 and 0 < ns["ALPHA_DEG"] < 90
    assert len(cap.cameras) == 3 and all(c is cap.cameras[0] for c in cap.cameras)   # 同一相机实例


def _tricker_arc_from_text(alpha, sigma_deg):
    """独立于脚本的复算：正文第 89 行起的整体变换矩阵 T(α) 作用在太阳方向 (cos Σ, 0, sin Σ) 上。"""
    s = np.deg2rad(sigma_deg)
    r = np.array([np.cos(s), 0.0, np.sin(s)])
    out = []
    for a in np.atleast_1d(alpha):
        T = np.array([[-0.75 - 0.25 * np.cos(2 * a), -0.25 * np.sin(2 * a), -np.sqrt(3) / 2 * np.sin(a)],
                      [-0.25 * np.sin(2 * a), -0.75 + 0.25 * np.cos(2 * a), np.sqrt(3) / 2 * np.cos(a)],
                      [np.sqrt(3) / 2 * np.sin(a), -np.sqrt(3) / 2 * np.cos(a), -0.5]])
        out.append(T @ r)
    return np.array(out)


def _check_tricker_curve(ns) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    alpha, curve, sigma = ns["ALPHA"], ns["CURVE"], ns["SUN_ELEVATION_DEG"]
    assert curve.shape == (len(alpha), 3) and alpha[0] == 0 and np.isclose(alpha[-1], 2 * np.pi)
    assert np.abs(np.linalg.norm(curve, axis=1) - 1.0).max() < 1e-12            # 落在单位球上
    assert np.abs(curve - _tricker_arc_from_text(alpha, sigma)).max() < 1e-12   # 与正文公式逐点一致
    assert np.abs(curve[0] - curve[-1]).max() < 1e-12                           # 闭合
    s = np.deg2rad(sigma)
    anthelic = np.array([-np.cos(s), 0.0, np.sin(s)])
    assert np.allclose(ns["anthelic_point"](), anthelic)
    # 反日点自交：解析地 A(α)=0 ⇔ sin α = √3 tan Σ 有两个根，两处都过该点
    roots = [np.arcsin(np.sqrt(3) * np.tan(s)), np.pi - np.arcsin(np.sqrt(3) * np.tan(s))]
    for a in roots:
        assert np.linalg.norm(ns["tricker_arc"](a) - anthelic) < 1e-9
    assert abs(roots[0] - roots[1]) > 0.1
    assert np.linalg.norm(curve - anthelic, axis=1).min() < 5e-3                # 采样点也贴近该点
    return curve, anthelic, alpha


def test_3_5_tricker_arc_is_the_text_formula(monkeypatch):
    cap, ns = run_figure(FIGURES["3.5"], monkeypatch)
    _check_tricker_curve(ns)
    assert cap.spheres.count("graticule") == 1 and cap.spheres.count("render_curve") == 1
    name, args, kw = [c for c in cap.sphere_calls if c[0] == "render_curve"][0]
    assert np.array_equal(args[2], ns["CURVE"]) and kw["split"] is False        # 整条弧一笔画（旧图不分前后）
    assert "render_cone" not in cap.spheres


def test_3_6_tricker_arc_lies_on_the_cone(monkeypatch):
    cap, ns = run_figure(FIGURES["3.6"], monkeypatch)
    curve, anthelic, _ = _check_tricker_curve(ns)
    # 曲线上每点相对锥顶（反日点）的方向与竖直轴夹角恒为 30°（上叶）或 150°（下叶）：|cos| = √3/2
    rel = curve - anthelic
    keep = np.linalg.norm(rel, axis=1) > 1e-6
    cos = rel[keep] @ [0, 0, 1] / np.linalg.norm(rel[keep], axis=1)
    assert np.abs(np.abs(cos) - np.sqrt(3) / 2).max() < 1e-9
    assert (cos > 0).any() and (cos < 0).any()                                  # 双叶都用到
    # 画出的锥面正是这个锥：顶点 = 反日点、轴竖直、半顶角 30°、两叶都画、按球裁剪
    cones = [c for c in cap.sphere_calls if c[0] == "render_cone"]
    assert len(cones) == 1
    _, args, kw = cones[0]
    assert np.allclose(args[1], anthelic) and _same_direction(args[2], [0, 0, 1]) and args[3] == 30.0
    assert kw["length_up"] > 0 and kw["length_down"] > 0 and kw["clip_inside"] is ns["SPHERE"]
    # 延伸长度盖过交线：交线上各点离锥顶的距离 ≤ 各叶长度
    d = np.linalg.norm(rel, axis=1)
    assert d[cos_full := (rel @ [0, 0, 1]) > 0].max() <= kw["length_up"] and d[~cos_full].max() <= kw["length_down"]


def test_5_1_three_interpolations_share_endpoints_and_differ_midway(monkeypatch):
    """左栏中间帧不再正交（det / RᵀR 偏离 > 0.1，恰好退化为 diag(1,0,0)）；右栏相邻帧旋转角相等且总角 = 起终
    相对旋转角（翻转场景下恰为 180°）；中栏欧拉角插值路径总旋转量明显超过 180°（多余旋转）且中途 c 轴几乎
    横躺；三栏首末帧相等；静态三联取首 / 中 / 末三帧且与 gif 同一帧序列（同一 render_frame）；跑一遍不落盘
    真实 gif / png。"""
    from halo_notes.draw.interp import relative_angle_deg
    gif = ROOT / "05-rotation-3d/img/ch5_interp.gif"
    png = ROOT / "05-rotation-3d/img/ch5_interp.png"
    before = (gif.read_bytes() if gif.exists() else None, png.read_bytes() if png.exists() else None)
    cap, ns = run_figure(FIGURES["5.1"], monkeypatch)
    assert (gif.read_bytes() if gif.exists() else None, png.read_bytes() if png.exists() else None) == before
    n, pose = ns["N_FRAMES"], ns["pose"]
    R0, R1 = ns["R_START"], ns["R_END"]
    total = relative_angle_deg(R0, R1)
    assert np.isclose(total, 180.0, atol=1e-6)                     # 面 1 朝下 → 朝上，恰好翻转 180°
    for m in range(3):
        assert np.abs(pose(m, 0) - R0).max() < 1e-9 and np.abs(pose(m, n - 1) - R1).max() < 1e-9
    M = pose(0, n // 2)
    assert abs(np.linalg.det(M) - 1.0) > 0.1 and np.abs(M.T @ M - np.eye(3)).max() > 0.1
    assert np.abs(M - np.diag([1.0, 0.0, 0.0])).max() < 1e-9       # R_START + R_END 恰好抵消成这个奇异矩阵
    steps = [relative_angle_deg(pose(2, i), pose(2, i + 1)) for i in range(n - 1)]
    assert np.ptp(steps) < 1e-6 and np.isclose(sum(steps), total, atol=1e-6)
    E, S = pose(1, n // 2), pose(2, n // 2)
    assert np.abs(E.T @ E - np.eye(3)).max() < 1e-9 and np.abs(E - S).max() > 0.1    # 欧拉角插值刚性但走另一条路
    euler_steps = [relative_angle_deg(pose(1, i), pose(1, i + 1)) for i in range(n - 1)]
    assert sum(euler_steps) > 180.0 + 60.0                         # 多余旋转：路径总长明显超过测地线 180°
    mid_c_axis_angle = np.degrees(np.arccos(np.clip(E[:, 2] @ [0.0, 0.0, 1.0], -1.0, 1.0)))
    assert mid_c_axis_angle > 80.0                                 # 中途 c 轴几乎横躺（垂直于世界 z 轴）
    # 渲染次序：gif 每帧三栏（3n 个晶体），再静态三联 len(STATIC_FRAMES) 行 × 3 栏；静态各行 = gif 对应下标帧
    static = ns["STATIC_FRAMES"]
    assert tuple(static) == (0, n // 2, n - 1)
    assert len(cap.bodies) == 3 * n + 3 * len(static)
    for r, i in enumerate(static):
        for m in range(3):
            assert np.allclose(cap.bodies[3 * n + 3 * r + m].vertices, cap.bodies[3 * i + m].vertices)
    assert all(c is cap.cameras[0] for c in cap.cameras)           # 帧间相机一致


def test_6_1_pose_clouds_match_their_main_axes(monkeypatch):
    """片晶：点云方向均值与主轴箭头夹角 < 2°，天顶角分布与脚本声明的 std 一致（|N(0,σ)| 的折叠正态：均值 σ√(2/π)、
    标准差 σ√(1−2/π)）；柱晶：天顶角均值 ≈ 90°、std 与声明一致、方位角覆盖四个象限，主轴箭头躺在赤道带内；
    两栏各画了网格 + 赤道 + 晶体 + 主轴箭头 + 该栏的点云。"""
    cap, ns = run_figure(FIGURES["6.1"], monkeypatch)
    clouds, axes_, zenith = ns["CLOUDS"], ns["AXES"], ns["zenith_deg"]
    assert cap.spheres.count("graticule") == 2 and cap.spheres.count("render_great_circle") == 2
    assert len(cap.bodies) == 2 and len(cap.arrows) == 2
    arrows = {tuple(np.round(a[2], 9)) for a in cap.arrows}
    assert arrows == {tuple(np.round(unit(axes_["plate"]), 9)), tuple(np.round(unit(axes_["column"]), 9))}
    drawn = [c for c in cap.sphere_calls if c[0] == "render_point_cloud"]
    assert len(drawn) == 2
    assert np.array_equal(drawn[0][1][2], clouds["plate"]) and np.array_equal(drawn[1][1][2], clouds["column"])
    # 片晶
    plate = clouds["plate"]
    assert np.allclose(np.linalg.norm(plate, axis=1), 1.0)
    mean_dir = unit(plate.mean(axis=0))
    assert np.degrees(np.arccos(np.clip(mean_dir @ unit(axes_["plate"]), -1, 1))) < 2.0
    sigma = ns["PLATE_ZENITH_STD_DEG"]
    z = zenith(plate)
    assert abs(z.mean() - sigma * np.sqrt(2 / np.pi)) < 0.15 * sigma
    assert abs(z.std() - sigma * np.sqrt(1 - 2 / np.pi)) < 0.15 * sigma
    # 柱晶
    col = clouds["column"]
    zc = zenith(col)
    assert abs(zc.mean() - 90.0) < 0.3 and abs(zc.std() - ns["COLUMN_ZENITH_STD_DEG"]) < 0.3
    az = np.degrees(np.arctan2(col[:, 1], col[:, 0]))
    assert all(((az >= lo) & (az < lo + 90)).mean() > 0.2 for lo in (-180, -90, 0, 90))   # 方位均匀
    assert abs(zenith(np.asarray(axes_["column"])[None, :])[0] - 90.0) < 1e-9             # 主轴在赤道面内
    assert abs(zenith(np.asarray(axes_["plate"])[None, :])[0]) < 1e-9


# ---- ch7（task-draw-ch7-figs）：逐图语义单测，判据来自 issue「机械核验」列 -------------------------------

def _normal_permutation(M: np.ndarray) -> dict[int, int]:
    """矩阵 M 作用在侧面法向上诱导的置换 ``{原位置上的面号: 现在落在该位置的面号}``（与 symmetry.face_permutation 同一约定）。"""
    from halo_notes.math import reflection_group as rg
    out = {}
    for k in range(3, 9):
        target = int(np.argmin([np.linalg.norm(M @ rg.NORMALS[k] - rg.NORMALS[j]) for j in range(3, 9)])) + 3
        out[target] = k
    return out


def test_7_1_four_mirrors_axes_are_the_three_side_mirrors(monkeypatch):
    """三条反射轴两两夹 60°；每条轴 ⟂ 它标注的一对相对面的法向；轴的翻转置换 == reflection_group 里对应 S_φ 矩阵作用在面上的置换
    （从 CrossSection 反推，不硬编码）；侧视 inset 画了面 1/2 上下、3/6 左右的矩形 + 一条水平的底面镜轴。"""
    from halo_notes.math import reflection_group as rg
    cap, ns = run_figure(FIGURES["7.1"], monkeypatch)
    section = ns["SECTION"]
    mirrors = ns["MIRRORS"]
    assert len(mirrors) == 3 and {xy for xy, _, _ in mirrors} == {"s90", "s30", "s-30"}
    dirs = {xy: axis.direction(section) for xy, _, axis in mirrors}
    for a, b in [("s90", "s30"), ("s30", "s-30"), ("s90", "s-30")]:
        assert abs(abs(dirs[a] @ dirs[b]) - 0.5) < 1e-9           # 夹角 60°（或 120°，同一条线）
    for xy, (fa, fb), axis in mirrors:
        d = dirs[xy]
        assert fb - fa == 3 and (fa, fb) == rg.MIRROR_FACES[xy]
        for k in (fa, fb):
            assert abs(d @ section.normal(section.face(k))) < 1e-9   # 轴 ⟂ 该对面的法向（公共垂线）
        perm = draw.face_permutation(section, draw.flip(section, axis))
        assert perm == _normal_permutation(rg.XY_MATRIX[xy]), xy
        assert perm[fa] == fb and perm[fb] == fa                        # 这面镜子把这对面的法向对调（n ↦ −n）
    # 画出的三条轴方向就是上面的三条（主图），外加 inset 里一条水平轴（底面镜）
    main_ax, inset_ax = cap.axes2d[0], cap.axes2d[1]
    main_dirs = [d for ax, p, d in cap.flip_axes if ax is main_ax and np.allclose(p, section.centroid())]
    assert len(main_dirs) == 3 and all(any(abs(abs(d @ v) - 1) < 1e-9 for v in dirs.values()) for d in main_dirs)
    inset = [d for ax, _, d in cap.flip_axes if ax is inset_ax]
    assert len(inset) == 1 and _same_direction(inset[0], [1, 0])
    rect = [b for b in cap.bodies if {f.number for f in b.faces} == {1, 2, 3, 6}]
    assert len(rect) == 1
    assert _same_direction(rect[0].normal(rect[0].face(1)), [0, 1]) and _same_direction(rect[0].normal(rect[0].face(3)), [1, 0])


def test_7_2_two_adjacent_mirrors_turn_the_ray_by_120(monkeypatch):
    """追迹光路 1-3-4-2：入射 / 出射方向的水平方位差 == ±120°（< 1e-9），弧的轴 = z、张角 = 该转角；两反射面 4、3 法向夹 60°；
    对比线 sketch=True、方向 = 入射水平方向只转 60°、不在 PATHS 里；正俯视（正交、视线沿 z）。"""
    cap, ns = run_figure(FIGURES["7.2"], monkeypatch)
    path, crystal = ns["PATH"], ns["CRYSTAL"]
    assert face_sequence(path) == [1, 3, 4, 2] and list(ns["PATHS"].values()) == [[1, 3, 4, 2]]
    d_in, d_out = unit(path.points[1] - path.points[0]), unit(path.points[-1] - path.points[-2])
    h_in, h_out = unit([d_in[0], d_in[1], 0]), unit([d_out[0], d_out[1], 0])
    rot = ns["ROTATION_DEG"]
    assert abs(abs(rot) - 120.0) < 1e-9
    assert _same_direction(draw.rotation((0, 0, 1), rot) @ h_in, h_out)      # 水平方向确实转了 rot
    assert abs(abs(d_in[2]) - abs(d_out[2])) < 1e-9                          # 首尾面平行：竖直分量只变号
    n3, n4 = crystal.normal(crystal.face(3)), crystal.normal(crystal.face(4))
    assert abs(np.degrees(np.arccos(n3 @ n4)) - 60.0) < 1e-9
    assert len(cap.arcs) == 1
    _, axis, angle, sem = cap.arcs[0]
    assert _same_direction(axis, [0, 0, 1]) and abs(angle - rot) < 1e-9 and sem == "arc_azimuth"
    sketches = [p for p, _ in cap.paths if p.sketch]
    assert len(sketches) == 1 and not sketches[0].events
    d_c = unit(sketches[0].points[-1] - sketches[0].points[0])
    assert _same_direction(draw.rotation((0, 0, 1), np.sign(rot) * 60.0) @ h_in, unit([d_c[0], d_c[1], 0]))
    assert np.allclose(sketches[0].points[0], path.points[-2])               # 从出射点画起
    cam = ns["CAMERA"]
    assert cam.projection == "orthographic" and _same_direction(cam.view_dir, [0, 0, 1])
    assert _same_direction(cam.right, [1, 0, 0]) and _same_direction(cam.cam_up, [0, 1, 0])


def test_7_3_grid_cells_are_the_twelve_elements(monkeypatch):
    """每格 (列符号, 行符号) 合成矩阵 == 权威表里该编号的矩阵（< 1e-12），12 格编号恰为 1–12 各一次；格内截面的面编号置换 ==
    该 xy 操作作用在面上的置换；格下晕名 == 该编号发表类型的晕名（查权威表）；列序 = 正文第 92 行；下行格各画一个翻转标记；
    旋转列画弧（张角 ±120° / 0）、反射列画轴（方向 = 该 S_φ 的不变线）。"""
    from halo_notes.math import reflection_group as rg
    cap, ns = run_figure(FIGURES["7.3"], monkeypatch)
    cells, base = ns["CELLS"], ns["BASE"]
    assert tuple(ns["COLUMNS"]) == ("e", "r+", "r-", "s90", "s30", "s-30") and tuple(ns["ROWS"]) == (1, -1)
    assert [(c["xy"], c["z"]) for c in cells] == [(xy, z) for z in ns["ROWS"] for xy in ns["COLUMNS"]]
    numbers = []
    for c in cells:
        Mz = np.diag([1.0, 1.0, float(c["z"])])
        M = Mz @ rg.XY_MATRIX[c["xy"]]
        e = c["element"]
        assert np.abs(M - rg.MATRICES[e.number]).max() < 1e-12
        assert rg.identify(M).number == e.number
        numbers.append(e.number)
        assert draw.face_permutation(base, c["section"]) == _normal_permutation(rg.XY_MATRIX[c["xy"]]), c["xy"]
        col, plate = rg.HALO_NAMES[rg.PUBLISHED[e.number]]
        assert c["title"].splitlines() == [f"#{e.number}", f"柱晶：{col}", f"片晶：{plate}"]
    assert sorted(numbers) == list(range(1, 13))
    # 正文第 94 行：#11 在 e 列下行，#2 在 S_90 列上行
    assert cells[6]["element"].number == 11 and cells[3]["element"].number == 2
    assert len(cap.bodies) == 12 and len(cap.flip_markers) == 6 and len(cap.arcs2d) == 6 and len(cap.flip_axes) == 6
    axes_by_cell = {id(b_ax): i for i, b_ax in enumerate(cap.axes2d)}   # 第 i 个截面画在第 i 格
    assert len(axes_by_cell) == 12
    for ax, _, s, e_ in cap.arcs2d:
        i = axes_by_cell[id(ax)]
        step = {"e": 0, "r+": 120.0, "r-": -120.0}[cells[i]["xy"]]
        assert abs((e_ - s) - step) < 1e-9
    for ax, p, d in cap.flip_axes:
        i = axes_by_cell[id(ax)]
        xy = cells[i]["xy"]
        phi = {"s90": 90.0, "s30": 30.0, "s-30": -30.0}[xy]
        assert abs(abs(d @ [np.cos(np.radians(phi)), np.sin(np.radians(phi))]) - 1) < 1e-9, xy   # 轴 = S_φ 的不变线
    marker_cells = {axes_by_cell[id(ax)] for ax, _ in cap.flip_markers}
    assert marker_cells == {i for i, c in enumerate(cells) if c["z"] < 0}


def test_7_4_rot90_moves_side_mirror_to_basal_but_is_no_symmetry(monkeypatch):
    """右栏晶体 = R_y(90°) 作用于左栏晶体；R_y(90°)·n_3 = ±e_z（< 1e-12）；转后面法向集合 ≠ 转前；弧的轴 = y、张角 = 90°；
    两栏同一相机实例；变体 b 的平面：法向 ∥ 面 3 法向、中心在晶体质心（左栏竖直、右栏水平）；变体 a 不画平面。"""
    cap, ns = run_figure(FIGURES["7.4"], monkeypatch)
    crystal, turned, R = ns["CRYSTAL"], ns["TURNED"], ns["R"]
    assert np.abs(R - draw.rotation((0, 1, 0), 90.0)).max() < 1e-12
    assert np.allclose(turned.vertices, crystal.vertices @ R.T)
    n3 = crystal.normal(crystal.face(3))
    assert np.linalg.norm(np.abs(R @ n3) - [0, 0, 1]) < 1e-12
    before = {tuple(np.round(crystal.normal(f), 6)) for f in crystal.faces}
    after = {tuple(np.round(turned.normal(f), 6)) for f in turned.faces}
    assert before != after
    # 两个变体各渲染 3 个实体（左晶体、右幽灵、右转后晶体），且右栏实体的顶点 == R·左栏
    assert len(cap.bodies) == 6
    for k in (0, 3):
        assert np.allclose(cap.bodies[k].vertices, crystal.vertices)
        assert np.allclose(cap.bodies[k + 1].vertices, crystal.vertices)          # 幽灵 = 原直立晶体
        assert np.allclose(cap.bodies[k + 2].vertices, crystal.vertices @ R.T)
    assert all(c is cap.cameras[0] for c in cap.cameras[:3]) and all(c is cap.cameras[3] for c in cap.cameras[3:])
    assert len(cap.arcs) == 2
    for _, axis, angle, sem in cap.arcs:
        assert _same_direction(axis, [0, 1, 0]) and np.isclose(angle, 90.0) and sem == "arc_tilt"
    assert len(cap.planes) == 2                                                   # 只有变体 b 画平面：左右各一
    for (_, body, face_number, quad), expect_n in zip(cap.planes, ([1, 0, 0], [0, 0, -1])):
        assert face_number == 3
        qn = np.cross(quad[1] - quad[0], quad[3] - quad[0])
        assert abs(abs(qn @ body.normal(body.face(3))) - np.linalg.norm(qn)) < 1e-9
        assert _same_direction(body.normal(body.face(3)), expect_n)
        assert np.allclose(quad.mean(axis=0), body.centroid())


def _tricker_point(ns_helper, psi_deg: float) -> np.ndarray:
    return ns_helper.TRICKER.tricker_arc(np.radians(psi_deg))


def test_7_5_pose_to_sky_compresses_theta_for_br_but_not_for_s(monkeypatch):
    """三个晶体姿态 = column_attitude(ψ0, θi)（同一 ψ0）；三面板入射方向逐位相等（= −太阳方向）；每条光路由 search_raypath
    在固定入射方向下解出、面序列 == PATHS；上行：三出射方向两两 |Δ| < 1e-9、== −sky_direction(br, R_i, ŝ)、落在特里克尔弧
    上（== tricker_arc(ψ0)）；下行：两两夹角 > 2°、各 == −sky_direction(s, R_i, ŝ)；引线端点 == 数据坐标换算值；
    两行左栏 artist 逐个相同。"""
    from halo_notes.math import reflection_group as rg
    from halo_notes.math.attitude import column_attitude, sky_direction
    cap, ns = run_figure(FIGURES["7.5"], monkeypatch)
    P = sys.modules["_pose_to_sky"]
    rows, psi0, thetas = ns["ROW_DATA"], ns["PSI0"], ns["THETAS"]
    d_in = P.D_IN
    assert _same_direction(d_in, -P.SUN) and np.isclose(P.SUN_ELEVATION_DEG, 10.0)
    outs = {}
    for n, data in rows.items():
        assert list(data.faces) in ns["PATHS"].values()
        for k, (R, crystal, path, sky) in enumerate(zip(data.attitudes, data.crystals, data.paths, data.sky_points)):
            assert np.abs(R - column_attitude(psi0, thetas[k])).max() < 1e-12
            assert np.allclose(crystal.vertices, P.CRYSTAL.vertices @ R.T)
            assert face_sequence(path) == list(data.faces)
            assert _same_direction(path.points[1] - path.points[0], d_in)
            d_out = unit(path.points[-1] - path.points[-2])
            assert np.linalg.norm(-d_out - sky_direction(rg.MATRICES[n], R, P.SUN)) < 1e-9
            assert np.linalg.norm(sky - sky_direction(rg.MATRICES[n], R, P.SUN)) < 1e-12
            outs.setdefault(n, []).append(d_out)
    assert thetas[0] < thetas[1] < thetas[2]
    br, s_ = outs[3], outs[2]
    assert all(np.linalg.norm(a - b) < 1e-9 for a in br for b in br)                   # 上行：压成一点
    assert np.linalg.norm(rows[3].sky_points[0] - _tricker_point(P, psi0)) < 1e-9       # 在特里克尔弧上
    for i in range(3):
        for j in range(i + 1, 3):
            assert np.linalg.norm(s_[i] - s_[j]) > np.radians(2.0)                       # 下行：三个点分开
    # 引线：每行 6 条（左→中 3、中→右 3），三张图共 24 条；端点全是数据坐标换算值
    assert len(cap.connectors) == 24
    anchor = P.CAMERA_3D.project_xy(np.zeros(3))[0]
    left_axes = []
    for c in cap.connectors:
        if c.axesA.get_xlim() == (0.0, 360.0):                                            # 左栏 → 中栏
            left_axes.append(c.axesA)
            k = [i for i, t in enumerate(thetas) if np.allclose(c.xy1, (psi0, t))]
            assert len(k) == 1 and np.allclose(c.xy2, anchor)
        else:                                                                             # 中栏 → 右栏
            ends = [P.CAMERA_3D.project_xy(p.end)[0] for d in rows.values() for p in d.paths]
            assert any(np.allclose(c.xy1, e) for e in ends)
            skies = [P.CAMERAS_SKY[n].project_xy(P.SPHERE.on_surface([p]))[0] for n, d in rows.items() for p in d.sky_points]
            assert any(np.allclose(c.xy2, q) for q in skies)
    # 两行左栏逐 artist 相同（合成图里的两个左栏）
    lefts = list(dict.fromkeys(left_axes))
    assert len(lefts) == 4                                                                # 合成图 2 + 单行图各 1

    def signature(ax):
        return ([l.get_xydata().tolist() + [l.get_color(), l.get_markersize()] for l in ax.lines],
                [(t.get_text(), t.get_position()) for t in ax.texts], ax.get_xlim(), ax.get_ylim())
    assert signature(lefts[0]) == signature(lefts[1]) == signature(lefts[2]) == signature(lefts[3])


def test_7_5_gif_sky_point_holds_still_for_br_and_moves_for_s(monkeypatch):
    """每帧光路可行且面序列 == 声明；br 版：同一 ψ 段内所有帧天空点两两距离 < 1e-9、两段之间 > 阈值、都在特里克尔弧上；
    s 版：同一 ψ 段内天空点沿曲线单调移动（相邻步方向不反转、步长 > 0）；所有帧尺寸相同；θ 区间来自 1° 扫描并写进脚本注释。"""
    from halo_notes.math import reflection_group as rg
    from halo_notes.math.attitude import sky_direction
    cap, ns = run_figure(FIGURES["7.5g"], monkeypatch)
    P = sys.modules["_pose_to_sky"]
    frames, rows = ns["FRAMES"], ns["ROWS"]
    assert set(frames) == {3, 2}
    for n, fr in frames.items():
        segments: dict[float, list] = {}
        for f in fr:
            assert face_sequence(f["path"]) == list(rows[n].faces)
            assert _same_direction(f["path"].points[1] - f["path"].points[0], P.D_IN)
            assert np.linalg.norm(-unit(f["path"].points[-1] - f["path"].points[-2]) - f["sky"]) < 1e-9
            assert np.linalg.norm(f["sky"] - sky_direction(rg.MATRICES[n], f["R"], P.SUN)) < 1e-12
            segments.setdefault(f["psi"], []).append(f)
        assert list(segments) == [psi for psi, _ in rows[n].sweeps]
        for psi, seg in segments.items():
            a, b = dict(rows[n].sweeps)[psi]
            th = [f["theta"] for f in seg]
            assert min(th) == a and max(th) == b and th[0] == a and th[-1] == a       # 来回扫：a → b → a
            assert max(np.diff(th[:th.index(b) + 1])) > 0 and min(np.diff(th[th.index(b):])) < 0
            pts = np.array([f["sky"] for f in seg])
            if n == 3:
                assert np.abs(pts - pts[0]).max() < 1e-9                                  # 纹丝不动
                assert np.linalg.norm(pts[0] - _tricker_point(P, psi)) < 1e-9             # 在弧上
            else:
                forth = pts[:th.index(b) + 1]
                steps = np.diff(forth, axis=0)
                assert np.linalg.norm(steps, axis=1).min() > 1e-6                          # 每步都动
                assert all(steps[i] @ steps[i + 1] > 0 for i in range(len(steps) - 1))    # 沿曲线单调、不折返
        if n == 3:
            p0, p1 = (segments[psi][0]["sky"] for psi, _ in rows[n].sweeps)
            assert np.linalg.norm(p0 - p1) > np.radians(1.0)                              # 换 ψ 才挪
    assert len(cap.gif_frames) == sum(ns["N_FRAMES"].values()) and len(set(cap.gif_frames)) == 1
    src = (ROOT / FIGURES["7.5g"]).read_text(encoding="utf-8") + (ROOT / CH7 / "_pose_to_sky.py").read_text(encoding="utf-8")
    assert "1°" in src and "扫描" in src
