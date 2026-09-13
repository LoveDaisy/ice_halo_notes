"""``halo_notes.sim.projection``：等积鱼眼正投影与 Lumice 的相机 / 镜头约定一致——公式层面自检 + 用仓里一张真实渲染图
（ch7 图 6 的 col_3，带经纬网格）逐像素比对。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from halo_notes.sim.projection import camera_rotation, pixels_per_degree, project_equal_area, view_direction

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


def test_projection_reproduces_the_grid_lumice_drew():
    """图 6 col_3 渲染图（fov 340、反日点为中心、每 30° 经纬网格）：把仰角 ±30° 圈与方位 90° / 150° 经线按本模块投影后，
    ≥ 99% 的采样点 2 px 窗内有网格亮度（≥ 40）；同一条线平移 6 px 后只剩不到一半（排除「到处都亮」的假阳性）。"""
    cfg = json.loads((CH7 / "data" / "halo_columns.col_3.lumice.json").read_text())
    r = cfg["render"][0]
    assert r["lens"]["type"] == "fisheye_equal_area"
    img = np.asarray(Image.open(CH7 / "data" / "halo_columns" / "col_3" / "img_01.png").convert("L"), float)
    assert img.shape == tuple(r["resolution"][::-1])
    # (线, 平移方向)：纬圈大致水平 → 竖直平移；经线大致竖直 → 水平平移
    lines = [([sky(30, a) for a in np.linspace(0, 360, 721)], (0.0, 6.0)),
             ([sky(-30, a) for a in np.linspace(0, 360, 721)], (0.0, 6.0)),
             ([sky(e, 90) for e in np.linspace(-89, 89, 357)], (6.0, 0.0)),
             ([sky(e, 150) for e in np.linspace(-89, 89, 357)], (6.0, 0.0))]

    def lit_fraction(uv: np.ndarray, half: int) -> float:
        hits = []
        for u, v in uv:
            if np.isnan(u) or not (half < u < img.shape[1] - half - 1 and half < v < img.shape[0] - half - 1):
                continue
            i, j = int(np.floor(v)), int(np.floor(u))
            hits.append(img[i - half:i + half + 1, j - half:j + half + 1].max() >= 40)
        assert len(hits) > 200
        return float(np.mean(hits))

    for pts, shift in lines:
        uv = project_equal_area(pts, r)
        assert lit_fraction(uv, 2) >= 0.99
        assert lit_fraction(uv + np.array(shift), 1) < 0.5


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
