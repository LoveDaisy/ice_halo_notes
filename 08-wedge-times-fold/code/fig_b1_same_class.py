# 产出 ../img/same_class.jpg（图 B1「同类异路」）与三张子图 ../img/same_class_<光路>.jpg：Φ 类 A60-10 里三条长度 6 的**单光路**
# `3-1-5-2-6-7` / `3-1-5-6-2-7` / `3-1-2-5-6-7` 各自单独仿真（不是整类），rectangular 全天图裁到反日点一侧同一窗口后上下叠放——
# 三条光路同一组面、都是两次底面反射，$b^2=e$，折叠与楔相同 ⇒ 方向映射 $\Phi$ 逐点相同，画出来是幻日环上离太阳约 150° 的同一团光；
# 差别只在定义域（哪些方向的光走得通）：前两条第二次底面反射插在不同位置（`5-2` 之间 / `6-2` 之间），亮度相同——非平凡的原因是
# 底面翻转 $b$ 与所有侧面反射对易，两个 $b$ 隔多远都抵消；第三条底面 `1-2` 相邻（平凡型），同一条弧只亮靠内侧的一段、暗约 5 倍。
# 为什么不再用 `3-5` vs `3-1-2-5`（旧版）：底面 1/2 本来平行，相邻互反一次就抵消，太平凡（作者裁定，见 scratchpad author-review §4）。
# 类里的最短代表 `3-4-5-7` / `3-5-6-7` 在定向片晶里走不通（侧面进、只在侧面间反射的光撑不到下一个侧面就先碰底面，单光路渲染全黑），
# 随机取向 MC 里它们占类内一半能量，定向片晶里为零——所以片晶下这团光全由长度 6 的成员扛着。
# 每条光路两次仿真、各自单独存（data/same_class.<tag>.lumice.json + data/same_class/<tag>/）：
#   ref_<tag>：全天 rectangular 1440×720、1×10⁸ 光线、absolute 低曝光（不削顶），量全天线性能量之比与窗口内像素相关系数（「亮度比 / 形状相同」的机械锚点）；
#   <tag>：全天 rectangular 5760×2880（1/16°/px）、absolute 正式曝光 + 经纬网格，裁窗口（方位 120°–180°、仰角 −5°…+25°）存子图。
# 三份 <tag> config **除光路过滤器外逐字段相同**（有单测）：单一片晶 population（本仓口径 h/a=0.2，Lumice height=0.1；zenith σ=0.5°）、
# 太阳高度 Σ=10°（与图 B2 同场景）、D65、同一光线数、**同一绝对曝光**（ev_mode=absolute、同一 intensity_factor——三张亮度可直接比）。
# absolute 曝光按发射能量归一，与分辨率无关（Lumice CHANGELOG #287），所以参考图与子图分辨率不同也是同一曝光尺度。
import sys
from pathlib import Path

import numpy as np

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num
from halo_notes.sim.projection import rectangular_pixel_directions

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _ch8_sim as S  # noqa: E402

NAME = "same_class"
CHAPTER = CODE_DIR.parent
RATIO, ORIENTATION = 0.2, "plate"
PATHS = {"3-1-5-2-6-7": (3, 1, 5, 2, 6, 7), "3-1-5-6-2-7": (3, 1, 5, 6, 2, 7), "3-1-2-5-6-7": (3, 1, 2, 5, 6, 7)}
BASE = "3-1-5-2-6-7"                      # 能量比 / 相关系数的基准
CLASS_ID = "A60-10"                       # 三条光路所属的 Φ 类（脚本内断言）
RAY_NUM = 200_000_000
REF_RAY_NUM = 100_000_000                 # 全天参考图（量能量比 / 相关系数）：2×10⁷ 时窗口相关系数被噪声压到 0.97，1×10⁸ 才够稳
REF_INTENSITY = 3.0                       # 参考图曝光：低到亮斑核心不饱和（2×10⁷ 光线、1.0 下 max_px 65；1×10⁸ 噪声峰更低），能量比才不被削顶
INTENSITY = 8.0                           # 正式子图曝光（absolute）：主对照两条核心接近但不削顶（2×10⁷ 光线冒烟：15 px 盒均值最亮 ≈ 75/255 @2.5）、尾巴可见；反衬那条暗 5 倍仍看得见
SUB_RESOLUTION = (5760, 2880)             # 1/16°/px：窗口 60°×30° → 960×480 像素
WINDOW_AZ, WINDOW_EL = (120.0, 180.0), (-5.0, 25.0)    # 反日点一侧（方位 180° = 反日点；场景关于太阳竖直面镜像对称，只取正侧）；亮斑在仰角≈10°，上下各留 15°
STRIP_HALF_DEG = 1.5                      # 幻日环条带（仰角 = 太阳高度 ± 1.5°）方位剖面，看每条光路亮哪一段
STRIP_BINS = np.arange(138.0, 167.0, 2.0)
GAP, MARGIN, LABEL_PX = 40, 40, 90
SUB_W, SUB_H = 960, 480                   # 裁出的子图尺寸（由 SUB_RESOLUTION 与窗口决定，脚本内断言）
WIDTH, HEIGHT = SUB_W + 2 * MARGIN, len(PATHS) * (SUB_H + LABEL_PX) + (len(PATHS) - 1) * GAP + 2 * MARGIN
SUB_TEXT = {"3-1-5-2-6-7": "第二次底面反射在 5–2 之间", "3-1-5-6-2-7": "第二次底面反射在 6–2 之间", "3-1-2-5-6-7": "底面 1–2 相邻"}


