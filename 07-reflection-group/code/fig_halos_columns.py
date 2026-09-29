# 产出 ../img/halos_2_vs_11.jpg（6a）与 ../img/halos_3_vs_2.jpg（6b）：柱晶取向下三个**矩阵类**各自单独仿真的 Lumice 球面外视图并排——
# 6a：#2 $s$（以太阳为中心的弥散区）| #11 $b$（幻日环）——同样一次镜面反射、同样的特征值，一片 vs 一条线；
# 6b：#3 $br$（特里克尔弧）| #2 $s$（复用同一张子图）——都只有一两次反射，差别只在是否与 $R_z(\theta)$ 对易。
# 子图各自单独仿真、单独存（data/halo_columns.col_<k>.lumice.json + data/halo_columns/col_<k>/），三份 config **除光路过滤器与
# render.view（帧中心）外逐字段相同**（有单测）：单一柱晶 population（h/a=2，zenith σ=0.5°，roll 均匀）、太阳高度 Σ=10°
#（同 3.5 / 图 5，作者裁定不改）、D65、同一镜头、同一光线数。子图落 img/halo_col_<k>.jpg，两张成图由子图像素拼成（compose 单测），
# `halo_col_2.jpg` 在 6a/6b 是同一文件。
# 过滤器（R2-1）：正文的 #k 是矩阵（共轭类），所以过滤器放进该类的**全部**光路——`_ch7_sim.class_filters(k)` 用
# `reflection_group.raypaths_of_class` 枚举长度 ≤ 6、折射抵消、镜面积 ∈ 该共轭类的全部面序列，按 PBD 轨道取代表（#3 类 36 条、
# #2 类 88 条、#11 类 22 条），装进 `complex` 复合过滤器（OR）。探针（2×10⁷ 光线、rectangular）：复合 = Σ 各代表单独渲染
#（能量比 1.07、亮像素集合 Jaccard 0.95，差异在 8-bit sRGB 量化 / 轻微压缩曲线之内；complex([一条]) 与该条单独渲染能量差 0.1%），
# 旧的单代表 1-2-3-5-1 只占 #3 类总能量的 0.4%（主力是 1-3-2-5-1、3-1-6-4-8、3-5-7-1-4、3-1-5-7-4 等横躺柱晶可达的家族）。
# 镜头（R2-3）：`globe` 球面外视（与 3.5 / 3.6 / 6.1 / 6.5 同一语言），fov 30（球占满短边 96%），帧中心 = 该晕的主体，**机械选取**：
# 先用同一 sim 出一张 `rectangular` 全天参考图（data/halo_columns/ref_<k>/，光线数 REF_RAY_NUM），对候选中心（太阳 / 反日点 /
# 侧向 az 90°，仰角 Σ；见 CANDIDATES）算 75.5° 球冠（globe 一帧可见范围）内的能量占比，取最大者（`choose_center`，单测用参考图
# 复现判定）。实测（2×10⁷ 光线参考图）：#2 太阳 0.84、#3 反日点 1.00、#11 侧向 0.47 > 太阳 0.40 > 反日点 0.35——幻日环整圈装不下，
# 判据把它放在侧向（与 issue 预期的「反日点侧」不同，以判据为准）。
# Lumice globe 语义：帧中心天空方向 = (view.azimuth + 180°, −view.elevation)，`halo_notes.sim.projection.globe_view_for` 换算。
# 经纬网格每 30° 一条（低透明度，地平线亮一档），`label` 关。角标下写「帧中心：xx」。
# 本脚本兼有两重职责：图 6a/6b 产出 + 复合过滤器 ↔ 权威表类的交叉验证入口（sim 单测 (c)：复合子过滤器 == 代表集合）。
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.energy import pixel_energy
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num
from halo_notes.sim.projection import GLOBE_CAP_DEG, frame_center, globe_view_for, rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch7_sim as S  # noqa: E402

NAME = "halo_columns"
CHAPTER = CODE_DIR.parent
SUN_ALTITUDE = 10.0
COLUMN_HEIGHT, ZENITH_STD = 2.0, 0.5
RAY_NUM = 200_000_000
REF_RAY_NUM = 20_000_000                  # 全天参考图（只用来选帧中心）
SKY_PX = 1400
LENS_TYPE, FOV_DEG = "globe", 30
REF_RESOLUTION = (1440, 720)
GRID_STEP, GRID_OPACITY, GRID_COLOR, GRID_LABEL = 30, 0.35, [0.55, 0.55, 0.55], False
NUMBERS = (2, 11, 3)
LABELS = {2: "#2  $s$", 11: "#11  $b$", 3: "#3  $br$"}
FIGURES = {"halos_2_vs_11": (2, 11), "halos_3_vs_2": (3, 2)}
GAP, MARGIN, LABEL_PX = 80, 40, 100
WIDTH, HEIGHT = 2 * SKY_PX + GAP + 2 * MARGIN, SKY_PX + 2 * MARGIN + LABEL_PX


def sky(el_deg: float, az_deg: float) -> np.ndarray:
    e, a = np.radians(el_deg), np.radians(az_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


# 候选帧中心（天空方向）与角标文字；Lumice 方位角 0° = +x = 太阳方向。场景关于太阳—反日点竖直面镜像对称（太阳方位 0、roll 均匀），
# 侧向 ±90° 物理上等价（探针实测两者占比只差蒙特卡洛噪声 0.473 / 0.475），所以只列 +90° 一个候选，免得由噪声掷硬币
CANDIDATES = {"sun": sky(SUN_ALTITUDE, 0), "anthelic": sky(SUN_ALTITUDE, 180), "side": sky(SUN_ALTITUDE, 90)}
CENTER_TEXT = {"sun": "帧中心：太阳", "anthelic": "帧中心：反日点", "side": "帧中心：侧向（方位角 90°）"}


def sky_grid(*, step: int = GRID_STEP, opacity: float = GRID_OPACITY, label: bool = GRID_LABEL) -> dict:
    """经纬网格：仰角 / 方位角每 ``step`` 度一条（低透明度），地平线单独一条更亮（`horizon: true` 是不可配色的暗红，不用）。"""
    elev = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(-90 + step, 90, step) if v != 0]
    elev.append(C.grid_line(0, opacity=min(1.0, opacity * 2), color=GRID_COLOR))
    lon = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(0, 360, step)]
    return C.grid(elevation=elev, longitude=lon, extra={"label": label})


def population_and_scene(number: int, ray_num: int = RAY_NUM) -> tuple[list[dict], list[dict], dict]:
    """crystal / filter / scene 三段（图 6 三张子图、7.5 底图、全天参考图共用）。"""
    column = C.prism_crystal(1, COLUMN_HEIGHT, axis=C.column_axis(ZENITH_STD))
    flts = S.class_filters(number)
    sc = C.scene(C.sun(SUN_ALTITUDE), ray_num, [C.entry(1, filter=S.FILTER_ID)], max_hits=7)
    return [column], flts, sc


def build_reference(number: int) -> dict:
    """全天 ``rectangular`` 参考图（无网格、absolute 曝光），只用于选帧中心。"""
    crystals, flts, sc = population_and_scene(number, REF_RAY_NUM)
    render = C.render_unit(1, C.lens("rectangular"), list(REF_RESOLUTION), visible="full", background=[0, 0, 0],
                           ev_mode="absolute", intensity_factor=3.0)
    return C.build_config(crystals, flts, sc, [render])


def cap_energy_fractions(image: np.ndarray, render: dict, candidates: dict[str, np.ndarray],
                         cap_deg: float = GLOBE_CAP_DEG) -> dict[str, float]:
    """参考图（rectangular）上，各候选中心周围 ``cap_deg`` 球冠内的能量占全天的比例
    （像素能量 = 线性亮度本身：Lumice 像素值已含立体角，不再乘 cos(lat)，见 `halo_notes.sim.energy`）。"""
    dirs, _ = rectangular_pixel_directions(render)
    energy = pixel_energy(image)
    total = energy.sum()
    cos_cap = np.cos(np.radians(cap_deg))
    return {name: float(energy[(dirs @ c) > cos_cap].sum() / total) for name, c in candidates.items()}


