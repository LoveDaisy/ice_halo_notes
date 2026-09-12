# 产出 ../img/c6.png：旋转对称群 C6——2×3 网格 $R^c_0=I$ … $R^c_5$：每格一个淡参考六边形（原位、向左上错开）+
# 转过 k·60° 的六边形（彩色编号随晶体转、字形随之转动）+ 从参考方向到目标方向的弧箭头（角度 = k·60°）。
# 重制 1.3 旧图 img/legacy/c6.png。读者要看出：编号 k 转到原来 k+1 的位置（3–8 循环），颜色让人追踪同一个面。
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from halo_notes.draw import (FACE_COLORS, PRESETS, CrossSection, draw_rotation_arc, face_permutation, finish,
                             multi_panel, render_section, rotate)

OUT = Path(__file__).resolve().parent.parent / "img" / "c6.png"
WIDTH, HEIGHT, DPI = 2400, 1982, 200  # = 旧图分辨率

PATHS: dict = {}   # 本图没有光路，只有对称操作；声明空字典让 test_figures 知道这是有意为之
PRESET = PRESETS["ice_filled"].replace(
    style_map=PRESETS["ice_filled"].style_map.replace(face_number_colors=FACE_COLORS))
REFERENCE_OFFSET = (-0.25, 0.40)   # 参考幽灵向左上错开（旧图），避免与主图重叠
SPOKE_DEG = -30.0                  # 参考方向：指向参考六边形右下顶点（旧图）
XLIM, YLIM = (-1.2, 1.2), (-1.12, 1.52)


def main() -> None:
    fig, axes = multi_panel(2, 3, WIDTH, HEIGHT, DPI, preset=PRESET,
                            titles=["$R^c_0 = I$"] + [f"$R^c_{k}$" for k in range(1, 6)])
    base = CrossSection(1.0)
    reference = base.transformed(translation=REFERENCE_OFFSET)
    for k, ax in enumerate(a for row in axes for a in row):
        turned = rotate(base, k)
        # 机械核验"编号 j 转到原来 j+k 的位置"：原来 j+k 位置上现在站着 j（3–8 循环）
        perm = face_permutation(base, turned)
        assert all(perm[(j + k - 3) % 6 + 3] == j for j in range(3, 9)), perm
        render_section(ax, reference, preset=PRESET, face_numbers=True, variant="reference")
        render_section(ax, turned, preset=PRESET, face_numbers=True)
        draw_rotation_arc(ax, reference.centroid(), 0.5, SPOKE_DEG, SPOKE_DEG + 60 * k,
                          preset=PRESET, spokes=1.0)
        finish(ax, XLIM, YLIM)
    fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
