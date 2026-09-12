# 产出 ../img/rp1-3_plt0.5_s25_i2_note.png：片晶 1-3 光路（面 1 入、面 3 出）的全天鱼眼渲染 = 只剩环天顶弧，
# 左：天顶心等面积鱼眼圆（细白圆边）+ 天顶（红点）/ 太阳位置（黄点）/ 环天顶弧（五个小红箭头）标注；
# 右上文字"片晶光路 1-3 全天鱼眼视图 / 太阳高度 25°"；右下"光路 1-3" + 白线框六方片晶 + 红色光路（halo_notes.draw 画）。
# 2880×1910 黑底。重制 2.1 旧图 img/legacy/rp1-3_plt0.5_s25_i2_note.png（psd 标注层全部代码化）。
#
# 旧文件名 rp1-3_plt0.5_s25_i2 的解读：rp1-3 = 光路 1-3；plt0.5 = 片晶 (plate) c/a = 0.5（猜）；s25 = 太阳高度 25°；
# i2 含义不明（猜：旧渲染器的 intensity 档位），不影响出图。原图是 3600×1800 dual fisheye 取左圆，这里直接单圆 1800×1800 渲染。
# 标注坐标按旧图量取（像素）；深色 inset 预设 DARK_INSET 定义在 halo_notes.sim.compose（待裁定是否上提到 draw）。
import sys
from pathlib import Path

import numpy as np

from halo_notes.draw import Camera
from halo_notes.sim import config as C
from halo_notes.sim import compose as X
from halo_notes.sim.figure import img_path, parse_args, sim_figure, with_ray_num

NAME = "rp1-3_plt0.5_s25_i2_note"
CHAPTER = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 2880, 1910
SUN_ALTITUDE, PLATE_HEIGHT, RAYPATH = 25.0, 0.5, [1, 3]
RAY_NUM = 100_000_000
FISHEYE = 1800                       # 鱼眼圆直径（像素）
CENTER = (955, 950)                  # 圆心 = 天顶（旧图量取）
RED, YELLOW = "#F0483C", "#F2C230"


def build() -> dict:
    plate = C.prism_crystal(1, PLATE_HEIGHT, axis=C.plate_axis(1.0))
    flt = C.raypath_filter(1, RAYPATH)
    sc = C.scene(C.sun(SUN_ALTITUDE, spectrum=C.LEGACY_SPECTRUM), RAY_NUM, [C.entry(1, 100, filter=1)], max_hits=3)
    render = C.render_unit(1, C.lens("fisheye_equal_area", fov=180), [FISHEYE, FISHEYE], view={"elevation": 90},
                           visible="full", background=[0, 0, 0])
    return C.build_config([plate], [flt], sc, [render])


def sky_point(zenith_deg: float, azimuth_deg: float = 0.0) -> tuple[float, float]:
    """等面积鱼眼（fov 180）里天顶距 / 方位 → 像素；方位 0（太阳）在圆的正下方，探针实测。"""
    r = FISHEYE / 2 * np.sin(np.radians(zenith_deg) / 2) / np.sin(np.radians(45))
    a = np.radians(azimuth_deg)
    return CENTER[0] + r * np.sin(a), CENTER[1] + r * np.cos(a)


def compose_note(sky_image: Path, out: Path) -> Path:
    fig, ax = X.pixel_canvas(WIDTH, HEIGHT, "black")
    X.paste_image(ax, sky_image, (CENTER[0] - FISHEYE / 2, CENTER[1] - FISHEYE / 2, FISHEYE, FISHEYE))
    X.add_circle(ax, CENTER, FISHEYE / 2, color="#D0D0D0", width_px=2)

    # 天顶：红点 + 从左上斜下来的箭头
    X.add_dot(ax, CENTER, radius_px=9, color=RED)
    X.add_arrow(ax, (842, 814), (935, 928), color=RED, width_px=5)
    X.add_text(ax, (814, 770), "天顶", size_px=58, color="#DDDDDD")
    # 太阳位置：黄点（天顶距 90−25）+ 箭头
    sun = sky_point(90 - SUN_ALTITUDE)
    X.add_dot(ax, sun, radius_px=9, color=YELLOW)
    X.add_arrow(ax, (842, 1526), (sun[0] - 20, sun[1] - 24), color=RED, width_px=5)
    X.add_text(ax, (801, 1473), "太阳位置", size_px=58, color="#DDDDDD")
    # 环天顶弧：五个小箭头从弧外侧指向弧（弧在太阳方向、天顶距约 18°）
    for az in (-24, -12, 0, 12, 24):
        tail, head = sky_point(29, az), sky_point(23, az)
        X.add_arrow(ax, tail, head, color=RED, width_px=4, head_px=18)
    X.add_text(ax, (1221, 1296), "环天顶弧", size_px=58, color="#DDDDDD")

    X.add_text(ax, (2383, 334), f"片晶光路 {RAYPATH[0]}-{RAYPATH[1]} 全天鱼眼视图", size_px=58, color="#DDDDDD")
    X.add_text(ax, (2383, 400), f"太阳高度 {SUN_ALTITUDE:g}°", size_px=58, color="#DDDDDD")
    X.add_text(ax, (2376, 1022), f"光路 {RAYPATH[0]}-{RAYPATH[1]}", size_px=58, color="#DDDDDD")
    path = X.add_crystal_inset(fig, (2010, 1090, 780, 720), (WIDTH, HEIGHT), raypath=RAYPATH, height_ratio=PLATE_HEIGHT,
                               camera=Camera(azimuth=-40, elevation=24, distance=9),
                               prefer_point=(0.4, 0.0, PLATE_HEIGHT / 2),          # 旧图：从顶面偏出射侧进（片晶太薄，从正中进到不了面 3）
                               prefer_direction=(0.55, 0.2, -0.8))                  # 斜向右前下方，从面 3（法向 +x，相机 az −40 时在右前）出
    compose_note.last_path = path  # 供单测核验面序列
    return X.save_canvas(fig, out)


def main(argv=None) -> Path:
    args = parse_args(argv, default_ray_num=RAY_NUM, description=NAME)
    cfg = with_ray_num(build(), args.ray_num)
    res = sim_figure(NAME, CHAPTER, cfg, out_root=args.out, workers=args.workers, backend=args.backend)
    out = compose_note(res.images[0], img_path(NAME, CHAPTER, "png", args.out))
    print(f"{out}  ({res.wall_clock_s:.1f} s, ray_num={args.ray_num:,})")
    return out


if __name__ == "__main__":
    main(sys.argv[1:])
