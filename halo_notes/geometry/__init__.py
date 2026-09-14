"""系列级共享几何：凸多面体本体（顶点 / 面 / 面编号 / 外法向 / 刚体变换 / 镜像 / 射线求交）、
六方柱 :class:`HexPrism` 与六方锥 :class:`Pyramid` 两种冰晶，以及只依赖面序列的光路展开
:func:`unfold_faces` / :func:`fold_matrix`。

这里是几何的**单一权威**：:mod:`halo_notes.draw` 的渲染、光路枚举器、signature 分类都从这里取几何，
:mod:`halo_notes.draw.geometry` 只是兼容 shim（原样 re-export），不再承载实现。
"""

from .core import (BASAL_BOTTOM, BASAL_TOP, PRISM_FACES, Face, HexPrism, Polyhedron, perp_basis, rotation,
                   rotation_between, rotation_from_frames, unit)

__all__ = [
    "BASAL_BOTTOM", "BASAL_TOP", "Face", "HexPrism", "PRISM_FACES", "Polyhedron",
    "perp_basis", "rotation", "rotation_between", "rotation_from_frames", "unit",
]
