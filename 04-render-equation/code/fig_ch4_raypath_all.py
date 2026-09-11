# 产出 ../img/ch4_raypath_all.png：三种典型光路——外反射 / 折射穿透 / 内反射，各配一个晶体。
# 重制 4.1 旧图 img/legacy/ch4_raypath_all.png（旧图无代码，光路按其光学语义用几何光学追迹反推）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, aim, face_toward, finish, new_figure,
                             render_crystal, rotation, rotation_between, trace)

OUT = Path(__file__).resolve().parent.parent / "img" / "ch4_raypath_all.png"
WIDTH, HEIGHT, DPI = 3616, 1148, 200  # 不低于旧图分辨率

CAMERA = Camera(azimuth=60, elevation=24)


def posed(prism: HexPrism, c_axis: np.ndarray, spin_deg: float, offset_right: float) -> HexPrism:
    """c 轴指向 ``c_axis``、绕 c 轴自转 ``spin_deg``、沿画面横向平移。"""
    r = rotation_between([0, 0, 1], c_axis) @ rotation([0, 0, 1], spin_deg)
    return prism.transformed(r, CAMERA.to_world(offset_right, 0, 0))


def main() -> None:
    preset = PRESETS["default"]
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    tail, head = preset.geom.incident_tail, preset.geom.exit_head

    # 1) 外反射：柱晶向右上倾倒、底面 1 朝观察者，光线从左前方射向底面 1 反射
    c1 = posed(HexPrism(1.0, 1.9), CAMERA.to_world(0.2, 0.7, 0.68), 15, -4.3)
    d1 = CAMERA.to_world(1.0, -0.45, -0.5)
    p1 = trace(c1, aim(c1, 1, d1), d1, ["reflect"], tail=tail, head=head)

    # 2) 折射穿透：长柱晶横卧，从朝观察者的下侧面射入、从右端底面 1 射出
    c2 = posed(HexPrism(1.0, 3.2), CAMERA.to_world(0.88, -0.05, 0.47), 0, 0.0)
    d2 = CAMERA.to_world(1.0, 0.3, 0.2)
    face2 = face_toward(c2, CAMERA.to_world(0, -0.6, 0.8))
    origin2 = aim(c2, face2, d2, offset=CAMERA.to_world(0.9, 0, 0))
    p2 = trace(c2, origin2, d2, ["refract", "refract"], tail=tail, head=head)

    # 3) 内反射：柱晶近乎直立，从左前侧面射入，在底面 1 内反射一次后从右侧面射出
    c3 = posed(HexPrism(1.0, 1.7), CAMERA.to_world(0.12, 0.95, 0.25), 20, 4.3)
    d3 = CAMERA.to_world(1.0, 1.0, 0.2)
    face3 = face_toward(c3, CAMERA.to_world(-1, 0, 0.6))
    origin3 = aim(c3, face3, d3, offset=CAMERA.to_world(0, -0.1, 0))
    p3 = trace(c3, origin3, d3, ["refract", "reflect", "refract"], tail=tail, head=head)

    for crystal, path in ((c1, p1), (c2, p2), (c3, p3)):
        render_crystal(ax, crystal, [path], camera=CAMERA, preset=preset)
        print([(e.face_number, e.kind.value) for e in path.events])

    finish(ax, (-6.3, 6.3), (-2.0, 2.0))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
