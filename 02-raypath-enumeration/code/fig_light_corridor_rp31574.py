# 产出 ../img/light_corridor_rp31574_00.png：光路 3-1-5-7-4（三次内反射）展开后的光线走廊——晶体 + 三个级联幽灵晶体
# 全部画成透明线框，五个走廊面高亮，展开直线（蓝）贯穿，真实折线光路（红点线）作对照。
# 重制 2.6 旧图 img/legacy/light_corridor_rp31574_00.png。
# 读者要看出：走廊布局与旧图一致——关于端面 1 镜像的幽灵沿轴延长，关于 5、7 镜像的幽灵阶梯下行；五个走廊面
# 全部可辨（尤其端面 1）；入射锥体在晶体外；折线与直线共入射点（同一条光线）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, Corridor, HexPrism, draw_raypath, finish, frame, new_figure,
                             render_corridor, rotation_from_frames, solve_raypath)

OUT = Path(__file__).resolve().parent.parent / "img" / "light_corridor_rp31574_00.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率

PATHS = {"3-1-5-7-4": [3, 1, 5, 7, 4]}
CAMERA = Camera(azimuth=-60, elevation=28, distance=14)  # 四个晶体串起来很长，相机退远些减小透视


def direction(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def main() -> None:
    preset = PRESETS["default"]
    geom = preset.geom
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)

    # 与 2.2 左图同一条光路：柱晶，从侧面 3 上半部斜向上射入，在 1、5、7 反射后从 4 出射（偏好沿用首版手调值）
    prism = HexPrism(1.0, 2.0)
    path = solve_raypath(prism, PATHS["3-1-5-7-4"], prefer_direction=direction(145, 30),
                         prefer_point=prism.centroid(prism.face(3)) + np.array([0, 0, 0.5]),
                         tail=geom.incident_tail, head=geom.exit_head)
    # 摆姿态复现旧图布局：c 轴（关于端面 1 镜像后幽灵沿轴延长的方向）指向画面右方略偏下；
    # 入射面 3 的法向朝观察者略偏上。于是关于 5 镜像的幽灵 2 向下错开（n5 在 ⊥c 平面里离 n3 120°），
    # 关于 7 镜像的幽灵 3 再沿 -n3 向下、向后错开（镜像把幽灵 2 的 n7 变成 n7+n5 = -n3）——阶梯下行
    r = rotation_from_frames([0, 0, 1], prism.normal(prism.face(3)),
                             CAMERA.to_world(1.0, -0.15, 0.5), CAMERA.to_world(0.0, 0.3, 0.95))
    crystal, path = prism.transformed(r), path.transformed(r)
    corridor = Corridor(crystal, path)

    chain = render_corridor(ax, crystal, path, camera=CAMERA, preset=preset)
    assert len(chain) == 4
    # 真实折线先画（退居次要）：入射段与展开直线重合、被后画的蓝线盖住
    draw_raypath(ax, path, crystal, camera=CAMERA, preset=preset, semantic="ray_folded")
    draw_raypath(ax, corridor.straight, chain[-1], camera=CAMERA, preset=preset, semantic="ray_unfolded")

    finish(ax, *frame(CAMERA, [c.vertices for c in chain] + [path.points, corridor.straight.points],
                      WIDTH, HEIGHT))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
