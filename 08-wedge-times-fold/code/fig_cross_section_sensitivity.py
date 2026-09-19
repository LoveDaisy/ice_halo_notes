# 产出 ../img/cross_section_sensitivity.png（图 7「截面敏感性」，task-revise-ch8 作者终审第 8 条；版式按 _ch8_plot 统一：中文标签、
# 格子用正文称呼、系列配色；`--replot` 不跑 Lumice，只从 ../data/cross_section_sensitivity*.csv 重画）：
# 片晶截面从正六边形逐步偏向正三角形时，A60-10（142° 锐边鼓包）与 A0-02（Liljequist 窄峰）两格在幻日环条带上的方位剖面怎么变。
# Lumice `face_distance` 六项按侧面 3..8 交替 [1, d, 1, d, 1, d]：d=1 正六边形，d→2 趋向正三角形（三个偶数面缩成点）；本图 d ∈ DS 四档。
# 太阳 0°、片晶 h/a=0.2（zenith σ=0.5°）、rectangular 全天参考图（1440×720、absolute、同一 intensity）、每次 RAY_NUM 光线，
# 4 档 × 2 类 = 8 次渲染；条带 ±1.5°、0.5° 桶的剖面调 `S.azimuth_profile`（与图 6 曲线同一实现），特征调 `S.profile_features`。
# 复现自探针 scratchpad/task-write-ch8/probe_face_distance.py（d 六档、2×10⁷ 光线）：A60-10 锐边 142° 纹丝不动、能量随 d 单调下降；
# A0-02 窄峰 d=1.2 即摊平成 150°→反日点的平台、总能量反升。为什么——留后篇，本图只摆现象。
# 出图：上排两栏（A60-10 / A0-02）对数纵轴曲线，各档 d 一条线，142° 锐边与 d=1 窄峰位置用竖线标出；下排四个截面小示意
# （matplotlib 多边形，不上 halo_notes.draw）。
# 数据：../data/cross_section_sensitivity.csv（各 d、各类的完整剖面）与 ../data/cross_section_sensitivity_summary.csv（各 d、各类的
# 条带能量 / 峰位 / 锐边 / 半高全宽），Lumice config 与 provenance 按 `sim_figure` 约定落 ../data/cross_section.d<d>_<class>.lumice.json
# 与 ../data/cross_section/d<d>_<class>/。
import csv
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_plot as P  # noqa: E402
import _ch8_sim as S  # noqa: E402

NAME = "cross_section"
FIG_NAME = "cross_section_sensitivity"
CHAPTER = CODE_DIR.parent
RATIO = 0.2
SUN_ALT = 0.0
RAY_NUM = 50_000_000
INTENSITY = 0.03                               # 与图 6 参考图同一绝对曝光
DS = (1.0, 1.2, 1.4, 1.8)                      # face_distance 交替项；探针跑过 {1,1.2,1.4,1.6,1.8,1.95}，正文只摆四档
CLASSES = ("A60-10", "A0-02")
PROFILE_HALF_DEG, PROFILE_BIN_DEG = 1.5, 0.5
PLOT_AZ = (130.0, 180.0)


def face_distance(d: float) -> list[float]:
    return [1.0, d, 1.0, d, 1.0, d]


def crystal(d: float) -> dict:
    """片晶（c 轴竖直，zenith σ 同 `S.crystal`），截面按 ``face_distance(d)`` 变形。"""
    return C.prism_crystal(1, C.hex_prism_height_ratio(RATIO), axis=C.plate_axis(S.ZENITH_STD), face_distance=face_distance(d))


def build(d: float, class_id: str, ray_num: int = RAY_NUM) -> dict:
    return C.build_config([crystal(d)], S.phi_class_filters(class_id, RATIO), S.scene(ray_num, SUN_ALT), [S.reference_render(INTENSITY)])


def variant(d: float, class_id: str) -> str:
    return f"d{d:g}_{class_id}"


def load_profiles(data_dir: Path) -> tuple[np.ndarray, dict[tuple[float, str], np.ndarray], dict[tuple[float, str], dict[str, float]]]:
    """从 ../data/cross_section_sensitivity.csv / _summary.csv 读回剖面与特征（`--replot` 用；列名 `<class>_d<d>` 与写出时一致）。"""
    with (data_dir / f"{FIG_NAME}.csv").open() as f:
        rows = list(csv.DictReader(f))
    centers = np.array([float(r["az_deg"]) for r in rows])
    profiles = {(d, cid): np.array([float(r[f"{cid}_d{d:g}"]) for r in rows]) for d in DS for cid in CLASSES}
    with (data_dir / f"{FIG_NAME}_summary.csv").open() as f:
        features = {(float(r["d"]), r["class"]): {k: float(v) for k, v in r.items() if k not in ("d", "class")} for r in csv.DictReader(f)}
    return centers, profiles, features


