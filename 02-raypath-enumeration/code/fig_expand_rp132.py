# 产出 ../img/expand_rp132_fn_00.png：光路 1-3-2 的反射展开——真实晶体 + 真实折线光路，关于面 3 镜像的幽灵晶体，
# 以及展开后不再转弯、从幽灵晶体的面 2 穿出的直线光路。重制 2.4 旧图 img/legacy/expand_rp132_fn_00.png。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, aim, draw_raypath, finish, new_figure,
                             render_crystal, straighten, trace, unfold, unfolded_tail)
from halo_notes.draw.style import DEFAULT_MAP, LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "expand_rp132_fn_00.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # = 旧图分辨率

CAMERA = Camera(azimuth=-95, elevation=25)  # 从 -y 侧看：反射面 3 在右侧近乎侧对，幽灵晶体展开到右边


def main() -> None:
    preset = PRESETS["default"]
    geom = preset.geom
    # 本图真实光路（含蓝色出射段）与展开直线同框，展开直线改点线以示"虚"（旧图观感）
    unfolded_preset = preset.replace(style_map=DEFAULT_MAP.replace(
        ray_unfolded=LineStyle("accent_cool", linewidth=1.6, linestyle=":")))
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    crystal = HexPrism(1.0, 0.8).transformed(translation=CAMERA.to_world(-1.3, 0, 0))

    # 1-3-2：从顶面 1 靠面 3 一侧斜射入，在面 3 反射后从底面 2 出射
    el, az = np.deg2rad(-25), np.deg2rad(-40)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    path = trace(crystal, aim(crystal, 1, d, offset=(0.5, 0.3, 0)), d, ["refract", "reflect", "refract"],
                 tail=geom.incident_tail, head=geom.exit_head)
    assert [e.face_number for e in path.events] == [1, 3, 2]
    ghosts = unfold(crystal, path)
    assert len(ghosts) == 1

    render_crystal(ax, crystal, [path], camera=CAMERA, preset=preset, face_numbers=True)
    render_crystal(ax, ghosts[0], camera=CAMERA, preset=preset, face_numbers=True, ghost=True)
    # 展开直线：入射段已随真实光路画过，只画从入射点起的直线与穿出幽灵晶体的出射段
    draw_raypath(ax, unfolded_tail(straighten(path)), ghosts[0], camera=CAMERA,
                 preset=unfolded_preset, semantic="ray_unfolded")

    finish(ax, (-4.2, 4.2), (-2.36, 2.36))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
