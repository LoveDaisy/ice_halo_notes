# 产出 ../img/halos_2_vs_11.jpg（6a）与 ../img/halos_3_vs_2.jpg（6b）：柱晶取向下三种光路各自单独仿真的 Lumice 全天图并排——
# 6a：#2 $s$（`1-3-2`，以太阳为中心的弥散区）| #11 $b$（`3-1-6`，幻日环）——同样一次镜面反射、同样的特征值，一片 vs 一条线；
# 6b：#3 $br$（`1-2-3-5-1`，特里克尔弧）| #2 $s$（复用同一张子图）——都只有一两次反射，差别只在是否与 $R_z(\theta)$ 对易。
# 子图各自单独仿真、单独存（data/halo_columns.col_<k>.lumice.json + data/halo_columns/col_<k>/），三份 config **除光路过滤器与
# render.view（视场中心）外逐字段相同**（有单测）：单一柱晶 population（h/a=2，zenith σ=0.5°，roll 均匀）、太阳高度 Σ=10°
#（同 3.5 / 图 5）、D65、同一镜头、同一光线数。子图落 img/halo_col_<k>.jpg，两张成图由子图像素拼成（compose 单测），
# `halo_col_2.jpg` 在 6a/6b 是同一文件。
# 过滤器：`raypath_filter(1, 典型光路, "PBD")`——PBD 把典型光路的全部 D6 像 + 上下互换都放进来，恰好覆盖该矩阵所在的共轭类
#（`halo_notes/math/tests/test_reflection_group.py::test_d6_images_of_representative_paths_cover_exactly_the_conjugacy_class`）。
# 镜头（R1-5，2026-09-13 探针，2×10⁷ 光线）：`fisheye_equal_area`，每张子图以它自己那种晕的中心为视场中心——#2 / #11 对准太阳、
# #3 对准反日点（`view.azimuth/elevation` 是相机朝向，Lumice 方位角 0° = +x = 太阳方向）。fov 探了 240 / 300 / 340：幻日环离太阳
# 最远 180° − 2Σ = 160°，要整圈装进去 fov ≥ 320°，取 340°（三张子图同一镜头，config 单测要求）。经纬网格每 30° 一条
#（低透明度，地平线亮一档），`label` 探针显示 CLI 把角度标签画在画面边缘、字号 ~10 px，1400 px 子图里不可读，关掉。
# Σ=10° 下特里克尔弧只是反日点处一个小 Λ（+ 地平线下两小段）；Σ=20° 的探针图（scratchpad probes/）里它是一个大 Λ——按 issue
# 不自行改 Σ，留给作者裁定。
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
SKY_PX = 1400
LENS_TYPE, FOV_DEG = "fisheye_equal_area", 340   # 探针见顶注
# 视场中心：每张子图对准它自己那种晕的中心——#2 / #11 太阳（az 0 / el Σ）、#3 反日点（az 180 / el Σ）
VIEW_CENTERS = {2: "sun", 11: "sun", 3: "anthelic"}
VIEW = {"sun": {"azimuth": 0, "elevation": SUN_ALTITUDE}, "anthelic": {"azimuth": 180, "elevation": SUN_ALTITUDE}}
CENTER_TEXT = {"sun": "视场中心：太阳", "anthelic": "视场中心：反日点"}
GRID_STEP, GRID_OPACITY, GRID_COLOR, GRID_LABEL = 30, 0.35, [0.55, 0.55, 0.55], False
# ch3 编号 → (典型光路, 角标)；光路取自 ch3 笔记「平行光路矩阵归总」，与 reflection_group.ELEMENTS 一致（单测断言）
PATHS = {2: [1, 3, 2], 11: [3, 1, 6], 3: [1, 2, 3, 5, 1]}
LABELS = {2: "#2  $s$", 11: "#11  $b$", 3: "#3  $br$"}
FIGURES = {"halos_2_vs_11": (2, 11), "halos_3_vs_2": (3, 2)}
GAP, MARGIN, LABEL_PX = 80, 40, 100
WIDTH, HEIGHT = 2 * SKY_PX + GAP + 2 * MARGIN, SKY_PX + 2 * MARGIN + LABEL_PX


def sky_grid(*, step: int = GRID_STEP, opacity: float = GRID_OPACITY, label: bool = GRID_LABEL) -> dict:
    """经纬网格：仰角 / 方位角每 ``step`` 度一条（低透明度），地平线单独一条更亮（`horizon: true` 是不可配色的暗红，不用）。"""
    elev = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(-90 + step, 90, step) if v != 0]
    elev.append(C.grid_line(0, opacity=min(1.0, opacity * 2), color=GRID_COLOR))
    lon = [C.grid_line(v, opacity=opacity, color=GRID_COLOR) for v in range(0, 360, step)]
    return C.grid(elevation=elev, longitude=lon, extra={"label": label})


def build(number: int, *, fov: float = FOV_DEG, grid: dict | None = None) -> dict:
    column = C.prism_crystal(1, COLUMN_HEIGHT, axis=C.column_axis(ZENITH_STD))
    flt = C.raypath_filter(1, PATHS[number], "PBD")
    sc = C.scene(C.sun(SUN_ALTITUDE), RAY_NUM, [C.entry(1, filter=1)], max_hits=7)
    render = C.render_unit(1, C.lens(LENS_TYPE, fov=fov), [SKY_PX, SKY_PX], view=VIEW[VIEW_CENTERS[number]],
                           visible="full", background=[0, 0, 0], grid=sky_grid() if grid is None else grid)
    return C.build_config([column], [flt], sc, [render])


def compose_pair(left: Path, right: Path, numbers: tuple[int, int], out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    for i, (img, k) in enumerate(zip((left, right), numbers)):
        x = MARGIN + i * (SKY_PX + GAP)
        X.paste_image(ax, img, (x, MARGIN + LABEL_PX, SKY_PX, SKY_PX))
        X.add_text(ax, (x + 20, MARGIN + 30), LABELS[k], size_px=56, color="white", ha="left",
                   family=("DejaVu Sans",), math_fontfamily="cm")
        X.add_text(ax, (x + 20, MARGIN + 82), CENTER_TEXT[VIEW_CENTERS[k]], size_px=30, color="#BBBBBB", ha="left",
                   family=X.CJK_SANS)
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
        outs[name] = compose_pair(subs[a], subs[b], (a, b), img_path(name, CHAPTER, "jpg", args.out))
        print(outs[name])
    return outs


if __name__ == "__main__":
    main(sys.argv[1:])