def plot(centers: np.ndarray, profiles: dict[tuple[float, str], np.ndarray], features: dict[tuple[float, str], dict[str, float]], out: Path) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    P.apply_style()
    colors = dict(zip(DS, P.SEQ_COLORS))
    fig = plt.figure(figsize=(11, 6.6))
    gs = fig.add_gridspec(2, len(DS), height_ratios=[3.2, 1.0], hspace=0.42, wspace=0.28)
    axes = [fig.add_subplot(gs[0, :len(DS) // 2]), fig.add_subplot(gs[0, len(DS) // 2:])]
    edge = features[(1.0, "A60-10")]["edge_az"]
    peak = features[(1.0, "A0-02")]["peak_az"]
    for ax, cid in zip(axes, CLASSES):
        for d in DS:
            label = f"d = {d:g}" + ("（正六边形）" if d == 1.0 else "")
            ax.plot(centers, profiles[(d, cid)], lw=1.5, color=colors[d], label=label)
        P.profile_axes(ax, az_range=PLOT_AZ, ylabel=(ax is axes[0]))
        ax.set_ylim(2e-3, 2.5)
        ax.set_title(P.CELL_LABEL[cid])
        P.mark_azimuth(ax, edge, f"{edge:.1f}° 锐边", ha="right")
    P.mark_azimuth(axes[1], peak, f"{peak:.1f}° 窄峰（d = 1）", ha="left")
    axes[0].legend(loc="upper right")
    for k, d in enumerate(DS):
        ax = fig.add_subplot(gs[1, k])
        ax.add_patch(Polygon(P.section_polygon(face_distance(1.0)), closed=True, facecolor="none", edgecolor=P.GUIDE_COLOR, lw=0.9, ls="--"))
        ax.add_patch(Polygon(P.section_polygon(face_distance(d)), closed=True, facecolor=colors[d], alpha=0.15, edgecolor="none"))
        ax.add_patch(Polygon(P.section_polygon(face_distance(d)), closed=True, facecolor="none", edgecolor=colors[d], lw=2.0))
        ax.set_xlim(-2.3, 2.3)
        ax.set_ylim(-2.3, 2.3)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"d = {d:g}", fontsize=11, color=colors[d])
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=FIG_NAME, replot=True)
    data_dir = (args.out or CHAPTER) / "data"
    if args.replot:
        out = plot(*load_profiles(data_dir), img_path(FIG_NAME, CHAPTER, "png", args.out))
        print(out)
        return out
    profiles: dict[tuple[float, str], np.ndarray] = {}
    features: dict[tuple[float, str], dict[str, float]] = {}
    centers = None
    for d in DS:
        for cid in CLASSES:
            cfg = with_ray_num(build(d, cid), args.ray_num)
            res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, variant=variant(d, cid), workers=args.workers, backend=args.backend)
            image = np.asarray(X.Image.open(res.images[0]).convert("RGB"))
            window_max = S.strip_max(image, cfg["render"][0], SUN_ALT, half_deg=PROFILE_HALF_DEG, az_range=S.FEATURE_WINDOW)
            assert window_max < 255, f"d={d:g} {cid} saturated within FEATURE_WINDOW: max_px={window_max}"
            centers, profiles[(d, cid)] = S.azimuth_profile(image, cfg["render"][0], SUN_ALT, half_deg=PROFILE_HALF_DEG, bin_deg=PROFILE_BIN_DEG)
            fe = features[(d, cid)] = S.profile_features(centers, profiles[(d, cid)])
            print(f"d={d:g} {cid}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, max_px {image.max()} (in-window {window_max}); strip energy {fe['energy']:.3f}, "
                  f"peak @{fe['peak_az']:.2f}°, edge @{fe['edge_az']:.2f}°, FWHM {fe['fwhm_deg']:.2f}°, outer @{fe['outer_az']:.2f}°")
    data_dir.mkdir(parents=True, exist_ok=True)
    keys = [(d, cid) for d in DS for cid in CLASSES]
    with (data_dir / f"{FIG_NAME}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["az_deg", *(f"{cid}_d{d:g}" for d, cid in keys)])
        for i, c in enumerate(centers):
            w.writerow([f"{c:.2f}"] + [f"{profiles[k][i]:.6f}" for k in keys])
    with (data_dir / f"{FIG_NAME}_summary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        cols = ["energy", "peak_az", "edge_az", "edge_width_deg", "fwhm_deg", "outer_az"]
        w.writerow(["d", "class", *cols])
        for d, cid in keys:
            w.writerow([f"{d:g}", cid] + [f"{features[(d, cid)][c]:.4f}" for c in cols])
    out = plot(centers, profiles, features, img_path(FIG_NAME, CHAPTER, "png", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
