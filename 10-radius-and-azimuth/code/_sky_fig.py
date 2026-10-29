# ch10 图 1/7 的 Lumice 配置、线性能量读取与全天证据；不改动已有地形图。
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim.fetch import LUMICE_VERSION, cached_binary, ensure_lumice, sha256_of
from halo_notes.sim.projection import rectangular_pixel_directions
from halo_notes.sim.raypath_probe import probe_config, sun_direction
from halo_notes.sim.run import config_sha256, render

CHAPTER = Path(__file__).resolve().parents[1]
DATA = CHAPTER / "data"
IMG = CHAPTER / "img"
FAMILIES = ("random", "column", "plate")
HEIGHTS = (0, 20, 40, 60)
PRISM_HEIGHT = 3.0  # 固定形状，只比较取向；避免片晶族的 3-5 被底面截断。
WAVELENGTH = 580.0
SUN_DIAMETER = 0.2  # 正式图的有限日面让理想片晶的细线可见；探针另用 0.02°。
PROBE_SUN_DIAMETER = 0.02
RAYS = 20_000_000
PROBE_RAYS = 500_000
RES = (1440, 720)
DISPLAY_RES = (800, 800)
FOV = 110.0


def build(family, altitude, *, rays=RAYS, symmetry="PBD", probe=False):
    """两种投影共用同一批光线：全天 rectangular 取证，太阳中心等面积图显示。

    PBD 为同一 3-5 光路的晶体对称像，不混入底面反射或 Parry 族。
    strict probe 可设 symmetry=''；它只取带编号的单条 3-5。
    """
    axes = {"plate": {"zenith": 0}, "column": {"zenith": 90}, "random": C.random_axis()}
    crystal = C.prism_crystal(1, PRISM_HEIGHT, axis=axes[family])
    cfg = probe_config(crystal, [3, 5], sun_altitude=altitude, rays=rays,
                       resolution=RES, sun_diameter=PROBE_SUN_DIAMETER if probe else SUN_DIAMETER,
                       wavelength=WAVELENGTH)
    cfg["filter"][0]["symmetry"] = symmetry
    if not probe:
        cfg["render"].append(C.render_unit(
            2, C.lens("fisheye_equal_area", fov=FOV), DISPLAY_RES,
            view={"azimuth": 0, "elevation": altitude}, visible="full"))
    return cfg


def release_binary():
    # ensure_lumice 的环境变量优先规则不能把本地 build 静默当 release。
    if os.environ.get("LUMICE_BIN"):
        raise RuntimeError("正式图/探针须用 release；请 unset LUMICE_BIN 后重跑")
    binary = ensure_lumice()
    if binary.resolve() != cached_binary().resolve():
        raise RuntimeError("未使用版本钉住的 release 缓存")
    return binary


def name(family, altitude, *, probe=False, strict=False):
    return f"sky_{'probe_' if probe else ''}{family}_{altitude:g}" + ("_strict" if strict else "")


def run_scene(family, altitude, *, rays=RAYS, probe=False, strict=False):
    stem = name(family, altitude, probe=probe, strict=strict)
    cfg = build(family, altitude, rays=rays, symmetry="" if strict else "PBD", probe=probe)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"{stem}.lumice.json").write_text(json.dumps(cfg, indent=2) + "\n")
    result = render(cfg, DATA / stem, fmt="npy", workers=4, bin=release_binary(), timeout=300)
    record = measure_scene(result.out_dir)
    (result.out_dir / "measurements.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"{stem}: {result.wall_clock_s:.2f}s, {record['lit_pixels']} lit, "
          f"D={record['min_deg']}..{record['max_deg']}, E(D>50)/E={record['fraction_above_50']:.6g}", flush=True)
    return record


def load_scene(folder, index=1):
    folder = Path(folder)
    cfg = json.loads((folder / "config.json").read_text())
    provenance = json.loads((folder / "provenance.json").read_text())
    if config_sha256(cfg) != provenance["config_sha256"]:
        raise ValueError(f"config/provenance 不一致：{folder}")
    side = json.loads((folder / f"img_{index:02d}.json").read_text())
    if (side.get("channels") != "XYZ" or side.get("normalization") != "raw"
            or side.get("sim_ray_num") != cfg["scene"]["ray_num"]):
        raise ValueError("sidecar 不是实际配置对应的 raw XYZ")
    xyz = np.load(folder / f"img_{index:02d}.npy")
    if xyz.shape != (*reversed(cfg["render"][index - 1]["resolution"]), 3):
        raise ValueError("线性输出形状与配置不一致")
    if not np.isfinite(xyz).all() or (xyz < 0).any() or side["emitted_energy"] <= 0:
        raise ValueError("无效线性 XYZ / emitted_energy")
    return xyz[..., 1].astype(float) / side["emitted_energy"], cfg, provenance


