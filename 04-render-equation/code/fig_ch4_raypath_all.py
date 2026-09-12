# 产出 ../img/ch4_raypath_all.png：三种典型光路——外反射 / 折射穿透 / 内反射，各配一个晶体。
# 重制 4.1 旧图 img/legacy/ch4_raypath_all.png（旧图无代码，光路按其光学语义用几何光学追迹反推）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, Camera, HexPrism, face_sequence, face_toward, finish, new_figure,
                             render_crystal, rotation, rotation_between, solve_raypath)

OUT = Path(__file__).resolve().parent.parent / "img" / "ch4_raypath_all.png"
WIDTH, HEIGHT, DPI = 3616, 1148, 200  # 不低于旧图分辨率

# 三种典型光路的面序列（单个面 = 外反射）；读者要看出：外反射弹开 / 折射穿透 / 内反射一次再出射
PATHS = {"external": [1], "through": [4, 1], "internal": [3, 1, 5]}

CAMERA = Camera(azimuth=60, elevation=24, distance=28)  # 三个晶体横向铺开 ±4.3，默认 8 是广角（~76°）；28 → ~25° 中长焦，与其他图一致


def posed(prism: HexPrism, c_axis: np.ndarray, spin_deg: float, offset_right: float) -> HexPrism:
    """c 轴指向 ``c_axis``、绕 c 轴自转 ``spin_deg``、沿画面横向平移。"""
    r = rotation_between([0, 0, 1], c_axis) @ rotation([0, 0, 1], spin_deg)
    return prism.transformed(r, CAMERA.to_world(offset_right, 0, 0))


def main() -> None:
    preset = PRESETS["default"]
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    tail, head = preset.geom.incident_tail, preset.geom.exit_head

    # 光路按面序列用 solve_raypath 反解；偏好的入射点 / 方向沿用首版（task-draw-foundation）手调值，
    # 它们本就能走出该序列，所以构图与首版逐点相同
    # 1) 外反射：柱晶向右上倾倒、底面 1 朝观察者，光线从左前方射向底面 1 反射
    c1 = posed(HexPrism(1.0, 1.9), CAMERA.to_world(0.2, 0.7, 0.68), 15, -4.3)
    p1 = solve_raypath(c1, PATHS["external"], prefer_point=c1.centroid(c1.face(1)),
                       prefer_direction=CAMERA.to_world(1.0, -0.45, -0.5), tail=tail, head=head)

    # 2) 折射穿透：长柱晶横卧，从朝观察者的下侧面射入、从右端底面 1 射出
    c2 = posed(HexPrism(1.0, 3.2), CAMERA.to_world(0.88, -0.05, 0.47), 0, 0.0)
    face2 = face_toward(c2, CAMERA.to_world(0, -0.6, 0.8))
    assert face2 == PATHS["through"][0]
    p2 = solve_raypath(c2, PATHS["through"],
                       prefer_point=c2.centroid(c2.face(face2)) + CAMERA.to_world(0.9, 0, 0),
                       prefer_direction=CAMERA.to_world(1.0, 0.3, 0.2), tail=tail, head=head)

    # 3) 内反射：柱晶近乎直立，从左前侧面射入，在底面 1 内反射一次后从右侧面射出
    c3 = posed(HexPrism(1.0, 1.7), CAMERA.to_world(0.12, 0.95, 0.25), 20, 4.3)
    face3 = face_toward(c3, CAMERA.to_world(-1, 0, 0.6))
    assert face3 == PATHS["internal"][0]
    p3 = solve_raypath(c3, PATHS["internal"],
                       prefer_point=c3.centroid(c3.face(face3)) + CAMERA.to_world(0, -0.1, 0),
                       prefer_direction=CAMERA.to_world(1.0, 1.0, 0.2), tail=tail, head=head)

    for crystal, path in ((c1, p1), (c2, p2), (c3, p3)):
        render_crystal(ax, crystal, [path], camera=CAMERA, preset=preset)
        print(face_sequence(path))

    finish(ax, (-6.3, 6.3), (-2.0, 2.0))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
