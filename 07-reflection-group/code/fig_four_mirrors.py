# 产出 ../img/four_mirrors.png：8 个面只有 4 面镜（正文第 44 行）。主图：六棱柱俯视截面（面编号 3–8，ch3 标准坐标：面 3 法向沿 +x），
# 三条反射轴穿过中心（$S_{90°}$ / $S_{30°}$ / $S_{-30°}$，点划线同 1.6 的翻转轴），每条轴标出它代表的**一对**相对侧面
#（3/6、5/8、4/7：法向相反的两面是同一面镜），三轴互夹 60°（标一个 60° 角）；右侧 inset：柱晶（h/a=2）的**侧视**——正交相机
# 从 −y 方向看（沿 +y 看去），可见面 7 / 8 及二者之间的棱线（编号贴在面上，由 `visible_faces` 推导、不硬编码），面 6 / 3 此时
# 是左右两条边缘线（引线标注），面 1 / 2 在上下；一条水平点划线 = 底面镜，与 c 轴垂直。
# 读者要看出：相对侧面共用一条反射轴；三条侧面镜轴互夹 60°；底面镜单独一面。
# 轴与面对的对应不手填：$S_\phi$ 的不变线 = 该面法向方位角 + 90°，落在过顶点的轴上（plan 附注推导；test_figures 用
# face_permutation 与 reflection_group 矩阵互相核验）。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (FACE_COLORS, PRESETS, Camera, CrossSection, FlipAxis, HexPrism, annotate, annotate_2d,
                             draw_flip_axis, face_permutation, finish, flip, new_figure, render_crystal, render_section)
from halo_notes.draw.projection import visible_faces
from halo_notes.draw.scene2d import Z_TEXT
from halo_notes.math import reflection_group as rg

OUT = Path(__file__).resolve().parent.parent / "img" / "four_mirrors.png"
WIDTH, HEIGHT, DPI = 2800, 1700, 200

PATHS: dict = {}   # 本图没有光路，只有镜面 / 反射轴
PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(face_number_colors=FACE_COLORS))
SECTION = CrossSection(1.0)
# 三面侧面镜：(xy 符号, 代表的相对面对, 不变线所在的顶点轴)。不变线方位角 = 面法向 + 90°：面 3（0°）→ 90° = 顶点 4|5 的轴，
# 面 5（120°）→ 210° ≡ 30° = 顶点 3|4 的轴，面 4（60°）→ 150° = 顶点 5|6 的轴
MIRRORS = [("s90", (3, 6), FlipAxis.vertex(4, 5)),
           ("s30", (5, 8), FlipAxis.vertex(3, 4)),
           ("s-30", (4, 7), FlipAxis.vertex(5, 6))]
AXIS_HALF, LABEL_AT = 1.6, 1.95        # 轴的半长、标签（符号 + 面对）沿轴的位置（轴的上半端）
ANGLE_ARC_R = 1.3                      # 60° 角标的半径（六边形之外、标签之内）
INSET_BOX = (0.70, 0.16, 0.27, 0.64)   # 右侧 inset（figure 比例）
XLIM, YLIM = (-2.5, 4.5), (-1.9, 2.35)
# inset：柱晶 h/a=2，正交相机从 −y 方向看（view_dir = (0, −1, 0)，画面 x = 世界 x、画面 y = c 轴）。可见面由几何推导：
# 侧面法向 y 分量 < 0 的面 7（240°）/ 8（300°）朝向观察者，面 3 / 6（法向 ±x）与面 1 / 2（法向 ±z）恰好侧对视线。
# h/a 取 3：这个视线下柱宽 = √3·a，h/a=2 画出来高宽比只有 1.15、近乎正方形，要「明显是柱」得再高一档（R1-7 的意图）
INSET_H_RATIO = 3.0
INSET_CRYSTAL = HexPrism(a=1.0, h=INSET_H_RATIO)
INSET_PRESET = PRESET.replace(geom=PRESET.geom.replace(face_number_height=0.42))
INSET_CAMERA = Camera(azimuth=-90.0, elevation=0.0, projection="orthographic")
INSET_VISIBLE = [f.number for f in visible_faces(INSET_CRYSTAL, INSET_CAMERA)]
assert INSET_VISIBLE == [7, 8], INSET_VISIBLE
INSET_LIMITS = ((-2.0, 2.0), (-2.35, 2.95))


