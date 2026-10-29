# 产出 ../img/sky_comparison.png：同一 3-5 对称路径、四太阳高度、三取向族的真实 MC 天图。
from __future__ import annotations

import argparse
import errno
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
import numpy as np

import _sky_fig as F
from check_parhelion import bravais, spherical_distance
from halo_notes.draw.style.candidate import scheme
from halo_notes.draw.style.mapping import CJK_SANS
from halo_notes.sim.fetch import sha256_of
from halo_notes.sim.projection import project_equal_area
from halo_notes.sim.run import config_sha256

S = scheme()
COLORS = dict(S.sky_glow)
LABELS = {"random": "随机取向 · 22° 晕", "column": "柱晶取向 · 切弧", "plate": "片晶取向 · 幻日"}
STRENGTH = {"random": 0.55, "column": 1.0, "plate": 1.0}
SOFTENING = 12.0


def style():
    plt.rcParams.update({"font.family": ["Helvetica Neue", *CJK_SANS], "font.size": 12,
                         "text.color": S.ink, "figure.facecolor": S.paper,
                         "savefig.facecolor": S.paper})


def tone(energy, white):
    """显示变换而非能量计算；零保持零，不平滑、不移位、不据阈值删像素。"""
    return np.clip(np.arcsinh(SOFTENING * energy / white) / np.arcsinh(SOFTENING), 0, 1)


def obtain(family, altitude, *, render=False, replot=False):
    folder = F.DATA / F.name(family, altitude)
    cfg = F.build(family, altitude)
    valid = False
    if not render and (folder / "img_02.npy").is_file():
        try:
            _, saved, provenance = F.load_scene(folder, 2)
        except (ValueError, KeyError, OSError):
            # 旧 config/provenance/sidecar/数组失效按缓存未命中处理，交由下方重渲；
            # 只有 --replot 才把缺数据当错误，避免迭代配置后无法重生。
            saved = provenance = None
        if saved is not None:
            valid = (config_sha256(saved) == config_sha256(cfg)
                     and provenance["lumice_version"] == F.LUMICE_VERSION)
            # 离线重画不要求安装二进制；若本机有 release 缓存，再核对其哈希。
            binary = F.cached_binary()
            if binary.is_file():
                valid = valid and provenance["lumice_bin_sha256"] == sha256_of(binary)
    if render or not valid:
        if replot:
            # 带 filename 才能被 repo.testing 的 local_data 钩子识别为「只留本地产物缺失」
            # 而正确 skip，而不是在干净 checkout 上报错。
            raise FileNotFoundError(
                errno.ENOENT, "缺少同配置的原始数据（去掉 --replot 重渲）",
                str(folder / "img_02.npy"))
        F.run_scene(family, altitude)
    return F.load_scene(folder, 2)


def panel_geometry(ax, altitude, cfg, *, horizon=True):
    unit = cfg["render"][1]
    w, h = unit["resolution"]
    center = np.array([w / 2, h / 2])
    ax.plot(*center, "o", ms=6, mfc=S.sun, mec=S.paper, mew=0.8)
    ax.text(center[0], center[1] + 19, "太阳", ha="center", va="top", fontsize=12, color=S.sky["ink"])
    if horizon:
        az = np.radians(np.linspace(-90, 90, 721))
        dirs = np.column_stack((np.cos(az), np.sin(az), np.zeros_like(az)))
        uv = project_equal_area(dirs, unit)
        ax.plot(*uv.T, color=S.sky["guide"], lw=0.5, alpha=.45)
        inside = (uv[:, 0] > 20) & (uv[:, 0] < w - 20) & (uv[:, 1] > 20) & (uv[:, 1] < h - 25)
        if inside.any():
            pos = uv[np.flatnonzero(inside)[0]]
            ax.text(*pos, "地平线", color=S.sky["ink"], fontsize=12, va="bottom")
    ax.set(xlim=(0, w), ylim=(h, 0))
    ax.axis("off")


