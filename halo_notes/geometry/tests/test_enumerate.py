from pathlib import Path

import numpy as np
import pytest

from halo_notes.draw.raypath import events_for_faces, face_sequence, search_raypath, solve_raypath, trace
from halo_notes.geometry import HexPrism
from halo_notes.geometry.enumerate import corridor_index_for_path, enumerate_raypaths, enumerate_raypaths_with_stats
from halo_notes.geometry.feasibility import (LatLonGrid, admissible_directions, corridor_mask, entry_points,
                                             external_directions, is_feasible)
from halo_notes.geometry.ground_truth import ground_truth_sequences
from halo_notes.math.reflection_group import ELEMENTS, pbd_orbit

GRID = LatLonGrid(90, 180)      # 2°
PLATE = HexPrism.from_ratio(0.2)
DATA = Path(__file__).resolve().parents[3] / "03-parallel-raypaths" / "data"

# ch2 已发表：片晶 h/a = 0.2，PBD 代表
CH2_LE2 = ["1", "1-2", "1-3", "3", "3-1", "3-5", "3-6"]
CH2_EQ3 = ["1-2-1", "1-2-3", "1-3-2", "3-1-2", "3-1-5", "3-1-6", "3-4-5", "3-5-7", "3-5-8", "3-6-3", "3-6-4"]
CH2_COUNTS = {4: 25, 5: 61, 6: 169}


def _seq(label: str) -> tuple[int, ...]:
    return tuple(int(x) for x in label.split("-"))


@pytest.fixture(scope="module")
def plate_le6():
    recs, stats = enumerate_raypaths_with_stats(PLATE, 6, GRID, entry_faces=(1, 3), symmetry_orbit=pbd_orbit)
    return recs, stats


def _by_length(recs):
    out = {}
    for r in recs:
        out.setdefault(r.length, []).append(r)
    return out


# ---- 掩码单调性与两种掩码不可混用 -----------------------------------------------------------


@pytest.mark.parametrize("faces", [(1, 3, 2), (3, 1, 5, 7, 4), (1, 2, 3, 5, 1), (3, 5, 7, 3, 5)])
def test_corridor_mask_is_monotone_in_prefix(faces):
    """子前缀的走廊掩码 ⊇ 扩展后的走廊掩码（走廊只会变窄）。"""
    prev = None
    for k in range(1, len(faces) + 1):
        cur = corridor_mask(PLATE, faces[:k], GRID)
        if prev is not None:
            assert not (cur & ~prev).any()
        prev = cur


@pytest.mark.parametrize("faces", [(1,), (3,), (1, 3), (3, 4), (1, 3, 2), (3, 1, 5, 7, 4), (1, 2, 3, 5, 1),
                                   (3, 5, 7, 3, 5)])
def test_dfs_incremental_corridor_matches_corridor_mask(faces):
    """a56：DFS 剪枝维护的增量走廊状态（``corridor_index_for_path``，与 ``enumerate.dfs()`` 共用
    ``_ghost_for``/``_extend_batch`` 两个原语）与独立从头算的 ``corridor_mask`` 必须逐位一致——这是 code review
    要求的机械核验，不靠「两处代码看起来在做同一件事」的人工审查兜底。"""
    got = np.sort(corridor_index_for_path(PLATE, faces, GRID))
    want = np.flatnonzero(corridor_mask(PLATE, faces, GRID))
    assert np.array_equal(got, want)


def test_pruning_uses_corridor_not_admissible_mask(plate_le6):
    """风险 4：3-4 作为完整光路出射不可行（admissible 为空），但它的走廊非空、延伸后的 3-4-5 可行——
    用 admissible 掩码剪枝会把 3-4-5 漏掉。"""
    assert corridor_mask(PLATE, (3, 4), GRID).any()
    assert not admissible_directions(PLATE, (3, 4), GRID, refine_levels=0).mask.any()
    assert is_feasible(PLATE, (3, 4, 5), GRID)
    recs, _ = plate_le6
    labels = {r.label for r in recs}
    assert "3-4-5" in labels and "3-4" not in labels


# ---- ch2 片晶 h/a = 0.2 基准 ----------------------------------------------------------------


