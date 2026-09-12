# 产出 ../img/halos_3-5.jpg：只含 3-5 光路的冰晕——**只开 P（C6 旋转）对称、不开 D（垂直镜面）对称**，
# 于是幻日只出一侧，而上下切弧 / Parry 弧 / 22° 晕完整（正文第 49 行的思考题）。重制 1.5 旧图 img/legacy/halos_3-5.jpg。
# 核心语义：filter.symmetry == "P"（不是 "PBD"）——有单测读 ../data/halos_3-5.lumice.json 断言。
#
# 参数来源（旧图无源 config，标"猜"的按旧图量取）：
# - 镜头：旧图 22° 晕半径 ≈ 0.1425×图宽 = 513 px ⇒ 焦距 ≈ 1270 px；Lumice linear 的 fov 是**短边**全视场（实测，见 config.lens）
#   ⇒ fov = 2·atan(1200/1270) ≈ 87°
# - 太阳高度 15°：旧图太阳在画面中心、地平线在 0.64 图高处 ⇒ atan(0.14×2400/1269) ≈ 15°；相机看向太阳（az 0, el 15）
# - 晶体：随机取向（22° 晕）、片晶（幻日）、柱晶（切弧）、Parry（Parry 弧）四个 population 共用同一条 3-5 过滤器
# - 波长 6 档 420–620 nm 等权：旧 template.json
import sys
from pathlib import Path

from halo_notes.sim import config as C
from halo_notes.sim.compose import Image
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "halos_3-5"
CHAPTER = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 3600, 2400
SUN_ALTITUDE = 15.0   # 猜（见顶注）
RAY_NUM = 200_000_000
RAYPATH, SYMMETRY = [3, 5], "P"


def build() -> dict:
    random = C.prism_crystal(1, 1.0, axis=C.random_axis())
    plate = C.prism_crystal(2, 0.3, axis=C.plate_axis(1.0))
    column = C.prism_crystal(3, 2.0, axis=C.column_axis(0.3))
    parry = C.prism_crystal(4, 2.0, axis=C.parry_axis(0.3, 1.0))
    flt = C.raypath_filter(1, RAYPATH, SYMMETRY)
    sc = C.scene(C.sun(SUN_ALTITUDE, spectrum=C.LEGACY_SPECTRUM), RAY_NUM,
                 [C.entry(1, 60, filter=1), C.entry(2, 100, filter=1), C.entry(3, 60, filter=1), C.entry(4, 25, filter=1)],
                 max_hits=3)
    render = C.render_unit(1, C.lens("linear", fov=87), [WIDTH, HEIGHT], view={"azimuth": 0, "elevation": SUN_ALTITUDE},
                           visible="full", background=[0, 0, 0],
                           grid=C.grid(elevation=[C.grid_line(0, opacity=0.8, color=[1, 1, 1])]))  # 地平线：horizon=true 是固定暗红，旧图是白线，改用 0° 纬线
    return C.build_config([random, plate, column, parry], [flt], sc, [render])


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
