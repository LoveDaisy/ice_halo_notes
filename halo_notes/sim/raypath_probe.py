"""单光路固定取向渲染探针：Lumice ``raypath`` 过滤 + ``rectangular`` 全天图的亮斑方向 vs 本仓几何（``phi``）预测的出射方向。

用途：取证 Lumice 的面编号 / 手性 / 旋转链与 :mod:`lumice_integral.geometry` 的多面体逐面一致（锥晶 fixture
``tests/data/pyramid_raypath_fixture.json`` 由 ``python -m halo_notes.sim.raypath_probe --write`` 生成）。链路只复用已验证模块
（``phi`` / ``projection`` / ``raypath_filter``），不另写一份光路追迹。

坐标约定（Lumice ``doc/coordinate-convention.md`` §4 / §6，``src/core/simulator.cpp:198,231-238``）：

- 太阳位置 ``s = (cos alt·cos az, cos alt·sin az, sin alt)``，光线传播方向 ``d = −s``（``SampleSphCapPoint(az+180, −alt)``）
- 晶体局部系 → 世界系 ``R = Rz(azimuth − 180°)·Ry(−zenith)·Rz(roll)``：``axis`` **整体省略**（"固定取向 0/0/0"）实际是
  ``R = Rz(−180°)``，晶体绕 c 轴转了半圈（局部面 3 朝世界 −x）；要让世界系 = 局部系（本仓 ``Pyramid`` / ``HexPrism`` 的生成姿态，
  面 3 法向 +x）须显式写 :data:`IDENTITY_AXIS`。两种写法都进 fixture 钉住
- 天空方向 = −出射传播方向；``rectangular`` 图每像素的天空方向由 :func:`~.projection.rectangular_pixel_directions` 给出
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image

from lumice_integral.geometry import Polyhedron, fold_matrix
from lumice_integral.geometry.feasibility import area_eps, corridor_polygons, geometric_ok
from ..math.signature import phi
from . import config as C
from .projection import rectangular_pixel_directions
from .run import RenderResult, render

IDENTITY_AXIS: dict[str, float] = {"zenith": 0, "azimuth": 180, "roll": 0}
"""让 Lumice 晶体旋转矩阵为单位阵的 ``axis``（``Rz(180 − 180°) = I``）；bare number = 固定值（doc §Value Range Validation）。"""

SPOT_THRESHOLD = 0.2
"""亮斑像素阈：≥ 峰值 × 该比例的像素进质心（8-bit 图，太阳视直径 0.2° 的斑只占几个像素）。"""


# ---------- 几何侧 ----------


def sun_direction(altitude: float, azimuth: float = 0.0) -> np.ndarray:
    """太阳 ``(altitude, azimuth)`` → 光线传播方向 ``d = −s``（单位向量，指向观察者）。"""
    a, b = np.radians(altitude), np.radians(azimuth)
    return -np.array([np.cos(a) * np.cos(b), np.cos(a) * np.sin(b), np.sin(a)])


def az_el(direction) -> tuple[float, float]:
    """单位向量 → ``(方位角, 仰角)``（度），方位角 ``(−180, 180]``。"""
    s = np.asarray(direction, float)
    s = s / np.linalg.norm(s)
    return float(np.degrees(np.arctan2(s[1], s[0]))), float(np.degrees(np.arcsin(np.clip(s[2], -1.0, 1.0))))


def predicted_sky(crystal: Polyhedron, faces: Sequence[int], d) -> np.ndarray | None:
    """面序列 ``faces`` 在传播方向 ``d`` 下的出射**天空方向**（−Φ(d)）；光学定义域外（``phi`` 为 None）或几何走廊不通
    （``geometric_ok``）返回 ``None``。"""
    faces = [int(f) for f in faces]
    d = np.asarray(d, float).reshape(3)
    o = phi(crystal, fold_matrix(crystal, faces), faces[0], faces[-1], d)
    if o is None:
        return None
    polys, _ = corridor_polygons(crystal, faces)
    if not geometric_ok(polys, d.reshape(1, 3), area_eps(crystal))[0]:
        return None
    return -o / np.linalg.norm(o)


def rotate_z(deg: float) -> np.ndarray:
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


# ---------- Lumice 侧 ----------


def probe_config(crystal: Mapping[str, Any], faces: Sequence[int], *, sun_altitude: float, sun_azimuth: float = 0.0,
                 rays: int = 1_000_000, resolution: Sequence[int] = (1440, 720), sun_diameter: float = 0.2,
                 wavelength: float = 550.0) -> dict[str, Any]:
    """一个晶体、一条光路：``raypath`` 过滤器（``symmetry=""``）挂在 scattering entry 上，一个 ``rectangular`` 全天 render
    （``visible=full``）。过滤器只能挂在 entry 上（``render[].filter`` 是多次散射层选择，不是光路过滤，v4.5.1 doc §render），
    所以一条光路一份 config、一次 Lumice。单波长 + 小日面让光路在图上只留一个几像素的亮斑。"""
    flt = C.raypath_filter(1, faces)
    rend = C.render_unit(1, C.lens("rectangular"), list(resolution), visible="full")
    light = C.sun(sun_altitude, azimuth=sun_azimuth, diameter=sun_diameter,
                  spectrum=[{"wavelength": float(wavelength), "weight": 1.0}])
    sc = C.scene(light, int(rays), [C.entry(crystal["id"], filter=1)], max_hits=len(faces) + 1)
    return C.build_config([crystal], [flt], sc, [rend])


def spot_direction(image: Path | str | Image.Image, render_unit: Mapping[str, Any],
                   threshold: float = SPOT_THRESHOLD) -> tuple[np.ndarray | None, int, float]:
    """渲染图里亮斑的天空方向：≥ ``峰值 × threshold`` 的像素按亮度加权求方向质心（单位向量平均，绕过 ±180° 折回）。
    返回 ``(方向 | None, 参与像素数, 峰值/255)``；全黑图给 ``None``。"""
    img = image if isinstance(image, Image.Image) else Image.open(image)
    lum = np.asarray(img.convert("L"), float)
    peak = float(lum.max())
    if peak <= 0:
        return None, 0, 0.0
    mask = lum >= peak * threshold
    dirs, _ = rectangular_pixel_directions(render_unit)
    w = lum[mask]
    v = (dirs[mask] * w[:, None]).sum(axis=0)
    return v / np.linalg.norm(v), int(mask.sum()), peak / 255.0


def run_probe(config: Mapping[str, Any], out_dir: Path | str, *, bin: Path | None = None, workers: int | None = None) -> RenderResult:
    return render(config, out_dir, bin=bin, workers=workers)


def spot_of(result: RenderResult, config: Mapping[str, Any]) -> dict[str, Any]:
    """一次 :func:`probe_config` 渲染的亮斑：``{"faces", "sky", "az_el", "n_pixels", "peak"}``（``sky`` 为 None 表示没渲染出亮斑）。"""
    faces = config["filter"][0]["raypath"]
    sky, n, peak = spot_direction(result.images[0], config["render"][0])
    return {"faces": faces, "sky": None if sky is None else [round(float(x), 6) for x in sky],
            "az_el": None if sky is None else [round(x, 3) for x in az_el(sky)], "n_pixels": n, "peak": round(peak, 3)}


def angle_deg(u, v) -> float:
    u, v = np.asarray(u, float), np.asarray(v, float)
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1.0, 1.0))))


# ---------- 锥晶 fixture ----------

PYRAMID_SUN = {"altitude": 35.0, "azimuth": 10.0}
"""固定取向锥晶下同时让上锥 / 下锥 / 侧面 / 左右手性光路都可行的太阳位置（2026-09-20 用 :func:`predicted_sky` 扫两面光路选定）。"""

PYRAMID_PATHS: tuple[tuple[int, ...], ...] = ((13, 26), (14, 6), (18, 6), (3, 27), (13, 27), (4, 6))
"""``IDENTITY_AXIS`` 下的取证光路：``13-26`` 上锥进下锥出（平行面，直穿）、``14-6`` / ``18-6`` 关于太阳所在竖直面互为镜像
（手性判据：两条都可行、落点不同）、``3-27`` 侧面进下锥出、``13-27`` 上锥进下锥出（非平行）、``4-6`` 纯棱柱对照。"""

PYRAMID_PATHS_AXIS_OMITTED: tuple[tuple[int, ...], ...] = ((16, 23), (17, 3), (15, 3))
"""``axis`` 省略（``R = Rz(−180°)``）下选的光路：晶体转了半圈，能走通的是面号 +3（mod 6）的那批，落点应与单位姿态下的
``13-26`` / ``14-6`` / ``18-6`` 重合。"""

FIXTURE_TOL_DEG = 0.5
"""容差：``rectangular`` 1440×720 ⇒ 0.25°/px，取 2 px；日面 0.2° 的亮斑质心误差远小于此。"""


def pyramid_fixture_configs(rays: int = 1_000_000) -> dict[str, list[dict[str, Any]]]:
    """两组 config（一条光路一份）：``identity``（显式 :data:`IDENTITY_AXIS`）与 ``omitted``（axis 省略）。"""
    from lumice_integral.geometry import Pyramid

    pyr = Pyramid()
    ident = C.pyramid_crystal_from_geometry(1, pyr, axis=IDENTITY_AXIS)
    omitted = C.pyramid_crystal_from_geometry(1, pyr)
    return {
        "identity": [probe_config(ident, faces, rays=rays, **_sun_kw()) for faces in PYRAMID_PATHS],
        "omitted": [probe_config(omitted, faces, rays=rays, **_sun_kw()) for faces in PYRAMID_PATHS_AXIS_OMITTED],
    }


def _sun_kw() -> dict[str, float]:
    return {"sun_altitude": PYRAMID_SUN["altitude"], "sun_azimuth": PYRAMID_SUN["azimuth"]}


def mirror_face(face: int) -> int:
    """关于 xz 平面（面 3 / 6 法向所在竖直面）的镜像面号：3、6、13、16、23、26 与底面不动，其余 ``i ↔ −i (mod 6)``。"""
    if face in (1, 2):
        return face
    base = 3 if face < 10 else (13 if face < 20 else 23)
    return base + (-(face - base)) % 6


ALT_C_OVER_A = C.LUMICE_ICE_C * 2 / 3
"""反假设之一：``upper_indices=[2,0,3]`` 的锥面（楔角 38.6°），用来证明 fixture 能分辨 ``[1,0,1]`` 与别的 Miller 指数。"""


def pyramid_predictions() -> dict[str, list[dict[str, Any]]]:
    """LI 侧预测：``identity`` 按 :data:`PYRAMID_PATHS` 直接算；``omitted`` 面号不变（面号跟着晶体转），晶体姿态是
    ``R = Rz(180°)``：局部入射方向 ``Rᵀd``，局部预测再乘 ``R`` 回世界系。按 C6 对称，``17-3`` 在 ``R`` 下的落点 = ``14-6`` 在
    单位姿态下的落点，所以两份 config 的预测数值成对相同——这正是"省略 axis = 转半圈"这条旋转链事实的判据。"""
    from lumice_integral.geometry import Pyramid

    pyr = Pyramid()
    d = sun_direction(**PYRAMID_SUN)
    out: dict[str, list[dict[str, Any]]] = {"identity": [], "omitted": []}
    alt_pyr = Pyramid(c_over_a=ALT_C_OVER_A)
    for faces in PYRAMID_PATHS:
        sky = predicted_sky(pyr, faces, d)
        row = {"faces": list(faces), "sky": None if sky is None else [round(float(x), 6) for x in sky],
               "az_el": None if sky is None else [round(x, 3) for x in az_el(sky)]}
        # 反假设落点（None = 该反假设下光路不可行，同样是可分辨的证据）
        alt_cone = predicted_sky(alt_pyr, faces, d)
        alt_mirror = predicted_sky(pyr, [mirror_face(f) for f in faces], d)
        row["alt_cone_az_el"] = None if alt_cone is None else [round(x, 3) for x in az_el(alt_cone)]
        row["alt_mirror_az_el"] = None if alt_mirror is None else [round(x, 3) for x in az_el(alt_mirror)]
        out["identity"].append(row)
    R = rotate_z(180.0)
    for faces in PYRAMID_PATHS_AXIS_OMITTED:
        sky = predicted_sky(pyr, faces, R.T @ d)
        sky_w = None if sky is None else R @ sky
        out["omitted"].append({"faces": list(faces), "sky": None if sky_w is None else [round(float(x), 6) for x in sky_w],
                               "az_el": None if sky_w is None else [round(x, 3) for x in az_el(sky_w)]})
    return out


def build_pyramid_fixture(out_root: Path, *, bin: Path | None = None, rays: int = 1_000_000) -> dict[str, Any]:
    """跑两份 config，把 Lumice 亮斑与几何预测逐条并排落成 fixture dict（含 provenance）。"""
    configs = pyramid_fixture_configs(rays)
    preds = pyramid_predictions()
    fixture: dict[str, Any] = {"sun": dict(PYRAMID_SUN), "tol_deg": FIXTURE_TOL_DEG, "runs": {}}
    for key, cfgs in configs.items():
        spots: list[dict[str, Any]] = []
        shas: list[str] = []
        for cfg in cfgs:
            faces = "-".join(map(str, cfg["filter"][0]["raypath"]))
            res = run_probe(cfg, Path(out_root) / key / faces, bin=bin)
            spots.append(spot_of(res, cfg))
            shas.append(res.provenance["config_sha256"])
        rows = []
        for spot, pred in zip(spots, preds[key], strict=True):
            assert spot["faces"] == pred["faces"]
            row = {**pred, "lumice_sky": spot["sky"], "lumice_az_el": spot["az_el"], "n_pixels": spot["n_pixels"], "peak": spot["peak"]}
            row["diff_deg"] = None if (spot["sky"] is None or pred["sky"] is None) else round(angle_deg(spot["sky"], pred["sky"]), 4)
            rows.append(row)
        fixture["runs"][key] = {
            "axis": cfgs[0]["crystal"][0].get("axis"),
            "config_sha256": shas,
            "lumice_bin_sha256": res.provenance["lumice_bin_sha256"],
            "lumice_version": None if bin is not None or os.environ.get("LUMICE_BIN") else res.provenance["lumice_version"],
            "rows": rows,
        }
    return fixture


def main(argv: Sequence[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="生成 / 打印锥晶面编号 fixture（真跑 Lumice）")
    p.add_argument("--write", type=Path, default=None, help="fixture JSON 输出路径")
    p.add_argument("--out", type=Path, default=None, help="Lumice 原始输出目录（默认临时目录）")
    p.add_argument("--rays", type=int, default=1_000_000)
    a = p.parse_args(argv)
    import tempfile

    out = a.out or Path(tempfile.mkdtemp(prefix="pyramid-probe-"))
    bin_env = os.environ.get("LUMICE_BIN")
    fx = build_pyramid_fixture(out, bin=Path(bin_env) if bin_env else None, rays=a.rays)
    for key, run in fx["runs"].items():
        print(f"[{key}] axis={run['axis']} bin={run['lumice_bin_sha256'][:12]}")
        for r in run["rows"]:
            print(f"  {'-'.join(map(str, r['faces'])):>6}: LI {r['az_el']}  Lumice {r['lumice_az_el']}  "
                  f"diff={r['diff_deg']}°  px={r['n_pixels']} peak={r['peak']}")
    if a.write:
        a.write.write_text(json.dumps(fx, indent=2, ensure_ascii=False) + "\n")
        print("→", a.write)
    print("raw:", out)


if __name__ == "__main__":
    main()
