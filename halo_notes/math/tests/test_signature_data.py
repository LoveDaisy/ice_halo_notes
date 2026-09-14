"""对 ``08-wedge-times-fold/data/`` 里由 ``enumerate_signatures.py`` / ``check_ground_truth_signature.py`` 产出的数据文件做断言：
不在 pytest 里重跑五档 × max_len=8 的全量枚举（那是脚本的事，~85 s），只核验产出文件的结构、类归属可复算、可达性声明有独立
的追迹见证（a01：不信枚举器自报，用 ``draw.raypath.trace`` 这条不共享失效模式的链路取证），以及 ch3 ground truth 的分组一致性。"""

import csv
import re
from pathlib import Path

import numpy as np
import pytest

from halo_notes.draw.raypath import events_for_faces, face_sequence, trace
from halo_notes.geometry import HexPrism, fold_matrix
from halo_notes.geometry.feasibility import LatLonGrid, admissible_directions, entry_points, external_directions
from halo_notes.geometry.ground_truth import ground_truth_groups
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import phi_batch, phi_class, phi_class_table

DATA = Path(__file__).resolve().parents[3] / "08-wedge-times-fold" / "data"
RATIOS = (0.2, 0.5, 1.0, 2.0, 5.0)
GRID = LatLonGrid(90, 180)
PLATE = HexPrism.from_ratio(0.2)
TABLE = {r.id: r for r in phi_class_table(PLATE)}
BY_CLASS = {r.phi_class: r for r in TABLE.values()}


def _csv(ratio: float) -> list[dict]:
    with (DATA / f"signature_table_{ratio:g}.csv").open() as fp:
        return list(csv.DictReader(fp))


def _seq(label: str) -> tuple[int, ...]:
    return tuple(int(x) for x in label.split("-"))


# ---- signature_table.md / csv 的结构 --------------------------------------------------------------


def test_md_has_34_class_rows_and_summary():
    text = (DATA / "signature_table.md").read_text()
    main = text.split("## 主表")[1].split("## 光路条数")[0]
    ids = re.findall(r"^\| (A\d+-\d\d) \|", main, flags=re.M)
    assert ids == [r.id for r in TABLE.values() if r.transmittable]
    assert len(ids) == 34
    assert "| 可达 Φ 类数 | 28 | 34 | 34 | 34 | 34 | 34 | 34 |" in text


@pytest.mark.parametrize("ratio", RATIOS)
def test_csv_rows_reference_table_and_signatures(ratio):
    rows = _csv(ratio)
    assert len(rows) == (36 if ratio == 0.2 else 42)
    seen = set()
    for row in rows:
        r = TABLE[row["phi_class_id"]]
        assert float(row["wedge_deg"]) == r.wedge_deg and row["family"] == r.family
        sig = (int(row["sig_fold"]), int(row["sig_entry"]), int(row["sig_exit"]))
        assert any((rg.identify(np.array(k).reshape(3, 3)).number, a, b) == sig for k, a, b in r.signatures)
        assert sig not in seen
        seen.add(sig)
        # 最短代表复算后落在声明的类里
        faces = _seq(row["shortest_path"])
        crystal = HexPrism.from_ratio(ratio)
        assert BY_CLASS[phi_class(crystal, fold_matrix(crystal, faces), faces[0], faces[-1])].id == row["phi_class_id"]


def test_known_paths_in_plate_csv():
    shortest: dict[str, str] = {}
    for row in _csv(0.2):                      # 0° 类有多条 signature 行，取 (长度, 字典序) 最小者
        cur = shortest.get(row["phi_class_id"])
        if cur is None or (len(_seq(row["shortest_path"])), _seq(row["shortest_path"])) < (len(_seq(cur)), _seq(cur)):
            shortest[row["phi_class_id"]] = row["shortest_path"]
    assert shortest["A60-12"] == "3-5" and shortest["A60-11"] == "3-1-5" and shortest["A90-15"] == "1-3"
    assert shortest["A0-06"] == "1-2" and shortest["A90-16"] == "3-1"


# ---- 可达性声明的独立见证：每个 csv 行的最短代表都能被 trace 追出同一面序列 ---------------------------