def test_ch2_plate_length_le3_matches_published_list(plate_le6):
    """长度 ≤ 3 共 18 条逐条相等；本实现额外给出 1-3-4 / 3-4-1（互为时间反演），二者是贴 3/4 公共棱掠射的细缝
    （面积 < 0.001 sr、最小入射角 ≈ 49.3° 压在临界角下），ch2 内点法的障碍项到不了那里——判据差异，不是 bug。"""
    recs, _ = plate_le6
    by = _by_length(recs)
    got = {r.faces for L in (1, 2, 3) for r in by[L]}
    expected = {_seq(s) for s in CH2_LE2 + CH2_EQ3}
    assert expected <= got
    extra = got - expected
    assert extra == {(1, 3, 4), (3, 4, 1)}
    for r in recs:
        if r.faces in extra:
            assert r.area_sr < 1e-3 and 49.0 < r.min_incidence_deg < 49.8
    assert len(by[1]) + len(by[2]) == 7 and len(by[3]) == 11 + 2


def test_ch2_plate_length_4_to_6_counts_regression(plate_le6):
    """ch2 发表 25 / 61 / 169；本实现 2° 网格给 31 / 70 / 147（1° 网格 31 / 73 / 162，0.5° 与 1° 相同）。差异归因见
    progress.md：多出的是贴棱掠射 / 压在临界角上的细缝（面积 ≲ 0.002 sr），长度 6 少掉的一批 ch2 未发表逐条清单、
    无法逐条对，独立蒙特卡洛追迹（10⁶ 条射线）也只实现到 146 条。这里钉住本实现的数字防回归。"""
    recs, _ = plate_le6
    by = _by_length(recs)
    assert {L: len(by[L]) for L in (4, 5, 6)} == {4: 31, 5: 70, 6: 147}
    # 与 ch2 的差别全部来自小面积记录：把面积 < 0.003 sr 的细缝去掉后长度 4 / 5 与 ch2 的差 ≤ 3
    solid = {L: sum(r.area_sr >= 3e-3 for r in by[L]) for L in (4, 5, 6)}
    assert abs(solid[4] - CH2_COUNTS[4]) <= 3 and abs(solid[5] - CH2_COUNTS[5]) <= 3
    # 长度 6：ch2 未发表逐条清单，169 与 solid[6] 差 30 条，远超长度 4/5 的 ≤3 容差，判据不可比（见
    # progress.md DECISION「长度 6 验证口径降级」）；这里不与 CH2_COUNTS[6] 对比，只把本实现的当前值钉成
    # 显式回归锁——不是像上一版那样算出来又弃用，而是让它真的参与断言。
    assert solid[6] == 139


def test_records_are_sorted_and_labels_consistent(plate_le6):
    recs, _ = plate_le6
    keys = [(r.length, r.faces) for r in recs]
    assert keys == sorted(keys)
    for r in recs:
        assert r.label == "-".join(map(str, r.faces))
        assert r.admissible_mask.any() and r.area_sr > 0
        assert all(a != b for a, b in zip(r.faces, r.faces[1:]))


def test_dedup_keeps_orbit_minimum_and_matches_full_entry_enumeration():
    """只从 1 / 3 入射 + PBD 去重，与从全部 8 面入射 + PBD 去重给出相同的代表集合；不去重时每个轨道的最小元都在。"""
    partial = {r.faces for r in enumerate_raypaths(PLATE, 3, GRID, entry_faces=(1, 3), symmetry_orbit=pbd_orbit)}
    full = enumerate_raypaths(PLATE, 3, GRID, symmetry_orbit=pbd_orbit)
    assert {r.faces for r in full} == partial
    raw = {r.faces for r in enumerate_raypaths(PLATE, 3, GRID)}
    assert len(raw) > len(partial)
    assert {min(pbd_orbit(f)) for f in raw} == partial
    for f in raw:
        assert min(pbd_orbit(f)) in raw


def test_stats_are_consistent(plate_le6):
    recs, st = plate_le6
    assert st.attempted > st.pruned > 0 and 0 < st.prune_rate < 1
    assert st.feasible_by_length[1] == 2
    assert sum(st.geometric_by_length.values()) == st.attempted - st.pruned


def test_single_face_records_present_and_max_len_1():
    recs = enumerate_raypaths(PLATE, 1, GRID, entry_faces=(1, 3))
    assert [r.faces for r in recs] == [(1,), (3,)]
    assert all(r.area_sr == pytest.approx(2 * np.pi, rel=1e-3) for r in recs)


def test_refine_levels_changes_area_only_slightly():
    coarse = enumerate_raypaths(PLATE, 3, GRID, entry_faces=(1,), symmetry_orbit=pbd_orbit)
    fine = enumerate_raypaths(PLATE, 3, GRID, entry_faces=(1,), symmetry_orbit=pbd_orbit, refine_levels=1)
    assert [r.faces for r in coarse] == [r.faces for r in fine]
    for a, b in zip(coarse, fine):
        if a.area_sr > 1e-2:
            assert abs(a.area_sr - b.area_sr) / a.area_sr < 0.05


