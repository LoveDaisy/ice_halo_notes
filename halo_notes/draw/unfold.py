"""光路展开：每次内反射把晶体关于反射面镜像成一个"幽灵晶体"，反射折线随之拉直。

- :func:`unfold`：按光路里的内反射事件级联镜像，返回幽灵晶体序列
  （第 k 个幽灵是对第 k-1 个幽灵——而非原晶体——做镜像，面编号跟着晶体走）
- :func:`straighten`：把同一条光路的内部折线收缩成一条直线段，直线段的
  出射端落在最后一个幽灵晶体的出射面上，可直接交给 ``draw_raypath`` 渲染
- :func:`unfolded_tail`：只取拉直光路从入射点起的部分（真实光路已画了入射段时用）
- :func:`corridor_faces`：光走廊——光路依次穿过的面在 [晶体, 幽灵 1, 幽灵 2, …] 上的
  归属，供高亮
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .geometry import Polyhedron, unit
from .raypath import EventKind, RayEvent, RayPath, SegmentKind


def _reflection_faces(events: Sequence[RayEvent]) -> list[int]:
    """按发生顺序取出内反射事件的面号。"""
    return [ev.face_number for ev in events if ev.kind is EventKind.REFLECT_INTERNAL]


def unfold(crystal: Polyhedron, raypath: RayPath) -> list[Polyhedron]:
    """返回光路 ``raypath`` 在 ``crystal`` 内每次内反射对应的幽灵晶体（级联镜像）。

    无内反射时返回空列表。
    """
    ghosts: list[Polyhedron] = []
    current = crystal
    for number in _reflection_faces(raypath.events):
        current = current.mirrored(current.face(number))
        ghosts.append(current)
    return ghosts


def _endpoint_events(events: Sequence[RayEvent]) -> tuple[RayEvent, RayEvent]:
    kinds = {ev.kind: ev for ev in events}
    try:
        return kinds[EventKind.REFRACT_IN], kinds[EventKind.REFRACT_OUT]
    except KeyError:
        raise ValueError("straighten() needs a path that enters and leaves the crystal") from None


def straighten(raypath: RayPath) -> RayPath:
    """把折射进入到折射出射之间的内部折线拉成一条直线（展开空间里的光路）。

    直线从入射点出发、沿第一段内部方向、长度等于各内部段长度之和——这正是
    展开后光线在幽灵晶体串里走过的路程。出射段长度不变、方向经级联镜像搬到
    展开空间（等于直线在最后一个幽灵的出射面上折射的方向）。事件只保留
    ``REFRACT_IN`` / ``REFRACT_OUT``（中间反射点已不是折线端点）。
    """
    ev_in, ev_out = _endpoint_events(raypath.events)
    pts = raypath.points
    i_in, i_out = ev_in.point_index, ev_out.point_index
    entry = pts[i_in]
    dirs = [unit(pts[k + 1] - pts[k]) for k in range(i_in, i_out)]  # 各内部段方向
    d1 = dirs[0]
    total = sum(float(np.linalg.norm(pts[k + 1] - pts[k])) for k in range(i_in, i_out))
    straight_exit = entry + d1 * total
    # 出射段方向也要搬进展开空间：依次撤销每次反射（镜像面法向由方向突变 d_k - d_{k-1} 给出，
    # 与几何法向只差符号，镜像不区分符号），最内层的反射先撤销
    exit_dir = pts[-1] - pts[i_out]
    for k in range(len(dirs) - 1, 0, -1):
        n = unit(dirs[k] - dirs[k - 1])
        exit_dir = exit_dir - 2.0 * (n @ exit_dir) * n
    points = np.array([pts[0], entry, straight_exit, straight_exit + exit_dir])
    kinds = (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.EXIT)
    events = (RayEvent(1, ev_in.face_number, EventKind.REFRACT_IN),
              RayEvent(2, ev_out.face_number, EventKind.REFRACT_OUT))
    return RayPath(points, kinds, events)


def unfolded_tail(straight: RayPath) -> RayPath:
    """去掉 :func:`straighten` 结果的入射段：从入射点起的直线 + 出射段（事件下标同步前移）。"""
    events = tuple(RayEvent(ev.point_index - 1, ev.face_number, ev.kind) for ev in straight.events)
    return RayPath(straight.points[1:], straight.kinds[1:], events)


def corridor_faces(raypath: RayPath) -> list[tuple[int, int]]:
    """光走廊的各面：``(k, face_number)``，``k=0`` 指真实晶体，``k≥1`` 指 ``unfold()`` 的
    第 k 个幽灵。入射面在真实晶体上；第 k 次反射面归到幽灵 k（它与晶体 k-1 的同编号面
    共面，光线正是穿过这个面进入幽灵 k）；出射面在最后一个幽灵上。
    """
    out: list[tuple[int, int]] = []
    k = 0
    for ev in raypath.events:
        if ev.kind is EventKind.REFRACT_IN:
            out.append((0, ev.face_number))
        elif ev.kind is EventKind.REFLECT_INTERNAL:
            k += 1
            out.append((k, ev.face_number))
        elif ev.kind is EventKind.REFRACT_OUT:
            out.append((k, ev.face_number))
    return out
