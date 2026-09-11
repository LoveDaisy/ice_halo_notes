"""光路展开：每次内反射把晶体关于反射面镜像成一个"幽灵晶体"，反射折线随之拉直。

- :func:`unfold`：按光路里的内反射事件级联镜像，返回幽灵晶体序列
  （第 k 个幽灵是对第 k-1 个幽灵——而非原晶体——做镜像，面编号跟着晶体走）
- :func:`straighten`：把同一条光路的内部折线收缩成一条直线段，直线段的
  出射端落在最后一个幽灵晶体的出射面上，可直接交给 ``draw_raypath`` 渲染
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
    展开后光线在幽灵晶体串里走过的路程。出射段保持原来的长度与相对方向平移
    到直线终点。事件只保留 ``REFRACT_IN`` / ``REFRACT_OUT``（中间反射点已
    不是折线端点）。
    """
    ev_in, ev_out = _endpoint_events(raypath.events)
    pts = raypath.points
    i_in, i_out = ev_in.point_index, ev_out.point_index
    entry = pts[i_in]
    d1 = unit(pts[i_in + 1] - pts[i_in])
    total = sum(float(np.linalg.norm(pts[k + 1] - pts[k])) for k in range(i_in, i_out))
    straight_exit = entry + d1 * total
    points = np.array([pts[0], entry, straight_exit, straight_exit + (pts[-1] - pts[i_out])])
    kinds = (SegmentKind.INCIDENT, SegmentKind.INTERNAL, SegmentKind.EXIT)
    events = (RayEvent(1, ev_in.face_number, EventKind.REFRACT_IN),
              RayEvent(2, ev_out.face_number, EventKind.REFRACT_OUT))
    return RayPath(points, kinds, events)
