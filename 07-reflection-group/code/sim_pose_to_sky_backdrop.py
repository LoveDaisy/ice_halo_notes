# 产出 7.5（fig_pose_to_sky.py / fig_pose_to_sky_gif.py）右栏的两张 Lumice 底图：data/pose_to_sky_backdrop/col_3/img_01.png
#（#3 $br$ 类，帧中心在反日点一侧）与 data/pose_to_sky_backdrop/col_2/img_01.png（#2 $s$ 类，帧中心在太阳一侧）。
# 与图 6 **同一份仿真**：crystal / filter / scene 三段逐字段取自 fig_halos_columns.population_and_scene(k)（复合过滤器 =
# 该矩阵类的全部光路，R2-1；有单测），只换 render 段——`globe` 球面外视（R2-3，与 3.5 / 3.6 / 6.1 / 6.5 同一语言）、fov 30、
# 帧中心 = `_pose_to_sky.backdrop_center(k)`（该行参考点与三个样本天空点质心的角平分方向，Lumice globe 语义
# view = (az + 180°, −el) 由 `globe_view_for` 换算），同一套 30° 经纬网格；1000×1000。正式图脚本读这两张 png 作底、用
# `halo_notes.sim.projection.project` 把样本点 / 公式曲线投到同一像素坐标叠加，对齐核验见 test_figures（7.5）。
# 不是章节插图，所以不落 img/，只落 data/（LFS）；光线数与图 6 相同（2×10⁸，每张 ~40 s）。
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.figure import parse_args, sim_figure, with_ray_num

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import _pose_to_sky as P  # noqa: E402
import fig_halos_columns as HC  # noqa: E402

NAME = "pose_to_sky_backdrop"
CHAPTER = CODE_DIR.parent
BACKDROP_PX = 1000
FOV = HC.FOV_DEG
ROWS = (3, 2)


def build(number: int) -> dict:
    crystals, flts, sc = HC.population_and_scene(number)
    render = C.render_unit(1, C.lens(HC.LENS_TYPE, fov=FOV), [BACKDROP_PX, BACKDROP_PX], view=P.backdrop_view(number),
                           visible="full", background=[0, 0, 0], grid=HC.sky_grid())
    return C.build_config(crystals, flts, sc, [render])


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
