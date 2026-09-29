"""Lumice 渲染图的正投影：天空方向 → 图片像素坐标，供在渲染图上叠加标注（7.5 的样本点 / 公式曲线）与从渲染图反推
每像素的天空方向（图 6 的帧中心选择）。

逐行对照 Lumice v4.5.1 源码（``src/core/scatter_accum.hpp::MakeCameraRotation``、
``src/core/shared/projection_shared.h::ProjectExitToPixel`` / ``FisheyeEqualAreaForward`` / ``RectangularForward``、
``src/core/lens_proj_build.hpp::ComputeLensScale``）复刻，不按文档臆测：

- 相机旋转 ``R = Rz(az) · Ry(90° − el) · Rz(−90° + roll)``（列 = 相机 x / y / z 轴在世界系里的方向，z = 视线）
- 相机系向量 ``c = Rᵀ · s``（``s`` 指向天空、即 −出射光方向）
- ``fisheye_equal_area``：``(x, y) = (c_x, c_y) / √(1 + c_z)``，画面左右取反（``xy.x = -xy.x``，"right = +az"），
  ``scale = short/2/√2/sin(fov/4)``；等价的角半径公式 ``r = (short/2) · sin(θ/2) / sin(fov/4)``（θ = 与视线的夹角）
- ``globe``（球面外视）：相机在相机系 z 轴上距离 ``D = 4`` 处看单位球，只画 ``c_z < −1/D`` 的那顶球冠（角半径
  ``acos(1/D) ≈ 75.5°``，帧中心 = −视线，即 ``(az + 180°, −el)``），``(x, y) = (−c_x, c_y) / (D + c_z)``，
  ``scale = short/2/tan(fov/2)``（同 linear）；``roll`` 在 globe 下被强制为 0
- ``rectangular``（全天等距柱状）：``lon = atan2(−c_x, c_z)``、``lat = asin(−c_y)``，``u = lon·scale + W/2``、
  ``v = −lat·scale + H/2``，``scale = min(W/2, H)/π``，``u`` 按 W 取模
- 再 ``u = x · scale + W/2``、``v = y · scale + H/2``；像素下标 = floor(u, v)，所以 ``(u, v)`` 是「像素 i 覆盖 [i, i+1)」的
  连续坐标，与 ``imshow(extent=(0, W, H, 0))`` 的数据坐标一致
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


def _rot(axis: np.ndarray, deg: float) -> np.ndarray:
    """绕 ``axis`` 转 ``deg`` 度的主动旋转矩阵（Rodrigues，同 Lumice ``Rotation::FillMat``）。"""
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return c * np.eye(3) + s * K + (1 - c) * np.outer(a, a)


def camera_rotation(view: Mapping[str, float] | None) -> np.ndarray:
    """``render.view`` → 相机旋转矩阵（列 = 相机 x / y / z 轴）；缺省字段按 Lumice 默认 0。"""
    v = dict(view or {})
    az, el, roll = float(v.get("azimuth", 0.0)), float(v.get("elevation", 0.0)), float(v.get("roll", 0.0))
    z, y = np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0])
    return _rot(z, az) @ _rot(y, 90.0 - el) @ _rot(z, -90.0 + roll)


def view_direction(view: Mapping[str, float] | None) -> np.ndarray:
    """视线（相机 z 轴）在世界系里的单位向量。"""
    return camera_rotation(view)[:, 2]


GLOBE_CAMERA_D = 4.0          # projection_shared.h::kGlobeCameraD
GLOBE_CAP_DEG = float(np.degrees(np.arccos(1.0 / GLOBE_CAMERA_D)))   # 75.5°：globe 一帧能看到的球冠角半径


def equal_area_scale(fov_deg: float, width: int, height: int) -> float:
    return min(width, height) / 2.0 / np.sqrt(2.0) / np.sin(np.radians(fov_deg) / 4.0)


def globe_scale(fov_deg: float, width: int, height: int) -> float:
    return min(width, height) / 2.0 / np.tan(np.radians(fov_deg) / 2.0)


def rectangular_scale(width: int, height: int) -> float:
    return min(width // 2, height) / np.pi


def _camera_frame(directions, render: Mapping[str, Any]) -> tuple[np.ndarray, int, int]:
    s = np.asarray(directions, float).reshape(-1, 3)
    s = s / np.linalg.norm(s, axis=1, keepdims=True)
    view = dict(render.get("view") or {})
    if render["lens"]["type"] == "globe":
        view["roll"] = 0.0                                  # doc §globe：渲染时 roll 强制为 0
    R = camera_rotation(view)
    return s @ R, int(render["resolution"][0]), int(render["resolution"][1])       # (Rᵀ s)ᵀ


def project_equal_area(directions, render: Mapping[str, Any]) -> np.ndarray:
    """天空方向（(N,3) 或 (3,)，指向天空的单位向量）→ 连续像素坐标 (N,2)。``render`` 是一个 render 段
    （``lens.type`` 必须是 ``fisheye_equal_area``，``fov`` 必填；``resolution``、``view``、可选 ``lens_shift``）。
    视线反方向附近（c_z ≤ −1 + 1e-6）Lumice 判为 miss，这里返回 NaN。"""
    if render["lens"]["type"] != "fisheye_equal_area":
        raise ValueError(f"project_equal_area 只接受 fisheye_equal_area，收到 {render['lens']['type']!r}")
    c, w, h = _camera_frame(directions, render)
    scale = equal_area_scale(float(render["lens"]["fov"]), w, h)
    cz = c[:, 2]
    miss = cz < -1.0 + 1e-6
    k = 1.0 / np.sqrt(1.0 + np.clip(cz, -1.0 + 1e-6, 1.0))
    x, y = -k * c[:, 0], k * c[:, 1]
    shift = render.get("lens_shift", (0, 0))
    uv = np.column_stack([x * scale + w / 2.0 + float(shift[0]), y * scale + h / 2.0 + float(shift[1])])
    uv[miss] = np.nan
    return uv


def project_globe(directions, render: Mapping[str, Any]) -> np.ndarray:
    """``globe`` 镜头：只有 ``c_z < −1/D`` 的球冠可见（其余 NaN）；``(x, y) = (−c_x, c_y)/(D + c_z)``、``scale`` 同 linear。"""
    if render["lens"]["type"] != "globe":
        raise ValueError(f"project_globe 只接受 globe，收到 {render['lens']['type']!r}")
    c, w, h = _camera_frame(directions, render)
    scale = globe_scale(float(render["lens"].get("fov", 30.0)), w, h)
    cz = c[:, 2]
    miss = cz >= -1.0 / GLOBE_CAMERA_D
    denom = GLOBE_CAMERA_D + cz
    shift = render.get("lens_shift", (0, 0))
    uv = np.column_stack([-c[:, 0] / denom * scale + w / 2.0 + float(shift[0]),
                          c[:, 1] / denom * scale + h / 2.0 + float(shift[1])])
    uv[miss] = np.nan
    return uv


def project_rectangular(directions, render: Mapping[str, Any]) -> np.ndarray:
    """``rectangular`` 全天图：``lon = atan2(−c_x, c_z)``、``lat = asin(−c_y)``；u 按宽度取模（lon = +π 折回第 0 列）。"""
    if render["lens"]["type"] != "rectangular":
        raise ValueError(f"project_rectangular 只接受 rectangular，收到 {render['lens']['type']!r}")
    c, w, h = _camera_frame(directions, render)
    scale = rectangular_scale(w, h)
    lon = np.arctan2(-c[:, 0], c[:, 2])
    lat = np.arcsin(np.clip(-c[:, 1], -1.0, 1.0))
    u = np.mod(lon * scale + w / 2.0, w)
    v = -lat * scale + h / 2.0
    return np.column_stack([u, v])


def rectangular_pixel_directions(render: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """``rectangular`` 图每个像素中心对应的天空方向 (H, W, 3) 与它的立体角权重 cos(lat) (H, W)——
    :func:`project_rectangular` 的逆（像素中心 ``(j + ½, i + ½)``）。"""
    w, h = int(render["resolution"][0]), int(render["resolution"][1])
    scale = rectangular_scale(w, h)
    j, i = np.meshgrid(np.arange(w), np.arange(h))
    lon = (j + 0.5 - w / 2.0) / scale
    lat = -(i + 0.5 - h / 2.0) / scale
    view = dict(render.get("view") or {})
    R = camera_rotation(view)
    # c = (c_x, c_y, c_z)：lon = atan2(−c_x, c_z)、lat = asin(−c_y)
    c = np.stack([-np.cos(lat) * np.sin(lon), -np.sin(lat), np.cos(lat) * np.cos(lon)], axis=-1)
    # 2-D matmul：3-D (H, W, 3) @ (3, 3) 在 numpy 2.5.3 + Accelerate 下 2880×1440 第 2–3 次调用 SIGSEGV
    return (c.reshape(-1, 3) @ R.T).reshape(c.shape), np.cos(lat)


PROJECTORS = {"fisheye_equal_area": project_equal_area, "globe": project_globe, "rectangular": project_rectangular}


def project(directions, render: Mapping[str, Any]) -> np.ndarray:
    """按 ``render.lens.type`` 分派到对应正投影（本仓用到的三种镜头）。"""
    t = render["lens"]["type"]
    if t not in PROJECTORS:
        raise ValueError(f"未实现 {t!r} 的正投影，可选 {sorted(PROJECTORS)}")
    return PROJECTORS[t](directions, render)


def frame_center(render: Mapping[str, Any]) -> np.ndarray:
    """帧中心对应的天空方向：单镜头 = 视线；globe = −视线（doc §globe：``(az + 180°, −el)``）。"""
    z = view_direction(render.get("view"))
    return -z if render["lens"]["type"] == "globe" else z


def globe_view_for(center) -> dict[str, float]:
    """让 globe 帧中心落在天空方向 ``center`` 的 ``render.view``：``azimuth = az + 180°``、``elevation = −el``。"""
    s = np.asarray(center, float)
    s = s / np.linalg.norm(s)
    az = float(np.degrees(np.arctan2(s[1], s[0]))) % 360.0
    el = float(np.degrees(np.arcsin(np.clip(s[2], -1.0, 1.0))))
    return {"azimuth": round((az + 180.0) % 360.0, 6), "elevation": round(-el, 6)}     # 六位小数：config 落盘干净


def pixels_per_degree(direction, render: Mapping[str, Any], eps_deg: float = 0.05) -> float:
    """``direction`` 处 1° 对应多少像素（沿离开视线的方向数值微分），供把角度容差换算成像素。"""
    s = np.asarray(direction, float)
    s = s / np.linalg.norm(s)
    z = frame_center(render)
    r = s - (s @ z) * z                            # s 的径向分量：s = cosθ·z + sinθ·r̂
    if np.linalg.norm(r) < 1e-9:                   # 正对视线：任取一个垂直方向
        r = np.cross(z, [1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.cross(z, [0.0, 1.0, 0.0])
    r /= np.linalg.norm(r)
    t = -(np.sqrt(max(1.0 - (s @ z) ** 2, 0.0))) * z + (s @ z) * r    # dθ 方向：−sinθ·z + cosθ·r̂
    t /= np.linalg.norm(t)
    step = np.cos(np.radians(eps_deg)) * s + np.sin(np.radians(eps_deg)) * t
    a, b = project([s, step], render)
    return float(np.linalg.norm(b - a) / eps_deg)
