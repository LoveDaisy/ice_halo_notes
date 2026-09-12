# 产出 ../img/light_corridor_rp132_01.png：光路 1-3-2 的光线走廊里，连接三个面质心的直线——由对称性可知共线，
# 几何约束成立。重制 2.7 旧图 img/legacy/light_corridor_rp132_01.png。
# 读者要看出：三个面心连线（虚线，几何候选线）与真实光线（实线）并列——共线只靠对称性就能知道，
# 但它不是光线（面 1 处没有折射折点）。
import matplotlib

matplotlib.use("Agg")

from _light_corridor_rp132 import CAMERA, CORRIDOR, FACES, PRESET, centroid_line, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import draw_raypath  # noqa: E402
from halo_notes.draw.style import DEFAULT_MAP, LineStyle  # noqa: E402

PATHS = {"1-3-2": FACES}
# 几何候选线用同色虚线，与真实光线（实线）区分
SKETCH = PRESET.replace(style_map=DEFAULT_MAP.replace(
    ray_unfolded=LineStyle("accent_cool", linewidth=1.6, linestyle="--", alpha=0.75)))


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    draw_raypath(ax, CORRIDOR.straight, chain[-1], camera=CAMERA, preset=PRESET, semantic="ray_unfolded")
    draw_raypath(ax, centroid_line(chain), chain[0], camera=CAMERA, preset=SKETCH, semantic="ray_unfolded")
    save(fig, "light_corridor_rp132_01.png")


if __name__ == "__main__":
    main()