def angular_data(cfg):
    directions, _ = rectangular_pixel_directions(cfg["render"][0])
    altitude = cfg["scene"]["light_source"]["altitude"]
    sun = -sun_direction(altitude)
    # 显式逐分量求点积，避免 Accelerate 大数组 matmul 的已知崩溃。
    d = np.degrees(np.arccos(np.clip(np.sum(directions * sun, axis=-1), -1, 1)))
    h = np.radians(altitude)
    up = np.array([-np.sin(h), 0, np.cos(h)])
    east = np.array([0, 1, 0])
    pa = np.degrees(np.arctan2(np.sum(directions * east, axis=-1),
                               np.sum(directions * up, axis=-1))) % 360
    return d, pa, directions


def measure_scene(folder):
    """用 raw Y>0 统计非零能量，不使用可见性阈值；像素能量不再乘 cos(lat)。"""
    folder = Path(folder)
    energy, cfg, prov = load_scene(folder)
    d, pa, directions = angular_data(cfg)
    lit = energy > 0
    total = float(energy.sum())
    result = {
        "config_sha256": config_sha256(cfg), "lumice_version": prov["lumice_version"],
        "lumice_bin_sha256": prov["lumice_bin_sha256"], "wall_clock_s": prov["wall_clock_s"],
        "raw_sha256": sha256_of(folder / "img_01.npy"),
        "criterion": "raw linear XYZ Y > 0; no exposure, no visibility cutoff",
        "lit_pixels": int(lit.sum()), "total_Y_per_emitted_energy": total,
        "min_deg": float(d[lit].min()) if lit.any() else None,
        "max_deg": float(d[lit].max()) if lit.any() else None,
        "pixels_above_50": int((lit & (d > 50)).sum()),
        "fraction_above_50": float(energy[d > 50].sum() / total) if total else 0.0,
        "fraction_above_55": float(energy[d > 55].sum() / total) if total else 0.0,
        "radial_bins": [], "rings": [],
    }
    for lo, hi in zip((0, 21, 22, 25, 30, 40, 50, 55, 60), (21, 22, 25, 30, 40, 50, 55, 60, 180)):
        mask = (d >= lo) & (d < hi)
        result["radial_bins"].append({"lo": lo, "hi": hi, "lit_pixels": int((mask & lit).sum()),
                                     "fraction": float(energy[mask].sum() / total) if total else 0.0})
    # 一条圆的像素化实测：±0.3° 环带、5° 位置角桶，完整保留各桶能量，不能据投影画满整圈。
    for radius in (22, 25, 30, 40, 50, 55):
        mask = np.abs(d - radius) <= 0.3
        hist, _ = np.histogram(pa[mask], bins=np.arange(0, 361, 5), weights=energy[mask])
        result["rings"].append({"radius_deg": radius, "half_width_deg": 0.3,
                                "position_angle_bin_deg": 5,
                                "bin_Y_per_emitted_energy": hist.tolist()})
    if lit.any():
        k = int(np.argmax(np.where(lit, d, -1)))
        v = directions.reshape(-1, 3)[k]
        result["outermost_pixel"] = {"row_col": list(map(int, np.unravel_index(k, d.shape))),
                                     "azimuth_deg": float(np.degrees(np.arctan2(v[1], v[0]))),
                                     "elevation_deg": float(np.degrees(np.arcsin(v[2]))),
                                     "Y_per_emitted_energy": float(energy.flat[k])}
    return result


def run_probe():
    rows = {}
    for altitude in HEIGHTS:
        for family in FAMILIES:
            key = name(family, altitude, probe=True)
            rows[key] = run_scene(family, altitude, rays=PROBE_RAYS, probe=True)
    # 高于片晶临界高度的负对照；严格路径复核图7，独立于对称像。
    rows[name("plate", 65, probe=True)] = run_scene("plate", 65, rays=PROBE_RAYS, probe=True)
    rows[name("column", 20, probe=True, strict=True)] = run_scene(
        "column", 20, rays=2_000_000, probe=True, strict=True)
    (DATA / "sky_probe_summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows
