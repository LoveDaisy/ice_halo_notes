# 产出 ../img/unnamed_cell.jpg（图 B2「无名格子」候选）：Φ 类 A60-10（最短代表 `3-4-5-7`，22° 楔 + 120° 旋转折叠）**整类**的 Lumice
# 球面外视图——过滤器装该类在该 h/a 下枚举出的**全部**可行光路（PBD 代表，OR 复合过滤器；片晶 h/a=0.2 共 59 条），不只放最短代表。
# 取向：片晶（h/a=0.2，zenith σ=0.5°）。issue 要求片晶 / 柱晶各看一眼、明显更好看的只出一张：探针（4×10⁶ 光线、rectangular、absolute）
# 片晶下能量集中在反日点一侧、是两个紧凑亮斑（幻日环上离太阳约 ±152°、仰角≈太阳高度，两个 5° 圆内装下 66% 的全天能量）；
# 柱晶（h/a=2）下是穿过反日点的两条宽弧（类似反日弧的 X 形），总能量约为片晶的一半但摊得很开（5° 圆内 0%），峰值面亮度只有片晶
# 亮斑的约 1/12，参考图要把曝光拉高 100× 才看得见——所以正式图只出片晶，柱晶只留一张全天参考图（data/unnamed_cell/ref_column/）作证据。
# 「无名」是提纲的说法，渲染结果表明它有名字：作者 ch3 光路清单把 `3-4-5-7` 标为「142 幻日(环)」（data/ground_truth_signature.md），
# 文献里 150–160° 处幻日环上的亮斑叫 Liljequist 幻日，主要光路 `3-5-6-7`（同属 A60-10）；正文措辞由作者裁定，文件名沿 plan 不改。
# 其余参数与图 B1 相同（Σ=10°、D65、globe fov 30、经纬网格 30°），config 除过滤器 / render.view / 曝光模式外与 B1 逐字段相同（有单测）。
# 帧中心机械选取（同 ch7 / B1）：全天参考图上 75.5° 球冠能量占比最大的候选（实测：反日点 1.00）。
# 机械锚点（review 要求的量化辅助）：脚本打印参考图上两个亮斑的质心方位 / 仰角与 5° 圆内能量占比（紧凑度）、全天能量（与 B1 的 `3-5`
# 参考图同一绝对曝光，可直接比）——目视裁定「成立」以这些数字为佐证，记录见 scratchpad progress。
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
CHAPTER = CODE_DIR.parent
CLASS_ID = "A60-10"
ORIENTATIONS = {"plate": 0.2, "column": 2.0}   # 取向 → h/a（本仓口径）；两档都出参考图
CHOSEN = "plate"                               # 正式图只出这一档（理由见文件头）
RAY_NUM = 200_000_000
REF_RAY_NUM = 20_000_000
REF_INTENSITY = {"plate": 0.03, "column": 3.0}  # 片晶与 fig_b1_same_class.REF_INTENSITY 相同（能量可直接比）；柱晶太暗，曝光拉高 100×
                                                # 才看得见它弥散在哪（探针：0.03 下峰值像素 1、全天能量 0.00），比能量时除回 100
SPOT_RADIUS_DEG = 5.0                          # 紧凑度锚点：亮斑质心周围 5° 圆
GAP, MARGIN, LABEL_PX = 80, 40, 100
SKY_PX = S.SKY_PX
WIDTH, HEIGHT = SKY_PX + 2 * MARGIN, SKY_PX + 2 * MARGIN + LABEL_PX


def population_and_scene(orientation: str, ray_num: int = RAY_NUM) -> tuple[list[dict], list[dict], dict]:
    ratio = ORIENTATIONS[orientation]
    return [S.crystal(ratio, orientation)], S.phi_class_filters(CLASS_ID, ratio), S.scene(ray_num)


def build_reference(orientation: str) -> dict:
    crystals, flts, sc = population_and_scene(orientation, REF_RAY_NUM)
    return C.build_config(crystals, flts, sc, [S.reference_render(REF_INTENSITY[orientation])])


def build(orientation: str, center: str) -> dict:
    crystals, flts, sc = population_and_scene(orientation)
    return C.build_config(crystals, flts, sc, [S.globe_render(globe_view_for(S.CANDIDATES[center]))])


def center_of(config: dict) -> str:
    c = frame_center(config["render"][0])
    for name, v in S.CANDIDATES.items():
        if np.linalg.norm(c - v) < 1e-6:
            return name
    raise ValueError("render.view 的帧中心不是任何候选中心")


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


def compose_single(sub: Path, center: str, out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    X.paste_image(ax, sub, (MARGIN, MARGIN + LABEL_PX, SKY_PX, SKY_PX))
    X.add_text(ax, (MARGIN + 20, MARGIN + 30), f"{CLASS_ID}  (3-4-5-7 …)", size_px=56, color="white", ha="left",
               family=("DejaVu Sans Mono",))
    X.add_text(ax, (MARGIN + 20, MARGIN + 82), S.CENTER_TEXT[center], size_px=30, color="#BBBBBB", ha="left", family=X.CJK_SANS)
    return X.save_canvas(fig, out)


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    ref_ray = min(args.ray_num, REF_RAY_NUM)
    centers: dict[str, str] = {}
    for orientation in ORIENTATIONS:
        ref = sim_figure(NAME, CHAPTER, with_ray_num(build_reference(orientation), ref_ray), out_root=args.out,
                         variant=f"ref_{orientation}", workers=args.workers, backend=args.backend)
        image = np.asarray(X.Image.open(ref.images[0]).convert("RGB"))
        render = build_reference(orientation)["render"][0]
        centers[orientation], fr = S.choose_center(image, render)
        st = spot_stats(image, render)
        print(f"ref_{orientation}: {ref.wall_clock_s:.1f} s, ray_num={ref_ray:,}, {len(build_reference(orientation)['filter']) - 1} paths; "
              f"cap energy " + ", ".join(f"{n}={v:.3f}" for n, v in fr.items()) + f" -> {centers[orientation]}; "
              f"sky energy {S.sky_energy(image, render):.2f} @intensity {REF_INTENSITY[orientation]:g}, max_px {image.max()}; spots az ±{st['az_deg']:.1f}° el {st['el_deg']:.1f}°, "
              f"{SPOT_RADIUS_DEG:g}° 圆内能量 {st['within_frac']:.3f}")
    res = sim_figure(NAME, CHAPTER, with_ray_num(build(CHOSEN, centers[CHOSEN]), args.ray_num), out_root=args.out, variant=CHOSEN,
                     workers=args.workers, backend=args.backend)
    sub = img_path(f"unnamed_cell_{CHOSEN}", CHAPTER, "jpg", args.out)
    X.Image.open(res.images[0]).convert("RGB").save(sub, quality=95)
    print(f"{CHOSEN}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}")
    out = compose_single(sub, centers[CHOSEN], img_path(NAME, CHAPTER, "jpg", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
