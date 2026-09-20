# 产出 ../img/cross_section_renders.png（图 7 的仿真渲染配图，2026-09-20 作者审校时提出：曲线剖面之外再给一眼能看到的画面）：
# 片晶截面从正六边形逐步偏向正三角形（`fig_cross_section_sensitivity.DS` 四档 d，同一 `face_distance` 变形），每档渲染**全部光路**
# （不装过滤器——与图 6 右上同一思路：肉眼所见，分光路的拆解交给图 7 的曲线），裁到图 6 右上同一方位范围（125°–180°）、仰角收窄到
# ±4°（作者 2026-09-20：四行叠放沿用 −8°…12° 图太高；亮斑上下各约 3° 就到底了），
# 上下叠成四行：左列截面小示意（与图 7 下排同一画法、同一配色），右列对应的渲染局部。
# 渲染口径逐字沿图 6 右上（`fig_b2_unnamed_cell.build_rect`：太阳 0°、片晶 h/a=0.2、zenith σ=0.5°、rectangular 5760×2880、absolute 曝光
# 0.35），只换晶体段；四行同一绝对曝光，亮暗可以互相比、也可以与图 6 比。d=1 那一行与图 6 右上是同一 config 重跑（face_distance 显式写 1）。
# 参考线：142° 锐边（d=1 的 A60-10 内侧半高）与 d=1 的 Liljequist 窄峰位置，数值从 ../data/cross_section_sensitivity_summary.csv 读
# （图 7 的产物），本图不重算。`--replot` 不跑 Lumice，只从 ../data/cross_section_renders/d<d>/img_01.png 重画。
import csv
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_plot as P  # noqa: E402
import _ch8_sim as S  # noqa: E402
import fig_b2_unnamed_cell as B2  # noqa: E402
import fig_cross_section_sensitivity as CS  # noqa: E402

NAME = "cross_section_renders"
CHAPTER = CODE_DIR.parent
DS = CS.DS
RAY_NUM = B2.RAY_NUM
SUN_ALT = B2.SUN_ALT
WINDOW_AZ, WINDOW_EL = B2.WINDOW_AZ, (-4.0, 4.0)
YTICKS = (-4, 0, 4)


def build(d: float, ray_num: int = RAY_NUM) -> dict:
    return B2.build_rect(ray_num, crystal_list=[CS.crystal(d)])


def variant(d: float) -> str:
    return f"d{d:g}"


def load_features(data_dir: Path) -> tuple[float, float]:
    """(142° 锐边, d=1 窄峰) 的方位，取自图 7 的 summary 表。"""
    with (data_dir / f"{CS.FIG_NAME}_summary.csv").open() as f:
        rows = {(float(r["d"]), r["class"]): r for r in csv.DictReader(f)}
    return float(rows[(1.0, "A60-10")]["edge_az"]), float(rows[(1.0, "A0-02")]["peak_az"])


def crop(image: "X.Image.Image", render: dict) -> "X.Image.Image":
    rows, cols = S.rectangular_window(render, WINDOW_AZ, WINDOW_EL)
    return image.crop((cols.start, rows.start, cols.stop, rows.stop))


def crops(data_dir: Path) -> dict[float, "X.Image.Image"]:
    import json
    out = {}
    for d in DS:
        cfg = json.loads((data_dir / f"{NAME}.{variant(d)}.lumice.json").read_text())
        out[d] = crop(X.Image.open(data_dir / NAME / variant(d) / "img_01.png").convert("RGB"), cfg["render"][0])
    return out


