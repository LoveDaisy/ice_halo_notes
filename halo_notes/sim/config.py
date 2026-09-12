"""Lumice config builder：生成 ``crystal / filter / scene / render`` 四段 dict（字段以 v4.5.1 ``doc/configuration.md`` 为准）。

只做拼装与 ID 唯一性 / 引用有效性自检，不解释语义；不支持的字段一律经 ``extra`` 透传（覆盖同名键）。
关键语义提醒（doc 原文）：

- ``axis`` 整体缺省 = 固定取向 ``zenith=azimuth=roll=0``；写了 ``axis`` 但省略 ``azimuth`` / ``roll`` = 该轴 0–360° 均匀
- ``scene.ray_num`` 是**全部波长的总数**（不是每波长各发一份）；``scattering[].prob`` 必填
- ``filter.symmetry``：``"P"`` C6 旋转、``"B"`` 水平镜面、``"D"`` 垂直镜面，任意组合，默认 ``""``
- ``raypath`` 面编号：basal = 1/2，prism = 3–8
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

Number = int | float
Dist = Number | Mapping[str, Any]

# 旧 template.json 的 6 档等权波长（420–620 nm），本仓复刻旧图沿用
LEGACY_SPECTRUM: list[dict[str, float]] = [{"wavelength": float(w), "weight": 1.0} for w in (420, 460, 500, 540, 580, 620)]


# ---------- 分布 ----------


def gauss(mean: Number, std: Number) -> dict[str, Any]:
    return {"type": "gauss", "mean": mean, "std": std}


def uniform(center: Number, width: Number) -> dict[str, Any]:
    """``mean`` / ``std`` 对 uniform 是区间中点与全宽（doc 明说不是统计均值 / 标准差）。"""
    return {"type": "uniform", "mean": center, "std": width}


def uniform_360() -> dict[str, Any]:
    return uniform(180, 360)


# ---------- crystal ----------


def prism_crystal(
    id: int,
    height: Dist = 1.0,
    *,
    axis: Mapping[str, Dist] | None = None,
    face_distance: Sequence[Dist] | None = None,
    sync_group: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """六方柱晶体；``height`` = h/a（< 1 片晶、> 1 柱晶）。``axis=None`` 表示整体省略 = 固定取向（见模块 docstring）。"""
    shape: dict[str, Any] = {"height": height}
    if face_distance is not None:
        if len(face_distance) != 6:
            raise ValueError(f"face_distance 必须 6 项，收到 {len(face_distance)} 项")
        shape["face_distance"] = list(face_distance)
    if sync_group is not None:
        shape["sync_group"] = dict(sync_group)
    out: dict[str, Any] = {"id": id, "type": "prism", "shape": shape}
    if axis is not None:
        if "zenith" not in axis:
            raise ValueError("写了 axis 就必须给 zenith（doc: axis present ⇒ zenith required）")
        out["axis"] = dict(axis)
    out.update(extra or {})
    return out


def plate_axis(zenith_std: Number = 1.0, *, roll: Dist | None = None) -> dict[str, Any]:
    """片晶取向：c 轴竖直（``zenith≈0`` 高斯），azimuth / roll 省略 = 均匀。"""
    axis: dict[str, Any] = {"zenith": gauss(0, zenith_std)}
    if roll is not None:
        axis["roll"] = roll
    return axis


def column_axis(zenith_std: Number = 1.0, *, roll: Dist | None = None) -> dict[str, Any]:
    """柱晶取向：c 轴水平（``zenith≈90`` 高斯），绕 c 轴 roll 默认均匀（省略）。"""
    axis: dict[str, Any] = {"zenith": gauss(90, zenith_std)}
    if roll is not None:
        axis["roll"] = roll
    return axis


def parry_axis(zenith_std: Number = 1.0, roll_std: Number = 1.0, roll_mean: Number = 0) -> dict[str, Any]:
    """Parry 取向：c 轴水平 + 一对棱面水平（roll 固定在 ``roll_mean`` 附近，非均匀）。

    roll 零点对应哪对棱面水平取决于 Lumice 的旋转链约定（doc/coordinate-convention.md），调用方按渲染结果核对。
    """
    return {"zenith": gauss(90, zenith_std), "roll": gauss(roll_mean, roll_std)}


def random_axis() -> dict[str, Any]:
    """完全随机取向：zenith 在球面上均匀（0–180° 均匀 + 面积 Jacobian 由 Lumice 处理），azimuth / roll 省略 = 均匀。"""
    return {"zenith": uniform(90, 180)}


# ---------- filter ----------


def none_filter(id: int) -> dict[str, Any]:
    return {"id": id, "type": "none"}


def raypath_filter(id: int, raypath: Sequence[int], symmetry: str = "", *, action: str = "filter_in") -> dict[str, Any]:
    """光路过滤器；``symmetry`` 只允许 P / B / D 的组合（大小写敏感，doc 原文大写）。"""
    bad = set(symmetry) - set("PBD")
    if bad:
        raise ValueError(f"symmetry 只能由 P/B/D 组成，收到 {symmetry!r}")
    return {"id": id, "type": "raypath", "raypath": [int(f) for f in raypath], "symmetry": symmetry, "action": action}


# ---------- scene ----------


def sun(altitude: Number, *, azimuth: Number = 0, diameter: Number = 0.5, spectrum: str | Sequence[Mapping[str, Any]] = "D65") -> dict[str, Any]:
    return {
        "type": "sun",
        "altitude": altitude,
        "azimuth": azimuth,
        "diameter": diameter,
        "spectrum": spectrum if isinstance(spectrum, str) else [dict(s) for s in spectrum],
    }


def entry(crystal: int, proportion: Number = 100, filter: int | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"crystal": crystal, "proportion": proportion}
    if filter is not None:
        out["filter"] = filter
    return out


def scene(
    light_source: Mapping[str, Any],
    total_ray_num: int | str,
    entries: Sequence[Mapping[str, Any]],
    *,
    max_hits: int = 7,
    prob: Number = 0,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """``total_ray_num`` 是全部波长的总光线数（v4.5.1 语义），整数或 ``"infinite"``。"""
    if isinstance(total_ray_num, bool) or not (isinstance(total_ray_num, int) or total_ray_num == "infinite"):
        raise TypeError(f"total_ray_num 必须是 int 或 'infinite'，收到 {total_ray_num!r}")
    out = {
        "light_source": dict(light_source),
        "ray_num": total_ray_num,
        "max_hits": max_hits,
        "scattering": [{"prob": prob, "entries": [dict(e) for e in entries]}],
    }
    out.update(extra or {})
    return out


# ---------- render ----------

LENS_TYPES = (
    "linear", "fisheye_equal_area", "fisheye_equidistant", "fisheye_stereographic", "fisheye_orthographic",
    "dual_fisheye_equal_area", "dual_fisheye_equidistant", "dual_fisheye_stereographic", "dual_fisheye_orthographic",
    "rectangular", "globe",
)


def lens(type: str, *, fov: Number | None = None, f: Number | None = None) -> dict[str, Any]:
    """镜头。v4.5.1 CLI 解析器要求 ``fov`` / ``f`` 二者必有其一（doc 写的"默认 90°"在 CLI 里实测报 MISSING_FIELD，
    2026-09-12 探针确认）；``dual_*`` / ``rectangular`` 忽略 fov（全天），这里自动补 180，``globe`` 补 doc 默认 30。"""
    if type not in LENS_TYPES:
        raise ValueError(f"未知镜头 {type!r}，可选 {LENS_TYPES}")
    out: dict[str, Any] = {"type": type}
    if fov is None and f is None:
        if type.startswith("dual_") or type == "rectangular":
            fov = 180
        elif type == "globe":
            fov = 30
        else:
            raise ValueError(f"镜头 {type!r} 必须显式给 fov 或 f（CLI 解析器不接受缺省）")
    if fov is not None:
        out["fov"] = fov
    if f is not None:
        out["f"] = f
    return out


def grid_line(value: Number, *, opacity: Number = 1.0, color: Sequence[Number] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"value": value, "opacity": opacity}
    if color is not None:
        out["color"] = list(color)
    return out


def grid(
    *,
    angular_dist: Sequence[Mapping[str, Any]] = (),
    elevation: Sequence[Mapping[str, Any]] = (),
    longitude: Sequence[Mapping[str, Any]] = (),
    horizon: bool = False,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "angular_dist": [dict(g) for g in angular_dist],
        "elevation": [dict(g) for g in elevation],
        "longitude": [dict(g) for g in longitude],
        "horizon": horizon,
    }
    out.update(extra or {})
    return out


def render_unit(
    id: int,
    lens: Mapping[str, Any],
    resolution: Sequence[int],
    *,
    view: Mapping[str, Number] | None = None,
    visible: str = "upper",
    background: Sequence[Number] | None = None,
    ray_color: Sequence[Number] | None = None,
    intensity_factor: Number = 1.0,
    ev_mode: str = "relative",
    grid: Mapping[str, Any] | None = None,
    filter_ids: Sequence[int] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if visible not in ("upper", "lower", "full"):
        raise ValueError(f"visible 只能是 upper/lower/full，收到 {visible!r}")
    if ev_mode not in ("relative", "absolute"):
        raise ValueError(f"ev_mode 只能是 relative/absolute，收到 {ev_mode!r}")
    if len(resolution) != 2:
        raise ValueError("resolution 必须是 [width, height]")
    out: dict[str, Any] = {
        "id": id,
        "lens": dict(lens),
        "resolution": [int(resolution[0]), int(resolution[1])],
        "visible": visible,
        "intensity_factor": intensity_factor,
        "ev_mode": ev_mode,
    }
    if view is not None:
        out["view"] = dict(view)
    if background is not None:
        out["background"] = list(background)
    if ray_color is not None:
        out["ray_color"] = list(ray_color)
    if grid is not None:
        out["grid"] = dict(grid)
    if filter_ids:
        out["filter"] = [int(i) for i in filter_ids]
    out.update(extra or {})
    return out


# ---------- 顶层 ----------


def _check_unique_ids(section: str, items: Sequence[Mapping[str, Any]]) -> set[int]:
    ids = [it["id"] for it in items]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError(f"{section} 段 id 重复：{sorted(dup)}")
    bad = [i for i in ids if not isinstance(i, int) or i <= 0]
    if bad:
        raise ValueError(f"{section} 段 id 必须是正整数：{bad}")
    return set(ids)


def build_config(
    crystals: Sequence[Mapping[str, Any]],
    filters: Sequence[Mapping[str, Any]],
    scene: Mapping[str, Any],
    renders: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """拼顶层四段，并自检 id 唯一、``scattering`` / ``render.filter`` 引用的 id 存在（不等 Lumice 跑起来才报错）。"""
    crystal_ids = _check_unique_ids("crystal", crystals)
    filter_ids = _check_unique_ids("filter", filters)
    _check_unique_ids("render", renders)
    for layer in scene["scattering"]:
        for e in layer["entries"]:
            if e["crystal"] not in crystal_ids:
                raise ValueError(f"scattering 引用了不存在的 crystal id {e['crystal']}")
            if "filter" in e and e["filter"] not in filter_ids:
                raise ValueError(f"scattering 引用了不存在的 filter id {e['filter']}")
    for r in renders:
        for fid in r.get("filter", []):
            if fid not in filter_ids:
                raise ValueError(f"render {r['id']} 引用了不存在的 filter id {fid}")
    return {
        "crystal": [dict(c) for c in crystals],
        "filter": [dict(f) for f in filters],
        "scene": dict(scene),
        "render": [dict(r) for r in renders],
    }