def draw(*, render=False, replot=False, output=None):
    style()
    scenes = {(fam, alt): obtain(fam, alt, render=render, replot=replot)
              for alt in F.HEIGHTS for fam in F.FAMILIES}
    # 每族共用四高度的一个曝光，不逐面板增强；颜色仅分族，不声称光谱颜色或族间亮度比。
    whites = {fam: float(np.quantile(np.concatenate([
        scenes[fam, alt][0][scenes[fam, alt][0] > 0] for alt in F.HEIGHTS]), .995))
        for fam in F.FAMILIES}
    # 幻日跨高度亮度差很大：以最弱场景定一个共同白点，低太阳的峰会削顶。
    # 四幅同样削顶/曝光，不做逐幅归一化，不把显示结果用于能量取数。
    whites["plate"] = min(float(np.quantile(scenes["plate", alt][0][scenes["plate", alt][0] > 0], .995))
                          for alt in F.HEIGHTS)
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 11.4))
    fig.subplots_adjust(left=.02, right=.98, top=.9, bottom=.04, wspace=.035, hspace=.16)
    metadata = {"source": "Lumice raw XYZ Y / emitted_energy; no spatial edits",
                "heights": list(F.HEIGHTS), "white_per_family": whites,
                "strength_per_family": STRENGTH, "softening": SOFTENING,
                "colors": COLORS, "scenes": {}}
    for ax, altitude in zip(axes.flat, F.HEIGHTS):
        rgb = np.zeros((*reversed(F.DISPLAY_RES), 3))
        for family in F.FAMILIES:
            y, cfg, prov = scenes[family, altitude]
            rgb += (STRENGTH[family] * tone(y, whites[family]))[..., None] * to_rgb(COLORS[family])
            folder = F.DATA / F.name(family, altitude)
            metadata["scenes"][F.name(family, altitude)] = {
                "config_sha256": config_sha256(cfg), "display_raw_sha256": sha256_of(folder / "img_02.npy"),
                "measurements": F.measure_scene(folder), "render_provenance": prov}
        ax.imshow(np.clip(rgb, 0, 1), extent=(0, F.DISPLAY_RES[0], F.DISPLAY_RES[1], 0), interpolation="none")
        panel_geometry(ax, altitude, cfg)
        dphi = bravais(altitude)[1]
        d = float(spherical_distance(altitude, dphi))
        ax.set_title(f"太阳高度 {altitude}°", color=S.ink, pad=9, fontsize=15)
        ax.text(.5, -.025, f"幻日内缘 {d:.2f}°  ·  切弧 / 晕内缘 21.84°",
                transform=ax.transAxes, ha="center", va="top", fontsize=12)
    # 形状直接标注只放一幅，图例在全部面板前共享。
    ax = axes.flat[1]
    ax.annotate("上切弧", xy=(400, 235), xytext=(400, 105), color=S.sky["ink"],
                ha="center", fontsize=12, arrowprops={"arrowstyle": "-", "color": S.sky["ink"], "lw": .6})
    # 幻日标在右侧光弧下方的暗处，不压在弧上。
    ax.text(640, 410, "幻日", color=S.sky["ink"], fontsize=12, ha="center", va="top")
    ax.text(255, 525, "22° 晕", color=S.sky["ink"], fontsize=12)
    handles = [Line2D([], [], color=COLORS[f], lw=3, label=LABELS[f]) for f in F.FAMILIES]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.5, .995),
               fontsize=13, handlelength=2.4, columnspacing=2.6)
    out = Path(output) if output is not None else F.IMG / "sky_comparison.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    meta_path = out.with_suffix(".json") if output is not None else F.DATA / "sky_comparison.json"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    metadata["figure_sha256"] = sha256_of(out)
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(out)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--render", action="store_true", help="重新运行所有正式场景")
    group.add_argument("--replot", action="store_true", help="只读原始线性输出；不运行 Lumice")
    group.add_argument("--probe", action="store_true", help="只跑低成本探针并写取证数据")
    parser.add_argument("--output", type=Path, help="输出图片路径；派生JSON写在同目录同名.json，不改章内成图/派生元数据")
    args = parser.parse_args(argv)
    if args.probe:
        if args.output is not None:
            parser.error("--probe 不生成配图，不能使用 --output")
        F.run_probe()
    else:
        draw(render=args.render, replot=args.replot, output=args.output)


if __name__ == "__main__":
    main()
