# 产出 ../img/plate_arcs.png（图 11「片晶姿态、太阳 10° 时 max_hits = 2 / 4 / 8 的全天图三联」）+ ../data/plate_arcs*（新渲染）：
# 参考几何 (1, 0.5) 锥晶、片晶姿态 `plate_axis(zenith_std=1°)`、太阳 10°、D65、无过滤器，光线最多打 2 / 4 / 8 个面，各 RAY_NUM 条光线，
# 全天 rectangular 1440×720。探针 `scratchpad/probe-plate-arcs/probe.py` 的正式版：去掉绝对路径与裸二进制路径，二进制走
# `_ch9_sim.ensure_lumice_version()`（release、拒绝 LUMICE_BIN），光谱从探针的 550 nm 换成 D65（与本章其余渲染一致），光线数 5×10⁷ → 2×10⁸。
# 输出用 Lumice `--format npy`（未曝光线性 XYZ float32）：弧的判据要在同一把「相对背景」的尺子上量，8-bit png 装不下弧与背景之间 4 个量级的
# 动态范围。npy 渲染走 `halo_notes.sim.run.render(fmt="npy")` + `_ch9_fig.load_npy_render`（与返工 R1 的
# 天顶渲染共用一份实现），provenance 字段与 `run.render` 同形（版本 / 二进制 sha256 / config sha256 / 墙钟 / 命令行）。npy 不在 LFS 规则里，三份打成
# `data/plate_arcs.zip`（确定性 zip，走 LFS），`data/plate_arcs/mh<k>/` 只留 config / provenance / lumice.log / img_01.json。
# 「结构数」判据沿用探针（机械核验用，不进图面）：像素辐亮度（Y / cos(lat)，`_ch9_fig.linear_radiance`）除以太阳 2° 外中位数得对比度，
# log10 对比度 ≥ ARC_LOG_CONTRAST 的像素做 8 邻接连通域，面积 ≥ MIN_PX 的计一个结构，PCA 主 / 次轴比 ≥ ARC_ELONGATION 的计「弧状」。
# 显示：XYZ → 线性 sRGB，亮度按 log10(对比度) / DISPLAY_DECADES 映射到 0–1（背景 = 黑、10^DISPLAY_DECADES 倍背景 = 满），保留色度。
# Lumice 是无固定 seed 的 MC，重渲不逐字节复现；`--replot` 从 zip 重画，逐字节复现。
# 读者要看出：截断越长，天球上的细弧与条带越多。
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

import _ch9_fig as F
import _ch9_sim as S
import enumerate_signatures as ES
from halo_notes.sim import config as C, run
from halo_notes.sim.projection import rectangular_pixel_directions

NAME = "plate_arcs"
MAX_HITS = (2, 4, 8)
SUN_ALT = 10.0
RAY_NUM = 200_000_000
RESOLUTION = (1440, 720)
ZIP = F.DATA / f"{NAME}.zip"
SUN_MASK_DEG = 2.0
ARC_LOG_CONTRAST = 1.0          # 10× 背景（探针 th1.0）
MIN_PX = 30
ARC_ELONGATION = 3.0
DISPLAY_DECADES = 3.0
WIDTH, DPI = 2000, 200
PAL = F.PAL
FONT = {"family": list(F.CHART_FONTS)}


def build(max_hits: int, ray_num: int = RAY_NUM) -> dict:
    crystal = C.pyramid_crystal_from_geometry(1, ES.tier_pyramid(S.TIER), axis=C.plate_axis(1.0))
    scene = C.scene(C.sun(SUN_ALT), ray_num, [C.entry(1)], max_hits=max_hits)
    ru = C.render_unit(1, C.lens("rectangular"), list(RESOLUTION), visible="full", background=[0, 0, 0],
                       ev_mode="absolute", intensity_factor=1.0)
    return C.build_config([crystal], [], scene, [ru])


def variant_dir(max_hits: int, root: Path | None = None) -> Path:
    return (root or F.CHAPTER) / "data" / NAME / f"mh{max_hits}"


def render_npy(config: dict, out_dir: Path, binary: Path) -> np.ndarray:
    """跑一次 Lumice（`--format npy`，经 `halo_notes.sim.run.render`），返回 (H, W, 3) XYZ。"""
    arrays, _ = F.load_npy_render(run.render(config, out_dir, fmt="npy", bin=binary))
    return arrays[0]