def choose_center(image: np.ndarray, render: dict, candidates: dict[str, np.ndarray] = CANDIDATES) -> tuple[str, dict[str, float]]:
    """帧中心 = 球冠内能量占比最大的候选（并列取 CANDIDATES 顺序靠前者）。"""
    fr = cap_energy_fractions(image, render, candidates)
    best = max(candidates, key=lambda n: (round(fr[n], 9), -list(candidates).index(n)))
    return best, fr


def build(number: int, center: str, *, fov: float = FOV_DEG, grid: dict | None = None) -> dict:
    """正式子图 config：globe，帧中心 = ``CANDIDATES[center]``。"""
    crystals, flts, sc = population_and_scene(number)
    render = C.render_unit(1, C.lens(LENS_TYPE, fov=fov), [SKY_PX, SKY_PX], view=globe_view_for(CANDIDATES[center]),
                           visible="full", background=[0, 0, 0], grid=sky_grid() if grid is None else grid)
    return C.build_config(crystals, flts, sc, [render])


def center_of(config: dict) -> str:
    """从落盘 config 反推帧中心是哪个候选（单测 / 拼图角标用），不另存一份。"""
    c = frame_center(config["render"][0])
    for name, v in CANDIDATES.items():
        if np.linalg.norm(c - v) < 1e-6:
            return name
    raise ValueError("render.view 的帧中心不是任何候选中心")


def compose_pair(left: Path, right: Path, numbers: tuple[int, int], centers: dict[int, str], out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    for i, (img, k) in enumerate(zip((left, right), numbers)):
        x = MARGIN + i * (SKY_PX + GAP)
        X.paste_image(ax, img, (x, MARGIN + LABEL_PX, SKY_PX, SKY_PX))
        X.add_text(ax, (x + 20, MARGIN + 30), LABELS[k], size_px=56, color="white", ha="left",
                   family=("DejaVu Sans",), math_fontfamily="cm")
        X.add_text(ax, (x + 20, MARGIN + 82), CENTER_TEXT[centers[k]], size_px=30, color="#BBBBBB", ha="left",
                   family=X.CJK_SANS)
    return X.save_canvas(fig, out)


def main(argv=None) -> dict[str, Path]:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    subs: dict[int, Path] = {}
    centers: dict[int, str] = {}
    for k in NUMBERS:
        ref_ray = min(args.ray_num, REF_RAY_NUM)
        ref = sim_figure(NAME, CHAPTER, with_ray_num(build_reference(k), ref_ray), out_root=args.out, variant=f"ref_{k}",
                         workers=args.workers, backend=args.backend)
        image = np.asarray(X.Image.open(ref.images[0]).convert("RGB"))
        centers[k], fr = choose_center(image, build_reference(k)["render"][0])
        print(f"ref_{k}: {ref.wall_clock_s:.1f} s, ray_num={ref_ray:,}; cap energy " +
              ", ".join(f"{n}={v:.3f}" for n, v in fr.items()) + f" -> {centers[k]}")
        res = sim_figure(NAME, CHAPTER, with_ray_num(build(k, centers[k]), args.ray_num), out_root=args.out, variant=f"col_{k}",
                         workers=args.workers, backend=args.backend)
        subs[k] = img_path(f"halo_col_{k}", CHAPTER, "jpg", args.out)
        X.Image.open(res.images[0]).convert("RGB").save(subs[k], quality=95)
        print(f"col_{k}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}")
    outs = {}
    for name, (a, b) in FIGURES.items():
        outs[name] = compose_pair(subs[a], subs[b], (a, b), centers, img_path(name, CHAPTER, "jpg", args.out))
        print(outs[name])
    return outs


if __name__ == "__main__":
    main(sys.argv[1:])