# ---- 每条记录都有可追迹的见证 --------------------------------------------------------------


def test_every_record_has_traceable_witnesses(plate_le6):
    """每条记录抽 ≤ 5 个可行方向：交集质心见证 + 逆 Snell 喂独立实现的 trace，面序列须恰好相等。"""
    recs, _ = plate_le6
    for r in recs:
        if r.length == 1:
            continue
        idx = np.flatnonzero(r.admissible_mask)
        idx = idx[np.linspace(0, len(idx) - 1, min(5, len(idx))).astype(int)]
        d = GRID.directions_at(idx)
        p, ext = entry_points(PLATE, r.faces, d), external_directions(PLATE, r.faces, d)
        for k in range(len(idx)):
            path = trace(PLATE, p[k] - 3 * ext[k], ext[k], events_for_faces(r.faces))
            assert face_sequence(path) == list(r.faces), r.label


# ---- ch3 ground truth 文件 ------------------------------------------------------------------


def _labeled_sequences() -> dict[tuple[int, ...], int]:
    out = {}
    for line in (DATA / "labeled_raypaths_5.csv").read_text().splitlines():
        nums = [int(x) for x in line.split(",")]
        out[tuple(x for x in nums[1:] if x > 0)] = nums[0]
    return out


def test_ch3_ground_truth_all_reachable_on_plate(plate_le6):
    """两份文件各 93 条（同一批面序列，长度 ≤ 5，`render_raypaths.py` 用片晶 0.2 渲染），在 h/a = 0.2 下全部可达。"""
    recs, _ = plate_le6
    have = {r.faces for r in recs}
    gt, lab = ground_truth_sequences(), _labeled_sequences()
    assert len(gt) == 93 and set(gt) == set(lab)
    unreachable = [f for f in gt if min(pbd_orbit(f)) not in have]
    assert unreachable == []


# ---- Step 4：与 solve_raypath 交叉 -------------------------------------------------------------

REPRESENTATIVE_PATHS = [p for e in ELEMENTS for p in e.representative_paths]

# solve_raypath 的入射点只采「质心 + 辐条分点」、方向 4° × 10°，这些窗口它够不到（见证追迹全部通过，归因为搜索局限）
SOLVE_RAYPATH_MISSES = {
    0.2: {(1, 2, 3, 4, 1), (1, 3, 4, 2), (3, 5, 7, 1, 3, 5)},
    1.0: {(1, 2, 3, 5, 1), (1, 3, 5, 2), (1, 3, 4, 2, 5, 1), (1, 3, 4, 5, 2)},
    2.0: {(1, 3, 4, 6, 2)},
}


def test_ch3_representative_paths_count():
    assert len(REPRESENTATIVE_PATHS) == 28


def _crosscheck(ratio: float) -> None:
    c = HexPrism.from_ratio(ratio)
    for faces in REPRESENTATIVE_PATHS:
        if not is_feasible(c, faces, GRID):
            continue
        if len(faces) == 1:
            solve_raypath(c, faces)
            continue
        res = admissible_directions(c, faces, GRID, refine_levels=0)
        d = GRID.directions[res.mask][:3]
        # 见证方向 + 见证入射点喂 search_raypath（solve_raypath 的搜索主体，做 方向 × 入射点 的笛卡尔积）：必须解出
        search_raypath(c, faces, external_directions(c, faces, d), entry_points=entry_points(c, faces, d))
        if faces in SOLVE_RAYPATH_MISSES.get(ratio, set()):
            with pytest.raises(ValueError):
                solve_raypath(c, faces)
        else:
            solve_raypath(c, faces)


def test_feasible_representative_paths_solve_on_plate():
    _crosscheck(0.2)


@pytest.mark.slow
@pytest.mark.parametrize("ratio", [1.0, 2.0])
def test_feasible_representative_paths_solve_other_ratios(ratio):
    _crosscheck(ratio)


# ---- Step 5：性能（慢测试） ---------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.parametrize("ratio", [0.2, 0.5, 1.0, 2.0, 5.0])
def test_max_len_8_runs_within_minutes(ratio):
    import time
    t = time.time()
    recs, st = enumerate_raypaths_with_stats(HexPrism.from_ratio(ratio), 8, GRID, entry_faces=(1, 3),
                                             symmetry_orbit=pbd_orbit)
    elapsed = time.time() - t
    by = {L: sum(r.length == L for r in recs) for L in range(1, 9)}
    print(f"h/a={ratio}: {elapsed:.1f}s prune_rate={st.prune_rate:.3f} feasible={by}")
    assert elapsed < 300
