# 产出图 6 的三张分立文件（task-revise-ch8，作者 2026-09-19 终审第 7 条；拼版与美化留后续绘图任务）：
#   ../img/unnamed_cell_globe.jpg  globe 斜视定位图：Φ 类 A60-10（最短代表 `3-4-5-7`，60° 楔 + 120° 旋转折叠）**整类**，相机方位偏离反日点
#                                  GLOBE_OFFSET_DEG（不正对反日点，能同时看到两个亮斑与它们相对反日点 / 地平线的位置）；
#   rect 局部（拼版右上）：**全部光路**、全天 5760×2880（1/16°/px）裁到反日点一侧窗口（方位 120°–180°、仰角 −10°…+20°）——肉眼所见；
#   ../img/far_side_profile.png    幻日环方位剖面曲线（临时 matplotlib）：A60-10 整类 / A0-02 整类 / 全部光路三条，对数纵轴；
#                                  数据 ../data/far_side_profile.csv，机械提取的数字 tee 到 ../data/far_side_profile_numbers.txt。
# 太阳高度 **0°**（`S.scene(..., sun_alt=SUN_ALT)`，不改 `_ch8_sim.SUN_ALTITUDE`——图 5 仍是 10°）：A60-10 的 142° 锐边鼓包与 A0-02 的
# Liljequist 窄峰（`3-5-6-7-3` 一族，与 `1-3-2` 同 Φ、定义域窄）两层同现要太阳贴地平线；10° 时窄峰几乎消失（探针 probe_liljequist_azimuth.py）。
# 取向：片晶（h/a=0.2，zenith σ=0.5°）。上一轮的柱晶对照分支已删（片晶 / 柱晶的取向裁定在 task-write-ch8 已定，与太阳高度无关；旧 ref_column
# 产物在 git 历史 `6431f8b` 可查）。过滤器装该类在该 h/a 下枚举出的**全部**可行光路（PBD 代表，OR 复合过滤器；A60-10 59 条、A0-02 108 条）。
# 三张参考图（rectangular 1440×720、absolute、同一 intensity、REF_RAY_NUM 光线）只用于取数，不入正文：
#   锐边 / 峰值 / 外缘方位（`S.profile_features`：峰值 = 剖面 argmax；锐边 = 内侧半高交点；外缘 = 外侧降到峰值 OUTER_FRAC 的交点；
#   都在 0.5° 桶上线性插值）、两个亮斑质心与 5° 圆内能量占比（`spot_stats`，沿上一轮）、A0-02 窄峰的峰位与半高全宽。
# 其余参数沿图 B1 / ch7（D65、globe fov 30、经纬网格 30°、max_hits 9）；config 与 B1 共用 crystal 段（有单测）。
import csv
import json
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num
from halo_notes.sim.projection import frame_center, globe_view_for, project_globe, rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_plot as P  # noqa: E402
import _ch8_sim as S  # noqa: E402

NAME = "unnamed_cell"
PROFILE_NAME = "far_side_profile"
CHAPTER = CODE_DIR.parent
CLASS_ID = "A60-10"
LILJEQUIST_ID = "A0-02"                        # 窄峰所属的格子（0° 楔平行族、`3-5-6-7-3` 一族），只进曲线，不单独出图
RATIO, ORIENTATION = 0.2, "plate"
SUN_ALT = 0.0                                  # 本图系列太阳高度（图 5 仍用 S.SUN_ALTITUDE=10°）
RAY_NUM = 200_000_000
REF_RAY_NUM = 100_000_000
REF_INTENSITY = 0.03                           # 参考图曝光（absolute，与上一轮片晶参考图相同；A60-10 峰值像素 ≈ 27/255，不削顶）
INTENSITY = 0.35                               # rectangular 局部正式图曝光（absolute）：局部图自 2026-09-19 起画**全部光路**（肉眼所见，下方曲线再拆分），
                                               # 全光路在窗口里比单格亮约 4×（剖面 all/A60-10 峰值比 ≈ 3.8），单格时 1.5 不削顶；2×10⁷ 光线冒烟 @0.4：窗口 99.9% 像素 202、2 个噪声饱和点，正式取 0.35 留余量
