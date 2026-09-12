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


def run_figure(script: str, monkeypatch) -> tuple[Capture, dict]:
    cap = Capture()
    install_spies(cap, monkeypatch)
    path = ROOT / script
    monkeypatch.syspath_prepend(str(path.parent))
    for helper in ("_light_corridor_rp132", "_tricker_arc"):   # 章内共享 helper 每图重新导入，拿到本次的 spy
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
        try:
            verify_path(path, lambda ev: locate_body(cap.bodies, path, ev), tol=1e-9, min_margin=1e-6)
        except (ValueError, AssertionError) as e:
            problems.append(f"{tag}: {e}")
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
