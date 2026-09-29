"""``halo_notes.sim.projection``：等积鱼眼正投影与 Lumice 的相机 / 镜头约定一致——公式层面自检 + 用仓里一张真实渲染图
（ch7 图 6 的 col_3，带经纬网格）逐像素比对。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from halo_notes.sim.projection import (GLOBE_CAP_DEG, camera_rotation, frame_center, globe_view_for, pixels_per_degree,
                                       project, project_equal_area, project_globe, project_rectangular,
                                       rectangular_pixel_directions, view_direction)

ROOT = Path(__file__).resolve().parents[3]
CH7 = ROOT / "07-reflection-group"


def sky(el_deg: float, az_deg: float) -> np.ndarray:
    e, a = np.radians(el_deg), np.radians(az_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def render(fov: float, view: dict, size: int = 1000) -> dict:
    return {"lens": {"type": "fisheye_equal_area", "fov": fov}, "resolution": [size, size], "view": view}


def test_camera_axes_follow_the_lumice_convention():
    """视线 = (cos el cos az, cos el sin az, sin el)（doc §9.1）；roll=0 时相机 y 轴指向天底一侧（画面 y 向下、天顶在上）。"""
    for az, el in ((0, 0), (90, 0), (180, 10), (35, 60)):
        R = camera_rotation({"azimuth": az, "elevation": el})
        assert np.allclose(R @ R.T, np.eye(3)) and np.isclose(np.linalg.det(R), 1.0)
        assert np.allclose(R[:, 2], sky(el, az))
        assert R[2, 1] < 0 or el == 90                 # 相机 y 轴的世界 z 分量为负：画面向下 = 世界向下
    assert np.allclose(view_direction(None), [1, 0, 0])


def test_equal_area_radius_formula_and_screen_handedness():
    """r = (short/2)·sin(θ/2)/sin(fov/4)（θ = 与视线夹角）；视线中心落在图片中心；仰角更高的方向 v 更小（在上）；
    方位角 +Δ 的方向 u 更大（右 = +az）；视线正后方判 miss（NaN）。"""
    r = render(120, {"azimuth": 180, "elevation": 10})
    c = project_equal_area(sky(10, 180), r)[0]
    assert np.allclose(c, [500, 500])
    for theta in (5.0, 30.0, 59.0):
        p = project_equal_area(sky(10 + theta, 180), r)[0]
        assert np.isclose(np.linalg.norm(p - c), 500 * np.sin(np.radians(theta) / 2) / np.sin(np.radians(120) / 4))
        assert p[1] < c[1] and np.isclose(p[0], c[0])      # 正上方
    right = project_equal_area(sky(10, 180 + 20), r)[0]
    assert right[0] > c[0]
    assert np.isnan(project_equal_area(sky(-10, 0), r)[0]).all()
    assert pixels_per_degree(sky(10, 180), r) == pytest.approx(500 * np.radians(1) / 2 / np.sin(np.radians(30)), rel=1e-3)


@pytest.mark.local_data
def test_projection_reproduces_the_grid_lumice_drew():
    """图 6 col_3 渲染图（globe、fov 30、反日点为帧中心、每 30° 经纬网格）：把仰角 ±30° 圈与方位 150° / 210° 经线按本模块
    投影后，≥ 99% 的采样点 2 px 窗内有网格亮度（≥ 40）；同一条线平移 6 px 后只剩不到一半（排除「到处都亮」的假阳性）。"""
    cfg = json.loads((CH7 / "data" / "halo_columns.col_3.lumice.json").read_text())
    r = cfg["render"][0]
    assert r["lens"]["type"] == "globe"
    img = np.asarray(Image.open(CH7 / "data" / "halo_columns" / "col_3" / "img_01.png").convert("L"), float)
    assert img.shape == tuple(r["resolution"][::-1])
    # (线, 平移方向)：纬圈大致水平 → 竖直平移；经线大致竖直 → 水平平移；只取离帧中心 < 65° 的采样点（球冠边缘透视压扁）
    center = frame_center(r)
    lines = [([sky(30, a) for a in np.linspace(0, 360, 1441)], (0.0, 6.0)),
             ([sky(-30, a) for a in np.linspace(0, 360, 1441)], (0.0, 6.0)),
             ([sky(e, 150) for e in np.linspace(-89, 89, 713)], (6.0, 0.0)),
             ([sky(e, 210) for e in np.linspace(-89, 89, 713)], (6.0, 0.0))]

    def lit_fraction(pts, uv: np.ndarray, half: int) -> float:
        hits = []
        for p_, (u, v) in zip(pts, uv):
            if np.isnan(u) or p_ @ center < np.cos(np.radians(65)):
                continue
            if not (half < u < img.shape[1] - half - 1 and half < v < img.shape[0] - half - 1):
                continue
            i, j = int(np.floor(v)), int(np.floor(u))
            hits.append(img[i - half:i + half + 1, j - half:j + half + 1].max() >= 40)
        assert len(hits) > 200
        return float(np.mean(hits))

    for pts, shift in lines:
        uv = project(pts, r)
        assert lit_fraction(pts, uv, 2) >= 0.99
        assert lit_fraction(pts, uv + np.array(shift), 1) < 0.5


def test_screen_handedness_pinned_by_an_asymmetric_bare_grid_render():
    """对称的网格 / 晕分不清左右镜像（每 30° 一条的经线关于视线对称），所以另用一张只画「视线右侧 40° 一条经线 +
    视线上方 25° 一条纬圈」的小渲染图（tests/data，config 同目录）钉住左右 / 上下：投影后这两条线落在亮像素上（≥ 99%），
    它们关于视线的镜像（方位 −40° / 仰角 −25°）几乎全落在黑处（< 10%）。"""
    d = Path(__file__).resolve().parent / "data"
    cfg = json.loads((d / "equal_area_handedness.lumice.json").read_text())
    r = cfg["render"][0]
    az0, el0 = r["view"]["azimuth"], r["view"]["elevation"]
    lon = cfg["render"][0]["grid"]["longitude"][0]["value"]
    lat = cfg["render"][0]["grid"]["elevation"][0]["value"]
    assert lon == az0 + 40 and lat == el0 + 25
    img = np.asarray(Image.open(d / "equal_area_handedness.png").convert("L"), float)
    assert img.shape == tuple(r["resolution"][::-1])

    def lit_fraction(pts) -> float:
        uv = project_equal_area(pts, r)
        hits = []
        for u, v in uv:
            if np.isnan(u) or not (2 < u < img.shape[1] - 3 and 2 < v < img.shape[0] - 3):
                continue
            i, j = int(np.floor(v)), int(np.floor(u))
            hits.append(img[i - 2:i + 3, j - 2:j + 3].max() >= 128)
        assert len(hits) > 30
        return float(np.mean(hits))

    assert lit_fraction([sky(e, lon) for e in np.linspace(-60, 89, 300)]) >= 0.99
    assert lit_fraction([sky(e, az0 - 40) for e in np.linspace(-60, 89, 300)]) < 0.1
    assert lit_fraction([sky(lat, a) for a in np.linspace(0, 360, 721)]) >= 0.99
    assert lit_fraction([sky(el0 - 25, a) for a in np.linspace(0, 360, 721)]) < 0.1


# ---- globe / rectangular（R2-3） ----


def globe(view: dict, fov: float = 30.0, size: int = 1000) -> dict:
    return {"lens": {"type": "globe", "fov": fov}, "resolution": [size, size], "view": view}


def test_globe_frame_center_cap_and_scale():
    """帧中心天空方向 = (az + 180°, −el) 落在图片中心；离帧中心 θ 的方向落在半径 (short/2)/tan(fov/2) · sinθ/(D − cosθ) 处；
    θ ≥ 75.5°（c_z ≥ −1/4）判不可见（NaN）；fov=30 时球的边缘（θ→75.5°）在短边的 ~96%（doc）；roll 被忽略。"""
    c = sky(10, 0)
    r = globe(globe_view_for(c))
    assert r["view"] == {"azimuth": 180.0, "elevation": -10.0}
    assert np.allclose(frame_center(r), c) and np.allclose(project_globe(c, r), [[500, 500]])
    f = 500 / np.tan(np.radians(15))
    for theta in (10, 40, 70, 75):
        p = sky(10 + theta, 0)                                       # 帧中心正上方 θ
        uv = project_globe(p, r)[0]
        rad = np.sin(np.radians(theta)) / (4.0 - np.cos(np.radians(theta))) * f
        assert np.isclose(uv[0], 500) and np.isclose(500 - uv[1], rad), theta
    assert np.isnan(project_globe(sky(10 + 76, 0), r)).all() and np.isnan(project_globe(-c, r)).all()
    assert np.isclose(GLOBE_CAP_DEG, np.degrees(np.arccos(0.25)))
    rim = np.sin(np.radians(GLOBE_CAP_DEG)) / (4.0 - np.cos(np.radians(GLOBE_CAP_DEG))) * f
    assert 0.95 < rim / 500 < 0.97
    assert np.allclose(project_globe(sky(30, 40), r), project_globe(sky(30, 40), globe(dict(r["view"], roll=35))))
    assert np.allclose(project(c, r), project_globe(c, r))
    with pytest.raises(ValueError):
        project_globe(c, render(120, {"azimuth": 0, "elevation": 0}))


def test_globe_handedness_pinned_by_an_asymmetric_bare_grid_render():
    """球面外视左右与内视相反（+az 在画面左侧）：tests/data 的 globe 裸网格小图（帧中心 (az 30, el 20)，只画 az 70 经线 +
    el 45 纬圈）——投影后两条线落在亮像素上（≥ 99%），其镜像（az −10 / el −5）几乎全黑（< 10%）；亮像素质心在左半幅。"""
    d = Path(__file__).resolve().parent / "data"
    cfg = json.loads((d / "globe_handedness.lumice.json").read_text())
    r = cfg["render"][0]
    assert r["lens"]["type"] == "globe" and r["view"] == {"azimuth": 210.0, "elevation": -20.0}
    lon = r["grid"]["longitude"][0]["value"]
    lat = r["grid"]["elevation"][0]["value"]
    assert lon == 30 + 40 and lat == 20 + 25
    img = np.asarray(Image.open(d / "globe_handedness.png").convert("L"), float)
    assert img.shape == tuple(r["resolution"][::-1])

    def lit_fraction(pts) -> float:
        uv = project_globe(pts, r)
        hits = []
        for u, v in uv:
            if np.isnan(u) or not (2 < u < img.shape[1] - 3 and 2 < v < img.shape[0] - 3):
                continue
            i, j = int(np.floor(v)), int(np.floor(u))
            hits.append(img[i - 2:i + 3, j - 2:j + 3].max() >= 128)
        assert len(hits) > 30
        return float(np.mean(hits))

    assert lit_fraction([sky(e, lon) for e in np.linspace(-60, 89, 300)]) >= 0.99
    assert lit_fraction([sky(e, 30 - 40) for e in np.linspace(-60, 89, 300)]) < 0.1
    assert lit_fraction([sky(lat, a) for a in np.linspace(0, 360, 721)]) >= 0.99
    assert lit_fraction([sky(20 - 25, a) for a in np.linspace(0, 360, 721)]) < 0.1
    ys, xs = np.nonzero(img >= 128)
    assert xs.mean() < img.shape[1] / 2 and ys.mean() < img.shape[0] / 2     # az 70 经线在左、el 45 纬圈在上


def test_rectangular_projection_and_its_inverse():
    """全天等距柱状图（view 默认）：u = (az/360 + ½)·W（+az 向右）、v = (½ − el/180)·H；像素中心方向 ↔ 像素坐标互逆；
    立体角权重 = cos(lat)。"""
    r = {"lens": {"type": "rectangular", "fov": 180}, "resolution": [720, 360], "view": {"azimuth": 0, "elevation": 0}}
    assert np.allclose(project_rectangular(sky(10, 0), r), [[360, 160]])
    assert np.allclose(project_rectangular(sky(0, 90), r), [[540, 180]])
    assert np.allclose(project_rectangular(sky(-45, 180), r), [[0, 270]]) or np.allclose(project_rectangular(sky(-45, 180), r), [[720, 270]])
    dirs, wgt = rectangular_pixel_directions(r)
    assert dirs.shape == (360, 720, 3) and wgt.shape == (360, 720)
    j, i = np.meshgrid(np.arange(720), np.arange(360))
    uv = project_rectangular(dirs.reshape(-1, 3), r)
    assert np.abs(uv - np.column_stack([j.ravel() + 0.5, i.ravel() + 0.5])).max() < 1e-9
    assert np.allclose(wgt[180, :], np.cos(np.radians(0.25))) and wgt[0, 0] < 0.01
    assert np.allclose(np.linalg.norm(dirs, axis=-1), 1.0)


def test_rectangular_pixel_directions_matches_3d_matmul_at_small_res():
    """2-D reshape 实现与原 (H, W, 3) @ R.T 逐元素一致。"""
    render = {"lens": {"type": "rectangular"}, "resolution": [96, 48], "view": {"azimuth": 30, "elevation": 20, "roll": 10}}
    d, w = rectangular_pixel_directions(render)
    w_, h_ = 96, 48
    scale = min(w_ // 2, h_) / np.pi
    j, i = np.meshgrid(np.arange(w_), np.arange(h_))
    lon, lat = (j + 0.5 - w_ / 2.0) / scale, -(i + 0.5 - h_ / 2.0) / scale
    c = np.stack([-np.cos(lat) * np.sin(lon), -np.sin(lat), np.cos(lat) * np.cos(lon)], axis=-1)
    np.testing.assert_allclose(d, c @ camera_rotation(render["view"]).T, atol=1e-14)
    np.testing.assert_allclose(w, np.cos(lat))


def test_rectangular_pixel_directions_repeated_full_size_calls_do_not_crash():
    """numpy 2.5.3 + Accelerate 下 3-D matmul 在 2880×1440 第 2–3 次调用 SIGSEGV；连调 4 次（进程崩了整个 pytest 挂）。"""
    render = {"lens": {"type": "rectangular"}, "resolution": [2880, 1440], "view": {"elevation": 30}}
    for _ in range(4):
        d, _w = rectangular_pixel_directions(render)
        assert d.shape == (1440, 2880, 3)
