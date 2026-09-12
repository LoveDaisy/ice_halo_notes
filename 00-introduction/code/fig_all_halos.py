# 产出 ../img/all_halos.jpg：「各种冰晕的全天图像」——片晶 + 柱晶 + Parry + 随机取向四个 population 的
# dual fisheye 全天渲染，3600×1800，左圆天顶心（上半球）、右圆天底心（下半球）。重制 0.1 旧图 img/legacy/all_halos.jpg。
# 正文第 13 行："运行 220 秒追踪了 2 亿条光线"——正式出图 ray_num=2e8，本机墙钟见 ../data/all_halos/provenance.json。
#
# 参数来源（全部标"猜"，旧图无源 config；旧图版式经 2026-09-12 探针确认 = Lumice dual_fisheye 的天顶 / 天底双圆，
# 不是 issue 里读的"左片晶右柱晶"两幅——右圆有映日与映幻日，是下半球）：
# - 太阳高度 15°：旧图幻日离天顶 430/500 圆半径 ⇒ 天顶距 ≈ 75°
# - 波长 6 档 420–620 nm 等权：旧 template.json
# - 晶体：片晶 h/a=0.3（σ=1°）100、柱晶 h/a=2（σ=0.3°）60、Parry 柱晶 15、随机取向 h/a=1 30（旧图 22° 晕是完整圆环）
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.compose import Image
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "all_halos"
CHAPTER = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 3600, 1800
SUN_ALTITUDE = 15.0     # 猜（见顶注）
RAY_NUM = 200_000_000   # 正文"2 亿条光线"


def build() -> dict:
    plate = C.prism_crystal(1, 0.3, axis=C.plate_axis(1.0))
    column = C.prism_crystal(2, 2.0, axis=C.column_axis(0.3))
    parry = C.prism_crystal(3, 2.0, axis=C.parry_axis(0.3, 1.0))
    random = C.prism_crystal(4, 1.0, axis=C.random_axis())
    sc = C.scene(C.sun(SUN_ALTITUDE, spectrum=C.LEGACY_SPECTRUM), RAY_NUM,
                 [C.entry(1, 100), C.entry(2, 60), C.entry(3, 15), C.entry(4, 30)], max_hits=7)
    render = C.render_unit(1, C.lens("dual_fisheye_equal_area"), [WIDTH, HEIGHT], visible="full",
                           background=[0, 0, 0])
    return C.build_config([plate, column, parry, random], [], sc, [render])


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    cfg = with_ray_num(build(), args.ray_num)
    res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, workers=args.workers, backend=args.backend)
    out = img_path(NAME, CHAPTER, "jpg", args.out)
    Image.open(res.images[0]).convert("RGB").save(out, quality=95)
    print(f"{out}  ({res.wall_clock_s:.1f} s, ray_num={args.ray_num:,})")
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
