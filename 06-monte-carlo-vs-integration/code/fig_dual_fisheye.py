# 产出 ../img/dual_fisheye.jpg：一种冰晕组合（片晶 + 柱晶 + Parry 柱晶）的 dual fisheye 全天渲染，
# 2048×1024，左圆天顶心（上半球）、右圆天底心（下半球，映日 / 映幻日可见）。重制 6.3 旧图 img/legacy/dual_fisheye.jpg。
# 正文第 43 行："2 亿光线、不到 20 秒"——正式出图 ray_num=2e8，本机墙钟记在 ../data/dual_fisheye/provenance.json。
#
# 参数来源（全部标"猜"，旧图无源 config）：
# - 太阳高度 20°：旧图幻日 / 幻日环在等面积鱼眼里离天顶 403/512 圆半径 ⇒ 天顶距 ≈ 70° ⇒ 高度 ≈ 20°
# - 波长 6 档 420–620 nm 等权：旧 template.json（IceHaloEndless 时代）
# - 晶体组合：片晶 h/a=0.3（zenith σ=1°）、柱晶 h/a=2（σ=0.3°）、Parry 柱晶（roll σ=1°），比例 100 : 50 : 15——
#   按旧图观感（幻日 / CZA 强、切弧与 Parry 弧可见、幻日环完整）反推
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.compose import Image
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "dual_fisheye"
CHAPTER = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 2048, 1024
SUN_ALTITUDE = 20.0     # 猜（见顶注）
RAY_NUM = 200_000_000   # 正文"2 亿光线"


def build() -> dict:
    plate = C.prism_crystal(1, 0.3, axis=C.plate_axis(1.0))
    column = C.prism_crystal(2, 2.0, axis=C.column_axis(0.3))
    parry = C.prism_crystal(3, 2.0, axis=C.parry_axis(0.3, 1.0))
    sc = C.scene(C.sun(SUN_ALTITUDE, spectrum=C.LEGACY_SPECTRUM), RAY_NUM,
                 [C.entry(1, 100), C.entry(2, 50), C.entry(3, 15)], max_hits=7)
    render = C.render_unit(1, C.lens("dual_fisheye_equal_area"), [WIDTH, HEIGHT], visible="full",
                           background=[0, 0, 0])
    return C.build_config([plate, column, parry], [], sc, [render])


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=__doc__ or NAME)
    cfg = with_ray_num(build(), args.ray_num)
    res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, workers=args.workers, backend=args.backend)
    out = img_path(NAME, CHAPTER, "jpg", args.out)
    Image.open(res.images[0]).convert("RGB").save(out, quality=95)
    print(f"{out}  ({res.wall_clock_s:.1f} s, ray_num={args.ray_num:,})")
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
