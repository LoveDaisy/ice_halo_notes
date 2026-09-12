# 产出 ../img/d6_f.png：D6 群的翻转操作——2×3 网格 $F^f_3, F^f_4, F^f_5$（轴过面心）/ $F^d_{3,4}, F^d_{4,5}, F^d_{5,6}$
#（轴过顶点）：每格淡参考六边形 + 翻转后的六边形（彩色编号镜像）+ 翻转轴点划线 + 轴一端的双向箭头。
# 重制 1.6 旧图 img/legacy/d6_f.png。读者要看出：上排轴过面心、下排轴过顶点；翻转后编号字形镜像；
# 被轴穿过的面 / 顶点位置不变，其余成对互换。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (FACE_COLORS, PRESETS, CrossSection, FlipAxis, draw_flip_axis, face_permutation,
                             finish, flip, multi_panel, render_section)

OUT = Path(__file__).resolve().parent.parent / "img" / "d6_f.png"
WIDTH, HEIGHT, DPI = 2898, 2542, 200  # = 旧图分辨率

PATHS: dict = {}   # 本图没有光路，只有对称操作；声明空字典让 test_figures 知道这是有意为之
PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(face_number_colors=FACE_COLORS))
AXES = [FlipAxis.face(3), FlipAxis.face(4), FlipAxis.face(5),
        FlipAxis.vertex(3, 4), FlipAxis.vertex(4, 5), FlipAxis.vertex(5, 6)]
REFERENCE_OFFSET = (-0.25, 0.40)   # 参考幽灵向左上错开（旧图）；翻转轴画在参考幽灵上
XLIM, YLIM = (-1.5, 1.5), (-1.12, 1.95)


def main() -> None:
    fig, axes = multi_panel(2, 3, WIDTH, HEIGHT, DPI, preset=PRESET, titles=[a.label for a in AXES],
                            title_frac=0.12)
    base = CrossSection(1.0)
    reference = base.transformed(translation=REFERENCE_OFFSET)
    for axis, ax in zip(AXES, (a for row in axes for a in row)):
        flipped = flip(base, axis)
        perm = face_permutation(base, flipped)
        if axis.kind == "face":   # 被轴穿过的面及其对面不动
            k = axis.numbers[0]
            assert perm[k] == k and perm[(k + 3 - 3) % 6 + 3] == (k + 3 - 3) % 6 + 3, perm
        else:                     # 轴过顶点：两侧的边互换，顶点不动
            k, j = axis.numbers
            assert perm[k] == j and perm[j] == k, perm
            assert np.allclose(flipped.vertex_between(k, j), base.vertex_between(k, j))
        assert np.linalg.det(flipped.frame) < 0   # 编号字形镜像
        render_section(ax, reference, preset=PRESET, face_numbers=True, variant="reference")
        render_section(ax, flipped, preset=PRESET, face_numbers=True)
        draw_flip_axis(ax, reference.centroid(), axis.direction(reference), 1.55, preset=PRESET,
                       arrow_at=1.35, arrow_half=0.32)
        finish(ax, XLIM, YLIM)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
