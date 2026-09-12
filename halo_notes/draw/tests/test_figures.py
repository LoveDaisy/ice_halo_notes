"""逐图语义单测：跑每个 fig 脚本，抓它实际画出的每条 ``RayPath``，白盒复核"画的是不是声明的那条光路"。

每条画出的光路必须二选一：
- 面序列 ∈ 该图声明的 ``PATHS``，且每个事件点落在**本图已渲染的某个多面体**的该编号面内部、
  方向变化满足对应定律（Snell / 反射 / 穿越不变；:func:`raypath.verify_path`）；
  事件在折线端点上（如 ``unfolded_tail`` 去掉入射段后的展开直线）时，必须接续本图另一条
  完整光路在同一点、同一面的同一事件（同一条光线的两种画法）
- 或显式 ``sketch=True``（手画示意线）

事件所属多面体按几何定位（事件点在哪个已渲染多面体的该编号面上），不借用 ``draw_raypath``
调用点传入的 crystal / 遮挡体参数——旧审计脚本正是用错这个参数得出 2.6 "面 3 处 111°" 的假阳性。
渲染输出被 monkeypatch 掉（``Figure.savefig`` 空操作），不会覆盖 ``img/`` 里的正式图。
"""

from __future__ import annotations

import contextlib
import io
import runpy
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import halo_notes.draw as draw  # noqa: E402
import halo_notes.draw.scene as scene  # noqa: E402
from halo_notes.draw.geometry import Polyhedron, unit  # noqa: E402
from halo_notes.draw.raypath import EventKind, RayEvent, RayPath, face_sequence, verify_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CH2, CH3, CH4 = "02-raypath-enumeration/code", "03-parallel-raypaths/code", "04-render-equation/code"

# 图 → (脚本, 期望面序列)。第一版写死在这里出红灯基线；Step 5 逐图补 PATHS 后改为从脚本读取
FIGURES = {
    "2.2": (f"{CH2}/fig_tricker_arc_raypath.py", {"3-1-5-7-4": [3, 1, 5, 7, 4], "1-2-3-5-1": [1, 2, 3, 5, 1]}),
    "2.3": (f"{CH2}/fig_geo_validation.py", {"1-3-2": [1, 3, 2]}),
    "2.4": (f"{CH2}/fig_expand_rp132.py", {"1-3-2": [1, 3, 2]}),
    "2.5": (f"{CH2}/fig_light_corridor_rp132_00.py", {"1-3-2": [1, 3, 2]}),
    "2.6": (f"{CH2}/fig_light_corridor_rp31574.py", {"3-1-5-7-4": [3, 1, 5, 7, 4]}),
    "2.7": (f"{CH2}/fig_light_corridor_rp132_01.py", {"1-3-2": [1, 3, 2]}),
    "2.8": (f"{CH2}/fig_light_corridor_rp132_02_note.py", {"1-3-2": [1, 3, 2], "refract-in": [1]}),
    "2.9": (f"{CH2}/fig_light_corridor_rp132_03.py", {"1-3-2": [1, 3, 2]}),
    "3.2": (f"{CH3}/fig_tricker_arc_raypath_expand.py", {"3-1-5-7-4": [3, 1, 5, 7, 4], "1-2-3-5-1": [1, 2, 3, 5, 1]}),
    "4.1": (f"{CH4}/fig_ch4_raypath_all.py", {"1": [1], "4-1": [4, 1], "3-1-5": [3, 1, 5]}),
}


class Capture:
    """spy：记录本图渲染的所有多面体与画出的所有光路。"""

    def __init__(self):
        self.bodies: list[Polyhedron] = []
        self.paths: list[tuple[RayPath, str | None]] = []


def run_figure(script: str, monkeypatch) -> tuple[Capture, dict]:
    cap = Capture()
    real_render, real_draw = scene.render_crystal, scene.draw_raypath

    def spy_render(ax, crystal, raypaths=None, **kw):
        cap.bodies.append(crystal)
        return real_render(ax, crystal, raypaths, **kw)

    def spy_draw(ax, path, crystal=None, **kw):
        cap.paths.append((path, kw.get("semantic")))
        return real_draw(ax, path, crystal, **kw)

    for mod in (scene, draw):
        monkeypatch.setattr(mod, "render_crystal", spy_render)
        monkeypatch.setattr(mod, "draw_raypath", spy_draw)
    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", lambda *a, **k: None)
    path = ROOT / script
    monkeypatch.syspath_prepend(str(path.parent))
    sys.modules.pop("_light_corridor_rp132", None)  # 共享 helper 每图重新导入，拿到本次的 spy
    with contextlib.redirect_stdout(io.StringIO()):
        ns = runpy.run_path(str(path), run_name="__main__")
    plt.close("all")
    return cap, ns


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
    script, expected = FIGURES[fig]
    cap, _ = run_figure(script, monkeypatch)
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
