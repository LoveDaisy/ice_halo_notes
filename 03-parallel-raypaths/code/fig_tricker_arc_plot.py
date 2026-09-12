# 产出 ../img/tricker_arc_plot_1200.jpg：单位球（细黑经纬网格，只画朝向观察者的半球）上的特里克尔弧——正文第 104–110 行
# 参数方程 r̂'(α)，α 从 0 到 2π，太阳高度角 Σ = 10°（取自旧 Mathematica 脚本 plot_figures.nb）。
# 重制 3.5 旧图 img/legacy/tricker_arc_plot_1200.jpg。读者要看出：曲线闭合、在反日点 (−cos Σ, 0, sin Σ) 处自交。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from _tricker_arc import (ALPHA, CURVE, PRESET, SUN_ELEVATION_DEG, anthelic_point, draw_sphere_and_arc,  # noqa: F401
                          limits, make_camera, tricker_arc)
from halo_notes.draw import finish, new_figure

OUT = Path(__file__).resolve().parent.parent / "img" / "tricker_arc_plot_1200.jpg"
WIDTH, HEIGHT, DPI = 1200, 1200, 200  # = 旧图分辨率

PATHS: dict = {}   # 本图没有光路（弧是出射方向的轨迹，不是一条光线）


def main() -> None:
    camera = make_camera()
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    draw_sphere_and_arc(ax, camera)
    finish(ax, *limits(camera, WIDTH, HEIGHT))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
