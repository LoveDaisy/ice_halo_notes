"""raypath_probe.py 单测：锥晶面编号 / 手性 / 旋转链 fixture（快：对照存好的数值；slow：真跑当前二进制重取证）。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from lumice_integral.geometry import Pyramid
from halo_notes.sim import raypath_probe as P

FIXTURE = Path(__file__).resolve().parent / "data" / "pyramid_raypath_fixture.json"
ALT_MIN_DEG = 2.0     # 反假设（别的 Miller 指数 / 镜像面号）的落点至少离 Lumice 亮斑这么远，fixture 才有分辨力


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def test_sun_direction_and_az_el_roundtrip():
    d = P.sun_direction(35.0, 10.0)
    assert np.isclose(np.linalg.norm(d), 1.0)
    assert P.az_el(-d) == pytest.approx((10.0, 35.0))            # −d 指回太阳
    assert P.az_el([0, 0, 1]) == pytest.approx((0.0, 90.0))


def test_predicted_sky_parallel_faces_pass_straight_through():
    """上锥面 13 与下锥面 26 平行（法向互为相反数）：折射抵消，出射天空方向 = 太阳位置；几何走廊不通的方向给 None。"""
    pyr = Pyramid()
    d = P.sun_direction(**P.PYRAMID_SUN)
    assert P.az_el(P.predicted_sky(pyr, (13, 26), d)) == pytest.approx((10.0, 35.0), abs=1e-6)
    assert P.predicted_sky(pyr, (3, 13), d) is None               # 同方位角侧面进上锥面出：太阳在地平线上不可行
    assert P.predicted_sky(pyr, (8, 6), d) is None                # 4-6 的镜像：走廊不通


def test_mirror_face_is_an_involution_fixing_the_xz_plane():
    for f in (1, 2, 3, 6, 13, 16, 23, 26):
        assert P.mirror_face(f) == f
    assert P.mirror_face(14) == 18 and P.mirror_face(15) == 17 and P.mirror_face(4) == 8 and P.mirror_face(27) == 25
    for f in range(3, 9):
        assert P.mirror_face(P.mirror_face(f)) == f


def test_spot_direction_recovers_a_painted_pixel():
    r = {"lens": {"type": "rectangular", "fov": 180}, "resolution": [360, 180], "visible": "full"}
    dirs, _ = P.rectangular_pixel_directions(r)
    img = np.zeros((180, 360), np.uint8)
    img[40, 200] = 200
    img[41, 200] = 100
    sky, n, peak = P.spot_direction(Image.fromarray(img), r)
    assert n == 2 and peak == pytest.approx(200 / 255)
    expect = (dirs[40, 200] * 200 + dirs[41, 200] * 100)
    assert P.angle_deg(sky, expect) < 1e-6
    assert P.spot_direction(Image.fromarray(np.zeros((180, 360), np.uint8)), r)[0] is None


def test_probe_config_shape():
    cfg = P.probe_config({"id": 1, "type": "prism", "shape": {"height": 1.0}}, (3, 5), sun_altitude=20.0, rays=1000)
    assert cfg["filter"] == [{"id": 1, "type": "raypath", "raypath": [3, 5], "symmetry": "", "action": "filter_in"}]
    assert cfg["scene"]["scattering"][0]["entries"] == [{"crystal": 1, "proportion": 100, "filter": 1}]
    assert cfg["scene"]["max_hits"] == 3 and cfg["scene"]["ray_num"] == 1000
    assert cfg["render"][0]["lens"]["type"] == "rectangular" and cfg["render"][0]["visible"] == "full"


# ---------- 锥晶 fixture（快：对照 2026-09-20 用 release v4.5.1 取证的数值） ----------


def test_pyramid_fixture_lumice_matches_geometry_within_tolerance():
    """9 条光路（6 条显式单位姿态 + 3 条 axis 省略）Lumice 亮斑与 ``phi`` 预测的夹角全部 ≤ 0.5°（实测 ≤ 0.19°）。"""
    fx = _fixture()
    assert fx["runs"]["identity"]["lumice_version"] == "v4.5.1"
    assert fx["runs"]["identity"]["axis"] == P.IDENTITY_AXIS and fx["runs"]["omitted"]["axis"] is None
    for key, run in fx["runs"].items():
        for row in run["rows"]:
            assert row["sky"] is not None and row["lumice_sky"] is not None, (key, row["faces"])
            assert row["n_pixels"] >= 3 and row["peak"] > 0.5, (key, row["faces"])
            assert row["diff_deg"] <= fx["tol_deg"], (key, row["faces"], row["diff_deg"])
            assert P.angle_deg(row["sky"], row["lumice_sky"]) == pytest.approx(row["diff_deg"], abs=1e-3)


def test_pyramid_fixture_predictions_are_reproducible_from_current_geometry():
    """fixture 里的几何预测（含反假设落点）与当前 LI ``Pyramid`` + ``phi`` 重算一致——LI 侧几何若漂移，这里先红。"""
    fx = _fixture()
    fresh = P.pyramid_predictions()
    for key in ("identity", "omitted"):
        for stored, now in zip(fx["runs"][key]["rows"], fresh[key], strict=True):
            assert stored["faces"] == now["faces"]
            assert stored["az_el"] == pytest.approx(now["az_el"], abs=2e-3)
            for alt in ("alt_cone_az_el", "alt_mirror_az_el"):
                if alt in now:
                    assert stored[alt] == now[alt] or stored[alt] == pytest.approx(now[alt], abs=2e-3)


def test_pyramid_fixture_discriminates_miller_indices_and_chirality():
    """尺子先受审（a16）：Lumice 亮斑离「``[2,0,3]`` 锥面」与「镜像面号」的预测都 ≥ 2°（或反假设下光路根本不可行），
    fixture 才真的分辨得出 ``[1,0,1]`` 与手性；``13-26`` 平行直穿对两者都不敏感、``4-6`` 纯棱柱对锥角不敏感，是设计内的对照。"""
    fx = _fixture()
    rows = {tuple(r["faces"]): r for r in fx["runs"]["identity"]["rows"]}
    sensitive_cone, sensitive_mirror = 0, 0
    for faces, r in rows.items():
        lum = r["lumice_az_el"]
        for alt, counter in (("alt_cone_az_el", "cone"), ("alt_mirror_az_el", "mirror")):
            a = r[alt]
            if a is None:
                # 反假设下不可行而 Lumice 有亮斑：本身就是否证
                if counter == "cone":
                    sensitive_cone += 1
                else:
                    sensitive_mirror += 1
                continue
            sep = P.angle_deg(_vec(*a), _vec(*lum))
            if sep >= ALT_MIN_DEG:
                if counter == "cone":
                    sensitive_cone += 1
                else:
                    sensitive_mirror += 1
            else:
                # 只允许两条按设计就不敏感的：13-26 平行直穿（对两者都不敏感）、4-6 纯棱柱（不含锥面，对锥角不敏感）
                assert faces == (13, 26) or (faces == (4, 6) and counter == "cone"), (faces, alt, sep)
    assert sensitive_cone >= 4 and sensitive_mirror >= 4
    # 手性对：14-6 与 18-6 互为镜像，Lumice 各自落在 LI 同号光路的位置，而不是对方的位置
    assert P.angle_deg(_vec(*rows[(14, 6)]["lumice_az_el"]), _vec(*rows[(18, 6)]["az_el"])) > 30


def test_pyramid_fixture_axis_omitted_equals_half_turn():
    """axis 省略 = ``Rz(−180°)``：面号 +3（mod 6）的三条光路与单位姿态下的原光路落点重合（Lumice 亮斑两两 ≤ 0.02°）。"""
    fx = _fixture()
    ident = {tuple(r["faces"]): r for r in fx["runs"]["identity"]["rows"]}
    for r in fx["runs"]["omitted"]["rows"]:
        partner = tuple(f if f in (1, 2) else _shift(f, -3) for f in r["faces"])
        assert partner in ident, r["faces"]
        assert P.angle_deg(r["lumice_sky"], ident[partner]["lumice_sky"]) < 0.02


def _shift(face: int, k: int) -> int:
    base = 3 if face < 10 else (13 if face < 20 else 23)
    return base + (face - base + k) % 6


def _vec(az: float, el: float) -> np.ndarray:
    a, e = np.radians(az), np.radians(el)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


# ---------- slow：真跑当前二进制（默认 release v4.5.1；LUMICE_BIN 指本地 build 时为对照跑） ----------


@pytest.mark.slow
def test_real_lumice_pyramid_raypaths_match_geometry_and_fixture(tmp_path):
    """重取证：当前二进制下 9 条光路的亮斑 (a) 与 ``phi`` 预测夹角 ≤ 0.5°；(b) 与 fixture 存的 release 亮斑 ≤ 0.1°
    （两套二进制的锥晶几何代码相同，若不一致如实红掉，不调容差）。"""
    bin_env = os.environ.get("LUMICE_BIN")
    fx = P.build_pyramid_fixture(tmp_path, bin=Path(bin_env) if bin_env else None, rays=300_000)
    stored = _fixture()
    for key, run in fx["runs"].items():
        for row, ref in zip(run["rows"], stored["runs"][key]["rows"], strict=True):
            assert row["faces"] == ref["faces"]
            assert row["lumice_sky"] is not None, (key, row["faces"])
            assert row["diff_deg"] <= P.FIXTURE_TOL_DEG, (key, row["faces"], row["diff_deg"])
            assert P.angle_deg(row["lumice_sky"], ref["lumice_sky"]) <= 0.1, (key, row["faces"])
