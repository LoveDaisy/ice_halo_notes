# 产出 ../img/tricker_arc_cone_plot_1200.jpg：3.5 的球面 + 特里克尔弧，再叠一个圆锥面——锥顶在球面上的反日点
# ŝ_a = (−cos Σ, 0, sin Σ)，轴竖直（沿 z），半顶角 30°。正文第 117–138 行：r̂' − ŝ_a = A(α)·(½ sin α, −½ cos α, √3/2)，
# 括号里的向量模长为 1、z 分量固定 √3/2 ⇒ 它与 z 轴夹角恒为 arccos(√3/2) = 30°，与 α 无关；系数 A(α) 只改长度、可正可负
# ⇒ 曲线落在以 ŝ_a 为顶、轴竖直、半顶角 30° 的**双叶**圆锥面上（A>0 在上叶、A<0 在下叶），特里克尔弧 = 该锥面 ∩ 单位球。
# 锥面只画一个扇区（旧 nb：方位角 −30°…170°，缺口朝观察者，弧不被遮住），穿过球面处按"球不透明"裁掉球内的网格。
# 重制 3.6 旧图 img/legacy/tricker_arc_cone_plot_1200.jpg。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from _tricker_arc import (ALPHA, CURVE, PRESET, SPHERE, SUN_ELEVATION_DEG, anthelic_point,  # noqa: F401
                          draw_sphere_and_arc, limits, make_camera, tricker_arc)
from halo_notes.draw import finish, new_figure, render_cone

OUT = Path(__file__).resolve().parent.parent / "img" / "tricker_arc_cone_plot_1200.jpg"
WIDTH, HEIGHT, DPI = 1200, 1200, 200  # = 旧图分辨率

PATHS: dict = {}
APEX = anthelic_point()
CONE_AXIS = np.array([0.0, 0.0, 1.0])
HALF_ANGLE_DEG = 30.0
PHI_RANGE, PHI_FROM = (-30.0, 170.0), (1.0, 0.0, 0.0)   # 旧 nb 的扇区：从 +x 起量方位角
# 两叶各延伸到与球面交线之外 cone_extend 倍：交线上各点离锥顶的距离就是 |A(α)|，按符号分叶取最大值
_A = (CURVE - APEX) @ np.array([0.0, 0.0, 2 / np.sqrt(3)])     # A(α) = (r̂' − ŝ_a)·ẑ / (√3/2)
LENGTH_UP = float(_A[_A > 0].max()) * PRESET.geom.cone_extend
LENGTH_DOWN = float(-_A[_A < 0].min()) * PRESET.geom.cone_extend


def main() -> None:
    camera = make_camera()
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    draw_sphere_and_arc(ax, camera)
    leaves = render_cone(ax, APEX, CONE_AXIS, HALF_ANGLE_DEG, camera=camera, preset=PRESET, length_up=LENGTH_UP,
                         length_down=LENGTH_DOWN, phi_range=PHI_RANGE, phi_from=PHI_FROM, n_phi=40, n_r=10,
                         clip_inside=SPHERE)
    finish(ax, *limits(camera, WIDTH, HEIGHT, [g.reshape(-1, 3) for g in leaves]))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
