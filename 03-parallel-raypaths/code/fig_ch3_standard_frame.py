# 产出 ../img/ch3_standard_frame.png：冰晶标准坐标系——c 轴沿 z、面 3 法向沿 x，配 xyz 坐标轴与面编号。
# 重制 3.3 旧图 img/legacy/ch3_standard_frame_000.png。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from halo_notes.draw import PRESETS, Camera, HexPrism, draw_axes, finish, new_figure, render_crystal

OUT = Path(__file__).resolve().parent.parent / "img" / "ch3_standard_frame.png"
WIDTH, HEIGHT, DPI = 2400, 1350, 200  # 不低于旧图分辨率


def main() -> None:
    crystal = HexPrism(a=1.0, h=0.8)  # 片晶
    camera = Camera(azimuth=72, elevation=22)  # 面 4 正对、面 3/5 侧对，与旧图视角一致
    preset = PRESETS["default"]

    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    render_crystal(ax, crystal, camera=camera, preset=preset, face_numbers=True)
    draw_axes(ax, camera=camera, preset=preset, occluder=crystal, length=(2.1, 2.1, 1.4))
    finish(ax, (-2.9, 2.9), (-1.63, 1.63))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