def plot(images: dict[float, "X.Image.Image"], edge: float, peak: float, out: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    P.apply_style()
    colors = dict(zip(DS, P.SEQ_COLORS))
    (a0, a1), (e0, e1) = WINDOW_AZ, WINDOW_EL

    fig_w = 9.5
    left, right, wspace = 0.03, 0.985, 0.22
    top_in, bottom_in, gap_in = 0.45, 0.62, 0.42                 # 上边距（首行标注）、下边距（方位轴刻度 + 轴标）、行距，英寸
    w_sec, w_img = 1.0, 4.6                                     # 列宽比：截面小图 : 渲染局部
    col_img = (right - left) * fig_w / (1 + wspace) * w_img / (w_sec + w_img)
    row_h = col_img * (e1 - e0) / (a1 - a0)                      # 渲染局部 1° = 1°
    fig_h = top_in + len(DS) * row_h + (len(DS) - 1) * gap_in + bottom_in
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(len(DS), 2, width_ratios=[w_sec, w_img], left=left, right=right, bottom=bottom_in / fig_h,
                          top=1 - top_in / fig_h, wspace=wspace, hspace=gap_in / row_h)

    yticks = list(YTICKS)
    ax_first = None
    for k, d in enumerate(DS):
        # ---- 左：截面 ----
        ax = fig.add_subplot(gs[k, 0])
        ax.add_patch(Polygon(P.section_polygon(CS.face_distance(1.0)), closed=True, facecolor="none", edgecolor=P.GUIDE_COLOR, lw=0.9, ls="--"))
        ax.add_patch(Polygon(P.section_polygon(CS.face_distance(d)), closed=True, facecolor=colors[d], alpha=0.15, edgecolor="none"))
        ax.add_patch(Polygon(P.section_polygon(CS.face_distance(d)), closed=True, facecolor="none", edgecolor=colors[d], lw=2.0))
        ax.set_xlim(-2.1, 2.1)
        ax.set_ylim(-2.1, 2.1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.text(0.5, 1.0, f"d = {d:g}" + ("（正六边形）" if d == 1.0 else ""), transform=ax.transAxes, ha="center", va="bottom",
                fontsize=10.5, color=colors[d])
        # ---- 右：渲染局部 ----
        ax_r = fig.add_subplot(gs[k, 1], sharex=ax_first)
        if ax_first is None:
            ax_first = ax_r
        ax_r.imshow(images[d], extent=(a0, a1, e0, e1), interpolation="bilinear", aspect="auto")   # 行高已按 1°=1° 算好
        ax_r.set_xlim(a0, a1)
        ax_r.set_ylim(e0, e1)
        ax_r.set_yticks(yticks)
        ax_r.set_yticklabels([P.deg(v) for v in yticks])
        ax_r.set_ylabel("仰角")
        for sp in ("top", "right"):
            ax_r.spines[sp].set_visible(False)
        for az in (edge, peak):
            P.mark_azimuth(ax_r, az, "", color=P.PAL["ink_faint"])
        if k == 0:
            ax_r.text(edge - 0.6, 0.95, f"{edge:.1f}° 锐边", transform=ax_r.get_xaxis_transform(), ha="right", va="top", fontsize=9.5, color="#BBBBBB")
            ax_r.text(peak + 0.6, 0.95, f"{peak:.1f}° 窄峰（d = 1）", transform=ax_r.get_xaxis_transform(), ha="left", va="top", fontsize=9.5, color="#BBBBBB")
        if k < len(DS) - 1:
            ax_r.tick_params(axis="x", labelbottom=False)
        else:
            ticks = np.arange(np.ceil(a0 / 10) * 10, a1 + 1e-9, 10)
            ax_r.set_xticks(ticks)
            ax_r.set_xticklabels([P.deg(t) for t in ticks])
            ax_r.set_xlabel(P.AZ_LABEL)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME, replot=True)
    data_dir = (args.out or CHAPTER) / "data"
    if not args.replot:
        for d in DS:
            cfg = with_ray_num(build(d), args.ray_num)
            res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, variant=variant(d), workers=args.workers, backend=args.backend)
            crop_px = np.asarray(crop(X.Image.open(res.images[0]).convert("RGB"), cfg["render"][0]))
            print(f"d={d:g}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, window max_px {crop_px.max()}, "
                  f"saturated px {(crop_px.max(axis=-1) >= 255).sum()}, 99.9% {np.percentile(crop_px.max(axis=-1), 99.9):.0f} @intensity {B2.INTENSITY:g}")
    features_dir = CHAPTER / "data" if args.out else data_dir     # 参考线数值只在正式 data/ 里有（图 7 产物）
    out = plot(crops(data_dir), *load_features(features_dir), img_path(NAME, CHAPTER, "png", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
