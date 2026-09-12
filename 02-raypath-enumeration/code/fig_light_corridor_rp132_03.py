# 产出 ../img/light_corridor_rp132_03.png：光路 1-3-2 的光线走廊里，同时满足光学约束的解——直线贴着面 1 / 面 3
# 的棱边、几乎垂直穿过两个底面（入/出射角接近 0）。重制 2.9 旧图 img/legacy/light_corridor_rp132_03.png。
# 读者要看出：蓝线是真实光线，贴着面 1 / 面 3 的棱边、近乎垂直地穿过走廊。
import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

from _light_corridor_rp132 import CAMERA, CRYSTAL, FACES, PRESET, new_corridor_figure, save, solve_132  # noqa: E402
from halo_notes.draw import Corridor, draw_raypath  # noqa: E402
from halo_notes.draw.raypath import N_ICE  # noqa: E402

PATHS = {"1-3-2": FACES}


def main() -> None:
    fig, ax, chain = new_corridor_figure()
    # 晶体内直线与底面法向夹角 θ≈3.6°（正文里 cos θ = 0.998），朝面 3 倾斜；入射角按 Snell 反推
    theta = np.arccos(0.998)
    theta_in = np.arcsin(N_ICE * np.sin(theta))
    d = np.array([np.sin(theta_in), 0.0, -np.cos(theta_in)])
    # 入射点离面 1 / 面 3 的棱边多远，取决于直线穿过整个厚度 h 时横向走过的距离
    reach = CRYSTAL.h * np.tan(theta)
    x_edge = np.sqrt(3) / 2 * CRYSTAL.a
    path = solve_132(d, offset=(x_edge - reach / 2, 0.0, 0.0))
    draw_raypath(ax, Corridor(CRYSTAL, path).straight, chain[-1], camera=CAMERA, preset=PRESET,
                 semantic="ray_unfolded")
    save(fig, "light_corridor_rp132_03.png")


if __name__ == "__main__":
    main()
