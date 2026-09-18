# 产出图 6 的三张分立文件（task-revise-ch8，作者 2026-09-19 终审第 7 条；拼版与美化留后续绘图任务）：
#   ../img/unnamed_cell_globe.jpg  globe 斜视定位图：Φ 类 A60-10（最短代表 `3-4-5-7`，60° 楔 + 120° 旋转折叠）**整类**，相机方位偏离反日点
#                                  GLOBE_OFFSET_DEG（不正对反日点，能同时看到两个亮斑与它们相对反日点 / 地平线的位置）；
#   ../img/unnamed_cell_rect.jpg   rectangular 局部图：同一场景全天 5760×2880（1/16°/px）裁到反日点一侧窗口（方位 120°–180°、仰角 −10°…+20°）；
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
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num
from halo_notes.sim.projection import frame_center, globe_view_for, rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
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
INTENSITY = 1.5                                # rectangular 局部正式图曝光（absolute；2×10⁷ 光线冒烟 @2.5：15 px 盒均值最亮 211/255、940 px 削顶，降到 1.5 留余量）
SUB_RESOLUTION = (5760, 2880)                  # 1/16°/px：窗口 60°×30° → 960×480 像素（同 B1）
WINDOW_AZ, WINDOW_EL = (120.0, 180.0), (-10.0, 20.0)   # 反日点一侧；太阳 0° 时亮斑骑在地平线上，上下各留 10°/20°
SUB_W, SUB_H = 960, 480
GLOBE_OFFSET_DEG = 25.0                        # globe 帧中心方位 = 180° − 25° = 155°（作者：偏离反日点 20–30°，不要正对）
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
    flts, sc = filters_and_scene(CLASS_ID, ray_num)
    render = C.render_unit(1, C.lens("rectangular"), list(SUB_RESOLUTION), visible="full", background=[0, 0, 0],
                           ev_mode="absolute", intensity_factor=INTENSITY, grid=S.sky_grid())
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


def plot_profiles(centers: np.ndarray, hists: dict[str, np.ndarray], features: dict[str, dict[str, float]], out: Path, ray_num: int) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = {CLASS_ID: f"{CLASS_ID} class (3-4-5-7 …)", LILJEQUIST_ID: f"{LILJEQUIST_ID} class (1-3-2, 3-5-6-7-3 …)", "all": "all raypaths"}
    for name, h in hists.items():
        ax.plot(centers, h, lw=1.2, label=labels[name])
    f = features[CLASS_ID]
    for x, ls in ((f["edge_az"], "--"), (f["peak_az"], ":"), (f["outer_az"], "--")):
        ax.axvline(x, color="gray", lw=0.6, ls=ls)
    ax.axvline(features[LILJEQUIST_ID]["peak_az"], color="tab:orange", lw=0.6, ls=":")
    ax.set_yscale("log")
    ax.set_xlim(120, 180)
    ax.set_xlabel("azimuth from sun (deg)")
    ax.set_ylabel(f"linear energy / {PROFILE_BIN_DEG:g}° bin")
    ax.set_title(f"plate h/a={RATIO}, sun {SUN_ALT:g}°, parhelic-circle strip |el−sun| ≤ {PROFILE_HALF_DEG:g}°, {ray_num:,} rays each")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    ref_ray = min(args.ray_num, REF_RAY_NUM)
    lines: list[str] = []

    def say(msg: str) -> None:
        print(msg)
        lines.append(msg)

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

    data_dir = (args.out or CHAPTER) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / f"{PROFILE_NAME}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["az_deg", *CURVES])
        for i, c in enumerate(centers):
            w.writerow([f"{c:.2f}"] + [f"{hists[n][i]:.6f}" for n in CURVES])
    curve = plot_profiles(centers, hists, features, img_path(PROFILE_NAME, CHAPTER, "png", args.out), ref_ray)

    res = sim_figure(NAME, CHAPTER, with_ray_num(build_globe(), args.ray_num), out_root=args.out, variant="globe",
                     workers=args.workers, backend=args.backend)
    globe = img_path(f"{NAME}_globe", CHAPTER, "jpg", args.out)
    X.Image.open(res.images[0]).convert("RGB").save(globe, quality=95)
    say(f"globe: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, frame center offset from anthelic {globe_offset_of(build_globe()):g}°")
    cfg = with_ray_num(build_rect(), args.ray_num)
    res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, variant="rect", workers=args.workers, backend=args.backend)
    rect = img_path(f"{NAME}_rect", CHAPTER, "jpg", args.out)
    full = X.Image.open(res.images[0]).convert("RGB")
    crop_sub(full, cfg["render"][0]).save(rect, quality=95)
    say(f"rect: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}, max_px {np.asarray(full).max()} @intensity {INTENSITY:g}, "
        f"window az {WINDOW_AZ} el {WINDOW_EL} → {SUB_W}×{SUB_H}")
    (data_dir / f"{PROFILE_NAME}_numbers.txt").write_text("\n".join(lines) + "\n")
    for p in (globe, rect, curve):
        print(p)
    return rect


if __name__ == "__main__":
    main(sys.argv[1:])
