"""Lumice 渲染图的正投影：天空方向 → 图片像素坐标，供在渲染图上叠加标注（7.5 的样本点 / 公式曲线）。

逐行对照 Lumice v4.5.1 源码（``src/core/scatter_accum.hpp::MakeCameraRotation``、
``src/core/shared/projection_shared.h::ProjectExitToPixel`` / ``FisheyeEqualAreaForward``、
``src/core/lens_proj_build.hpp::ComputeLensScale``）复刻，不按文档臆测：

- 相机旋转 ``R = Rz(az) · Ry(90° − el) · Rz(−90° + roll)``（列 = 相机 x / y / z 轴在世界系里的方向，z = 视线）
- 相机系向量 ``c = Rᵀ · s``（``s`` 指向天空、即 −出射光方向）；等积鱼眼 ``(x, y) = (c_x, c_y) / √(1 + c_z)``
- 画面左右取反（``xy.x = -xy.x``，"right = +az"），再 ``u = x · scale + W/2``、``v = y · scale + H/2``，
  ``scale = short/2/√2/sin(fov/4)``；像素下标 = floor(u, v)，所以 ``(u, v)`` 是「像素 i 覆盖 [i, i+1)」的连续坐标，
  与 ``imshow(extent=(0, W, H, 0))`` 的数据坐标一致

等价的角半径公式：``r = (short/2) · sin(θ/2) / sin(fov/4)``（θ = 与视线的夹角）。只实现本仓用到的 ``fisheye_equal_area``。
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


def equal_area_scale(fov_deg: float, width: int, height: int) -> float:
    return min(width, height) / 2.0 / np.sqrt(2.0) / np.sin(np.radians(fov_deg) / 4.0)


def project_equal_area(directions, render: Mapping[str, Any]) -> np.ndarray:
    """天空方向（(N,3) 或 (3,)，指向天空的单位向量）→ 连续像素坐标 (N,2)。``render`` 是一个 render 段
    （``lens.type`` 必须是 ``fisheye_equal_area``，``fov`` 必填；``resolution``、``view``、可选 ``lens_shift``）。
    视线反方向附近（c_z ≤ −1 + 1e-6）Lumice 判为 miss，这里返回 NaN。"""
    if render["lens"]["type"] != "fisheye_equal_area":
        raise ValueError(f"只实现了 fisheye_equal_area，收到 {render['lens']['type']!r}")
    s = np.asarray(directions, float).reshape(-1, 3)
    s = s / np.linalg.norm(s, axis=1, keepdims=True)
    R = camera_rotation(render.get("view"))
    c = s @ R                      # = (Rᵀ s)ᵀ
    w, h = int(render["resolution"][0]), int(render["resolution"][1])
    scale = equal_area_scale(float(render["lens"]["fov"]), w, h)
    cz = c[:, 2]
    miss = cz < -1.0 + 1e-6
    k = 1.0 / np.sqrt(1.0 + np.clip(cz, -1.0 + 1e-6, 1.0))
    x, y = -k * c[:, 0], k * c[:, 1]
    shift = render.get("lens_shift", (0, 0))
    uv = np.column_stack([x * scale + w / 2.0 + float(shift[0]), y * scale + h / 2.0 + float(shift[1])])
    uv[miss] = np.nan
    return uv


def pixels_per_degree(direction, render: Mapping[str, Any], eps_deg: float = 0.05) -> float:
    """``direction`` 处 1° 对应多少像素（沿离开视线的方向数值微分），供把角度容差换算成像素。"""
    s = np.asarray(direction, float)
    s = s / np.linalg.norm(s)
    z = view_direction(render.get("view"))
    r = s - (s @ z) * z                            # s 的径向分量：s = cosθ·z + sinθ·r̂
    if np.linalg.norm(r) < 1e-9:                   # 正对视线：任取一个垂直方向
        r = np.cross(z, [1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.cross(z, [0.0, 1.0, 0.0])
    r /= np.linalg.norm(r)
    t = -(np.sqrt(max(1.0 - (s @ z) ** 2, 0.0))) * z + (s @ z) * r    # dθ 方向：−sinθ·z + cosθ·r̂
    t /= np.linalg.norm(t)
    step = np.cos(np.radians(eps_deg)) * s + np.sin(np.radians(eps_deg)) * t
    a, b = project_equal_area([s, step], render)
    return float(np.linalg.norm(b - a) / eps_deg)
