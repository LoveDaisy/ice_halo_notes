# 产出 ../img/light_corridor_rp132_02_note.png：光路 1-3-2 的光线走廊里，三面质心连线满足几何约束却违反光学约束——
# 一束从各个方向射向入射点的光线（折射后都到不了这条直线的方向），以及这条直线反推出去的"全反射路径"。
# 重制 2.8 旧图 img/legacy/light_corridor_rp132_02_note.png（旧图为示意，光线数量 / 角度不必逐条复刻）。
import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

from _light_corridor_rp132 import CAMERA, PRESET, centroid_line, new_corridor_figure, save  # noqa: E402
from halo_notes.draw import RayPath, SegmentKind, annotate, draw_raypath  # noqa: E402
from halo_notes.draw.geometry import unit  # noqa: E402


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    line = centroid_line(chain)
    draw_raypath(ax, line, chain[0], camera=CAMERA, preset=PRESET, semantic="ray_unfolded")

    entry, d_line = line.points[0], unit(line.points[1] - line.points[0])
    tail = PRESET.geom.incident_tail

    # 折射路径：从画面左上方以一组不同入射角射向同一入射点的光线，只画到入射面为止——
    # 它们折射进晶体后的方向与走廊直线都对不上（示意，不做逐条追迹）
    for k, tilt in enumerate(np.linspace(-0.3, 0.3, 5)):
        d = -unit(CAMERA.to_world(-0.6 + 1.2 * tilt, 1.0, 0.15))
        ray = RayPath([entry - d * tail * (1.15 - 0.05 * k), entry], (SegmentKind.INCIDENT,))
        draw_raypath(ax, ray, camera=CAMERA, preset=PRESET, semantic="ray_folded")
    annotate(ax, "折射路径：不满足折射定律", entry, (-2.6, 1.6), camera=CAMERA, preset=PRESET,
             va="bottom")

    # 全反射路径：把走廊直线沿反方向延长到晶体外——要产生这条内部直线，外面的光线得从这里来，
    # 但这个角度在底面上只会全反射
    tir = RayPath([entry - d_line * tail, entry], (SegmentKind.INCIDENT,))
    draw_raypath(ax, tir, camera=CAMERA, preset=PRESET, semantic="ray_folded")
    annotate(ax, "全反射路径", entry - d_line * tail, (-0.1, -0.5), camera=CAMERA, preset=PRESET,
             ha="center")

    save(fig, "light_corridor_rp132_02_note.png")


if __name__ == "__main__":
    main()
