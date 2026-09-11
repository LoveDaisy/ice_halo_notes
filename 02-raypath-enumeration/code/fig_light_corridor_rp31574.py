# 产出 ../img/light_corridor_rp31574_00.png：光路 3-1-5-7-4（三次内反射）展开后的光线走廊——晶体 + 三个级联幽灵晶体
# 全部画成透明线框，五个走廊面高亮，展开直线（蓝）贯穿，真实折线光路（红点线）作对照。
# 重制 2.6 旧图 img/legacy/light_corridor_rp31574_00.png。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, aim, draw_raypath, finish, frame, new_figure,
                             render_corridor, rotation, rotation_between, straighten, trace)

OUT = Path(__file__).resolve().parent.parent / "img" / "light_corridor_rp31574_00.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率

CAMERA = Camera(azimuth=-60, elevation=28, distance=12)  # 四个晶体串起来很长，相机退远些减小透视


def main() -> None:
    preset = PRESETS["default"]
    geom = preset.geom
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)

    # 与 2.2 左图同一条光路：柱晶，从侧面 3 上半部斜向上射入，在 1、5、7 反射后从 4 出射
    prism = HexPrism(1.0, 2.0)
    el, az = np.deg2rad(30), np.deg2rad(145)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    path = trace(prism, aim(prism, 3, d, offset=(0, 0, 0.5)), d,
                 ["refract", "reflect", "reflect", "reflect", "refract"],
                 tail=geom.incident_tail, head=geom.exit_head)
    assert [e.face_number for e in path.events] == [3, 1, 5, 7, 4]
    # 摆姿态：让展开直线（晶体内第一段的方向）沿画面横向略向下，再绕它自转到侧面朝观察者
    d_inside = path.points[2] - path.points[1]
    along = CAMERA.to_world(1, -0.25, 0.3)
    r = rotation(along, 90) @ rotation_between(d_inside, along)
    crystal, path = prism.transformed(r), path.transformed(r)

    chain = render_corridor(ax, crystal, path, camera=CAMERA, preset=preset)
    assert len(chain) == 4
    straight = straighten(path)
    draw_raypath(ax, path, crystal, camera=CAMERA, preset=preset, semantic="ray_folded")
    draw_raypath(ax, straight, chain[-1], camera=CAMERA, preset=preset, semantic="ray_unfolded")

    finish(ax, *frame(CAMERA, [c.vertices for c in chain] + [path.points, straight.points], WIDTH, HEIGHT))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
