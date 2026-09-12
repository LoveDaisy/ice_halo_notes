# 产出 ../img/trace.jpg：两种追踪光线的方式——左：蒙特卡洛，光线在每个界面处按反射 / 折射光强为概率随机选一支继续
#（未选中的画成灰虚线）；右：追踪并记录所有分支。介质是两条不平行界面夹着的平板（浅蓝填充、波浪端）。
# 重制 6.2 旧图 img/legacy/trace.jpg。读者要看出：两种策略的区别；每个界面处反射角 = 入射角、折射按 Snell（n=1.31），
# 角度由 schematic.split_tree 用 trace / reflect 算出，不手画。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, annotate_2d, draw_raypath_2d, finish, new_figure, render_medium,
                             split_tree, two_face_medium)
from halo_notes.draw.schematic import ENTRY_FACE, EXIT_FACE
from halo_notes.draw.style import LineStyle

OUT = Path(__file__).resolve().parent.parent / "img" / "trace.jpg"
WIDTH, HEIGHT, DPI = 3421, 1778, 200  # = 旧图分辨率

PATHS = {"through": [ENTRY_FACE, EXIT_FACE], "external": [ENTRY_FACE]}   # 内反射支的面序列也是 [1, 2]
PRESET = PRESETS["default"].replace(
    geom=PRESETS["default"].geom.replace(arrow2d_length=0.32, arrow2d_width=0.24))   # 旧图的大箭头
RAY = LineStyle("ink", linewidth=2.6)
DISCARDED = "ray2d_discarded"
# 入射角（与上界面法向的夹角）。旧图手画的 45° 入射配不出它那条内部折线；且两界面夹角约 15.7°，内部光线到下界面的
# 入射角 = 折射角 + 15.7°，超过 45° 左右就全反射（trace 会直接报错）——所以取 38°，下界面处约 44°，仍能折出
INCIDENCE_DEG = 38.0
COLS = (-5.6, 5.6)     # 两栏中心


def plate(offset_x: float):
    """两条不平行界面夹的平板：上界面向右上微倾、下界面向右下微倾（旧图），横向 ±2.25、中心厚 4.8。"""
    x0, x1 = offset_x - 2.25, offset_x + 2.25
    return two_face_medium(entry=([x0, 2.4 - 0.128 * 2.25], [x1, 2.4 + 0.128 * 2.25]),
                           exit=([x1, -2.4 - 0.147 * 2.25], [x0, -2.4 + 0.147 * 2.25]))


def tree(medium, entry_x: float):
    """射向上界面 x = entry_x 处、入射角 INCIDENCE_DEG（从左上方来）的分光树。"""
    a, b = medium.face_vertices(medium.face(ENTRY_FACE))
    t = (entry_x - a[0]) / (b[0] - a[0])
    hit = a + t * (b - a)
    n = medium.normal(medium.face(ENTRY_FACE))
    th = np.deg2rad(INCIDENCE_DEG)
    d = -np.cos(th) * n + np.sin(th) * np.array([n[1], -n[0]])   # 朝 +x 侧偏
    assert d[0] > 0 and d[1] < 0
    return split_tree(medium, hit - d * 3.0, d, tail=3.3, head=2.3, inside_length=2.6)


def main() -> None:
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    for k, cx in enumerate(COLS):
        medium = plate(cx)
        render_medium(ax, medium, preset=PRESET, closure="wavy", fill="plate_fill", edge="plate_edge",
                      amplitude=0.16)
        t = tree(medium, cx - 1.4)
        monte_carlo = k == 0
        draw_raypath_2d(ax, t.transmitted, preset=PRESET, semantic=RAY,
                        exit=DISCARDED if monte_carlo else None, arrows=[(0, 1.0), (1, 1.0), (2, 1.0)])
        draw_raypath_2d(ax, t.reflected_outside, preset=PRESET, semantic=RAY,
                        exit=DISCARDED if monte_carlo else None, arrows=[(1, 1.0)])
        draw_raypath_2d(ax, t.reflected_inside, preset=PRESET, semantic=RAY, arrows=[(1, 1.0)])

        def mid(path, i):
            p0, p1 = path.points[i], path.points[i + 1]
            return (p0 + p1) / 2

        if monte_carlo:
            annotate_2d(ax, "反射光线", mid(t.reflected_outside, 1) + [0.45, -0.3], preset=PRESET)
            annotate_2d(ax, "折射光线", mid(t.transmitted, 1) + [0.35, 0.1], preset=PRESET)
            annotate_2d(ax, "以两者光强度为概率\n随机选择一条继续计算", t.transmitted.points[1] + [2.3, -0.3],
                        preset=PRESET, va="top")
        else:
            label = np.array([cx + 2.55, 1.2])
            targets = [mid(t.reflected_outside, 1), mid(t.transmitted, 1) + [0.2, 0.0],
                       mid(t.reflected_inside, 1), mid(t.transmitted, 2)]
            annotate_2d(ax, "追踪并记录\n所有的光线", label, preset=PRESET, va="center", leader_to=targets)
    half_h = HEIGHT / 2 / 171.0
    finish(ax, (-WIDTH / 2 / 171.0, WIDTH / 2 / 171.0), (-half_h, half_h))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 95})
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
