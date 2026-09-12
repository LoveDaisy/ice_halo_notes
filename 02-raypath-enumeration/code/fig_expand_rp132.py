# 产出 ../img/expand_rp132_fn_00.png：光路 1-3-2 的反射展开——真实晶体 + 真实折线光路，关于面 3 镜像的幽灵晶体，
# 以及展开后不再转弯、从幽灵晶体的面 2 穿出的直线光路。重制 2.4 旧图 img/legacy/expand_rp132_fn_00.png。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, Corridor, HexPrism, draw_raypath, finish, new_figure,
                             render_crystal, solve_raypath, unfolded_tail)
from halo_notes.draw.style import DEFAULT_MAP, LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "expand_rp132_fn_00.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率

# 读者要看出：实体与关于面 3 镜像的幽灵是一对镜像（编号字形与位置都镜像）；红折线在面 3 反射、
# 蓝点线在展开空间里是直线，二者是同一条光线（同一入射点、同一入射段）
PATHS = {"1-3-2": [1, 3, 2]}

CAMERA = Camera(azimuth=-95, elevation=25)  # 从 -y 侧看：反射面 3 在右侧近乎侧对，幽灵晶体展开到右边


def main() -> None:
    preset = PRESETS["default"]
    geom = preset.geom
    # 本图真实光路（含蓝色出射段）与展开直线同框，展开直线改点线以示"虚"（旧图观感）
    unfolded_preset = preset.replace(style_map=DEFAULT_MAP.replace(
        ray_unfolded=LineStyle("accent_cool", linewidth=1.6, linestyle=":")))
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    crystal = HexPrism(1.0, 0.8).transformed(translation=CAMERA.to_world(-1.3, 0, 0))

    # 1-3-2：从顶面 1 靠面 3 一侧斜射入，在面 3 反射后从底面 2 出射（偏好沿用首版手调值）
    el, az = np.deg2rad(-25), np.deg2rad(-40)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    path = solve_raypath(crystal, PATHS["1-3-2"], prefer_direction=d,
                         prefer_point=crystal.centroid(crystal.face(1)) + np.array([0.5, 0.3, 0]),
                         tail=geom.incident_tail, head=geom.exit_head)
    corridor = Corridor(crystal, path)   # 构造时已断言直线穿过 1 / 3 / 幽灵 2 三个面的内部
    ghost, = corridor.ghosts

    render_crystal(ax, crystal, [path], camera=CAMERA, preset=preset, face_numbers=True)
    render_crystal(ax, ghost, camera=CAMERA, preset=preset, face_numbers=True, ghost=True)
    # 展开直线：入射段已随真实光路画过，只画从入射点起的直线（穿过面 3 处有蓝点）与穿出幽灵的出射段
    draw_raypath(ax, unfolded_tail(corridor.straight), ghost, camera=CAMERA,
                 preset=unfolded_preset, semantic="ray_unfolded")

    finish(ax, (-4.2, 4.2), (-2.36, 2.36))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
