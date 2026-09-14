"""按字长枚举几何 + 光学都可行的光路（ch2「穷举、规约、剪枝搜索一波流」的 python 复活版）。

DFS 按面序列延伸（相邻面不重复，入射面 / 出射面均可为任意面；单面序列 = 外反射，按 ch2 计入）。每个节点持有
:data:`~halo_notes.geometry.feasibility.CorridorMask`（几何走廊 ∧ 入射约束）及每个可行方向上的走廊投影交集
多边形；追加一个面时，末面变成镜面、走廊只多出一个多边形（新幽灵上的新面），所以子节点只需把父节点的交集多边形
再裁一次——**单调性**（走廊只会变窄）保证父掩码为空即可剪掉整棵子树。出射光学约束只在「就在这里出射」的候选上
叠加（:func:`~halo_notes.geometry.feasibility.admissible_directions` 的语义），不参与剪枝。

对称去重：六棱柱用 :func:`halo_notes.math.reflection_group.pbd_orbit`（D6 × 上下互换 = ch2 规约用的对称），
一般多面体传 ``None`` 不去重（锥晶的对称留给后续章节）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

import numpy as np

from .core import Polyhedron, Vec3
from .feasibility import (AdmissibleMask, CorridorMask, LatLonGrid, _clip_by_polygon, _ensure_ccw, _initial_batch,
                          _PolyBatch, _project, admissible_directions, area_eps, entry_ok, exit_ok,
                          incidence_objective_deg, perp_bases)

SymmetryOrbit = Callable[[Sequence[int]], Iterable[Sequence[int]]]


@dataclass(frozen=True)
class RaypathRecord:
    """一条可行光路：面序列、可行方向掩码（网格同序）、可行方向集球面面积、「首尾入（出）射角较大者」的最小值。"""

    faces: tuple[int, ...]
    admissible_mask: AdmissibleMask
    area_sr: float
    min_incidence_deg: float

    @property
    def length(self) -> int:
        return len(self.faces)

    @property
    def label(self) -> str:
        return "-".join(str(f) for f in self.faces)


@dataclass
class EnumerationStats:
    """剪枝统计。``attempted`` = 尝试扩展（父节点 + 一个新面）的次数，``pruned`` = 其中走廊掩码为空、整棵子树被
    剪掉的次数；``prune_rate = pruned / attempted``。``feasible_by_length`` 按字长计几何 + 光学都可行（去重前）的条数，
    ``geometric_by_length`` 计几何可行（走廊掩码非空）的节点数。"""

    attempted: int = 0
    pruned: int = 0
    feasible_by_length: dict[int, int] = field(default_factory=dict)
    geometric_by_length: dict[int, int] = field(default_factory=dict)

    @property
    def prune_rate(self) -> float:
        return self.pruned / self.attempted if self.attempted else 0.0


@dataclass
class _Node:
    """DFS 节点：面序列、当前幽灵晶体、掩码为 True 的方向的平铺下标、这些方向上的走廊投影交集多边形。"""

    faces: tuple[int, ...]
    body: Polyhedron
    index: np.ndarray
    batch: _PolyBatch


def enumerate_raypaths_with_stats(crystal: Polyhedron, max_len: int, grid: LatLonGrid, *,
                                  entry_faces: Sequence[int] | None = None, symmetry_orbit: SymmetryOrbit | None = None,
                                  eps: float | None = None,
                                  refine_levels: int = 0) -> tuple[list[RaypathRecord], EnumerationStats]:
    """枚举长度 ≤ ``max_len`` 的全部可行光路，附剪枝统计。

    - ``entry_faces``：只从这些面入射（默认全部面）。六棱柱在 PBD 去重下只需 ``(1, 3)``；
    - ``symmetry_orbit``：面序列 → 其对称轨道，给定时每个轨道只保留字典序最小者（若该代表自身未被枚举到——
      比如 ``entry_faces`` 没含它的入射面——则保留轨道里已枚举到的最小者）；
    - ``eps``：走廊交集面积阈值，默认 :func:`~halo_notes.geometry.feasibility.area_eps`；
    - ``refine_levels``：emit 前对候选做边界细化的级数（0 = 用粗网格面积与最小入射角，最快）。

    输出按 (长度, 字典序) 排序。
    """
    eps = area_eps(crystal) if eps is None else eps
    stats = EnumerationStats()
    records: list[RaypathRecord] = []
    all_dirs = grid.directions
    u_all, w_all = perp_bases(all_dirs)
    weights = grid.weights
    faces_all = [f.number for f in crystal.faces]
    entries = faces_all if entry_faces is None else [int(f) for f in entry_faces]

    def emit(faces: tuple[int, ...], n_a: Vec3, n_tilde_b: Vec3, index: np.ndarray) -> None:
        d = all_dirs[index]
        ok = exit_ok(n_tilde_b, d)
        if not ok.any():
            return
        mask = np.zeros(grid.size, dtype=bool)
        mask[index[ok]] = True
        if refine_levels > 0:
            res = admissible_directions(crystal, faces, grid, CorridorMask(_full_mask(grid, index)), eps,
                                        refine_levels)
            area, best = res.area_sr, res.min_incidence_deg
        else:
            area = float(weights[index[ok]].sum())
            best = float(incidence_objective_deg(n_a, n_tilde_b, d[ok]).min())
        records.append(RaypathRecord(faces, AdmissibleMask(mask), area, best))
        stats.feasible_by_length[len(faces)] = stats.feasible_by_length.get(len(faces), 0) + 1

    def dfs(node: _Node, n_a: Vec3) -> None:
        if len(node.faces) >= max_len:
            return
        last = node.faces[-1]
        # 末面变镜面（入射面除外：[a] → [a, f] 时 f 仍在原晶体上）；所有子节点共用这一个新幽灵
        ghost = node.body if len(node.faces) == 1 else node.body.mirrored(node.body.face(last))
        u, w = u_all[node.index], w_all[node.index]
        for f in faces_all:
            if f == last:
                continue
            stats.attempted += 1
            face = ghost.face(f)
            poly = _ensure_ccw(_project(ghost.face_vertices(face), u, w))
            batch = _clip_by_polygon(node.batch, poly)
            keep = batch.area() > eps
            if not keep.any():
                stats.pruned += 1
                continue
            child = _Node(node.faces + (f,), ghost, node.index[keep], batch.take(np.flatnonzero(keep)))
            stats.geometric_by_length[len(child.faces)] = stats.geometric_by_length.get(len(child.faces), 0) + 1
            emit(child.faces, n_a, ghost.normal(face), child.index)
            dfs(child, n_a)

    for a in entries:
        face = crystal.face(a)
        n_a = crystal.normal(face)
        # 单面 = 外反射：没有走廊也没有临界角，可行集恒为半球
        hemi = np.flatnonzero(-(all_dirs @ n_a) > 0)
        mask = np.zeros(grid.size, dtype=bool)
        mask[hemi] = True
        records.append(RaypathRecord((a,), AdmissibleMask(mask), float(weights[hemi].sum()), 0.0))
        stats.feasible_by_length[1] = stats.feasible_by_length.get(1, 0) + 1
        if max_len < 2:
            continue
        root_index = np.flatnonzero(entry_ok(n_a, all_dirs))
        root_poly = _ensure_ccw(_project(crystal.face_vertices(face), u_all[root_index], w_all[root_index]))
        dfs(_Node((a,), crystal, root_index, _initial_batch(root_poly)), n_a)

    if symmetry_orbit is not None:
        records = _dedup(records, symmetry_orbit)
    records.sort(key=lambda r: (r.length, r.faces))
    return records, stats


def _full_mask(grid: LatLonGrid, index: np.ndarray) -> np.ndarray:
    mask = np.zeros(grid.size, dtype=bool)
    mask[index] = True
    return mask


def _dedup(records: list[RaypathRecord], symmetry_orbit: SymmetryOrbit) -> list[RaypathRecord]:
    """按轨道分组，每组保留面序列字典序最小的那条记录。"""
    by_orbit: dict[frozenset, RaypathRecord] = {}
    for r in records:
        key = frozenset(tuple(int(f) for f in s) for s in symmetry_orbit(r.faces))
        cur = by_orbit.get(key)
        if cur is None or r.faces < cur.faces:
            by_orbit[key] = r
    return list(by_orbit.values())


def enumerate_raypaths(crystal: Polyhedron, max_len: int, grid: LatLonGrid, *,
                       entry_faces: Sequence[int] | None = None, symmetry_orbit: SymmetryOrbit | None = None,
                       eps: float | None = None, refine_levels: int = 0) -> list[RaypathRecord]:
    """:func:`enumerate_raypaths_with_stats` 去掉统计的薄封装。"""
    return enumerate_raypaths_with_stats(crystal, max_len, grid, entry_faces=entry_faces, symmetry_orbit=symmetry_orbit,
                                         eps=eps, refine_levels=refine_levels)[0]


__all__ = ["EnumerationStats", "RaypathRecord", "SymmetryOrbit", "enumerate_raypaths", "enumerate_raypaths_with_stats"]
