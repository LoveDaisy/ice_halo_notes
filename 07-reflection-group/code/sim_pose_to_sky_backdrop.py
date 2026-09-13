# 产出 7.5（fig_pose_to_sky.py / fig_pose_to_sky_gif.py）右栏的两张 Lumice 底图：data/pose_to_sky_backdrop/col_3/img_01.png
#（#3 $br$，反日点为视场中心）与 data/pose_to_sky_backdrop/col_2/img_01.png（#2 $s$，太阳为视场中心）。
# 与图 6 **同一份仿真**：crystal / filter / scene 三段逐字段取自 fig_halos_columns.build(k)（有单测），只换 render 段——
# `fisheye_equal_area`，视场中心对准该行的晕心，fov 上行 120°（公式特里克尔弧地平线以上最远离反日点 40°）、下行 160°
#（三个样本天空点离太阳 59–70°，都在地平线下），同一套 30° 经纬网格；1000×1000。正式图脚本读这两张 png 作底、用
# `halo_notes.sim.projection` 把样本点 / 公式曲线投到同一像素坐标叠加，对齐核验见 test_figures（7.5）。
# 不是章节插图，所以不落 img/，只落 data/（LFS）；光线数与图 6 相同（2×10⁸，每张 ~40 s）。
import importlib.util
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args, sim_figure, with_ray_num

NAME = "pose_to_sky_backdrop"
CODE_DIR = Path(__file__).resolve().parent
CHAPTER = CODE_DIR.parent


def _load_halo_columns():
    """同目录的 fig_halos_columns.py：按路径加载（同 _pose_to_sky._load_tricker_arc 的做法），不复制 population / filter。"""
    spec = importlib.util.spec_from_file_location("fig_halos_columns", CODE_DIR / "fig_halos_columns.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("fig_halos_columns", mod)
    spec.loader.exec_module(mod)
    return mod


HC = _load_halo_columns()
BACKDROP_PX = 1000
FOV = {3: 120, 2: 160}
ROWS = (3, 2)


def build(number: int) -> dict:
    base = HC.build(number)
    render = C.render_unit(1, C.lens(HC.LENS_TYPE, fov=FOV[number]), [BACKDROP_PX, BACKDROP_PX],
                           view=HC.VIEW[HC.VIEW_CENTERS[number]], visible="full", background=[0, 0, 0],
                           grid=HC.sky_grid())
    return C.build_config(base["crystal"], base["filter"], base["scene"], [render])


def main(argv=None) -> dict[int, Path]:
    args = parse_args(argv, default_ray_num=HC.RAY_NUM, description=NAME)
    outs = {}
    for k in ROWS:
        res = sim_figure(NAME, CHAPTER, with_ray_num(build(k), args.ray_num), out_root=args.out, variant=f"col_{k}",
                         workers=args.workers, backend=args.backend)
        outs[k] = res.images[0]
        print(f"col_{k}: {res.wall_clock_s:.1f} s, ray_num={args.ray_num:,} -> {res.images[0]}")
    return outs


if __name__ == "__main__":
    main(sys.argv[1:])
