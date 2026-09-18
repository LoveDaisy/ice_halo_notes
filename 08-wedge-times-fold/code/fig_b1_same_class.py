# 产出 ../img/same_class.jpg（图 B1「同类异路」）：`3-5` 与 `3-1-2-5` 两条**单光路**（不是类）各自单独仿真的 Lumice 球面外视图并排——
# 两条光路的 $M$ 都是 $e$（`3-1-2-5` 上下底面各弹一次，$b^2=e$），同属 Φ 类 A60-12，方向映射逐点相同，所以图上是同一个幻日；
# 差别只在亮度（由可行方向集 / 晶体几何决定，不由 Φ 决定）。
# 子图各自单独仿真、单独存（data/same_class.<tag>.lumice.json + data/same_class/<tag>/），两份 config **除光路过滤器与 render.view
# （帧中心）外逐字段相同**（有单测）：单一片晶 population（本仓口径 h/a=0.2，Lumice height=0.1；zenith σ=0.5°）、太阳高度 Σ=10°、
# D65、同一镜头（globe fov 30）、同一光线数、**同一绝对曝光**（ev_mode=absolute、同一 intensity_factor——两张图的亮度可直接比）。
# 晶体为什么是片晶而不是 ch7 图 6 的柱晶：`3-1-2-5` 要在两个底面之间各弹一次再从侧面出去，柱晶（h/a=2）几何上不可行（枚举器
# 在 h/a=2 下根本没有这条光路，随机朝向 MC 5×10⁷ 光线也 0 命中）；h/a=0.5 片晶取向下也全黑；只有薄片（h/a=0.2）两条都亮。
# 提纲里「暗 3 个数量级（0.006% vs 15%）」与数据不符：随机朝向 MC（energy_table 口径）h/a=0.2 为 3.34% vs 2.26%、h/a=1 为
# 14.65% vs 0.15%、h/a≥2 后者不存在；本图（片晶取向、Σ=10°）两条能量比约 1 : 0.95——实测数字见 progress / prompt 附录。
# 曝光策略：既然亮度几乎相同，issue 设想的「右图另附一档拉亮的小图」不再需要；同一绝对曝光并排即可，脚本把两张参考图
# （rectangular、absolute、同一 intensity_factor）的全天线性能量之比与两张子图的像素相关系数打印出来，作为「形状相同、亮度可比」的机械锚点。
# 帧中心机械选取（同 ch7）：全天 rectangular 参考图上 75.5° 球冠能量占比最大的候选；两条光路 Φ 相同，帧中心理应一致，脚本断言，
# 不一致则报错不静默各用各的。
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num
from halo_notes.sim.projection import frame_center, globe_view_for

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_sim as S  # noqa: E402

NAME = "same_class"
CHAPTER = CODE_DIR.parent
RATIO, ORIENTATION = 0.2, "plate"
PATHS = {"3-5": (3, 5), "3-1-2-5": (3, 1, 2, 5)}
CLASS_ID = "A60-12"                       # 两条光路所属的 Φ 类（脚本内断言）
RAY_NUM = 200_000_000
REF_RAY_NUM = 20_000_000                  # 全天参考图（选帧中心 + 量能量比）
REF_INTENSITY = 0.03                      # 参考图曝光：低到幻日核心不饱和（探针 4×10⁶ 光线 max_px 173），能量比才不被削顶
INTENSITY = 0.5                           # 正式子图曝光（absolute）：核心保留色彩、尾巴可见
GAP, MARGIN, LABEL_PX = 80, 40, 100
SKY_PX = S.SKY_PX
WIDTH, HEIGHT = 2 * SKY_PX + GAP + 2 * MARGIN, SKY_PX + 2 * MARGIN + LABEL_PX


def population_and_scene(tag: str, ray_num: int = RAY_NUM) -> tuple[list[dict], list[dict], dict]:
    return [S.crystal(RATIO, ORIENTATION)], S.single_raypath_filter(PATHS[tag]), S.scene(ray_num)