def main() -> None:
    fig, ax = new_figure(WIDTH, HEIGHT, DPI, PRESET)
    c = SECTION.centroid()
    render_section(ax, SECTION, preset=PRESET, face_numbers=True)
    for xy, (a, b), axis in MIRRORS:
        d = axis.direction(SECTION)
        # 机械自检：轴 ⟂ 这对面的法向，且沿此轴翻转的面置换 == reflection_group 矩阵对面法向的作用
        for k in (a, b):
            assert abs(d @ SECTION.normal(SECTION.face(k))) < 1e-9, (xy, k)
        perm = face_permutation(SECTION, flip(SECTION, axis))
        M = rg.XY_MATRIX[xy]
        for k in range(3, 9):
            target = np.argmin([np.linalg.norm(M @ rg.NORMALS[k] - rg.NORMALS[j]) for j in range(3, 9)]) + 3
            assert perm[target] == k, (xy, k, perm)
        draw_flip_axis(ax, c, d, AXIS_HALF, preset=PRESET)
        annotate_2d(ax, f"{rg.XY_LATEX[xy]}\n面 {a} / {b}", c + d * LABEL_AT, preset=PRESET, ha="center",
                    va="center", math_fontfamily="cm", linespacing=1.4)
    # 相邻两轴的 60°：从 30° 轴到 90° 轴
    th = np.deg2rad(np.linspace(30.0, 90.0, 32))
    ax.plot(c[0] + ANGLE_ARC_R * np.cos(th), c[1] + ANGLE_ARC_R * np.sin(th), zorder=Z_TEXT,
            **PRESET.line_kwargs("angle_mark"))
    mid = np.deg2rad(60.0)
    annotate_2d(ax, "60°", c + (ANGLE_ARC_R - 0.24) * np.array([np.cos(mid), np.sin(mid)]), preset=PRESET,
                ha="center", va="center")
    finish(ax, XLIM, YLIM)

    # inset：侧视（3D 正交）+ 底面镜
    ins = fig.add_axes(INSET_BOX)
    cam, cr = INSET_CAMERA, INSET_CRYSTAL
    render_crystal(ins, cr, camera=cam, preset=INSET_PRESET, face_numbers=INSET_VISIBLE)
    for k, dx in ((6, -0.6), (3, 0.6)):        # 边缘线上的面：引线从文字指到该面质心
        annotate(ins, f"面 {k}", cr.centroid(cr.face(k)), (dx, 0.7), camera=cam, preset=PRESET, ha="center",
                 va="bottom", arrow=True)
    annotate(ins, "面 1", cr.centroid(cr.face(1)), (-0.15, 0.08), camera=cam, preset=PRESET, ha="right", va="bottom")
    annotate(ins, "面 2", cr.centroid(cr.face(2)), (0.0, -0.1), camera=cam, preset=PRESET, ha="center", va="top")
    draw_flip_axis(ins, cam.project_xy(cr.centroid())[0], (1.0, 0.0), 1.75, preset=PRESET)
    c_top = cam.project_xy(cr.centroid(cr.face(1)))[0]
    ins.annotate("", xy=(0.0, c_top[1] + 0.55), xytext=(0.0, 0.0), zorder=Z_TEXT,
                 arrowprops=dict(arrowstyle="-|>", color=PRESET.palette["ink"], linewidth=1.0))
    annotate_2d(ins, "$c$", (0.12, c_top[1] + 0.5), preset=PRESET, ha="left", va="center", semantic="axis_label")
    annotate_2d(ins, "底面镜 ⊥ c 轴", (0.0, -c_top[1] - 0.55), preset=PRESET, ha="center", va="top")
    annotate_2d(ins, "侧视（沿 +y 看去）", (-1.95, 2.9), preset=PRESET, ha="left", va="top", semantic="caption")
    finish(ins, *INSET_LIMITS)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
