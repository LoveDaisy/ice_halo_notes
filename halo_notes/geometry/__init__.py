"""系列级共享几何：凸多面体本体（顶点 / 面 / 面编号 / 外法向 / 刚体变换 / 镜像 / 射线求交）、
六方柱 :class:`HexPrism` 与六方锥 :class:`Pyramid` 两种冰晶，以及只依赖面序列的光路展开
:func:`unfold_faces` / :func:`fold_matrix`。

这里是几何的**单一权威**：:mod:`halo_notes.draw` 的渲染、光路枚举器、signature 分类都从这里取几何，
:mod:`halo_notes.draw.geometry` 只是兼容 shim（原样 re-export），不再承载实现。
"""

from .core import (BASAL_BOTTOM, BASAL_TOP, PRISM_FACES, Face, HexPrism, Polyhedron, perp_basis, rotation,
                   rotation_between, rotation_from_frames, unit)
from .pyramid import C_OVER_A_ICE, LOWER_PYRAMID_FACES, UPPER_PYRAMID_FACES, Pyramid, pyramid_face_angle
from .unfold import fold_matrix, unfold_faces

__all__ = [
    "BASAL_BOTTOM", "BASAL_TOP", "C_OVER_A_ICE", "Face", "HexPrism", "LOWER_PYRAMID_FACES", "PRISM_FACES",
    "Polyhedron", "Pyramid", "UPPER_PYRAMID_FACES",
    "fold_matrix", "perp_basis", "pyramid_face_angle", "rotation", "rotation_between", "rotation_from_frames",
    "unfold_faces", "unit",
]
