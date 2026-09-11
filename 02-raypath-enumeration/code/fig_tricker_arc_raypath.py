# 产出 ../img/Tricker_arc_raypath.png：两种特里克尔弧光路——3-1-5-7-4（侧面进出）与 1-2-3-5-1（同一底面进出），
# 各配一个柱晶 + 面编号 + 图注。重制 2.2 旧图 img/legacy/Tricker_arc_raypath.png（旧图无代码，光路按面序列用几何光学追迹反推）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, aim, annotate, finish, new_figure,
                             render_crystal, rotation, rotation_between, trace)

OUT = Path(__file__).resolve().parent.parent / "img" / "Tricker_arc_raypath.png"
WIDTH, HEIGHT, DPI = 2832, 1246, 200  # = 旧图分辨率

CAMERA = Camera(azimuth=60, elevation=24)


def direction(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """晶体标准系（c 轴沿 z、面 3 法向沿 x）里的单位方向。"""
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def pose(c_axis: np.ndarray, spin_deg: float, offset_right: float):
    """标准系 → 画面：c 轴指向 ``c_axis``、绕 c 轴自转 ``spin_deg``、沿画面横向平移。"""
    r = rotation_between([0, 0, 1], c_axis) @ rotation([0, 0, 1], spin_deg)
    return r, CAMERA.to_world(offset_right, 0, 0)


def main() -> None:
    preset = PRESETS["default"]
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    tail, head = preset.geom.incident_tail, preset.geom.exit_head
    crystal = HexPrism(1.0, 2.0)

    # 1) 3-1-5-7-4：从侧面 3 上半部斜向上射入，在顶面 1 反射后依次在 5、7 反射，从 4 出射
    d1 = direction(145, 30)
    p1 = trace(crystal, aim(crystal, 3, d1, offset=(0, 0, 0.5)), d1,
               ["refract", "reflect", "reflect", "reflect", "refract"], tail=tail, head=head)
    assert [e.face_number for e in p1.events] == [3, 1, 5, 7, 4]
    r1, t1 = pose(CAMERA.to_world(0.85, -0.25, 0.35), -75, -3.5)

    # 2) 1-2-3-5-1：从顶面 1 斜向下射入，在底面 2 反射后依次在 3、5 反射，仍从顶面 1 出射
    d2 = direction(25, -40)
    p2 = trace(crystal, aim(crystal, 1, d2, offset=(-0.5, -0.3, 0)), d2,
               ["refract", "reflect", "reflect", "reflect", "refract"], tail=tail, head=head)
    assert [e.face_number for e in p2.events] == [1, 2, 3, 5, 1]
    r2, t2 = pose(CAMERA.to_world(-0.8, -0.25, 0.4), -15, 3.5)

    for (r, t), path, caption in ((r1, t1), p1, "光路 3-1-5-7-4"), ((r2, t2), p2, "光路 1-2-3-5-1"):
        c = crystal.transformed(r, t)
        render_crystal(ax, c, [path.transformed(r, t)], camera=CAMERA, preset=preset,
                       face_numbers=True)
        annotate(ax, caption, c.centroid(), (0, -2.55), camera=CAMERA, preset=preset, ha="center")
        print([(e.face_number, e.kind.value) for e in path.events])

    finish(ax, (-6.6, 6.6), (-2.9, 2.9))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