SUB_RESOLUTION = (5760, 2880)                  # 1/16°/px：窗口 60°×30° → 960×480 像素（同 B1）
WINDOW_AZ, WINDOW_EL = (120.0, 180.0), (-10.0, 20.0)   # 反日点一侧；太阳 0° 时亮斑骑在地平线上，上下各留 10°/20°
SUB_W, SUB_H = 960, 480
GLOBE_OFFSET_DEG = 10.0                        # globe 帧中心方位 = 180° − 10° = 170°（作者：不正对反日点；25° 时远侧亮斑压在球缘，2026-09-19 试渲 10°/15°/25° 后收到 10°）
GLOBE_CENTER = S.sky(SUN_ALT, 180.0 - GLOBE_OFFSET_DEG)
SPOT_RADIUS_DEG = 5.0                          # 紧凑度锚点：亮斑质心周围 5° 圆
PROFILE_HALF_DEG, PROFILE_BIN_DEG = 1.5, 0.5   # 幻日环条带 ±1.5°、方位 0.5° 桶（同探针）
FEATURE_WINDOW, OUTER_FRAC = S.FEATURE_WINDOW, S.OUTER_FRAC   # 取数窗口 / 「外缘」阈值（与截面敏感性图共用，定义在 _ch8_sim）
CURVES = {CLASS_ID: CLASS_ID, LILJEQUIST_ID: LILJEQUIST_ID, "all": None}   # 曲线名 → Φ 类 id（None = 全部光路）


def crystals() -> list[dict]:
    return [S.crystal(RATIO, ORIENTATION)]


def filters_and_scene(class_id: str | None, ray_num: int) -> tuple[list[dict], dict]:
    if class_id is None:
        return [], S.scene(ray_num, SUN_ALT, filtered=False)
    return S.phi_class_filters(class_id, RATIO), S.scene(ray_num, SUN_ALT)


def build_reference(class_id: str | None, ray_num: int = REF_RAY_NUM) -> dict:
    flts, sc = filters_and_scene(class_id, ray_num)
    return C.build_config(crystals(), flts, sc, [S.reference_render(REF_INTENSITY)])


def build_globe(ray_num: int = RAY_NUM) -> dict:
    flts, sc = filters_and_scene(CLASS_ID, ray_num)
    return C.build_config(crystals(), flts, sc, [S.globe_render(globe_view_for(GLOBE_CENTER))])


def build_rect(ray_num: int = RAY_NUM) -> dict:
    """rect 局部图：**全部光路**（不装过滤器）——右上是肉眼看到的那片天，两个格子各自的贡献由右下曲线拆分；globe 定位图仍只画本格。"""
    flts, sc = filters_and_scene(None, ray_num)
    # 不画 Lumice 网格：拼版时局部图带方位 / 仰角坐标轴，网格线（尤其地平线）只会压在骑在地平线上的亮斑上
    render = C.render_unit(1, C.lens("rectangular"), list(SUB_RESOLUTION), visible="full", background=[0, 0, 0],
                           ev_mode="absolute", intensity_factor=INTENSITY)
    return C.build_config(crystals(), flts, sc, [render])


def globe_offset_of(config: dict) -> float:
    """globe config 的帧中心相对反日点方向的方位偏离（度），单测用。"""
    c = frame_center(config["render"][0])
    az = float(np.degrees(np.arctan2(c[1], c[0])))
    el = float(np.degrees(np.arcsin(np.clip(c[2], -1, 1))))
    assert abs(el - SUN_ALT) < 1e-6, el
    return 180.0 - abs(az)


