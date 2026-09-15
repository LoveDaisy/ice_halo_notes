"""兼容 shim：几何本体已迁移至 :mod:`halo_notes.geometry`（单一权威），本模块只原样 re-export
同名符号，让 ``halo_notes.draw.geometry`` / ``from .geometry import ...`` 两条旧 import 路径继续可用。
**请勿在此新增实现**——新逻辑一律写到 ``halo_notes/geometry/``，否则会重新制造两份几何实现。
"""

from halo_notes.geometry import (BASAL_BOTTOM, BASAL_TOP, PRISM_FACES, Face, HexPrism, Polyhedron, perp_basis,
                                 rotation, rotation_between, rotation_from_frames, unit)

__all__ = [
    "BASAL_BOTTOM", "BASAL_TOP", "Face", "HexPrism", "PRISM_FACES", "Polyhedron",
    "perp_basis", "rotation", "rotation_between", "rotation_from_frames", "unit",
]