def population_and_scene(tag: str, ray_num: int = RAY_NUM) -> tuple[list[dict], list[dict], dict]:
    return [S.crystal(RATIO, ORIENTATION)], S.single_raypath_filter(PATHS[tag]), S.scene(ray_num)


def build_reference(tag: str) -> dict:
    crystals, flts, sc = population_and_scene(tag, REF_RAY_NUM)
    return C.build_config(crystals, flts, sc, [S.reference_render(REF_INTENSITY)])


def build(tag: str) -> dict:
    crystals, flts, sc = population_and_scene(tag)
    render = C.render_unit(1, C.lens("rectangular"), list(SUB_RESOLUTION), visible="full", background=[0, 0, 0],
                           ev_mode="absolute", intensity_factor=INTENSITY, grid=S.sky_grid())
    return C.build_config(crystals, flts, sc, [render])


def window_luminance(image: np.ndarray, render: dict) -> np.ndarray:
    """参考图窗口内的线性亮度（形状比对用；参考图无网格线，相关系数只看光）。"""
    rows, cols = S.rectangular_window(render, WINDOW_AZ, WINDOW_EL)
    return S.linear_luminance(image)[rows, cols]


def shape_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """两张窗口图（线性亮度）的皮尔逊相关系数：Φ 相同 ⇒ 形状相同 ⇒ 接近 1；定义域不同（只亮一段）⇒ 明显小于 1。"""
    return float(np.corrcoef(np.asarray(a, float).ravel(), np.asarray(b, float).ravel())[0, 1])


def strip_profile(image: np.ndarray, render: dict, *, half_deg: float = STRIP_HALF_DEG, bins: np.ndarray = STRIP_BINS) -> np.ndarray:
    """参考图上幻日环条带（仰角 = 太阳高度 ± ``half_deg``）的线性能量沿 |方位角| 分 ``bins``（度）的直方图。"""
    dirs, weight = rectangular_pixel_directions(render)
    el = np.degrees(np.arcsin(np.clip(dirs[..., 2], -1.0, 1.0)))
    az = np.abs(np.degrees(np.arctan2(dirs[..., 1], dirs[..., 0])))
    strip = np.abs(el - S.SUN_ALTITUDE) <= half_deg
    hist, _ = np.histogram(az[strip], bins=bins, weights=(S.linear_luminance(image) * weight)[strip])
    return hist


def crop_sub(image: "X.Image.Image", render: dict) -> "X.Image.Image":
    rows, cols = S.rectangular_window(render, WINDOW_AZ, WINDOW_EL)
    box = (cols.start, rows.start, cols.stop, rows.stop)
    out = image.crop(box)
    assert out.size == (SUB_W, SUB_H), out.size
    return out


def compose_stack(subs: dict[str, Path], out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    for i, tag in enumerate(PATHS):
        y = MARGIN + i * (SUB_H + LABEL_PX + GAP)
        X.add_text(ax, (MARGIN + 12, y + 28), tag, size_px=48, color="white", ha="left", family=("DejaVu Sans Mono",))
        X.add_text(ax, (MARGIN + 12, y + 70), SUB_TEXT[tag], size_px=28, color="#BBBBBB", ha="left", family=X.CJK_SANS)
        X.paste_image(ax, subs[tag], (MARGIN, y + LABEL_PX, SUB_W, SUB_H))
    return X.save_canvas(fig, out)


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    for tag, faces in PATHS.items():
        assert S.class_id_of(RATIO, faces) == CLASS_ID, (tag, faces)
    ref_ray = min(args.ray_num, REF_RAY_NUM)
    energies: dict[str, float] = {}
    windows: dict[str, np.ndarray] = {}
    profiles: dict[str, np.ndarray] = {}
    for tag in PATHS:
        ref = sim_figure(NAME, CHAPTER, with_ray_num(build_reference(tag), ref_ray), out_root=args.out, variant=f"ref_{tag}",
                         workers=args.workers, backend=args.backend)
        image = np.asarray(X.Image.open(ref.images[0]).convert("RGB"))
        render = build_reference(tag)["render"][0]
        energies[tag] = S.sky_energy(image, render)
        windows[tag] = window_luminance(image, render)
        profiles[tag] = strip_profile(image, render)
        print(f"ref_{tag}: {ref.wall_clock_s:.1f} s, ray_num={ref_ray:,}, max_px {image.max()}; sky energy {energies[tag]:.2f}, "
              f"window energy {windows[tag].sum():.2f}")
    for tag in PATHS:
        if tag != BASE:
            print(f"energy ratio {tag} / {BASE} = {energies[tag] / energies[BASE]:.3f}; "
                  f"shape similarity (window corrcoef) = {shape_similarity(windows[BASE], windows[tag]):.4f}")
    print("strip profile (|az| bin start → linear energy): " + " | ".join(f"{lo:.0f}°" for lo in STRIP_BINS[:-1]))
    for tag in PATHS:
        print(f"  {tag}: " + " | ".join(f"{v:.2f}" for v in profiles[tag]))
    subs: dict[str, Path] = {}
    for tag in PATHS:
        res = sim_figure(NAME, CHAPTER, with_ray_num(build(tag), args.ray_num), out_root=args.out, variant=tag,
                         workers=args.workers, backend=args.backend)
        subs[tag] = img_path(f"same_class_{tag}", CHAPTER, "jpg", args.out)
        crop_sub(X.Image.open(res.images[0]).convert("RGB"), build(tag)["render"][0]).save(subs[tag], quality=95)
        print(f"{tag}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}")
    out = compose_stack(subs, img_path(NAME, CHAPTER, "jpg", args.out))
    print(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