def spot_stats(image: np.ndarray, render: dict, radius_deg: float = SPOT_RADIUS_DEG) -> dict[str, float]:
    """参考图（rectangular）上按方位角正负分成两半，各取能量质心（方位 / 仰角），并算两个质心 ``radius_deg`` 圆内能量占全天的比例。
    场景关于太阳竖直面镜像对称，两个质心理应 ±方位对称；返回 ``{"az_deg", "el_deg", "within_frac"}``（方位取正侧）。"""
    dirs, weight = rectangular_pixel_directions(render)
    energy = S.linear_luminance(image) * weight
    total = energy.sum()
    if total <= 0:
        raise ValueError("参考图全黑")
    cos_r = np.cos(np.radians(radius_deg))
    out, within = {}, 0.0
    for sign in (+1, -1):
        m = (np.sign(dirs[..., 1]) == sign) & (energy > 0)
        c = (energy[m][:, None] * dirs[m]).sum(axis=0)
        c /= np.linalg.norm(c)
        within += energy[(dirs @ c) > cos_r].sum()
        if sign > 0:
            out["az_deg"] = float(np.degrees(np.arctan2(c[1], c[0])))
            out["el_deg"] = float(np.degrees(np.arcsin(np.clip(c[2], -1, 1))))
    out["within_frac"] = float(within / total)
    return out


def profile(image: np.ndarray, render: dict) -> tuple[np.ndarray, np.ndarray]:
    return S.azimuth_profile(image, render, SUN_ALT, half_deg=PROFILE_HALF_DEG, bin_deg=PROFILE_BIN_DEG)


def crop_sub(image: "X.Image.Image", render: dict) -> "X.Image.Image":
    rows, cols = S.rectangular_window(render, WINDOW_AZ, WINDOW_EL)
    out = image.crop((cols.start, rows.start, cols.stop, rows.stop))
    assert out.size == (SUB_W, SUB_H), out.size
    return out


def load_profiles(data_dir: Path) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, dict[str, float]]]:
    """从 ../data/far_side_profile.csv 读回三条曲线，特征用 `S.profile_features` 从曲线重算（与跑仿真时同一实现）。"""
    with (data_dir / f"{PROFILE_NAME}.csv").open() as f:
        rows = list(csv.DictReader(f))
    centers = np.array([float(r["az_deg"]) for r in rows])
    hists = {name: np.array([float(r[name]) for r in rows]) for name in CURVES}
    return centers, hists, {name: S.profile_features(centers, h) for name, h in hists.items()}


def _globe_uv(render: dict, points: list[tuple[float, float]]) -> np.ndarray:
    """(仰角, 方位) 列表 → globe 图像素坐标（不可见的为 NaN）。"""
    return project_globe([S.sky(el, az) for el, az in points], render)


def _window_outline(n: int = 60) -> list[tuple[float, float]]:
    """rect 局部窗口的边界折线（仰角, 方位），逆时针绕一圈，用来投影到 globe 上画框。"""
    (a0, a1), (e0, e1) = WINDOW_AZ, WINDOW_EL
    az = np.linspace(a0, a1, n)
    el = np.linspace(e0, e1, n)
    return ([(e0, a) for a in az] + [(e, a1) for e in el] + [(e1, a) for a in az[::-1]] + [(e, a0) for e in el[::-1]])