def pack(arrays: dict[int, np.ndarray], zip_path: Path = ZIP) -> None:
    """确定性 zip（固定时间戳、按 max_hits 排序）：``mh<k>.npy``。"""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for k in sorted(arrays):
            buf = io.BytesIO()
            np.save(buf, arrays[k].astype(np.float32))
            info = zipfile.ZipInfo(f"mh{k}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, buf.getvalue())


def load(zip_path: Path = ZIP) -> dict[int, np.ndarray]:
    if zip_path.stat().st_size < 1024 and zip_path.read_bytes().startswith(b"version https://git-lfs"):
        raise RuntimeError(f"{zip_path} 是 LFS 指针，先 `git lfs pull`")
    with zipfile.ZipFile(zip_path) as zf:
        return {k: np.load(io.BytesIO(zf.read(f"mh{k}.npy"))) for k in MAX_HITS}


def render_dict() -> dict:
    return {"lens": {"type": "rectangular"}, "resolution": list(RESOLUTION)}


def contrast(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(log10 对比度, 掩码)``：辐亮度 Y / cos(lat)（行方框平均后）除以太阳 SUN_MASK_DEG 外的正值中位数；掩码 = 太阳周围以外。"""
    Y = F.linear_radiance(xyz[..., 1:2], render_dict())[..., 0]
    dirs, _ = rectangular_pixel_directions(render_dict())
    ang = np.degrees(np.arccos(np.clip(dirs @ S.sun_direction(SUN_ALT), -1, 1)))
    mask = ang > SUN_MASK_DEG
    bg = float(np.median(Y[mask & (Y > 0)]))
    return np.log10(np.maximum(Y, 1e-30) / bg), mask


def count_structures(xyz: np.ndarray) -> dict[str, int]:
    """探针判据：log10 对比度 ≥ ARC_LOG_CONTRAST 的 8 邻接连通域，面积 ≥ MIN_PX 计结构，PCA 主 / 次轴比 ≥ ARC_ELONGATION 计弧状。"""
    c, mask = contrast(xyz)
    lab, n = ndimage.label((c >= ARC_LOG_CONTRAST) & mask, structure=np.ones((3, 3)))
    structures = arcs = 0
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        ys, xs = np.nonzero(lab[sl] == k)
        if ys.size < MIN_PX:
            continue
        structures += 1
        pts = np.stack([xs, ys], 1).astype(float)
        pts -= pts.mean(0)
        ev = np.linalg.eigvalsh(pts.T @ pts / len(pts))
        if np.sqrt(ev[1] / max(ev[0], 1e-9)) >= ARC_ELONGATION:
            arcs += 1
    return {"structures": structures, "arc_like": arcs}


XYZ_TO_SRGB = F.XYZ_TO_SRGB


def display(xyz: np.ndarray) -> np.ndarray:
    """XYZ → 显示用 sRGB uint8：亮度按 log10 对比度 / DISPLAY_DECADES 映射（背景以下 = 黑），色度取线性 sRGB 的比例。"""
    rad = F.linear_radiance(xyz, render_dict())
    c, _ = contrast(xyz)
    level = np.clip(c / DISPLAY_DECADES, 0, 1)
    rgb = np.clip(rad @ XYZ_TO_SRGB.T, 0, None)
    chroma = rgb / np.maximum(rgb.max(axis=-1, keepdims=True), 1e-30)
    return F._srgb_encode(chroma * level[..., None] ** 2.2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replot", action="store_true", help="不跑 Lumice，从 data/plate_arcs.zip 重画")
    ap.add_argument("--ray-num", type=int, default=RAY_NUM)
    args = ap.parse_args()
    if not args.replot:
        binary = S.ensure_lumice_version()
        arrays = {}
        for k in MAX_HITS:
            cfg = build(k, args.ray_num)
            (F.DATA / f"{NAME}.mh{k}.lumice.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
            arrays[k] = render_npy(cfg, variant_dir(k), binary)
            print(f"mh{k}: rendered", flush=True)
        pack(arrays)
    arrays = load()
    counts = {k: count_structures(arrays[k]) for k in MAX_HITS}
    S.write_numbers(NAME, {"tier": list(S.TIER), "sun_alt": SUN_ALT, "axis": "plate_axis(zenith_std=1°)", "spectrum": "D65",
                           "ray_num": json.loads((variant_dir(MAX_HITS[0]) / "config.json").read_text())["scene"]["ray_num"],
                           "criterion": {"log10_contrast": ARC_LOG_CONTRAST, "min_px": MIN_PX, "elongation": ARC_ELONGATION,
                                         "sun_mask_deg": SUN_MASK_DEG},
                           "counts": {f"mh{k}": v for k, v in counts.items()}})
    H = WIDTH // 2
    fig = plt.figure(figsize=((WIDTH + 0.5) / DPI, (3 * (H + 90) + 40 + 0.5) / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAL["background"])
    tot = 3 * (H + 90) + 40
    for i, k in enumerate(MAX_HITS):
        y0 = 1 - (i + 1) * (H + 90) / tot
        ax = fig.add_axes([0, y0 + 90 / tot, 1, H / tot])
        ax.imshow(display(arrays[k]), interpolation="lanczos", aspect="auto")
        ax.set_axis_off()
        fig.text(0.5, y0 + 45 / tot, f"光线最多打 {k} 次面", ha="center", va="center", fontsize=13, color=PAL["ink"], **FONT)
    fig.text(0.5, 20 / tot, "全天等距柱状投影，横向 360°、纵向 180°，太阳在中央；亮度取对数", ha="center", va="center", fontsize=10,
             color=PAL["slate"], **FONT)
    fig.savefig(F.out_png(NAME), dpi=DPI, facecolor=fig.get_facecolor(), metadata=F.PNG_META)
    print(f"saved {F.out_png(NAME)}  counts={counts}")


if __name__ == "__main__":
    main()
