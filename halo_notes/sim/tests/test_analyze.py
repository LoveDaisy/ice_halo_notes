"""analyze.py 单测：固定 CSV fixture 钉解析 / 聚合 / 互证逻辑；fake 可执行脚本钉参数拼装与落盘产物；slow 真跑本地 build。"""

from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path

import pytest

from lumice_integral.geometry import HexPrism

from halo_notes.sim import fetch
from lumice_integral.geometry.enumerate import RaypathRecord, enumerate_raypaths
from lumice_integral.geometry.feasibility import LatLonGrid
from halo_notes.math import reflection_group as rg
from halo_notes.math.signature import phi_class_table
from halo_notes.sim import analyze as A
from halo_notes.sim import config as C
from halo_notes.sim.run import LumiceError

# 2026-09-15 本地 build 实跑输出的逐字节形态（头 7 行、列头、正常行、相邻重复面行、other 行）
FIXTURE = """# Lumice raypath analysis
# exported_at: 2026-09-15 01:45:51
# region: whole sky
# symmetry: no symmetry
# total_rays: 2776462
# total_energy: 490984
# record_full_hits: 61788
Raypath,Energy,Cumulative %,+/-
1-2,11.2509,11.2509,0.20
2-1,11.2184,22.4693,0.20
1,1.5994,24.0687,0.15
3-5,1.5687,25.6374,0.56
3-1-5,0.4000,26.0374,2.00
5-5-6,0.0000,99.9464,100.00
4-4-2-1,0.0000,99.9985,100.00
1-2-1,0.3000,99.8263,50.00
other (not recorded),0.1737,100.0000,-
"""


def _rec(faces: tuple[int, ...], area: float = 0.1) -> RaypathRecord:
    return RaypathRecord(faces=faces, admissible_mask=None, area_sr=area, min_incidence_deg=10.0)


# ---------- 换算 / config ----------


def test_hex_prism_height_ratio_halves():
    assert C.hex_prism_height_ratio(1.0) == 0.5
    assert C.hex_prism_height_ratio(0.2) == pytest.approx(0.1)
    assert C.hex_prism_height_ratio(5) == 2.5


def test_analysis_config_shape():
    cfg = A.analysis_config(2.0, max_len=7, rays=5_000, sun_altitude=20)
    assert cfg["crystal"][0]["shape"]["height"] == 1.0            # ratio / 2
    assert cfg["crystal"][0]["axis"] == C.random_axis()
    assert cfg["scene"]["max_hits"] == 7                            # max_hits = 面数上限 = max_len（实测）
    assert cfg["scene"]["ray_num"] == 5_000
    assert cfg["scene"]["light_source"]["spectrum"] == [{"wavelength": 550.0, "weight": 1.0}]
    assert cfg["scene"]["scattering"][0]["prob"] == 0
    assert cfg["render"] == [] and cfg["filter"] == []
    with pytest.raises(ValueError):
        A.analysis_config(1.0, max_len=0, rays=10)


# ---------- CSV 解析 ----------


def test_parse_csv_header_and_rows():
    header, rows = A.parse_analysis_csv(FIXTURE)
    assert header.region == "whole sky" and header.symmetry == "no symmetry"
    assert header.total_rays == 2776462 and header.total_energy == 490984.0 and header.record_full_hits == 61788
    assert header.exported_at == "2026-09-15 01:45:51" and header.raw["total_rays"] == "2776462"
    assert len(rows) == 9
    r0 = rows[0]
    assert r0.faces == (1, 2) and not r0.is_other and r0.energy_pct == 11.2509 and r0.cumulative_pct == 11.2509
    assert r0.noise_pct == 0.20 and r0.count == pytest.approx(250_000) and r0.label == "1-2"
    assert rows[2].faces == (1,) and rows[2].label == "1"
    assert rows[5].faces == (5, 5, 6) and rows[5].has_adjacent_repeat
    assert rows[6].has_adjacent_repeat and not rows[4].has_adjacent_repeat
    other = rows[-1]
    assert other.is_other and other.faces == () and other.energy_pct == 0.1737 and other.noise_pct is None
    assert other.count is None and other.label == "other" and other.raw.startswith("other (not recorded)")


def test_parse_csv_rejects_bad_shapes():
    with pytest.raises(ValueError, match="列头"):
        A.parse_analysis_csv("# region: whole sky\nRaypath,Energy\n")
    with pytest.raises(ValueError, match="缺少键"):
        A.parse_analysis_csv("# region: whole sky\nRaypath,Energy,Cumulative %,+/-\n1-2,1,1,1\n")
    head = FIXTURE.split("Raypath,")[0] + "Raypath,Energy,Cumulative %,+/-\n"
    with pytest.raises(ValueError, match="多晶体"):
        A.parse_analysis_csv(head + "C1(3-5),1,1,1\n")
    with pytest.raises(ValueError, match="多晶体"):
        A.parse_analysis_csv(head + "3-5 -> 1-2,1,1,1\n")
    with pytest.raises(ValueError, match="4 列"):
        A.parse_analysis_csv(head + "3-5,1,1\n")


def test_parse_raypath():
    assert A.parse_raypath("3-5") == (3, 5) and A.parse_raypath(" 1 ") == (1,)
    assert A.has_adjacent_repeat((1, 2, 2)) and not A.has_adjacent_repeat((1, 2, 1))


# ---------- run_analysis（fake 二进制） ----------

FAKE_OK = r"""#!/bin/sh
# 校验子命令 / -f 存在，把固定 CSV 写到 --csv 路径
sub="$1"; shift
csv=; cfg=
while [ $# -gt 0 ]; do
  case "$1" in
    -f) cfg="$2"; shift 2;;
    --csv) csv="$2"; shift 2;;
    *) shift;;
  esac
done
test "$sub" = analyze || { echo "bad subcommand $sub" >&2; exit 3; }
test -f "$cfg" || { echo "no config" >&2; exit 2; }
cat > "$csv" <<'EOF'
""" + FIXTURE + """EOF
echo "[analyze] done" >&2
exit 0
"""

FAKE_FAIL = "#!/bin/sh\necho 'boom: bad config line 3' >&2\nexit 1\n"


def _script(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "fake-lumice"
    p.write_text(body)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return p


def test_run_analysis_products_and_provenance(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMICE_BIN", raising=False)
    binary = _script(tmp_path, FAKE_OK)
    cfg = A.analysis_config(1.0, max_len=7, rays=1234)
    out = tmp_path / "out"
    res = A.run_analysis(cfg, out, roi="sky", symmetry="none", seed=7, bin=binary)
    assert (out / "config.json").exists() and (out / "analysis.csv").exists() and (out / "lumice.log").exists()
    assert json.loads((out / "config.json").read_text()) == cfg
    assert res.header.record_full_hits == 61788 and len(res.rows) == 9
    prov = json.loads((out / "provenance.json").read_text())
    assert prov == res.provenance
    assert prov["cli_args"] == ["analyze", "-f", str(out / "config.json"), "--roi", "sky", "--symmetry", "none",
                                "--rays", "1234", "--csv", str(out / "analysis.csv"), "--seed", "7"]
    assert prov["local_build"] is True and prov["lumice_version"] is None      # 显式 bin ⇒ 非 release
    assert prov["rays"] == 1234 and prov["seed"] == 7 and prov["roi"] == "sky" and prov["symmetry"] == "none"
    assert prov["record_full_hits"] == 61788 and prov["total_rays"] == 2776462
    assert prov["config"] == cfg and len(prov["lumice_bin_sha256"]) == 64 and prov["lumice_bin_mtime"]
    assert prov["header"]["symmetry"] == "no symmetry"
    back = A.load_analysis(out)
    assert back.rows == res.rows and back.provenance == prov


def test_run_analysis_env_override_marks_local_build(tmp_path, monkeypatch):
    binary = _script(tmp_path, FAKE_OK)
    monkeypatch.setenv("LUMICE_BIN", str(binary))
    res = A.run_analysis(A.analysis_config(1.0, max_len=3, rays=10), tmp_path / "out")
    assert res.provenance["local_build"] is True and res.provenance["lumice_bin"] == str(binary)
    assert "--seed" not in res.provenance["cli_args"]


def test_run_analysis_release_path_records_version(tmp_path, monkeypatch):
    monkeypatch.delenv("LUMICE_BIN", raising=False)
    binary = _script(tmp_path, FAKE_OK)
    monkeypatch.setattr(A, "ensure_lumice", lambda: binary)
    res = A.run_analysis(A.analysis_config(1.0, max_len=3, rays=10), tmp_path / "out", workers=2, backend="cpu")
    assert res.provenance["local_build"] is False and res.provenance["lumice_version"] == fetch.LUMICE_VERSION
    assert res.provenance["lumice_git_head"] is None
    assert "--workers" in res.provenance["cli_args"] and "--backend" in res.provenance["cli_args"]


def test_run_analysis_failure_and_validation(tmp_path):
    cfg = A.analysis_config(1.0, max_len=3, rays=10)
    with pytest.raises(LumiceError, match="bad config line 3"):
        A.run_analysis(cfg, tmp_path / "out", bin=_script(tmp_path, FAKE_FAIL))
    assert not (tmp_path / "out" / "provenance.json").exists()
    ok = _script(tmp_path, FAKE_OK)
    with pytest.raises(ValueError):
        A.run_analysis(cfg, tmp_path / "o2", roi="moon", bin=ok)
    with pytest.raises(ValueError):
        A.run_analysis(cfg, tmp_path / "o2", symmetry="Q", bin=ok)
    with pytest.raises(TypeError):
        A.run_analysis(cfg, tmp_path / "o2", rays="infinite", bin=ok)


def test_run_analysis_clears_stale_csv(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / A.CSV_NAME).write_text("stale")
    res = A.run_analysis(A.analysis_config(1.0, max_len=3, rays=10), out, bin=_script(tmp_path, FAKE_OK))
    assert res.csv_path.read_text() == FIXTURE


# ---------- 聚合 / 互证 ----------


def test_usable_rows_filters():
    _, rows = A.parse_analysis_csv(FIXTURE)
    labels = [r.label for r in A.usable_rows(rows)]
    assert labels == ["1-2", "2-1", "3-5", "3-1-5", "1-2-1"]


def test_classify_rows_aggregates_by_phi_class():
    crystal = HexPrism.from_ratio(1.0)
    _, rows = A.parse_analysis_csv(FIXTURE)
    agg = A.classify_rows(crystal, rows)
    by_cls = {r.phi_class: r for r in phi_class_table(crystal)}
    ids = {by_cls[c].id: a for c, a in agg.items()}
    # 1-2 与 2-1 是同一 PBD 轨道（A0-06），能量相加、代表只有一个；3-5 是 A60-12；3-1-5 是 A60-11；1-2-1 是 A0-05
    assert set(ids) == {"A0-06", "A60-12", "A60-11", "A0-05"}
    a = ids["A0-06"]
    assert a.energy_pct == pytest.approx(11.2509 + 11.2184) and a.n_rows == 2 and a.reps == {(1, 2)}
    assert a.count == pytest.approx(2 * 250_000) and a.brightest.label == "1-2"
    assert ids["A60-12"].brightest.faces == (3, 5) and ids["A60-11"].reps == {(3, 1, 5)}
    assert sum(x.n_rows for x in agg.values()) == 5


def test_crosscheck_classifies_three_ways():
    _, rows = A.parse_analysis_csv(FIXTURE)
    exact = [_rec((1, 2), 10.0), _rec((3, 5), 1.0), _rec((1, 2, 1), 0.5), _rec((3, 4, 5, 7), 0.01),
             _rec((1, 2, 3, 4, 5, 6, 7, 8), 0.001), _rec((1,), 6.28)]
    res = A.crosscheck(rows, exact, mc_max_len=7)
    assert [rep for _, rep in res.violations] == [(3, 1, 5)]          # MC 命中、精确集里没有
    assert res.violations[0][0].label == "3-1-5"
    assert res.seen == {(1, 2): pytest.approx(11.2509 + 11.2184), (3, 5): pytest.approx(1.5687), (1, 2, 1): pytest.approx(0.3)}
    assert [r.faces for r in res.unseen] == [(3, 4, 5, 7)]           # 长度 ≤ 7 未见
    assert [r.faces for r in res.uncovered] == [(1, 2, 3, 4, 5, 6, 7, 8)]
    assert [r.label for r in res.dropped_adjacent_repeat] == ["5-5-6", "4-4-2-1"]
    assert res.dropped_energy_pct == 0.0 and res.other_energy_pct == pytest.approx(0.1737)
    assert res.single_face_energy_pct == pytest.approx(1.5994)
    assert not res.ok
    assert A.crosscheck(rows, exact + [_rec((3, 1, 5))], mc_max_len=7).ok


def test_crosscheck_pbd_orbit_membership():
    """MC 行是轨道里任意成员（如 7-5），精确集只存字典序最小代表（3-5）也能对上。"""
    rows = [A.AnalysisRow((7, 5), False, 1.0, 1.0, 1.0, "7-5,1,1,1")]
    assert min(rg.pbd_orbit((7, 5))) == (3, 5)
    assert A.crosscheck(rows, [_rec((3, 5))], mc_max_len=3).ok


def test_spearman_rho():
    assert A.spearman_rho([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert A.spearman_rho([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert A.spearman_rho([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(0.9486832980505138)   # 并列取平均秩
    assert math.isnan(A.spearman_rho([1, 1, 1], [1, 2, 3])) and math.isnan(A.spearman_rho([1], [2]))
    with pytest.raises(ValueError):
        A.spearman_rho([1, 2], [1])


# ---------- slow：真跑本地 build ----------


@pytest.mark.slow
def test_real_lumice_analyze_pipeline_smoke(tmp_path):
    """管线烟测：跑通、产出文件、CSV 可解析、classify/crosscheck 不抛异常；不对 violations/unseen 内容做断言
    （互证的通过 / 归因是人工步骤，见 task plan Step 5）。release 版没有 analyze 子命令 ⇒ 未设 LUMICE_BIN 时 skip。"""
    if not os.environ.get("LUMICE_BIN"):
        pytest.skip("需要 LUMICE_BIN 指向带 analyze 子命令的本地 build")
    ratio, max_len = 1.0, 4
    cfg = A.analysis_config(ratio, max_len=max_len, rays=200_000)
    try:
        res = A.run_analysis(cfg, tmp_path / "out", seed=7, timeout=300)
    except LumiceError as exc:
        if "analyze" in str(exc) and "Unknown" in str(exc):
            pytest.skip(f"该二进制不支持 analyze 子命令：{exc}")
        raise
    assert res.provenance["local_build"] is True and res.rows and max(len(r.faces) for r in res.rows) == max_len
    crystal = HexPrism.from_ratio(ratio)
    agg = A.classify_rows(crystal, res.rows)
    assert agg
    exact = enumerate_raypaths(crystal, max_len, LatLonGrid(45, 90), entry_faces=(1, 3), symmetry_orbit=rg.pbd_orbit)
    cc = A.crosscheck(res.rows, exact, mc_max_len=max_len)
    assert isinstance(cc.ok, bool) and not cc.uncovered


def test_pyramid_analysis_config_shape():
    """锥晶版与六棱柱版只差 crystal 段：类型 pyramid、换算字段来自 ``pyramid_crystal_from_geometry``、随机取向；六棱柱版不变。"""
    from lumice_integral.geometry import Pyramid

    cfg = A.pyramid_analysis_config(Pyramid(a=1.0, h=2.0, tip_ratio=0.3), max_len=5, rays=1234)
    c = cfg["crystal"][0]
    assert c["type"] == "pyramid" and c["axis"] == C.random_axis()
    assert c["shape"] == {"prism_h": 1.0, "upper_h": 0.3, "lower_h": 0.3, "upper_indices": [1, 0, 1], "lower_indices": [1, 0, 1]}
    assert cfg["scene"]["max_hits"] == 5 and cfg["scene"]["ray_num"] == 1234 and cfg["render"] == []
    hexcfg = A.analysis_config(1.0, max_len=5, rays=1234)
    assert {k: v for k, v in cfg.items() if k != "crystal"} == {k: v for k, v in hexcfg.items() if k != "crystal"}
    with pytest.raises(ValueError):
        A.pyramid_analysis_config(Pyramid(), max_len=0, rays=10)


@pytest.mark.slow
def test_real_lumice_analyze_pyramid_smoke(tmp_path):
    """锥晶 smoke（scrum ch9-prep 子任务 2）：随机取向 ``Pyramid()``、``max_len=4`` 跑通，CSV 出现上锥 13–18 与下锥 23–28 面，
    ``classify_rows(Pyramid(), rows)`` 归 Φ 类不报错且类数 > 1；不出表（子任务 4）。``max_len=4`` 是不撞 16384 槽驻留表的
    最大链长（2026-09-20 实测：4 ⇒ 7580 行 / ``record_full_hits=0``；5 ⇒ 16385 行 / 20374 次被拒、``other`` 0.7% 能量），
    这里顺带断言不溢出，子任务 4 要跑 5 以上必须先处理上限。"""
    if not os.environ.get("LUMICE_BIN"):
        pytest.skip("需要 LUMICE_BIN 指向带 analyze 子命令的本地 build")
    from lumice_integral.geometry import Pyramid
    from lumice_integral.geometry.pyramid import LOWER_PYRAMID_FACES, UPPER_PYRAMID_FACES

    pyramid, max_len = Pyramid(), 4
    cfg = A.pyramid_analysis_config(pyramid, max_len=max_len, rays=300_000)
    res = A.run_analysis(cfg, tmp_path / "out", seed=7, timeout=600)
    assert res.provenance["local_build"] is True and res.rows and max(len(r.faces) for r in res.rows) == max_len
    assert res.header.record_full_hits == 0 and not any(r.is_other for r in res.rows)
    faces_seen = {f for r in res.rows for f in r.faces}
    assert faces_seen & set(UPPER_PYRAMID_FACES) and faces_seen & set(LOWER_PYRAMID_FACES)
    assert faces_seen <= {1, 2, *range(3, 9), *UPPER_PYRAMID_FACES, *LOWER_PYRAMID_FACES}
    agg = A.classify_rows(pyramid, res.rows)
    assert len(agg) > 1
    assert sum(a.energy_pct for a in agg.values()) > 0
    print(f"pyramid smoke: {len(res.rows)} 行, record_full_hits={res.header.record_full_hits}, {len(agg)} 个 Φ 类")


def test_fine_grid_area_recovers_coarse_grid_miss():
    """h/a=1 的 `3-6-3-6-4`：2° 网格判不可达（枚举器口径），0.5° 细网格上有可行格（2026-09-15 互证违反项归因样例）；
    宽窗口的 `3-5` 两边都可行；单面序列拒绝。"""
    crystal = HexPrism.from_ratio(1.0)
    from lumice_integral.geometry.feasibility import is_feasible
    assert not is_feasible(crystal, [3, 6, 3, 6, 4], LatLonGrid(90, 180))
    area, n = A.fine_grid_area(crystal, [3, 6, 3, 6, 4], step_deg=0.5)
    assert n > 0 and 0 < area < 0.01
    area_wide, n_wide = A.fine_grid_area(crystal, [3, 5], step_deg=2.0)
    assert n_wide > 100 and area_wide > 0.5
    with pytest.raises(ValueError):
        A.fine_grid_area(crystal, [3])