def _witness(ratio: float) -> None:
    crystal = HexPrism.from_ratio(ratio)
    for row in _csv(ratio):
        faces = _seq(row["shortest_path"])
        res = admissible_directions(crystal, faces, GRID, refine_levels=0)
        idx = np.flatnonzero(res.mask)
        assert len(idx) > 0, (ratio, row["shortest_path"])
        idx = idx[np.linspace(0, len(idx) - 1, min(3, len(idx))).astype(int)]
        d = GRID.directions_at(idx)
        p, ext = entry_points(crystal, faces, d), external_directions(crystal, faces, d)
        for k in range(len(idx)):
            path = trace(crystal, p[k] - 3 * ext[k], ext[k], events_for_faces(faces))
            assert face_sequence(path) == list(faces), (ratio, row["shortest_path"])


@pytest.mark.parametrize("ratio", [0.2, 0.5])
def test_csv_shortest_paths_have_traceable_witnesses(ratio):
    _witness(ratio)


@pytest.mark.slow
@pytest.mark.parametrize("ratio", [1.0, 2.0, 5.0])
def test_csv_shortest_paths_have_traceable_witnesses_other_ratios(ratio):
    _witness(ratio)


# ---- ch3 ground truth 分组一致性 -----------------------------------------------------------------

# 两个不一致的组：ch3 按晕名（片晶旋转后的落点）归组，Φ 类分得更细；这里把脚本 check_ground_truth_signature.py 的结论钉成回归锁
EXPECTED_SPLIT = {
    "映幻日环": {"A0-01": 6, "A60-01": 2, "A60-02": 2},
    "幻日环": {"A0-02": 20, "R": 1, "A60-04": 5, "A60-05": 5, "A60-06": 2, "A60-12": 2},
}
GROUP_TO_PUBLISHED = {"映幻日环": 1, "幻日环": 2, "映120幻日": 3, "120幻日": 4, "映日": 5, "原路前进": 6}


def _classify(faces: tuple[int, ...]) -> str:
    if len(faces) == 1:
        return "R"
    return BY_CLASS[phi_class(PLATE, fold_matrix(PLATE, faces), faces[0], faces[-1])].id


def test_ground_truth_groups_map_to_single_phi_class_except_known_splits():
    groups = ground_truth_groups()
    assert sum(len(v) for v in groups.values()) == 93 and len(groups) == 16
    for name, members in groups.items():
        counts: dict[str, int] = {}
        for row in members:
            cid = _classify(row.faces)
            counts[cid] = counts.get(cid, 0) + 1
        if name in EXPECTED_SPLIT:
            assert counts == EXPECTED_SPLIT[name], name
        else:
            assert len(set(counts) - {"R"}) == 1, (name, counts)


def test_ground_truth_parallel_groups_match_published_classes():
    """0° 组的 Φ 类折叠 = ch7 该发表类型的元素集合；单面外反射的镜子编号也落在本组折叠类里。"""
    groups = ground_truth_groups()
    for name, t in GROUP_TO_PUBLISHED.items():
        ids = {cid for cid in (_classify(r.faces) for r in groups[name]) if cid != "R"}
        zero = [cid for cid in ids if TABLE[cid].wedge_deg == 0.0]
        assert len(zero) == 1, name
        assert TABLE[zero[0]].folds == tuple(sorted(e.number for e in rg.ELEMENTS if e.published_type == t))
        for r in groups[name]:
            if len(r.faces) == 1:
                assert rg.identify(rg.MIRRORS[r.faces[0]]).number in TABLE[zero[0]].folds


def test_split_members_preserve_elevation_like_their_group():
    """16 条落到 60° 类的「幻日环 / 映幻日环」成员：Φ 保持（幻日环）或翻转（映幻日环）入射方向的 z 分量——片晶绕 z 旋转后
    光仍落在同一条等仰角圆上，晕名归组没错，只是 Φ 类更细。这是独立于 phi_class 的机制层核验。"""
    rng = np.random.default_rng(1)
    dirs = rng.normal(size=(2000, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    groups = ground_truth_groups()
    checked = 0
    for name, expect in (("幻日环", 1), ("映幻日环", -1)):
        for r in groups[name]:
            cid = _classify(r.faces)
            if cid == "R" or TABLE[cid].wedge_deg == 0.0:
                continue
            out = phi_batch(PLATE, fold_matrix(PLATE, r.faces), r.faces[0], r.faces[-1], dirs)
            ok = ~np.isnan(out[:, 0])
            assert ok.sum() > 10
            assert np.allclose(out[ok, 2], expect * dirs[ok, 2], atol=1e-9), r.faces
            checked += 1
    assert checked == 18
