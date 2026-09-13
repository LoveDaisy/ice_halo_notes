# 产出 ../img/halos_2_vs_11.jpg（6a）与 ../img/halos_3_vs_2.jpg（6b）：柱晶取向下三种光路各自单独仿真的 Lumice 全天图并排——
# 6a：#2 $s$（`1-3-2`，以太阳为中心的弥散区）| #11 $b$（`3-1-6`，幻日环）——同样一次镜面反射、同样的特征值，一片 vs 一条线；
# 6b：#3 $br$（`1-2-3-5-1`，特里克尔弧）| #2 $s$（复用同一张子图）——都只有一两次反射，差别只在是否与 $R_z(\theta)$ 对易。
# 子图各自单独仿真、单独存（data/halo_columns.col_<k>.lumice.json + data/halo_columns/col_<k>/），三份 config **除光路过滤器外
# 逐字段相同**（有单测）：单一柱晶 population（h/a=2，zenith σ=0.5°，roll 均匀）、太阳高度 Σ=10°（同 3.5 / 图 5）、D65、
# 同一镜头、同一光线数。子图落 img/halo_col_<k>.jpg，两张成图由子图像素拼成（compose 单测），`halo_col_2.jpg` 在 6a/6b 是同一文件。
# 过滤器：`raypath_filter(1, 典型光路, "PBD")`——PBD 把典型光路的全部 D6 像 + 上下互换都放进来，恰好覆盖该矩阵所在的共轭类
#（`halo_notes/math/tests/test_reflection_group.py::test_d6_images_of_representative_paths_cover_exactly_the_conjugacy_class`）。
# 镜头（2026-09-13 探针，2×10⁷ 光线）：`rectangular` 全景把反日点切在两端 / 太阳在中央；`fisheye_equal_area` 朝天顶、fov 220°
# 一张图里太阳弥散区（下）、幻日环（整圈）、特里克尔弧（上，反日点处的 Λ）都看得见，且超出地平线 20° 把太阳周围的弥散区收全。
# 本脚本兼有两重职责：图 6a/6b 产出 + D6 面置换 ↔ 方向矩阵交叉验证的入口（PATHS 里的典型光路矩阵连乘 == 权威表矩阵，见 sim 单测）。
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "halo_columns"
CHAPTER = Path(__file__).resolve().parent.parent
SUN_ALTITUDE = 10.0
COLUMN_HEIGHT, ZENITH_STD = 2.0, 0.5
RAY_NUM = 200_000_000
FOV_DEG, SKY_PX = 220, 1400
# ch3 编号 → (典型光路, 角标)；光路取自 ch3 笔记「平行光路矩阵归总」，与 reflection_group.ELEMENTS 一致（单测断言）
PATHS = {2: [1, 3, 2], 11: [3, 1, 6], 3: [1, 2, 3, 5, 1]}
LABELS = {2: "#2  $s$", 11: "#11  $b$", 3: "#3  $br$"}
FIGURES = {"halos_2_vs_11": (2, 11), "halos_3_vs_2": (3, 2)}
GAP, MARGIN, LABEL_PX = 80, 40, 64
WIDTH, HEIGHT = 2 * SKY_PX + GAP + 2 * MARGIN, SKY_PX + 2 * MARGIN + LABEL_PX


def build(number: int) -> dict:
    column = C.prism_crystal(1, COLUMN_HEIGHT, axis=C.column_axis(ZENITH_STD))
    flt = C.raypath_filter(1, PATHS[number], "PBD")
    sc = C.scene(C.sun(SUN_ALTITUDE), RAY_NUM, [C.entry(1, filter=1)], max_hits=7)
    render = C.render_unit(1, C.lens("fisheye_equal_area", fov=FOV_DEG), [SKY_PX, SKY_PX],
                           view={"azimuth": 0, "elevation": 90}, visible="full", background=[0, 0, 0],
                           grid=C.grid(elevation=[C.grid_line(0, opacity=0.6, color=[0.45, 0.45, 0.45])]))  # 地平线
    return C.build_config([column], [flt], sc, [render])


def compose_pair(left: Path, right: Path, labels: tuple[str, str], out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    for i, (img, label) in enumerate(zip((left, right), labels)):
        x = MARGIN + i * (SKY_PX + GAP)
        X.paste_image(ax, img, (x, MARGIN + LABEL_PX, SKY_PX, SKY_PX))
        X.add_text(ax, (x + 20, MARGIN + LABEL_PX / 2), label, size_px=56, color="white", ha="left",
                   family=("DejaVu Sans",), math_fontfamily="cm")
    return X.save_canvas(fig, out)


def main(argv=None) -> dict[str, Path]:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    subs: dict[int, Path] = {}
    for k in PATHS:
        res = sim_figure(NAME, CHAPTER, with_ray_num(build(k), args.ray_num), out_root=args.out, variant=f"col_{k}",
                         workers=args.workers, backend=args.backend)
        subs[k] = img_path(f"halo_col_{k}", CHAPTER, "jpg", args.out)
        X.Image.open(res.images[0]).convert("RGB").save(subs[k], quality=95)
        print(f"col_{k}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,}")
    outs = {}
    for name, (a, b) in FIGURES.items():
        outs[name] = compose_pair(subs[a], subs[b], (LABELS[a], LABELS[b]), img_path(name, CHAPTER, "jpg", args.out))
        print(outs[name])
    return outs


if __name__ == "__main__":
    main(sys.argv[1:])