def compose(globe_png: Path, rect_png: Path, rect_render: dict, globe_render: dict, centers: np.ndarray, hists: dict[str, np.ndarray],
            features: dict[str, dict[str, float]], out: Path) -> Path:
    """拼版（ch6 图 6.5 的样式）：左 globe 反相定位图（只画本格；白底、标反日点 / 地平线、红框圈出局部窗口），右上 rect 局部（全部光路，
    黑底、带方位 / 仰角刻度），右下沿幻日环的方位剖面曲线把这片天拆成本格 / 幻日环格 / 全部三条；右侧两栏共用方位轴，142° 锐边与窄峰的
    参考线贯穿两栏。"""
    import matplotlib.pyplot as plt
    P.apply_style()
    globe = X.invert(globe_png)
    rect = crop_sub(X.Image.open(rect_png).convert("RGB"), rect_render)
    (a0, a1), (e0, e1) = WINDOW_AZ, WINDOW_EL

    fig = plt.figure(figsize=(14, 7.0))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.0, 0.9], left=0.02, right=0.98, bottom=0.09, top=0.97,
                          wspace=0.12, hspace=0.32)
    ax_g = fig.add_subplot(gs[:, 0])
    ax_r = fig.add_subplot(gs[0, 1])
    ax_p = fig.add_subplot(gs[1, 1], sharex=ax_r)

    # ---- 左：globe 定位图 ----
    w, h = globe.size
    ax_g.imshow(globe, extent=(0, w, h, 0), interpolation="bilinear")
    ax_g.set_xlim(0, w)
    ax_g.set_ylim(h, 0)
    ax_g.axis("off")
    box = _globe_uv(globe_render, _window_outline())
    ax_g.plot(box[:, 0], box[:, 1], color=P.PAL["accent_warm"], lw=1.6, solid_capstyle="round")
    anth = _globe_uv(globe_render, [(0.0, 180.0)])[0]
    ax_g.plot(anth[0], anth[1], "o", ms=5, color=P.PAL["ink"])
    ax_g.annotate("反日点", anth, xytext=(anth[0] - 30, anth[1] + 150), textcoords="data", ha="right", va="center", fontsize=12,
                  arrowprops=dict(arrowstyle="-", color=P.PAL["ink"], lw=0.9, shrinkA=0, shrinkB=4))
    hz = _globe_uv(globe_render, [(0.0, -128.0)])[0]      # 左侧亮斑再往外一点的地平线上
    ax_g.annotate("地平线（太阳 0°，也就是幻日环）", hz, xytext=(hz[0] + 330, hz[1] + 210), textcoords="data", ha="center", va="center",
                  fontsize=12, arrowprops=dict(arrowstyle="-", color=P.PAL["ink"], lw=0.9, shrinkA=0, shrinkB=2))

    # ---- 右上：rect 局部，方位 / 仰角刻度 ----
    ax_r.imshow(rect, extent=(a0, a1, e0, e1), interpolation="bilinear", aspect="auto")
    ax_r.set_ylim(e0, e1)
    ax_r.set_yticks([-10, 0, 10, 20])
    ax_r.set_yticklabels([P.deg(v) for v in (-10, 0, 10, 20)])
    ax_r.set_ylabel("仰角")
    ax_r.text(0.015, 0.95, "全部光路（肉眼所见的这片天）", transform=ax_r.transAxes, ha="left", va="top", fontsize=10, color="#BBBBBB")
    ax_r.tick_params(axis="x", labelbottom=False)
    for sp in ("top", "right"):
        ax_r.spines[sp].set_visible(False)

    # ---- 右下：方位剖面 ----
    for name, hist in hists.items():
        ax_p.plot(centers, hist, lw=1.6, color=P.CELL_COLOR[name], label=P.CELL_LABEL[name], zorder=3 if name != "all" else 2)
    P.profile_axes(ax_p, az_range=(a0, a1))
    ax_p.set_ylim(3e-3, 20)
    edge, peak = features[CLASS_ID]["edge_az"], features[LILJEQUIST_ID]["peak_az"]
    for ax in (ax_r, ax_p):
        P.mark_azimuth(ax, edge, "", color=P.PAL["ink_faint"] if ax is ax_r else P.TEXT_COLOR)
        P.mark_azimuth(ax, peak, "", color=P.PAL["ink_faint"] if ax is ax_r else P.TEXT_COLOR)
    ax_p.text(edge - 0.6, 0.03, f"{edge:.1f}° 锐边", transform=ax_p.get_xaxis_transform(), ha="right", va="bottom", fontsize=9.5, color=P.TEXT_COLOR)
    ax_p.text(peak + 0.6, 0.03, f"{peak:.1f}° 窄峰", transform=ax_p.get_xaxis_transform(), ha="left", va="bottom", fontsize=9.5, color=P.TEXT_COLOR)
    ax_p.legend(loc="upper left")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


STEPS = ("refs", "globe", "rect", "compose")


