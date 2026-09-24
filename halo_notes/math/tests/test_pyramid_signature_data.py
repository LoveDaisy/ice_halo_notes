"""对 ``09-pyramid/data/`` 里由 ``enumerate_signatures.py`` / ``analyze_energy.py`` 产出的数据文件做断言：不在 pytest 里重跑六档 ×
max_len=6 的枚举（那是脚本的事，每档数分钟），只核验产出文件的结构、族 / 类归属可复算、可达性声明有独立的追迹见证（a01：不信
枚举器自报，用 ``draw.raypath.trace`` 这条不共享失效模式的链路取证），以及「tip_ratio=0.8 时 90° 族首现字长从 2 升到 5」这条
ch9 素材有独立于枚举器 DFS 的几何见证。"""

import csv
import re
import sys
from pathlib import Path

import numpy as np
import pytest

from halo_notes.draw.raypath import events_for_faces, face_sequence, trace
from lumice_integral.geometry import Pyramid, fold_matrix
from lumice_integral.geometry.feasibility import LatLonGrid, admissible_directions, entry_points, external_directions
from lumice_integral.symmetry.signature import phi_class

CH9 = Path(__file__).resolve().parents[3] / "09-pyramid"
DATA = CH9 / "data"
sys.path.insert(0, str(CH9 / "code"))
from analyze_energy import MC_MAX_LEN  # noqa: E402
from enumerate_signatures import GRID, KNOWN_WEDGES, L_STAR, TIERS, family_of, tier_label, tier_pyramid  # noqa: E402

DEFAULT = (1.0, 0.5)
FAST_TIERS = [DEFAULT]
SLOW_TIERS = [t for t in TIERS if t != DEFAULT]


def _csv(tier) -> list[dict]:
    with (DATA / f"signature_table_{tier_label(tier)}.csv").open() as fp:
        return list(csv.DictReader(fp))


def _raypaths(tier) -> list[dict]:
    with (DATA / f"raypaths_{tier_label(tier)}.csv").open() as fp:
        return list(csv.DictReader(fp))


def _seq(label: str) -> tuple[int, ...]:
    return tuple(int(x) for x in label.split("-"))


def _md_table(text: str, heading: str) -> list[list[str]]:
    """取 ``## heading`` 下第一张表的数据行（去表头与分隔行），每行按 ``|`` 切开。"""
    sec = text.split(f"## {heading}")[1].split("\n## ")[0]
    rows = [ln for ln in sec.splitlines() if ln.startswith("|")]
    return [[c.strip() for c in ln.strip("|").split("|")] for ln in rows[2:]]


def _first_lengths() -> dict[float, list[int]]:
    """`signature_table.md`「每族首次出现的字长」表：楔角 → 按 TIERS 顺序的首现字长。这是「某档某族 MC 能否覆盖」的唯一权威来源
    （`analyze_energy.py` 判「MC 未覆盖」用的就是精确侧最短代表长度 > MC_MAX_LEN），energy_table 的断言从这里推，不另写 tip_ratio 阈值公式。"""
    text = (DATA / "signature_table.md").read_text()
    first = {float(r[0].rstrip("°")): [int(c) for c in r[1:]] for r in _md_table(text, "每族首次出现的字长")}
    assert set(first) == set(KNOWN_WEDGES) and all(len(v) == len(TIERS) for v in first.values())
    return first


# ---- signature_table.md / csv 的结构 --------------------------------------------------------------


def test_md_has_9_family_rows_all_reachable():
    text = (DATA / "signature_table.md").read_text()
    main = _md_table(text, "主表：9 个楔角族")
    assert [r[0] for r in main] == [f"{w:g}°" for w in KNOWN_WEDGES]
    for r in main:
        assert r[3] != "—", r                     # 每族至少一档可达（验收：无空族）
        assert all(c != "—" for c in r[4:]), r    # 且 L*=6 下六档全部可达
    assert f"| 9 族命中数 | {' | '.join('9' for _ in TIERS)} |" in text
    assert "不宣称穷尽" in text                   # 诚实声明必须在


