# 产出 ../img/geo_validation.png：光路的几何约束——1-3-2 几何上成立（真实追迹）vs 1-3-1 几何上不成立（示意折线）。
# 重制 2.3 旧图 img/legacy/geo_validation.png。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, RayPath, SegmentKind, aim, annotate, finish,
                             new_figure, render_crystal, trace)

OUT = Path(__file__).resolve().parent.parent / "img" / "geo_validation.png"
WIDTH, HEIGHT, DPI = 2832, 1246, 200  # = 旧图分辨率

CAMERA = Camera(azimuth=-30, elevation=25)  # 面 8 / 3 在前，与旧图一致（反射面 3 要正对观察者）


def main() -> None:
    preset = PRESETS["default"]
    geom = preset.geom
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    crystal = HexPrism(1.0, 0.8)
    left, right = CAMERA.to_world(-3.0, 0.1, 0), CAMERA.to_world(3.0, 0.1, 0)

    # 左：1-3-2 真实追迹——从顶面 1 靠近面 3 的一侧斜射入，在侧面 3 反射后从底面 2 出射
    c1 = crystal.transformed(translation=left)
    el, az = np.deg2rad(-25), np.deg2rad(-40)  # 带一点方位分量，出射段才不会正对/背对观察者
    d1 = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    p1 = trace(c1, aim(c1, 1, d1, offset=(0.5, 0.3, 0)), d1, ["refract", "reflect", "refract"],
               tail=geom.incident_tail, head=geom.exit_head)
    assert [e.face_number for e in p1.events] == [1, 3, 2]
    render_crystal(ax, c1, [p1], camera=CAMERA, preset=preset, face_numbers=True)
    annotate(ax, "光路 1-3-2：几何上成立", c1.centroid(), (0, -1.75), camera=CAMERA, preset=preset,
             ha="center")

    # 右：1-3-1 几何上不成立——光线从顶面进入后向下走，在竖直侧面 3 反射不改变竖直分量，
    # 不可能回到顶面。这里不经过 trace()（追迹出来不会是这条路），只画"声称的"折线示意：
    # 两条都射向面 3 上同一点的入射线，第二条就是"从 3 回到 1"那段的反向
    c2 = crystal.transformed(translation=right)
    hit = c2.centroid(c2.face(3)) + np.array([0, 0, -0.05])
    top = c2.centroid(c2.face(1))
    for a_on_top in (top + np.array([-0.3, 0.35, 0]), top + np.array([0.1, 0.5, 0])):
        d = (hit - a_on_top) / np.linalg.norm(hit - a_on_top)
        sketch = RayPath([a_on_top - d * geom.incident_tail, a_on_top, hit],
                         (SegmentKind.INCIDENT, SegmentKind.INTERNAL))
        render_crystal(ax, c2, [sketch], camera=CAMERA, preset=preset, face_numbers=True)
    annotate(ax, "光路 1-3-1：几何上不成立", c2.centroid(), (0, -1.75), camera=CAMERA, preset=preset,
             ha="center")

    finish(ax, (-5.6, 5.6), (-2.46, 2.46))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
