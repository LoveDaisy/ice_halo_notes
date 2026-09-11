# 产出 ../img/crystal03.png：六方柱冰晶的面编号约定（底面 1/2，侧面 3–8 绕 c 轴逆时针递增）。
# 重制 0.2 旧图 img/legacy/Crystal03.png 的左半（晶体 + 面编号）；右侧展开图属另一能力，不做。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from halo_notes.draw import PRESETS, Camera, HexPrism, finish, new_figure, render_crystal

OUT = Path(__file__).resolve().parent.parent / "img" / "crystal03.png"
WIDTH, HEIGHT, DPI = 1956, 1279, 200  # 不低于旧图分辨率


def main() -> None:
    crystal = HexPrism(a=1.0, h=1.7)
    # 视角：面 1/3/4/8 可见、7 掠过；roll 让 c 轴在画面里向右上倾斜（旧图观感）
    camera = Camera(azimuth=-15, elevation=30, roll=60)
    preset = PRESETS["ice_filled"]

    fig, ax = new_figure(WIDTH, HEIGHT, DPI, preset)
    render_crystal(ax, crystal, camera=camera, preset=preset, face_numbers=True)
    finish(ax, (-2.6, 2.6), (-1.7, 1.7))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