@pytest.mark.parametrize("tier", TIERS)
def test_md_family_cells_match_csv(tier):
    """md 主表每格的「类数 / 条数 / 面积」= csv 里该族全部行的 (行数, n_paths 之和, area_sr_sum 之和)。"""
    text = (DATA / "signature_table.md").read_text()
    col = 4 + TIERS.index(tier)
    rows = _csv(tier)
    for r in _md_table(text, "主表：9 个楔角族"):
        w = float(r[0].rstrip("°"))
        n_cls, n_paths, area = re.match(r"(\d+) / (\d+) / ([\d.]+)", r[col]).groups()
        mine = [x for x in rows if x["family"] and float(x["family"]) == w]
        assert len(mine) == int(n_cls), (tier, w)
        assert sum(int(x["n_paths"]) for x in mine) == int(n_paths), (tier, w)
        assert abs(sum(float(x["area_sr_sum"]) for x in mine) - float(area)) < 1e-3, (tier, w)


@pytest.mark.parametrize("tier", TIERS)
def test_csv_classes_recomputable_and_unique(tier):
    """每行的最短代表复算 phi_class 后楔角与族一致；规范 signature (fold, a, b) 全表唯一（一行一个 Φ 类）。"""
    pyramid = tier_pyramid(tier)
    seen = set()
    for row in _csv(tier):
        faces = _seq(row["shortest_path"])
        assert 2 <= len(faces) <= L_STAR
        cls = phi_class(pyramid, fold_matrix(pyramid, faces), faces[0], faces[-1])
        assert f"{cls.wedge_deg:.1f}" == row["wedge_deg"], row
        fam = family_of(cls.wedge_deg)
        assert (row["family"] == "" and fam is None) or float(row["family"]) == fam, row
        assert int(row["sliver"]) == (float(row["min_incidence_deg"]) > 49.0)
        key = (row["fold_matrix"], row["sig_entry"], row["sig_exit"])
        assert key not in seen, row
        seen.add(key)


@pytest.mark.parametrize("tier", TIERS)
def test_raypaths_csv_consistent_with_class_csv(tier):
    """raypaths 清单：长度 > 1 的行数 = 类表 n_paths 之和；每行 family 与 wedge_deg 按同一容差一致；每个类的最短代表都在清单里。"""
    paths = _raypaths(tier)
    multi = [p for p in paths if int(p["length"]) > 1]
    rows = _csv(tier)
    assert len(multi) == sum(int(r["n_paths"]) for r in rows)
    labels = {p["raypath"] for p in multi}
    for p in multi:
        fam = family_of(float(p["wedge_deg"]))
        assert (p["family"] == "" and fam is None) or float(p["family"]) == fam, p
        assert int(p["length"]) == len(_seq(p["raypath"]))
    for r in rows:
        assert r["shortest_path"] in labels, r["shortest_path"]


# ---- 可达性声明的独立见证：每族最短代表都能被 trace 追出同一面序列 ---------------------------------


def _witness(tier, faces: tuple[int, ...]) -> None:
    crystal = tier_pyramid(tier)
    res = admissible_directions(crystal, faces, GRID, refine_levels=0)
    idx = np.flatnonzero(res.mask)
    assert len(idx) > 0, (tier, faces)
    idx = idx[np.linspace(0, len(idx) - 1, min(3, len(idx))).astype(int)]
    d = GRID.directions_at(idx)
    p, ext = entry_points(crystal, faces, d), external_directions(crystal, faces, d)
    for k in range(len(idx)):
        path = trace(crystal, p[k] - 3 * ext[k], ext[k], events_for_faces(faces))
        assert face_sequence(path) == list(faces), (tier, faces)


