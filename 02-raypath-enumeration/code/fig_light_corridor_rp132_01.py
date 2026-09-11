# 产出 ../img/light_corridor_rp132_01.png：光路 1-3-2 的光线走廊里，连接三个面质心的直线——由对称性可知共线，
# 几何约束成立。重制 2.7 旧图 img/legacy/light_corridor_rp132_01.png。
import matplotlib

matplotlib.use("Agg")

from _light_corridor_rp132 import CAMERA, PRESET, centroid_line, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import draw_raypath  # noqa: E402


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    draw_raypath(ax, centroid_line(chain), chain[0], camera=CAMERA, preset=PRESET, semantic="ray_unfolded")
    save(fig, "light_corridor_rp132_01.png")


if __name__ == "__main__":
    main()