def build_reference(tag: str) -> dict:
    crystals, flts, sc = population_and_scene(tag, REF_RAY_NUM)
    return C.build_config(crystals, flts, sc, [S.reference_render(REF_INTENSITY)])


def build(tag: str, center: str) -> dict:
    crystals, flts, sc = population_and_scene(tag)
    render = S.globe_render(globe_view_for(S.CANDIDATES[center]), ev_mode="absolute", intensity_factor=INTENSITY)
    return C.build_config(crystals, flts, sc, [render])


def center_of(config: dict) -> str:
    c = frame_center(config["render"][0])
    for name, v in S.CANDIDATES.items():
        if np.linalg.norm(c - v) < 1e-6:
            return name
    raise ValueError("render.view 的帧中心不是任何候选中心")


def shape_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """两张子图（灰度）的皮尔逊相关系数：Φ 相同 ⇒ 形状相同 ⇒ 接近 1（网格线两张都有，不影响判断方向）。"""
    return float(np.corrcoef(np.asarray(a, float).ravel(), np.asarray(b, float).ravel())[0, 1])


def compose_pair(subs: dict[str, Path], center: str, out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    for i, tag in enumerate(PATHS):
        x = MARGIN + i * (SKY_PX + GAP)
        X.paste_image(ax, subs[tag], (x, MARGIN + LABEL_PX, SKY_PX, SKY_PX))
        X.add_text(ax, (x + 20, MARGIN + 30), tag, size_px=56, color="white", ha="left", family=("DejaVu Sans Mono",))
        X.add_text(ax, (x + 20, MARGIN + 82), S.CENTER_TEXT[center], size_px=30, color="#BBBBBB", ha="left", family=X.CJK_SANS)
    return X.save_canvas(fig, out)


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    for tag, faces in PATHS.items():
        assert S.class_id_of(RATIO, faces) == CLASS_ID, (tag, faces)
    ref_ray = min(args.ray_num, REF_RAY_NUM)
    centers: dict[str, str] = {}
    energies: dict[str, float] = {}
    for tag in PATHS:
        ref = sim_figure(NAME, CHAPTER, with_ray_num(build_reference(tag), ref_ray), out_root=args.out, variant=f"ref_{tag}",
                         workers=args.workers, backend=args.backend)
        image = np.asarray(X.Image.open(ref.images[0]).convert("RGB"))
        render = build_reference(tag)["render"][0]
        centers[tag], fr = S.choose_center(image, render)
        energies[tag] = S.sky_energy(image, render)
        print(f"ref_{tag}: {ref.wall_clock_s:.1f} s, ray_num={ref_ray:,}; cap energy " +
              ", ".join(f"{n}={v:.3f}" for n, v in fr.items()) + f" -> {centers[tag]}; sky energy {energies[tag]:.2f}")
    if len(set(centers.values())) != 1:
        raise RuntimeError(f"两条光路 Φ 相同、帧中心却不一致：{centers}（先查过滤器 / choose_center）")
    center = centers["3-5"]
    print(f"energy ratio 3-1-2-5 / 3-5 = {energies['3-1-2-5'] / energies['3-5']:.3f}")
    subs: dict[str, Path] = {}
    grays: dict[str, np.ndarray] = {}
    for tag in PATHS:
        res = sim_figure(NAME, CHAPTER, with_ray_num(build(tag, center), args.ray_num), out_root=args.out, variant=tag,
                         workers=args.workers, backend=args.backend)
        subs[tag] = img_path(f"same_class_{tag}", CHAPTER, "jpg", args.out)
        im = X.Image.open(res.images[0]).convert("RGB")
        im.save(subs[tag], quality=95)
        grays[tag] = np.asarray(im.convert("L"))
        print(f"{tag}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}")
    print(f"shape similarity (pixel corrcoef) = {shape_similarity(grays['3-5'], grays['3-1-2-5']):.4f}")
    out = compose_pair(subs, center, img_path(NAME, CHAPTER, "jpg", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