def _family_shortest(tier) -> dict[float, tuple[int, ...]]:
    text = (DATA / "signature_table.md").read_text()
    col = 1 + TIERS.index(tier)
    out = {}
    for r in _md_table(text, "每族每档位的最短代表"):
        out[float(r[0].rstrip("°"))] = _seq(re.match(r"`([\d-]+)`", r[col]).group(1))
    return out


@pytest.mark.parametrize("tier", FAST_TIERS)
def test_family_shortest_paths_have_traceable_witnesses(tier):
    for w, faces in _family_shortest(tier).items():
        _witness(tier, faces)


@pytest.mark.slow
@pytest.mark.parametrize("tier", SLOW_TIERS)
def test_family_shortest_paths_have_traceable_witnesses_other_tiers(tier):
    for w, faces in _family_shortest(tier).items():
        _witness(tier, faces)


@pytest.mark.slow
@pytest.mark.parametrize("tier", TIERS)
def test_sampled_class_shortest_paths_have_traceable_witnesses(tier):
    """类表每 40 行抽一行的最短代表做追迹见证（族内 + 族外都覆盖）。"""
    rows = _csv(tier)
    for row in rows[::40]:
        _witness(tier, _seq(row["shortest_path"]))


# ---- ch9 素材：tip_ratio=0.8 时 90° 族（顶面↔侧面）首现字长 2 → 5 ------------------------------------


def test_first_length_table_locks_tip_ratio_effect():
    """回归锁：钉住六档实测的首现字长。其余 8 族六档都在 L≤MC_MAX_LEN 出现；90° 族只随 tip_ratio 变——≥0.8 的三档（含 0.85）都是 5、
    其余三档（含 0.25）都是 2，h/a 从 0.3 到 3 不改这个数（task-pyramid-realistic-tiers 两个极端档把这条从「四档观察」加固为「六档观察」）。"""
    first = _first_lengths()
    for w in KNOWN_WEDGES:
        if w == 90.0:
            continue
        assert max(first[w]) <= MC_MAX_LEN, (w, first[w])
    for t, n in zip(TIERS, first[90.0]):
        assert n == (5 if t[1] >= 0.8 else 2), (t, n)


def test_top_to_side_corridor_closes_with_tip_ratio():
    """独立于枚举器 DFS 的几何见证：`1-3`（环天顶弧类）可行方向集随 tip_ratio 单调收缩，0.8 时为空；0.5 时非空且可追迹。"""
    grid = LatLonGrid(90, 180)
    areas = [admissible_directions(Pyramid(a=1.0, h=1.0, tip_ratio=tr), (1, 3), grid, refine_levels=0).area_sr
             for tr in (0.5, 0.7, 0.8)]
    assert areas[0] > areas[1] > 0 and areas[2] == 0, areas
    _witness((1.0, 0.5), (1, 3))


# ---- energy_table.md 的结构 -----------------------------------------------------------------------


def test_energy_table_structure():
    text = (DATA / "energy_table.md").read_text()
    main = _md_table(text, "主表：9 个楔角族的能量份额")
    assert [r[0] for r in main] == [f"{w:g}°" for w in KNOWN_WEDGES]
    first = _first_lengths()
    for r in main:
        w = float(r[0].rstrip("°"))
        for i, (t, cell) in enumerate(zip(TIERS, r[2:2 + len(TIERS)])):
            if first[w][i] > MC_MAX_LEN:                       # 两份数据互证：精确侧首现字长 > MC 链面上限 ⇔ MC 按设计看不到
                assert cell == "未覆盖", (r[0], t, cell)
            else:
                assert re.fullmatch(r"\d+\.\d{4}", cell), (r[0], t, cell)
    fam = _md_table(text, "族级互证")
    assert len(fam) == len(KNOWN_WEDGES)
    assert not any("违反" in c or "MC 未见" in c for r in fam for c in r[1:]), fam
    assert "## 族外背景注记" in text and "| `record_full_hits` |" in text
    assert "local_build" not in text or "本地 build" in text
    for t in TIERS:
        assert (DATA / f"analysis_{tier_label(t)}.lumice.json").exists()
