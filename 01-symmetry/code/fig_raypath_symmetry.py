# 产出 ../img/raypath_symmetry.png：光路的对称性——同一条光线不动，晶体转 60° / 沿对角线翻转后，
# 编号跟着晶体走，3-5 光路读作 4-6、4-6 读作 3-7。重制 1.2 旧图 img/legacy/raypath_symmetry.png
#（psd 里的箭头、文字、⟺ 全部代码化，psd 作废）。
# 读者要看出：下排三张图光线完全一样（同一组坐标），动的只是晶体和编号——旋转后编号字形随之转动、
# 翻转后字形镜像；截面光路是真实 Snell 折射（面 3 入、面 5 出各有折点）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (PRESETS, CrossSection, FlipAxis, annotate_2d, draw_flip_axis, draw_rotation_arc,
                             face_sequence, finish, flip, new_figure, reflection2d, render_section, rotate,
                             rotation2d, solve_raypath_2d)
from halo_notes.draw.raypath import N_ICE

OUT = Path(__file__).resolve().parent.parent / "img" / "raypath_symmetry.png"
WIDTH, HEIGHT, DPI = 3600, 2578, 200  # = 旧图分辨率

PATHS = {"3-5": [3, 5], "4-6": [4, 6], "3-7": [3, 7]}
PRESET = PRESETS["ice_filled"]
AXIS = FlipAxis.vertex(3, 4)   # 旧图点划线：过 3|4 与 6|7 之间的顶点（$F^d_{3,4}$）

# 版面（截面单位 a=1）：上排 y=+2.08、下排 y=−1.32，三列 x=−3 / 0 / +3（旧图量得）
TOP, BOTTOM = 2.08, -1.32
COLS = (-3.0, 0.0, 3.0)


def min_deviation_direction(section: CrossSection, entry: int, exit: int) -> np.ndarray:
    """对称光路（最小偏向）的入射方向：晶体内的光线与入射面、出射面的内法向夹角相等。"""
    n_in, n_out = section.normal(section.face(entry)), section.normal(section.face(exit))
    inside = -n_in + n_out               # 内部方向：从入射面内法向转向出射面外法向的角平分线方向
    inside /= np.linalg.norm(inside)
    cos_t = -(n_in @ inside)             # 折射角
    sin_i = N_ICE * np.sqrt(1 - cos_t * cos_t)
    if sin_i > 1:
        raise ValueError("no symmetric path: refraction angle exceeds the critical angle")
    ang = np.degrees(np.arcsin(sin_i))
    # 入射方向 = 内法向（-n_in）朝 inside 那一侧转过入射角
    sign = 1.0 if (-n_in[0] * inside[1] + n_in[1] * inside[0]) > 0 else -1.0
    return rotation2d(sign * ang) @ (-n_in)


def main() -> None:
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    base = CrossSection(1.0)
    tail, head = 1.0, 1.0   # 旧图晶体外的光线约一个边长

    # 下排的那条光线 R：从面 4 中点对称入射、面 6 中点出射（旧图量得）
    d = min_deviation_direction(base, 4, 6)
    mid4 = base.midpoint(base.face(4))

    def solve(section, faces, point, direction):
        path = solve_raypath_2d(section, faces, prefer_point=point, prefer_direction=direction,
                                tail=tail, head=head)
        assert face_sequence(path) == faces
        return path

    def place(section, path, x, y):
        return section.transformed(translation=[x, y]), path.transformed(translation=[x, y])

    # 上左：3-5 光路 = R 整体（连同晶体）顺时针转 60° 的样子
    r = rotation2d(-60)
    top_left, p35 = place(base, solve(base, PATHS["3-5"], r @ mid4, r @ d), COLS[0], TOP)
    # 上右：3-7 光路 = R 关于对角线镜像的样子
    m = reflection2d(AXIS.direction(base))
    top_right, p37 = place(base, solve(base, PATHS["3-7"], m @ mid4, m @ d), COLS[2], TOP)
    # 下排：同一条光线 R，三个晶体——左转 60°（编号随转）、原样、沿对角线翻转（编号镜像）
    p46 = solve(base, PATHS["4-6"], mid4, d)
    turned, flipped = rotate(base, 1), flip(base, AXIS)
    p35_turned = solve(turned, PATHS["3-5"], mid4, d)    # 晶体转了，同一条光线现在从 3 进 5 出
    p37_flipped = solve(flipped, PATHS["3-7"], mid4, d)  # 晶体翻了，同一条光线现在从 3 进 7 出
    # 机械核验"光线完全不变"：三条光路逐点相同
    assert np.allclose(p35_turned.points, p46.points, atol=1e-9)
    assert np.allclose(p37_flipped.points, p46.points, atol=1e-9)
    # 上排两条确实是 R 的旋转 / 镜像
    assert np.allclose(p35.points - [COLS[0], TOP], p46.points @ r.T, atol=1e-9)
    assert np.allclose(p37.points - [COLS[2], TOP], p46.points @ m.T, atol=1e-9)

    panels = [
        (top_left, p35), (top_right, p37),
        place(turned, p35_turned, COLS[0], BOTTOM), place(base, p46, COLS[1], BOTTOM),
        place(flipped, p37_flipped, COLS[2], BOTTOM),
    ]
    for section, path in panels:
        render_section(ax, section, [path], preset=PRESET, face_numbers=True)

    # 上左：旋转弧箭头（从右上方绕到上方，逆时针）；上右：翻转轴点划线
    c = top_left.centroid()
    draw_rotation_arc(ax, c, 1.4, 0, 65, preset=PRESET)
    draw_flip_axis(ax, top_right.centroid(), AXIS.direction(top_right), 1.25, preset=PRESET)

    # 图注与 ⇓ / ⟺（psd 标注代码化）
    for x, text in ((COLS[0], "左转 60°"), (COLS[2], "沿着对角线翻转")):
        annotate_2d(ax, text, (x, TOP - 1.35), preset=PRESET, ha="center", semantic="caption")
        annotate_2d(ax, "⇓", (x, TOP - 1.95), preset=PRESET, ha="center", semantic="symbol")
    for x, text in zip(COLS, ("3-5 光路", "4-6 光路", "3-7 光路")):
        annotate_2d(ax, text, (x, BOTTOM - 1.4), preset=PRESET, ha="center", semantic="caption")
    for x in (-1.5, 1.5):
        annotate_2d(ax, "⟺", (x, BOTTOM - 1.4), preset=PRESET, ha="center", semantic="symbol")

    half_w = WIDTH / 2 / 382.0   # 旧图比例：a ≈ 382 px
    finish(ax, (-half_w, half_w), (0.38 - HEIGHT / 2 / 382.0, 0.38 + HEIGHT / 2 / 382.0))
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
