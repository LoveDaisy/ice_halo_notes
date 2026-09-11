# 产出 ../img/light_corridor_rp132_00.png：光路 1-3-2 展开后的"光线走廊"——晶体与幽灵晶体都画成透明线框，
# 光路依次穿过的三个面（1、3、幽灵的 2）高亮，展开直线（蓝）贯穿走廊，真实的反射出射段（红点线）作对照。
# 重制 2.5 旧图 img/legacy/light_corridor_rp132_00.png。
import matplotlib

matplotlib.use("Agg")

from _light_corridor_rp132 import CAMERA, PRESET, REFERENCE, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import RayPath, SegmentKind, draw_raypath, straighten  # noqa: E402


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    draw_raypath(ax, straighten(REFERENCE), chain[-1], camera=CAMERA, preset=PRESET,
                 semantic="ray_unfolded")
    # 真实光路在面 3 反射后的出射段：从反射点起，退居次要
    p = REFERENCE.points
    folded_exit = RayPath(p[2:], (SegmentKind.INTERNAL, SegmentKind.EXIT))
    draw_raypath(ax, folded_exit, chain[0], camera=CAMERA, preset=PRESET, semantic="ray_folded")
    save(fig, "light_corridor_rp132_00.png")


if __name__ == "__main__":
    main()