def main(argv=None) -> Path:
    p_extra = [a for a in (argv or []) if a.startswith("--steps")]
    args = parse_args([a for a in (argv or []) if not a.startswith("--steps")], default_ray_num=RAY_NUM, description=NAME, replot=True)
    steps = set(STEPS)
    if p_extra:
        steps = set(p_extra[0].split("=", 1)[1].split(","))
        assert steps <= set(STEPS), steps
    if args.replot:
        steps = {"compose"}
    ref_ray = min(args.ray_num, REF_RAY_NUM)
    data_dir = (args.out or CHAPTER) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    def say(msg: str) -> None:
        print(msg)
        lines.append(msg)

    if "refs" in steps:
        hists: dict[str, np.ndarray] = {}
        features: dict[str, dict[str, float]] = {}
        centers = None
        for name, cid in CURVES.items():
            cfg = with_ray_num(build_reference(cid), ref_ray)
            ref = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, variant=f"ref_{name}", workers=args.workers, backend=args.backend)
            image = np.asarray(X.Image.open(ref.images[0]).convert("RGB"))
            render = cfg["render"][0]
            window_max = S.strip_max(image, render, SUN_ALT, half_deg=PROFILE_HALF_DEG, az_range=FEATURE_WINDOW)
            assert window_max < 255, f"ref_{name} saturated within FEATURE_WINDOW: max_px={window_max} @intensity {REF_INTENSITY:g}"
            centers, hists[name] = profile(image, render)
            features[name] = S.profile_features(centers, hists[name])
            n_paths = len(cfg["filter"]) - 1 if cfg["filter"] else "all"
            say(f"ref_{name}: {ref.wall_clock_s:.1f} s, ray_num={ref_ray:,}, sun {cfg['scene']['light_source']['altitude']:g}°, paths {n_paths}, "
                f"max_px {image.max()} (in-window {window_max}), sky energy {S.sky_energy(image, render):.2f} @intensity {REF_INTENSITY:g}")
            fe = features[name]
            say(f"  strip profile {FEATURE_WINDOW[0]:g}–{FEATURE_WINDOW[1]:g}°: peak @{fe['peak_az']:.2f}°, inner half-max (edge) @{fe['edge_az']:.2f}°, "
                f"edge width 10%→half {fe['edge_width_deg']:.2f}°, outer {OUTER_FRAC:g}×peak @{fe['outer_az']:.2f}°, FWHM {fe['fwhm_deg']:.2f}°, energy {fe['energy']:.3f}")
            if cid == CLASS_ID:
                st = spot_stats(image, render)
                say(f"  spots: centroid az ±{st['az_deg']:.2f}° el {st['el_deg']:.2f}°, {SPOT_RADIUS_DEG:g}° 圆内能量 {st['within_frac']:.3f}")
        a, b = features[CLASS_ID], features[LILJEQUIST_ID]
        say(f"{LILJEQUIST_ID} peak − {CLASS_ID} edge = {b['peak_az'] - a['edge_az']:.2f}°; strip energy ratio {LILJEQUIST_ID}/{CLASS_ID} = {b['energy'] / a['energy']:.3f}")
        with (data_dir / f"{PROFILE_NAME}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["az_deg", *CURVES])
            for i, c in enumerate(centers):
                w.writerow([f"{c:.2f}"] + [f"{hists[n][i]:.6f}" for n in CURVES])
        (data_dir / f"{PROFILE_NAME}_numbers.txt").write_text("\n".join(lines) + "\n")

    if "globe" in steps:
        res = sim_figure(NAME, CHAPTER, with_ray_num(build_globe(), args.ray_num), out_root=args.out, variant="globe",
                         workers=args.workers, backend=args.backend)
        print(f"globe: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, frame center offset from anthelic {globe_offset_of(build_globe()):g}°")
    if "rect" in steps:
        cfg = with_ray_num(build_rect(), args.ray_num)
        res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, variant="rect", workers=args.workers, backend=args.backend)
        full = X.Image.open(res.images[0]).convert("RGB")
        print(f"rect: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, max_px {np.asarray(full).max()} @intensity {INTENSITY:g}, "
              f"window az {WINDOW_AZ} el {WINDOW_EL} → {SUB_W}×{SUB_H}")

    out = img_path(NAME, CHAPTER, "png", args.out)
    if "compose" in steps:
        globe_cfg = json.loads((data_dir / f"{NAME}.globe.lumice.json").read_text())
        rect_cfg = json.loads((data_dir / f"{NAME}.rect.lumice.json").read_text())
        compose(data_dir / NAME / "globe" / "img_01.png", data_dir / NAME / "rect" / "img_01.png", rect_cfg["render"][0], globe_cfg["render"][0],
                *load_profiles(data_dir), out)
        print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
