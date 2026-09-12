# 产出 ../img/light_corridor_rp132_00.png：光路 1-3-2 展开后的"光线走廊"——晶体与幽灵晶体都画成透明线框，
# 光路依次穿过的三个面（1、3、幽灵的 2）高亮，展开直线（蓝）贯穿走廊，真实的反射出射段（红点线）作对照。
# 重制 2.5 旧图 img/legacy/light_corridor_rp132_00.png。
# 读者要看出：走廊三面高亮；蓝线是真实光线（面 1 处有折射折点），中间三个点依次落在三个走廊面上。
import matplotlib

matplotlib.use("Agg")

from _light_corridor_rp132 import CAMERA, CORRIDOR, FACES, PRESET, REFERENCE, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import draw_raypath  # noqa: E402

PATHS = {"1-3-2": FACES}


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    # 真实折线先画（退居次要的红点线）：入射段与展开直线重合、被后画的蓝线盖住，露出的是面 3 反射后的出射段
    draw_raypath(ax, REFERENCE, chain[0], camera=CAMERA, preset=PRESET, semantic="ray_folded")
    draw_raypath(ax, CORRIDOR.straight, chain[-1], camera=CAMERA, preset=PRESET, semantic="ray_unfolded")
    save(fig, "light_corridor_rp132_00.png")


if __name__ == "__main__":
    main()
